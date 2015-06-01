import logging
from cssselect import HTMLTranslator, SelectorError
from functools import lru_cache


class SelectorException(RuntimeError):
    def __init__(self, selector):
        self.selector = selector

translator = HTMLTranslator()

@lru_cache()
def xpath(pattern):
    return translator.css_to_xpath(pattern)

logger = logging.getLogger("selector")

class Selector(object):
    def __init__(self, document):
        self.document = document
        self.translator = HTMLTranslator()

    def find(self, pattern):
        expression = xpath(pattern)
        results = [Selector(d) for d in self.document.xpath(expression)]
        if len(results) == 0:
            logger.warning("Selector {0} found 0 results".format(pattern))
        return results

    def get(self, pattern):
        expression = xpath(pattern)
        results = self.document.xpath(expression)
        try:
            return Selector(results[0])
        except IndexError as e:
            raise SelectorException(pattern) from e

    def has_class(self, cls):
        return cls in self.attr.get("class", "").split(" ")

    @property
    def attr(self):
        return dict(self.document.items())

    @property
    def text(self):
        return self.document.text_content()

    @property
    def parent(self):
        return Selector(self.document.getparent())