from .requester import Requester
from .processors.unique import UniqueProcessor
from .lib import QueueDone
from .scraper import Scraper
import asyncio
import logging
import time

logger = logging.getLogger("pipeline")

PIPELINE_IDX = 0

class Pipeline(object):
    def __init__(self, name=""):
        global PIPELINE_IDX

        self.processes = []
        self.plugins = []
        self.input = None
        self.output_func = lambda x: None
        self.prepend_host = ""

        self.error_contents = ""
        self.not_found_contents = ""

        self.requester = None
        self.parent = None
        self.logger = logging.getLogger("pipeline-{0}".format(name or PIPELINE_IDX))
        self.processed = 0
        self.errors = {}

        PIPELINE_IDX += 1

    def __call__(self, input_queue, output_queue, requester, parent):
        self.feed(input_queue)
        self.output(output_queue)
        self.requester = requester
        self.parent = parent
        return self

    @classmethod
    def parallel(cls, *pipes):
        pass  # ToDo!

    def pipe(self, process):
        self.processes.append(process)
        return self

    def error(self, server_error="", not_found=""):
        self.error_contents = server_error
        self.not_found_contents = not_found

    def unique(self, key):
        self.processes.append(
            UniqueProcessor(key=key)
        )
        return self

    def feed(self, input):
        self.input = input
        return self

    def output(self, output_func):
        self.output_func = output_func
        return self

    def set_host(self, host):
        self.prepend_host = host
        return self

    def use(self, name):
        self.plugins.append(name)
        return self

    @asyncio.coroutine
    def start(self):
        start = time.time()
        logger.info("Starting pipeline")
        requester = self.requester or Requester(
            error_contents=self.error_contents,
            not_found_contents=self.not_found_contents
        )

        futures, processes = [], []
        if isinstance(self.input, asyncio.Queue):
            input_q = self.input
        else:
            input_q = asyncio.JoinableQueue(maxsize=10)

        process_queues = [input_q] + [asyncio.JoinableQueue(5) for _ in range(len(self.processes))]

        logger.info("Created {0} queues".format(len(process_queues)))

        for idx, process_cls in enumerate(self.processes):
            process = process_cls(process_queues[idx], process_queues[idx+1], requester, self)

            if isinstance(process, (Scraper, Pipeline)) and self.prepend_host:
                process.set_host(self.prepend_host)

            logger.info("Starting process {0}".format(process))
            processes.append(process)
            futures.append(process.start())

        if not isinstance(self.input, asyncio.Queue):
            logger.info("Using iterable input queue")

            @asyncio.coroutine
            def _input_func():
                for item in self.input:
                    yield from input_q.put(item)
                logger.info("Input queue drained")

                yield from input_q.put(QueueDone)

            futures.append(_input_func())

        @asyncio.coroutine
        def status_task():
            nonlocal process_queues
            while True:
                yield from asyncio.sleep(1)
                for p in processes:
                    print("{0:<20s}: {1:>6d}: {2}".format(p.__class__.__name__,
                                                          p.processed,
                                                          {k: v for k,v in p.errors.items() if v != 0}))
                print(" ")

        if "display" in self.plugins:
            asyncio.async(status_task())

        [asyncio.async(f) for f in futures]

        exit_queue = process_queues[-1]

        if isinstance(self.output_func, asyncio.Queue):
            output_func = self.output_func.put
        else:
            output_func = self.output_func

        while True:
            item = yield from exit_queue.get()

            if item is QueueDone:
                end = time.time()
                logger.info("Pipeline complete in {0}s".format(end - start))

                if isinstance(self.output_func, asyncio.Queue):
                    yield from self.output_func.put(QueueDone)

                return
            self.processed += 1
            if asyncio.iscoroutinefunction(output_func):
                yield from output_func(item[0])
            else:
                output_func(item[0])