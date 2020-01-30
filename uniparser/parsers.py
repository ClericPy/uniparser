from abc import ABC, abstractmethod
from typing import List, Union, Dict, Any
from warnings import filterwarnings

from bs4 import BeautifulSoup, Tag

filterwarnings('ignore', message='^No parser was')

__all__ = ['BaseParser', 'Rule', 'Tag', 'CSSParser', 'RegexParser']


def return_self(self, *args, **kwargs):
    return self


class BaseParser(ABC):
    """Sub class of BaseParser should have these features:
    1. class variable `name`
    2. `parse` method
    3. use lazy import, maybe
    """

    @abstractmethod
    def parse(self, input_object, method: str, param: str, value: str,
              context: Any):
        pass


class Rule(object):
    __slots__ = ()


class CSSParser(BaseParser):
    """CSS selector parser, requires bs4 and lxml.
    """
    name = 'css'
    operations = {
        '@attr': lambda element: element.get(),
        '$text': lambda element: element.text,
        '$innerHTML': lambda element: element.decode_contents(),
        '$outerHTML': lambda element: str(element),
        '$self': return_self,
    }

    def parse(self,
              input_object: Union[Tag, str],
              param: str,
              value: str,
              context=None) -> List[Union[Tag, str]]:
        """Parse the input object using css selector, features from BeautifulSoup.

        :param input_object: input object, could be Tag or str.
        :type input_object: [Tag, AnyStr]
        :param param: css selector path
        :type param: [str]
        :param value: operation for each item of result
        :type value: [str]

            @attribute: return element.get(xxx)

            $text: return element.text

            $innerHTML: return element.decode_contents()

            $outerHTML: return str(element)

            $self: return element

        :return: list of Tag / str
        :rtype: List[Union[AnyStr, Tag]]
        """
        result: List = []
        if not input_object:
            return result
        # ensure input_object is instance of BeautifulSoup
        if not isinstance(input_object, Tag):
            input_object = BeautifulSoup(input_object)
        operate = self.operations.get(value, return_self)
        if value.startswith('@'):
            result = [
                item.get(value[1:], '') for item in input_object.select(param)
            ]
        else:
            result = [operate(item) for item in input_object.select(param)]
        return result


class RegexParser(BaseParser):
    """Regex parser, requires python's re built-in lib.
    """
    name = 're'


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
    uni = Uniparser()
    uni.css.parse('<a>1</a>', 1, 1)
