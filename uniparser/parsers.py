# -*- coding: utf-8 -*-
# pip install jsonpath_ng

from abc import ABC, abstractmethod
from json import loads
from re import compile as re_compile
# from typing import List
from traceback import print_exc
from warnings import filterwarnings

from bs4 import BeautifulSoup, Tag
from jsonpath_ng.ext import parse as jp_parse
from objectpath import Tree as OP_Tree
from inspect import isgenerator

filterwarnings('ignore', message='^No parser was')

__all__ = ['BaseParser', 'Rule', 'Tag', 'CSSParser', 'RegexParser']


def return_self(self, *args, **kwargs):
    return self


class BaseParser(ABC):
    """Sub class of BaseParser should have these features:
    1. class variable `name`
    2. `_parse` method
    3. use lazy import, maybe
    """
    test_url = ''
    doc_url = ''

    @abstractmethod
    def _parse(self, input_object, param, value):
        pass

    def parse(self, input_object, param, value):
        try:
            if isinstance(input_object, list):
                return [
                    self._parse(item, param, value) for item in input_object
                ]
            else:
                return self._parse(input_object, param, value)
        except Exception:
            print_exc()
            return None


class Rule(object):
    __slots__ = ()


class CSSParser(BaseParser):
    """CSS selector parser, requires `bs4` and `lxml`(optional).

    Parse the input object with standard css selector, features from `BeautifulSoup`.

        :param input_object: input object, could be Tag or str.
        :type input_object: [Tag, str]
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
        :rtype: List[Union[str, Tag]]
    """
    name = 'css'
    doc_url = 'https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Selectors'
    operations = {
        '@attr': lambda element: element.get(),
        '$text': lambda element: element.text,
        '$innerHTML': lambda element: element.decode_contents(),
        '$outerHTML': lambda element: str(element),
        '$self': return_self,
    }

    def _parse(self, input_object, param, value):
        result = []
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
    """Parse the input object with standard regex, features from `re`.

        :param input_object: input object, could be str.
        :type input_object: [str]
        :param param: css selector path
        :type param: [str]
        :param value: operation for each item of result
        :type value: [str]

            @attribute: return element.get(xxx)

            $text: return element.text

            $innerHTML: return element.decode_contents()

            $outerHTML: return str(element)

            $self: return element

        :return: list of str
        :rtype: List[Union[str]]
    """
    name = 're'
    test_url = 'https://regex101.com/'
    doc_url = 'https://docs.microsoft.com/en-us/dotnet/standard/base-types/regular-expression-language-quick-reference'

    def _parse(self, input_object, param, value):
        assert isinstance(input_object,
                          str), ValueError(r'input_object type should be str')
        assert re_compile(r'^@|^\$\d+').match(value) or not value, ValueError(
            r'args1 should match ^@|^\$\d+')
        com = re_compile(param)
        if not value:
            return com.findall(input_object)
        prefix, arg = value[0], value[1:]
        if prefix == '@':
            result = com.sub(arg, input_object)
            return result
        elif prefix == '$':
            result = com.finditer(input_object)
            return [match.group(int(arg)) for match in result]


class JSONPathParser(BaseParser):
    """JSONPath parser, requires `jsonpath_ng` lib.

        :param input_object: input object, could be str, list, dict.
        :type input_object: [str, list, dict]
        :param param: JSON path
        :type param: [str]
        :param value: attribute of find result, default to '' as '$value'
        :type value: [str, None]
        :return: list of str
        :rtype: List[Union[str]]
    """
    name = 'jsonpath'
    doc_url = 'https://github.com/h2non/jsonpath-ng'
    test_url = 'https://jsonpath.com/'

    def _parse(self, input_object, param, value=''):
        if isinstance(input_object, str):
            input_object = loads(input_object)
        value = value or '$value'
        attr_name = value[1:]
        jsonpath_expr = jp_parse(param)
        result = [
            getattr(match, attr_name, match.value)
            for match in jsonpath_expr.find(input_object)
        ]
        return result


class ObjectPathParser(BaseParser):
    """ObjectPath parser, requires `objectpath` lib.

        :param input_object: input object, could be str, list, dict.
        :type input_object: [str, list, dict]
        :param param: JSON path
        :type param: [str]
        :param value: attribute of find result
        :type value: [str, None]
    """
    name = 'objectpath'
    doc_url = 'http://github.com/adriank/ObjectPath'
    test_url = 'http://objectpath.org/'

    def _parse(self, input_object, param, value=''):
        if isinstance(input_object, str):
            input_object = loads(input_object)
        tree = OP_Tree(input_object)
        result = tree.execute(param)
        if isgenerator(result):
            result = list(result)
        return result


# def parse_with_udf(scode):
#     exec(scode)
#     tmp = locals().get('parse')
#     if not tmp:
#         raise ValueError('UDF format error, snippet should be one function named `parse`')
#     return tmp(1)


class Uniparser(object):

    def __init__(self):
        self._prepare_default_parsers()
        self._prepare_custom_parsers()

    def parse(self, source, rule):
        assert isinstance(rule, Rule)

    def _prepare_default_parsers(self):
        self.css = CSSParser()
        self.re = RegexParser()
        self.jsonpath = JSONPathParser()
        self.objectpath = ObjectPathParser()

    def _prepare_custom_parsers(self):
        for parser in BaseParser.__subclasses__():
            if parser.name not in self.__dict__:
                self.__dict__[parser.name] = parser()
