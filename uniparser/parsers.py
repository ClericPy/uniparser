# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from hashlib import md5 as _md5
from inspect import isgenerator
from itertools import chain
from json import JSONDecodeError
from json import dumps as json_dumps
from json import loads as json_loads
from re import compile as re_compile
from time import localtime, mktime, strftime, strptime, timezone
from typing import List
from warnings import warn

from bs4 import BeautifulSoup, Tag
from jsonpath_ng.ext import parse as jp_parse
from objectpath import Tree as OP_Tree
from toml import loads as toml_loads
from yaml import full_load as yaml_full_load
from yaml import safe_load as yaml_safe_load

__all__ = [
    'BaseParser', 'ParseRule', 'CrawlerRule', 'HostRules', 'Tag', 'CSSParser',
    'XMLParser', 'RegexParser', 'JSONPathParser', 'ObjectPathParser',
    'PythonParser', 'UDFParser', 'LoaderParser'
]


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


class BaseParser(ABC):
    """Sub class of BaseParser should have these features:
    1. class variable `name`
    2. `_parse` method
    3. use lazy import, maybe
    4. Each parser subclass will recursion parse list of input_object, except PythonParser (self.)
    """
    test_url = 'https://github.com/ClericPy/uniparser'
    doc_url = 'https://github.com/ClericPy/uniparser'
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
            input_object = BeautifulSoup(input_object, 'lxml')
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
            input_object = BeautifulSoup(input_object, 'lxml-xml')
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
            input_object = json_loads(input_object)
        value = value or '$value'
        attr_name = value[1:]
        if param.startswith('JSON.'):
            param = '$%s' % param[4:]
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
            input_object = json_loads(input_object)
        if param.startswith('JSON.'):
            param = '$%s' % param[4:]
        tree = OP_Tree(input_object)
        result = tree.execute(param)
        if isgenerator(result):
            result = list(result)
        return result


class UDFParser(BaseParser):
    """Python source code snippets. globals will contain `input_object` and `context` variables.

        param & value:
            param: the python source code to be exec(param), either have the function named `parse`, or will return eval(param)
            value: will be renamed to `context`, which can be used in parser function. `value` often be set as the dict of request & response.
    """
    name = 'udf'
    doc_url = 'https://docs.python.org/3/'
    _ALLOW_IMPORT = False
    # Differ from others, treate list as list object
    _RECURSION_LIST = False

    def _parse(self, input_object, param, value=""):
        if value and isinstance(value, str):
            try:
                context = json_loads(value)
            except JSONDecodeError:
                context = value
        else:
            context = value
        if not self._ALLOW_IMPORT and 'import' in param:
            # cb = re_compile(r'^\s*(from  )?import \w+') # not strict enough
            raise RuntimeError(
                'UDFParser._ALLOW_IMPORT is False, so source code should not has `import` strictly. If you really want it, set `UDFParser._ALLOW_IMPORT = True` manually'
            )
        if 'parse' in param and ('lambda' in param or 'def ' in param):
            exec(param, locals(), locals())
            tmp = locals().get('parse')
            if not tmp:
                raise ValueError(
                    'UDF format error, snippet should have the function named `parse`'
                )
            return tmp(input_object)
        else:
            return eval(param)


class PythonParser(BaseParser):
    """Some frequently-used utils

        :param input_object: input object, any object.
        :type input_object: [object]
        param & value:

            1.  param: getitem
                value: could be [0] as index, [1:3] as slice
            2.  param: split
                value: return input_object.split(value or None)
            3.  param: join
                value: return value.join(input_object)
            4.  param: chain
                value: return list(itertools.chain(*input_object))
    """
    name = 'python'
    doc_url = 'https://docs.python.org/3/'
    # Differ from others, treate list as list object
    _RECURSION_LIST = False

    def _parse(self, input_object, param, value):
        param_functions = {
            'getitem': self._handle_getitem,
            'split': lambda input_object, param, value: input_object.split(value or None),
            'join': lambda input_object, param, value: value.join(input_object),
            'chain': lambda input_object, param, value: list(chain(*input_object)),
        }
        function = param_functions.get(param, return_self)
        return function(input_object, param, value)

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


class LoaderParser(BaseParser):
    """ObjectPath parser, requires `objectpath` lib.

        :param input_object: str match format of json / yaml / toml
        :type input_object: [str]
        :param param: loader name, such as: json, yaml, toml
        :type param: [str]
        :param value: some kwargs, input as json string
        :type value: [str]
    """
    name = 'loader'
    _RECURSION_LIST = False
    loaders = {
        'json': json_loads,
        'toml': toml_loads,
        'yaml': yaml_full_load,
        'yaml_safe_load': yaml_safe_load,
        'yaml_full_load': yaml_full_load,
    }

    def _parse(self, input_object, param, value=''):
        loader = self.loaders.get(param, return_self)
        if value:
            try:
                kwargs = json_loads(value)
                return loader(input_object, **kwargs)
            except JSONDecodeError as err:
                return err
        else:
            return loader(input_object)


class TimeParser(BaseParser):
    """Parse different format of time. Sometimes time string need a preprocessing with regex.

        :param input_object: str
        :type input_object: [str]
        :param param: encode / decode. encode: time string => timestamp; decode: timestamp => time string
        :type param: [str]
        :param value: standard strftime/strptime format
        :type value: [str]

    WARNING: time.struct_time do not have timezone info, so %z is always the local timezone
    """
    name = 'time'
    match_int_float = re_compile(r'^-?\d+(\.\d+)?$')
    # EAST8 = +8, WEST8 = -8
    _OS_LOCAL_TIME_ZONE: int = -int(timezone / 3600)
    LOCAL_TIME_ZONE: int = _OS_LOCAL_TIME_ZONE

    def _parse(self, input_object, param, value):
        value = value or "%Y-%m-%d %H:%M:%S"
        tz_fix_seconds = (
            self.LOCAL_TIME_ZONE - self._OS_LOCAL_TIME_ZONE) * 3600
        if param == 'encode':
            # time string => timestamp
            if '%z' in value:
                warn(
                    'TimeParser Warning: time.struct_time do not have timezone info, so %z is nonsense'
                )
            return mktime(strptime(input_object, value)) - tz_fix_seconds
        elif param == 'decode':
            if isinstance(input_object,
                          str) and self.match_int_float.match(input_object):
                input_object = float(input_object)
            # timestamp => time string
            return strftime(value, localtime(input_object + tz_fix_seconds))
        else:
            return input_object


class Uniparser(object):
    parser_classes = BaseParser.__subclasses__()

    def __init__(self):
        self._prepare_default_parsers()
        self._prepare_custom_parsers()

    def parse(self, input_object, rule: 'ParseRule', context=None):

        for parser_name, param, value in rule['parse_rules']:
            parser = getattr(self, parser_name)
            parser = parser.parse if parser else return_self
            if context and parser_name == 'udf' and not value:
                _value = context
            else:
                _value = value
            input_object = parser(input_object, param, _value)
        return input_object

    def _prepare_default_parsers(self):
        self.css = CSSParser()
        self.xml = XMLParser()
        self.re = RegexParser()
        self.jsonpath = JSONPathParser()
        self.objectpath = ObjectPathParser()
        self.python = PythonParser()
        self.loader = LoaderParser()
        self.time = TimeParser()

    def _prepare_custom_parsers(self):
        for parser in BaseParser.__subclasses__():
            if parser.name not in self.__dict__:
                self.__dict__[parser.name] = parser()


class JsonSerializable(dict):

    def __init__(self, **kwargs):
        super().__init__()
        self.update(kwargs)

    def to_dict(self):
        return dict(self)

    def to_json(self, *args, **kwargs):
        return json_dumps(self, *args, **kwargs)

    @classmethod
    def from_json(cls, json_string):
        return cls(**json_loads(json_string))


class ParseRule(JsonSerializable):

    def __init__(self, name: str, parse_rules: List, **kwargs):
        super().__init__(
            id=md5(name), name=name, parse_rules=parse_rules, **kwargs)


class CrawlerRule(JsonSerializable):

    def __init__(self,
                 name: str,
                 request_args: dict,
                 parse_rules: List,
                 regex: str = "",
                 **kwargs):
        super().__init__(
            name=name,
            parse_rules=parse_rules,
            request_args=request_args,
            regex=regex,
            **kwargs)


class HostRules(JsonSerializable):

    def __init__(self, host: str, rules: List[CrawlerRule] = None, **kwargs):
        super().__init__(host=host, rules=rules or [], **kwargs)

    def search(self, url):
        for rule in self['rules']:
            if rule['regex'] and re_compile(rule['regex']).search(url):
                return rule

    def match(self, url):
        for rule in self['rules']:
            if rule['regex'] and re_compile(rule['regex']).match(url):
                return rule

    def add(self, rule: CrawlerRule):
        if rule not in self['rules']:
            self['rules'].append(rule)

    def remove(self, rule: CrawlerRule):
        if rule in self['rules']:
            self['rules'].remove(rule)
