import asyncio
import aiohttp
import logging
import lxml.html
import json
from .selector import Selector

logger = logging.getLogger("requester")


class RequestError(RuntimeError):
    def __init__(self, url, *args, **kwargs):
        self.url = url
        super().__init__(*args, **kwargs)


class ServerError(RequestError):
    pass


class NotFoundError(RequestError):
    pass


class HttpError(RequestError):
    def __init__(self, url, code):
        self.code = code
        super().__init__(url, "HTTP {0} encountered".format(self.code))


class Response(Selector):
    def __init__(self, response, content, node):
        self.response = response
        self.is_json = False

        try:
            self.content = json.loads(content)
            self.is_json = True
        except Exception:
            self.content = content

        super().__init__(node)

    def __getitem__(self, item):
        if self.is_json:
            return self.content[item]
        else:
            raise RuntimeError("Response is not JSON")


class Requester(object):
    def __init__(self, error_contents="", not_found_contents=""):
        self.error_contents = error_contents
        self.not_found_contents = not_found_contents

    @asyncio.coroutine
    def get(self, url):
        logger.info("Requesting {0}".format(url))
        try:
            response = yield from aiohttp.request("GET", url, allow_redirects=True)
        except Exception as e:
            logger.error("Could not retrieve {0}".format(url))
            raise

        if 500 < response.status < 599:
            raise HttpError(url, response.status)
        elif response.status == 404:
            raise NotFoundError(url)

        data = yield from response.text()

        if self.error_contents and self.error_contents in data:
            raise ServerError(url)

        if self.not_found_contents and self.not_found_contents in data:
            raise NotFoundError(url)

        node = lxml.html.fromstring(data) #yield from asyncio.get_event_loop().run_in_executor(None, lxml.html.fromstring, data)

        return Response(response, data, node)