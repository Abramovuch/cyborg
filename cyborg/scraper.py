import asyncio
from .lib import QueueDone
from .page import Page
from .requester import Requester, ServerError, NotFoundError, HttpError
from .selector import SelectorException

import logging
import re
from collections import defaultdict
import traceback


class BaseHandler(object):
    MAX_TASKS = 5

    def __init__(self,
                 input_queue: asyncio.JoinableQueue,
                 output_queue: asyncio.JoinableQueue,
                 requester: Requester,
                 parent):
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.logger = logging.getLogger(self.__class__.__name__)
        self.requester = requester
        self.parent = parent

        self.errors = defaultdict(int, {
            "server":0,
            "notfound":0,
            "exception":0
        })
        self.processed = 0

        self.task_semaphore = asyncio.BoundedSemaphore(self.MAX_TASKS)

    @asyncio.coroutine
    def start(self):
        while True:
            obj = yield from self.input_queue.get()

            if obj is QueueDone:
                self.logger.info("Queue done, waiting extra tasks")
                self.input_queue.task_done()
                yield from self.input_queue.join()

                yield from self.complete()
                yield from self.output(QueueDone)
                self.logger.info("Task complete: {0} processed".format(self.processed))

                total_errors = sum(self.errors.values())
                if total_errors:
                    message = ", ".join("{0}: {1}".format(key, value)
                                        for key, value in self.errors.items() if value > 0)
                    self.logger.info("Errors: {0}".format(message))

                break

            self.logger.info("Input: {0}".format(obj))
            self.processed += 1

            yield from self.task_semaphore.acquire()
            asyncio.async(self.run_single(obj)) # ToDo: don't use async as it's deprecated

    @asyncio.coroutine
    def run_single(self, obj):
        try:
            yield from self._handle_input(obj)
        except ServerError:
            self.errors["server"] += 1
        except NotFoundError:
            self.errors["notfound"] += 1
        except HttpError as ex:
            self.errors[ex.code] += 1
        except SelectorException as e:
            self.logger.exception("Selector {0} failed".format(e.selector))
        except Exception as ex:
            self.errors["exception"] += 1
            self.logger.exception("Handle input raised exception")
            #self.logger.exception(traceback.format_exc())
        finally:
            self.input_queue.task_done()
            self.logger.debug("releasing " + str(self.task_semaphore))
            self.task_semaphore.release()

    @asyncio.coroutine
    def complete(self):
        return

    @asyncio.coroutine
    def output(self, obj):
        self.logger.info("Output: {0}".format(obj))
        yield from self.output_queue.put(obj)

    @asyncio.coroutine
    def _handle_input(self, obj):
        raise NotImplementedError()

    @asyncio.coroutine
    def get(self, url):
        return (yield from self.requester.get(url))

    def trim_whitespace(self, text):
        return re.sub("\s+", " ", text)


class Processor(BaseHandler):
    @asyncio.coroutine
    def _handle_input(self, obj):
        if isinstance(obj, tuple):
            data, url = obj
        else:
            data, url = obj, None

        new_data = yield from self.process(data, url)

        yield from self.handle_response(new_data)

    @asyncio.coroutine
    def handle_response(self, new_data):
        if new_data is not None:
            if isinstance(new_data, list):
                for d, u in new_data:
                    yield from self.output((d, u))
            else:
                yield from self.output(new_data)

    @asyncio.coroutine
    def process(self, data, url):
        raise NotImplementedError()


class BatchProcessor(Processor):
    BATCH_SIZE = 10
    MAX_TASKS = 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bucket = []

    @asyncio.coroutine
    def process(self, data, url):
        self.bucket.append((data, url))
        if len(self.bucket) > self.BATCH_SIZE:
            returner = yield from self.flush()
            return returner
        else:
            return None

    @asyncio.coroutine
    def flush(self):
        if not self.bucket:
            return []

        url = self.process_batch(self.bucket)
        response = yield from self.get(url)
        returner = [d for d in self.process_response(self.bucket, response)]
        self.bucket = []
        return returner

    @asyncio.coroutine
    def complete(self):
        response = yield from self.flush()
        yield from self.handle_response(response)

    def process_batch(self, batch):
        raise NotImplementedError()

    def process_response(self, batch, response):
        raise NotImplementedError()


class Scraper(BaseHandler):
    page_format = Page("{input}")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.page = self.page_format.copy()

    def set_host(self, host):
        self.page.set_host(host)

    @asyncio.coroutine
    def _handle_input(self, obj):
        if isinstance(obj, tuple):
            data, url = obj[0], self.page.get_url(obj[1])
        else:
            data, url = {}, self.page.get_url(obj)

        response = yield from self.get(url)

        for val in self.scrape(data, response):
            new_data, next_url = val
            yield from self.output((new_data, next_url))

    def scrape(self, data, response):
        raise NotImplementedError()