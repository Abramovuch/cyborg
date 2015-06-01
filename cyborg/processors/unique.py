from ..scraper import Processor
import asyncio
import operator


def UniqueProcessor(key):
    if isinstance(key, str):
        key_func = operator.itemgetter(key)
    elif callable(key):
        key_func = key
    else:
        raise RuntimeError("Key is not a string or callable")
        
    # This is a simple implementation that uses a dictionary. Could be improved a lot.

    class _UniqueProcessor(Processor):
        def __init__(self, *args, **kwargs):
            self.seen_keys = {}
            super().__init__(*args, **kwargs)

        @asyncio.coroutine
        def process(self, data, url):
            nonlocal key_func
            key = key_func(data)
            if key in self.seen_keys:
                self.errors["duplicates"] += 1
                return None
            else:
                self.seen_keys[key] = 0
                return data, url

    return _UniqueProcessor
