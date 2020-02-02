# -*- coding: utf-8 -*-
# pip install jsonpath_ng

from abc import ABC, abstractmethod
from functools import reduce
from hashlib import md5 as _md5
from inspect import isgenerator
from json import loads
from re import compile as re_compile
from typing import List, NamedTuple, Any
from warnings import filterwarnings

from bs4 import BeautifulSoup, Tag
from jsonpath_ng.ext import parse as jp_parse
from objectpath import Tree as OP_Tree

filterwarnings('ignore', message='^No parser was')

__all__ = ['BaseParser', 'Rule', 'Tag', 'CSSParser', 'RegexParser']


def return_self(self, *args, **kwargs):
    return self


def md5(string, n=32, encoding="utf-8", skip_encode=False):
    """str(obj) -> md5_string

    :param string: string to operate.
    :param n: md5_str length.

    >>> md5(1, 10)
    '923820dcc5'
    >>> md5('test')
    '098f6bcd4621d373cade4e832627b4f6'
    """
    todo = string if skip_encode else str(string).encode(encoding)
    if n == 32:
        return _md5(todo).hexdigest()
    elif isinstance(n, (int, float)):
        return _md5(todo).hexdigest()[(32 - n) // 2:(n - 32) // 2]
    elif isinstance(n, (tuple, list)):
        return _md5(todo).hexdigest()[n[0]:n[1]]


class ParseRule(NamedTuple):
    method: str
    input_object: Any
    param: str
    value: Any


class BaseParser(ABC):
    """Sub class of BaseParser should have these features:
    1. class variable `name`
    2. `_parse` method
    3. use lazy import, maybe
    4. Each parser subclass will recursion parse list of input_object, except PythonParser (self.)
    """
    test_url = ''
    doc_url = ''
    name = 'base'
    _RECURSION_LIST = True

    @abstractmethod
    def _parse(self, input_object, param, value):
        pass

    def parse(self, input_object, param, value):
        try:
            if isinstance(input_object, list) and self._RECURSION_LIST:
                return [
                    self._parse(item, param, value) for item in input_object
                ]
            else:
                return self._parse(input_object, param, value)
        except Exception as err:
            # for traceback
            return err


class Rule(object):
    __slots__ = ('id', 'name', 'parse_rules')

    def __init__(
            self,
            name: str,
            request: dict,
            parse_rules: List,
    ):
        assert name
        self.id = md5(name)
        self.name = name
        self.parse_rules = parse_rules

    def add_parse_rule(self, parse_rule: List):
        pass


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


class XMLParser(BaseParser):
    """XML parser, requires `bs4` and `lxml`(necessary).

    Parse the input object with css selector, `BeautifulSoup` with features='xml'.

        :param input_object: input object, could be Tag or str.
        :type input_object: [Tag, str]
        :param param: css selector path
        :type param: [str]
        :param value: operation for each item of result
        :type value: [str]

            @attribute: return element.get(xxx)

            $text: return element.text

            $innerXML: return element.decode_contents()

            $outerXML: return str(element)

            $self: return element

        :return: list of Tag / str
        :rtype: List[Union[str, Tag]]
    """
    name = 'xml'
    doc_url = 'https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Selectors'
    operations = {
        '@attr': lambda element: element.get(),
        '$text': lambda element: element.text,
        '$innerXML': lambda element: element.decode_contents(),
        '$outerXML': lambda element: str(element),
        '$self': return_self,
    }

    def _parse(self, input_object, param, value):
        result = []
        if not input_object:
            return result
        # ensure input_object is instance of BeautifulSoup
        if not isinstance(input_object, Tag):
            input_object = BeautifulSoup(input_object, 'xml')
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
        :param param: standard regex
        :type param: [str]
        :param value: operation for each item of result
        :type value: [str]

            @some string: using re.sub

            $0: re.finditer and return list of the whole matched string

            $1: re.finditer, $1 means return list of group 1

            '': null str, means using re.findall method

            -: return re.split(param, input_object)

        :return: list of str
        :rtype: List[Union[str]]
    """
    name = 're'
    test_url = 'https://regex101.com/'
    doc_url = 'https://docs.microsoft.com/en-us/dotnet/standard/base-types/regular-expression-language-quick-reference'

    def _parse(self, input_object, param, value):
        assert isinstance(input_object,
                          str), ValueError(r'input_object type should be str')
        assert re_compile(r'^@|^\$\d+|^-$').match(
            value) or not value, ValueError(r'args1 should match ^@|^\$\d+')
        com = re_compile(param)
        if not value:
            return com.findall(input_object)
        prefix, arg = value[0], value[1:]
        if prefix == '@':
            return com.sub(arg, input_object)
        elif prefix == '$':
            result = com.finditer(input_object)
            return [match.group(int(arg)) for match in result]
        elif prefix == '-':
            return com.split(input_object)


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
        :param value: not to use
        :type value: [Any]
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


class PythonParser(BaseParser):
    """

        :param input_object: input object, any object.
        :type input_object: [object]
        param & value:

            1.  param: udf
                value: the python source code to be exec(value), either have the function named `parse`, or will return eval(value)
            2.  param: getitem
                value: could be [0] as index, [1:3] as slice
            3.  param: split
                value: return input_object.split(value or None)
            3.  param: join
                value: return value.join(input_object)
    """
    name = 'python'
    doc_url = 'https://docs.python.org/3/'
    _ALLOW_IMPORT = False
    # Python will be different from others, treate list as list object
    _RECURSION_LIST = False

    def _parse(self, input_object, param, value):
        param_functions = {
            'udf': self._handle_udf,
            'getitem': self._handle_getitem,
            'split': lambda input_object, param, value: input_object.split(value or None),
            'join': lambda input_object, param, value: value.join(input_object),
        }
        function = param_functions.get(param, return_self)
        return function(input_object, param, value)

    def _handle_udf(self, input_object, param, value):
        if not self._ALLOW_IMPORT and 'import' in value:
            # cb = re_compile(r'^\s*(from  )?import \w+') # not strict enough
            raise RuntimeError(
                'UDFParser._ALLOW_IMPORT is False, so source code should not has `import` strictly. If you really want it, set `UDFParser._ALLOW_IMPORT = True` manually'
            )
        if 'parse' in value and ('lambda' in value or 'def ' in value):
            exec(value)
            tmp = locals().get('parse')
            if not tmp:
                raise ValueError(
                    'UDF format error, snippet should have the function named `parse`'
                )
            return tmp(input_object)
        else:
            return eval(value)

    def _handle_getitem(self, input_object, param, value):
        value = value[1:-1]
        if ':' in value:
            # as slice
            start, stop = value.split(':', 1)
            if ':' in stop:
                stop, step = stop.split(':')
            else:
                step = None
            start = int(start) if start else None
            stop = int(stop) if stop else None
            step = int(step) if step else None
            key = slice(start, stop, step)
        else:
            # as index
            key = int(value)
        return input_object[key]


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
        self.python = PythonParser()

    def _prepare_custom_parsers(self):
        for parser in BaseParser.__subclasses__():
            if parser.name not in self.__dict__:
                self.__dict__[parser.name] = parser()
