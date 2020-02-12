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
from typing import List, Union
from warnings import warn

from bs4 import BeautifulSoup, Tag
from jmespath import compile as jmespath_compile
from jsonpath_ng.ext import parse as jp_parse
from objectpath import Tree as OP_Tree
from toml import loads as toml_loads
from yaml import full_load as yaml_full_load
from yaml import safe_load as yaml_safe_load

from .utils import ensure_request, SyncRequestAdapter, AsyncRequestAdapter

__all__ = [
    'BaseParser', 'ParseRule', 'CrawlerRule', 'HostRule', 'Tag', 'CSSParser',
    'XMLParser', 'RegexParser', 'JSONPathParser', 'ObjectPathParser',
    'JMESPathParser', 'PythonParser', 'UDFParser', 'LoaderParser'
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
    4. Parsers will recursion parse list of input_object if it can only parse `str` object.
    """
    test_url = 'https://github.com/ClericPy/uniparser'
    doc_url = 'https://github.com/ClericPy/uniparser'
    name = 'base'
    _RECURSION_LIST = True
    __slots__ = ()

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
    """RegexParser. Parse the input object with standard regex, features from `re`.

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
    _RECURSION_LIST = False

    def _parse(self, input_object, param, value=''):
        if isinstance(input_object, str):
            input_object = json_loads(input_object)
        value = value or '$value'
        attr_name = value[1:]
        if param.startswith('JSON.'):
            param = '$%s' % param[4:]
        # try get the compiled jsonpath
        jsonpath_expr = getattr(param, 'code', jp_parse(param))
        result = [
            getattr(match, attr_name, match.value)
            for match in jsonpath_expr.find(input_object)
        ]
        return result


class ObjectPathParser(BaseParser):
    """ObjectPath parser, requires `objectpath` lib.

        :param input_object: input object, could be str, list, dict.
        :type input_object: [str, list, dict]
        :param param: ObjectPath
        :type param: [str]
        :param value: not to use
        :type value: [Any]
    """
    name = 'objectpath'
    doc_url = 'http://github.com/adriank/ObjectPath'
    test_url = 'http://objectpath.org/'
    _RECURSION_LIST = False

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


class JMESPathParser(BaseParser):
    """JMESPath parser, requires `jmespath` lib.

        :param input_object: input object, could be str, list, dict.
        :type input_object: [str, list, dict]
        :param param: JMESPath
        :type param: [str]
        :param value: not to use
        :type value: [Any]
    """
    name = 'jmespath'
    doc_url = 'https://github.com/jmespath/jmespath.py'
    test_url = 'http://jmespath.org/'
    _RECURSION_LIST = False

    def _parse(self, input_object, param, value=''):
        if isinstance(input_object, str):
            input_object = json_loads(input_object)
        code = getattr(param, 'code', jmespath_compile(param))
        return code.search(input_object)


class UDFParser(BaseParser):
    """UDFParser. Python source code snippets. globals will contain `input_object` and `context` variables.

        param & value:
            param: the python source code to be exec(param), either have the function named `parse`, or will return eval(param)
            value: will be renamed to `context`, which can be used in parser function. `value` often be set as the dict of request & response.
    """
    name = 'udf'
    doc_url = 'https://docs.python.org/3/'
    _ALLOW_IMPORT = False
    # Differ from others, treate list as list object
    _RECURSION_LIST = False
    # for udf globals, here could save some module can be used, such as: _GLOBALS_ARGS = {'requests': requests}
    _GLOBALS_ARGS = {'md5': md5}

    @staticmethod
    def get_code_mode(code):
        if isinstance(code, CompiledString):
            return code.operator
        if 'parse' in code and ('lambda' in code or 'def ' in code):
            return exec
        else:
            return eval

    def _parse(self, input_object, param, value=""):
        # context could be any type, if string, will try to json.loads
        # if value is null, will use the context dict from CrawlerRule & ParseRule
        if value and isinstance(value, str):
            try:
                context = json_loads(value)
            except JSONDecodeError:
                context = value
        else:
            context = value or {}
        if not self._ALLOW_IMPORT and 'import' in param:
            # cb = re_compile(r'^\s*(from  )?import \w+') # not strict enough
            raise RuntimeError(
                'UDFParser._ALLOW_IMPORT is False, so source code should not has `import` strictly. If you really want it, set `UDFParser._ALLOW_IMPORT = True` manually'
            )
        local_vars = locals()
        local_vars.update(self._GLOBALS_ARGS)
        # run code
        code = getattr(param, 'code', param)
        if self.get_code_mode(param) is exec:
            exec(code, local_vars, local_vars)
            parse_function = locals().get('parse')
            if not parse_function:
                raise ValueError(
                    'UDF snippet should have a function named `parse`')
            return parse_function(input_object)
        else:
            return eval(code, local_vars, local_vars)


class CompiledString(str):
    __slots__ = ('operator', 'code')
    __support__ = ('jmespath', 'jsonpath', 'udf')

    def __new__(cls, string, mode=None, *args, **kwargs):
        if isinstance(string, cls):
            return string
        obj = str.__new__(cls, string, *args, **kwargs)
        obj = cls.compile(obj, string, mode)
        return obj

    @classmethod
    def compile(cls, obj, string, mode=None):
        if mode == 'jmespath':
            obj.code = jmespath_compile(string)
        elif mode == 'jsonpath':
            obj.code = jp_parse(string)
        elif mode == 'udf':
            obj.operator = UDFParser.get_code_mode(string)
            # for higher performance, pre-compile the code
            obj.code = compile(string, string, obj.operator.__name__)
        return obj


class PythonParser(BaseParser):
    """PythonParser. Some frequently-used utils.

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
    """LoaderParser. Loads string with json / yaml / toml standard format.

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
    """TimeParser. Parse different format of time. Sometimes time string need a preprocessing with regex.

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


class JsonSerializable(dict):
    __slots__ = ()

    def __init__(self, **kwargs):
        super().__init__()
        self.update(kwargs)

    def to_dict(self):
        return dict(self)

    def dumps(self, *args, **kwargs):
        return json_dumps(self, *args, **kwargs)

    def to_json(self, *args, **kwargs):
        return self.dumps(*args, **kwargs)

    @classmethod
    def loads(cls, json_string):
        return cls(**json_loads(json_string))

    @classmethod
    def from_json(cls, json_string):
        return cls(**cls.loads(json_string))


class ParseRule(JsonSerializable):
    """ParseRule should contain this params:
    1. a rule name, will be set as result key.
    2. chain_rules: a list of [[parser_name, param, value], ...], will be parse one by one.
    3. child_rules: a list of ParseRule instances, nested to save different values as named.
    4. context: a dict shared values by udf parse of the rules, only when udf value is null. May be shared from upstream CrawlerRule.

    Recursion parsing like a matryoshka doll?

    Rule format like:
        {
            'name': 'parse_rule',
            'chain_rules': [['css', 'p', '$outerHTML'], ['css', 'b', '$text'],
                            ['python', 'getitem', '[0]'], ['python', 'getitem', '[0]']],
            'child_rules': [{
                'name': 'rule1',
                'chain_rules': [['python', 'getitem', '[:7]'],
                                ['udf', 'str(input_object)+" "+context', '']],
                'child_rules': [{
                    'name': 'rule2',
                    'chain_rules': [['udf', 'input_object[::-1]', '']],
                    'child_rules': []
                },
                                {
                                    'name': 'rule3',
                                    'chain_rules': [['udf', 'input_object[::-1]', '']],
                                    'child_rules': [{
                                        'name': 'rule4',
                                        'chain_rules': [[
                                            'udf', 'input_object[::-1]', ''
                                        ]],
                                        'child_rules': []
                                    }]
                                }]
            }]
        }

    Parse Result like:
        {
            'parse_rule': {
                'rule1': {
                    'rule2': 'dlrow olleh si sihT',
                    'rule3': {
                        'rule4': 'This is hello world'
                    }
                }
            }
        }

    """
    __slots__ = ('context',)

    def __init__(self,
                 name: str,
                 chain_rules: List[List],
                 child_rules: List['ParseRule'] = None,
                 context: dict = None,
                 **kwargs):
        chain_rules = self.compile_codes(chain_rules or [])
        # ensure items of child_rules is ParseRule
        child_rules = [
            self.__class__(**parse_rule) for parse_rule in child_rules or []
        ]
        self.context: dict = context or {}
        super().__init__(
            name=name,
            chain_rules=chain_rules,
            child_rules=child_rules,
            **kwargs)

    @staticmethod
    def compile_rule(chain_rule):
        if isinstance(chain_rule[1], CompiledString):
            return chain_rule
        if chain_rule[0] in CompiledString.__support__:
            chain_rule[1] = CompiledString(chain_rule[1], mode=chain_rule[0])
        return chain_rule

    def compile_codes(self, chain_rules):
        return [self.compile_rule(chain_rule) for chain_rule in chain_rules]


class CrawlerRule(JsonSerializable):
    """A standard CrawlerRule contains:
    1. a rule name, will be set as result key.
    2. request_args for sending request.
    3. parse_rules: list of [ParseRule: , ...].
    4. regex: regex which can match a given url.
    5. context: a dict shared values by udf parse of the rules, only when udf value is null. May be shared to downstream ParseRule.
    6 **kwargs: some extra kwargs, sometimes contains encoding param.

    Rule format like:
        {
            'name': 'crawler_rule',
            'parse_rules': [{
                'name': 'parse_rule',
                'chain_rules': [['css', 'p', '$outerHTML'], ['css', 'b', '$text'],
                                ['python', 'getitem', '[0]'],
                                ['python', 'getitem', '[0]']],
                'child_rules': [{
                    'name': 'rule1',
                    'chain_rules': [['python', 'getitem', '[:7]'],
                                    ['udf', 'str(input_object)+" "+context', '']],
                    'child_rules': [
                        {
                            'name': 'rule2',
                            'chain_rules': [['udf', 'input_object[::-1]', '']],
                            'child_rules': []
                        },
                        {
                            'name': 'rule3',
                            'chain_rules': [['udf', 'input_object[::-1]', '']],
                            'child_rules': [{
                                'name': 'rule4',
                                'chain_rules': [['udf', 'input_object[::-1]', '']],
                                'child_rules': []
                            }]
                        }
                    ]
                }]
            }],
            'request_args': {
                'method': 'get',
                'url': 'http://example.com',
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'
                }
            },
            'regex': ''
        }

    Parse Result like:
        {
            'crawler_rule': {
                'parse_rule': {
                    'rule1': {
                        'rule2': 'dlrow olleh si sihT',
                        'rule3': {
                            'rule4': 'This is hello world'
                        }
                    }
                }
            }
        }
    """
    __slots__ = ('context',)

    def __init__(self,
                 name: str,
                 request_args: Union[dict, str],
                 parse_rules: List[ParseRule] = None,
                 regex: str = None,
                 context: dict = None,
                 **kwargs):
        _request_args: dict = ensure_request(request_args)
        if _request_args:
            _request_args["headers"] = _request_args.setdefault(
                "headers", {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"
                })
        self.context = context or {}
        parse_rules = [
            ParseRule(context=self.context, **parse_rule)
            for parse_rule in parse_rules or []
        ]
        super().__init__(
            name=name,
            parse_rules=parse_rules,
            request_args=_request_args,
            regex=regex or '',
            **kwargs)

    def get_request(self, **request):
        for k, v in self['request_args'].items():
            if k not in request:
                request[k] = v
        return request

    def add_parse_rule(self, rule: ParseRule, context: dict = None):
        rule = ParseRule(context=context or self.context, **rule)
        self['parse_rules'].append(rule)

    def pop_parse_rule(self, index, default=None):
        try:
            return self['parse_rules'].pop(index)
        except IndexError:
            return default

    def clear_parse_rules(self):
        self['parse_rules'].clear()

    def search(self, url):
        return not self['regex'] or re_compile(self['regex']).search(url)

    def match(self, url):
        return not self['regex'] or re_compile(self['regex']).match(url)


class HostRule(JsonSerializable):
    __slots__ = ()

    def __init__(self,
                 host: str,
                 crawler_rules: List[CrawlerRule] = None,
                 **kwargs):
        crawler_rules = [
            CrawlerRule(**crawler_rule) for crawler_rule in crawler_rules or []
        ]
        super().__init__(host=host, crawler_rules=crawler_rules, **kwargs)

    def find(self, url):
        return self.search(url)

    def search(self, url):
        for rule in self['crawler_rules']:
            if rule.search(url):
                return rule

    def match(self, url):
        for rule in self['crawler_rules']:
            if rule.match(url):
                return rule

    def add(self, rule: CrawlerRule):
        if rule not in self['crawler_rules']:
            self['crawler_rules'].append(rule)

    def remove(self, rule: CrawlerRule):
        if rule in self['crawler_rules']:
            self['crawler_rules'].remove(rule)


class Uniparser(object):
    parser_classes = BaseParser.__subclasses__()

    def __init__(self,
                 request_adapter: Union[AsyncRequestAdapter,
                                        SyncRequestAdapter] = None):
        self._prepare_default_parsers()
        self._prepare_custom_parsers()
        self.request_adapter = request_adapter

    def parse_chain(self, input_object, chain_rules: List, context=None):
        for parser_name, param, value in chain_rules:
            parser = getattr(self, parser_name)
            if not parser:
                warn(f'Skip parsing for unknown name: {parser_name}')
                continue
            if context and parser_name == 'udf' and not value:
                value = context
            input_object = parser.parse(input_object, param, value)
        return input_object

    def parse_crawler_rule(self, input_object, rule: CrawlerRule, context=None):
        parse_rules = rule['parse_rules']
        result = {
            parse_rule['name']: self.parse_parse_rule(
                input_object, parse_rule, context).get(parse_rule['name'])
            for parse_rule in parse_rules
        }
        return {rule['name']: result}

    def parse_parse_rule(self, input_object, rule: ParseRule, context=None):
        # if context, use context; else use rule.context
        input_object = self.parse_chain(
            input_object,
            rule['chain_rules'],
            context=context or getattr(rule, 'context', {}))
        result = {rule['name']: input_object}
        if not rule['child_rules']:
            return {rule['name']: input_object}
        else:
            result = {rule['name']: {}}
        for sub_rule in rule['child_rules']:
            result[rule['name']][sub_rule['name']] = self.parse_parse_rule(
                input_object,
                sub_rule,
                context=context,
            ).get(sub_rule['name'])
        return result

    def parse(self,
              input_object,
              rule_object: Union[CrawlerRule, ParseRule],
              context=None):
        if isinstance(rule_object, CrawlerRule):
            return self.parse_crawler_rule(
                input_object=input_object, rule=rule_object, context=context)
        elif isinstance(rule_object, ParseRule):
            return self.parse_parse_rule(
                input_object=input_object, rule=rule_object, context=context)

    def _prepare_default_parsers(self):
        self.css = CSSParser()
        self.xml = XMLParser()
        self.re = RegexParser()
        self.jsonpath = JSONPathParser()
        self.objectpath = ObjectPathParser()
        self.jmespath = JMESPathParser()
        self.python = PythonParser()
        self.loader = LoaderParser()
        self.time = TimeParser()

    def _prepare_custom_parsers(self):
        for parser in BaseParser.__subclasses__():
            if parser.name not in self.__dict__:
                self.__dict__[parser.name] = parser()

    def crawl(self,
              crawler_rule: CrawlerRule,
              request_adapter: SyncRequestAdapter = None,
              context=None):
        request_adapter = request_adapter or self.request_adapter
        context = context or {}
        if not isinstance(request_adapter, SyncRequestAdapter):
            raise RuntimeError('bad request_adapter type')
        with request_adapter as req:
            input_object, resp = req.request(**crawler_rule['request_args'])
            context['resp'] = resp
        return self.parse(input_object, crawler_rule, context)

    async def acrawl(self,
                     crawler_rule: CrawlerRule,
                     request_adapter: AsyncRequestAdapter = None,
                     context=None):
        request_adapter = request_adapter or self.request_adapter
        context = context or {}
        if not isinstance(request_adapter, AsyncRequestAdapter):
            raise RuntimeError('bad request_adapter type')
        async with request_adapter as req:
            input_object, resp = await req.request(
                **crawler_rule['request_args'])
            context['resp'] = resp
        return self.parse(input_object, crawler_rule, context)
