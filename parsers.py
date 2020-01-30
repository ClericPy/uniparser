from abc import ABC, abstractmethod


class BaseParser(ABC):
    """Sub class of BaseParser should have these features:
    1. class variable `name`
    2. `parse` method
    3. maybe use lazy import
    4. 
    """

    @abstractmethod
    def parse(self, input_obj, condition, rtype):
        pass


class Rule(object):
    __slots__ = ()


class CSSParser(BaseParser):
    """CSS selector parser, requires bs4 and lxml.
    """
    name = 'css'

    def parse(self, input_obj, condition, rtype):
        pass


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


if __name__ == "__main__":
    print(Uniparser().css.__doc__)
