from .parsers import *


class Uniparser(object):

    def __init__(self):
        self._prepare_default_parsers()
        self._prepare_custom_parsers()

    def _prepare_default_parsers(self):
        self.css = CSSParser()

    def _prepare_custom_parsers(self):
        for parser in BaseParser.__subclasses__():
            if parser.name not in self.__dict__:
                self.__dict__[parser.name] = parser()
