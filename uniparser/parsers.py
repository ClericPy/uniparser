# -*- coding: utf-8 -*-

import asyncio
import re
from abc import ABC, abstractmethod
from base64 import (b16decode, b16encode, b32decode, b32encode, b64decode,
                    b64encode, b85decode, b85encode)
from hashlib import md5 as _md5
from itertools import chain
from logging import getLogger
from re import compile as re_compile
from string import Template
from time import localtime, mktime, strftime, strptime, timezone
from typing import Any, Callable, Dict, List, Union

from frequency_controller import AsyncFrequency, Frequency

from .config import GlobalConfig
from .exceptions import InvalidSchemaError, UnknownParserNameError
from .utils import (AsyncRequestAdapter, InputCallbacks, SyncRequestAdapter,
                    _lib, decode_as_base64, encode_as_base64,
                    ensure_await_result, ensure_request,
                    get_available_async_request, get_available_sync_request,
                    get_host)

__all__ = [
    'BaseParser', 'ParseRule', 'CrawlerRule', 'HostRule', 'CSSParser',
    'SelectolaxParser', 'XMLParser', 'RegexParser', 'JSONPathParser',
    'ObjectPathParser', 'JMESPathParser', 'PythonParser', 'UDFParser',
    'LoaderParser', 'Uniparser'
]

logger = getLogger('uniparser')


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
    Since most input object always should be string, _RECURSION_LIST will be True.

    1. class variable `name`
    2. `_parse` method
    3. use lazy import, maybe
    4. Parsers will recursion parse list of input_object if it can only parse `str` object.

    Test demo::

        def _partial_test_parser():
            from uniparser import Uniparser

            uni = Uniparser()
            args = [
                ['adcb', 'sort', ''],
            ]
            max_len = max([len(str(i)) for i in args])
            for i in args:
                print(f'{str(i):<{max_len}} => {uni.python.parse(*i)}')

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
            # traceback.format_exception(None, e, e.__traceback__)
            return err

    @property
    def doc(self):
        # If need dynamic doc, overwrite this method.
        return f'{self.__class__.__doc__}\n\n{self.doc_url}\n\n{self.test_url}'

    def __call__(self, *args, **kwargs):
        return self.parse(*args, **kwargs)


class CSSParser(BaseParser):
    """CSS selector parser, requires `bs4` and `lxml`(optional).
    Since HTML input object always should be string, _RECURSION_LIST will be True.

    Parse the input object with standard css selector, features from `BeautifulSoup`.

        :param input_object: input object, could be Tag or str.
        :type input_object: [Tag, str]
        :param param: css selector path
        :type param: [str]
        :param value: operation for each item of result
        :type value: [str]

            @attribute: return element.get(xxx)

            $text: return element.text

            $innerHTML, $html: return element.decode_contents()

            $outerHTML, $string: return str(element)

            $self: return element

        :return: list of Tag / str
        :rtype: List[Union[str, Tag]]

        examples:

            ['<a class="url" href="/">title</a>', 'a.url', '@href']      => ['/']
            ['<a class="url" href="/">title</a>', 'a.url', '$text']      => ['title']
            ['<a class="url" href="/">title</a>', 'a.url', '$innerHTML'] => ['title']
            ['<a class="url" href="/">title</a>', 'a.url', '$html']      => ['title']
            ['<a class="url" href="/">title</a>', 'a.url', '$outerHTML'] => ['<a class="url" href="/">title</a>']
            ['<a class="url" href="/">title</a>', 'a.url', '$string']    => ['<a class="url" href="/">title</a>']
            ['<a class="url" href="/">title</a>', 'a.url', '$self']      => [<a class="url" href="/">title</a>]

            WARNING: $self returns the original Tag object
    """
    name = 'css'
    doc_url = 'https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Selectors'
    operations = {
        '@attr': lambda element: element.get(),
        '$text': lambda element: element.text,
        '$innerHTML': lambda element: element.decode_contents(),
        '$html': lambda element: element.decode_contents(),
        '$outerHTML': lambda element: str(element),
        '$string': lambda element: str(element),
        '$self': return_self,
    }

    @property
    def doc(self):
        return f'{self.__class__.__doc__}\n\nvalid value args: {list(self.operations.keys())}\n\n{self.doc_url}\n\n{self.test_url}'

    def _parse(self, input_object, param, value):
        result = []
        if not input_object:
            return result
        # ensure input_object is instance of BeautifulSoup
        if not isinstance(input_object, _lib.Tag):
            input_object = _lib.BeautifulSoup(input_object, 'lxml')
        if value.startswith('@'):
            result = [
                item.get(value[1:], None) for item in input_object.select(param)
            ]
        else:
            operate = self.operations.get(value, return_self)
            result = [operate(item) for item in input_object.select(param)]
        return result


class CSSSingleParser(CSSParser):
    """Similar to CSSParser but use select_one instead of select method.
        examples:

            ['<a class="url" href="/">title</a>', 'a.url1', '@href']      => None
            ['<a class="url" href="/">title</a>', 'a.url', '@href']      => '/'
            ['<a class="url" href="/">title</a>', 'a.url', '$text']      => 'title'
            ['<a class="url" href="/">title</a>', 'a.url', '$innerHTML'] => 'title'
            ['<a class="url" href="/">title</a>', 'a.url', '$html']      => 'title'
            ['<a class="url" href="/">title</a>', 'a.url', '$outerHTML'] => '<a class="url" href="/">title</a>'
            ['<a class="url" href="/">title</a>', 'a.url', '$string']    => '<a class="url" href="/">title</a>'
            ['<a class="url" href="/">title</a>', 'a.url', '$self']      => <a class="url" href="/">title</a>
    """
    name = 'css1'

    def _parse(self, input_object, param, value):
        result = []
        if not input_object:
            return result
        # ensure input_object is instance of BeautifulSoup
        if not isinstance(input_object, _lib.Tag):
            input_object = _lib.BeautifulSoup(input_object, 'lxml')
        item = input_object.select_one(param)
        if item is None:
            return None
        if value.startswith('@'):
            return item.get(value[1:], None)
        operate = self.operations.get(value, return_self)
        return operate(item)


class SelectolaxParser(BaseParser):
    """CSS selector parser based on `selectolax`, faster than lxml.
    Since HTML input object always should be string, _RECURSION_LIST will be True.

    Parse the input object with standard css selector.

        :param input_object: input object, could be Node or str.
        :type input_object: [Node, str]
        :param param: css selector path
        :type param: [str]
        :param value: operation for each item of result
        :type value: [str]

            @attribute: return element.attributes.get(xxx)

            $text: return element.text

            $outerHTML, $html: return element.html

            $self: return element

        :return: list of Node / str
        :rtype: List[Union[str, Node]]

        examples:

            ['<a class="url" href="/">title</a>', 'a.url', '@href']      => ['/']
            ['<a class="url" href="/">title</a>', 'a.url', '$text']      => ['title']
            ['<a class="url" href="/">title</a>', 'a.url', '$string']    => ['<a class="url" href="/">title</a>']
            ['<a class="url" href="/">title</a>', 'a.url', '$outerHTML'] => ['<a class="url" href="/">title</a>']
            ['<a class="url" href="/">title</a>', 'a.url', '$self']      => [<a class="url" href="/">title</a>]
            ['<div>a <b>b</b> c</div>', 'div', '$html']                  => ['a <b>b</b> c']
            ['<div>a <b>b</b> c</div>', 'div', '$innerHTML']             => ['a <b>b</b> c']
            WARNING: $self returns the original Node object
    """
    name = 'selectolax'
    doc_url = 'https://github.com/rushter/selectolax'

    def get_inner_html(element):
        result = []
        element = element.child
        while element:
            result.append(element.html)
            element = element.next
        return ''.join(result)

    operations = {
        '@attr': lambda element: element.attributes.get(...),
        '$text': lambda element: element.text(),
        '$html': get_inner_html,
        '$innerHTML': get_inner_html,
        '$string': lambda element: element.html,
        '$outerHTML': lambda element: element.html,
        '$self': return_self,
    }

    @property
    def doc(self):
        return f'{self.__class__.__doc__}\n\nvalid value args: {list(self.operations.keys())}\n\n{self.doc_url}\n\n{self.test_url}'

    def _parse(self, input_object, param, value):
        result = []
        if not input_object:
            return result
        # ensure input_object is instance of Node
        if not isinstance(input_object, (_lib.Node, _lib.HTMLParser)):
            input_object = _lib.HTMLParser(input_object)
        if value.startswith('@'):
            result = [
                item.attributes.get(value[1:], None)
                for item in input_object.css(param)
            ]
        else:
            operate = self.operations.get(value, return_self)
            result = [operate(item) for item in input_object.css(param)]
        return result


class SelectolaxSingleParser(SelectolaxParser):
    """Similar to SelectolaxParser but use css_first instead of select method.
        examples:

            ['<a class="url" href="/">title</a>', 'a.url1', '@href']      => None
            ['<a class="url" href="/">title</a>', 'a.url', '@href']      => '/'
            ['<a class="url" href="/">title</a>', 'a.url', '$text']      => 'title'
            ['<a class="url" href="/">title</a>', 'a.url', '$innerHTML'] => 'title'
            ['<a class="url" href="/">title</a>', 'a.url', '$html']      => 'title'
            ['<a class="url" href="/">title</a>', 'a.url', '$outerHTML'] => '<a class="url" href="/">title</a>'
            ['<a class="url" href="/">title</a>', 'a.url', '$string']    => '<a class="url" href="/">title</a>'
            ['<a class="url" href="/">title</a>', 'a.url', '$self']      => <a class="url" href="/">title</a>
    """
    name = 'se1'

    def _parse(self, input_object, param, value):
        result = []
        if not input_object:
            return result
        # ensure input_object is instance of Node
        if not isinstance(input_object, (_lib.Node, _lib.HTMLParser)):
            input_object = _lib.HTMLParser(input_object)
        item = input_object.css_first(param)
        if item is None:
            return ''
        if value.startswith('@'):
            return item.attributes.get(value[1:], None)
        operate = self.operations.get(value, return_self)
        return operate(item)


class XMLParser(BaseParser):
    """XML parser, requires `bs4` and `lxml`(necessary), but not support `xpath` for now.
    Since XML input object always should be string, _RECURSION_LIST will be True.

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

        examples:

            ['<dc:creator><![CDATA[author]]></dc:creator>', 'creator', '$text']      => ['author']
            WARNING: $self returns the original Tag object
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

    @property
    def doc(self):
        return f'{self.__class__.__doc__}\n\nvalid value args: {list(self.operations.keys())}\n\n{self.doc_url}\n\n{self.test_url}'

    def _parse(self, input_object, param, value):
        result = []
        if not input_object:
            return result
        # ensure input_object is instance of BeautifulSoup
        if not isinstance(input_object, _lib.Tag):
            input_object = _lib.BeautifulSoup(input_object, 'lxml-xml')
        if value.startswith('@'):
            result = [
                item.get(value[1:], None) for item in input_object.select(param)
            ]
        else:
            operate = self.operations.get(value, return_self)
            result = [operate(item) for item in input_object.select(param)]
        return result


class RegexParser(BaseParser):
    """RegexParser. Parse the input object with standard regex, features from `re`.
    Since regex input object always should be string, _RECURSION_LIST will be True.

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

            #: return re.search(param, input_object).group(int(value[1:])), return '' if not matched.

        :return: list of str
        :rtype: List[Union[str]]

        examples:

            ['a a b b c c', 'a|c', '@b']     => 'b b b b b b'
            ['a a b b c c', 'a', '']         => ['a', 'a']
            ['a a b b c c', 'a (a b)', '$0'] => ['a a b']
            ['a a b b c c', 'a (a b)', '$1'] => ['a b']
            ['a a b b c c', 'b', '-']        => ['a a ', ' ', ' c c']
            ['abcd', '(b.)d', '#0']          => 'bcd'
            ['abcd', '(b.)', '#1']           => 'bc'
            ['abcd', '(b.)', '#2']           => ''
            ['abcd', '.(?:d)', '#0']         => 'cd'
            ['abcd', '.(?:d)', '#1']         => ''
            ['abcd', '.(?<=c).', '#0']       => 'cd'
            ['abcd', '.(?<=c).', '#1']       => ''
    """
    name = 're'
    test_url = 'https://regex101.com/'
    doc_url = 'https://docs.microsoft.com/en-us/dotnet/standard/base-types/regular-expression-language-quick-reference'
    VALID_VALUE_PATTERN = re_compile(r'^@|^\$\d+|^-$|^#\d+')

    def _parse(self, input_object, param, value):
        msg = f'input_object type should be str, but given {repr(input_object)[:30]}'
        assert isinstance(input_object, str), ValueError(msg)
        assert self.VALID_VALUE_PATTERN.match(value) or not value, ValueError(
            r'args1 should match ^@|^\$\d+|^-$|^#\d+')
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
        elif prefix == '#':
            matched = com.search(input_object)
            if not matched:
                return ''
            try:
                if arg.isdigit():
                    index = int(arg)
                else:
                    index = 1
                return matched.group(index)
            except IndexError:
                return ""


class JSONPathParser(BaseParser):
    """JSONPath parser, requires `jsonpath-rw-ext` library.
    Since json input object may be dict / list, _RECURSION_LIST will be False.

        :param input_object: input object, could be str, list, dict.
        :type input_object: [str, list, dict]
        :param param: JSON path
        :type param: [str]
        :param value: attribute of find result, default to '' as '$value'
        :type value: [str, None]
        :return: list of str
        :rtype: List[Union[str]]

        examples:

            [{'a': {'b': {'c': 1}}}, '$..c', ''] => [1]
    """
    name = 'jsonpath'
    doc_url = 'https://github.com/sileht/python-jsonpath-rw-ext'
    test_url = 'https://jsonpath.com/'
    _RECURSION_LIST = False

    def _parse(self, input_object, param, value=''):
        if isinstance(input_object, str):
            input_object = GlobalConfig.json_loads(input_object)
        value = value or '$value'
        attr_name = value[1:]
        if param.startswith('JSON.'):
            param = '$%s' % param[4:]
        # try get the compiled jsonpath
        jsonpath_expr = getattr(param, 'code', _lib.jp_parse(param))
        result = [
            getattr(match, attr_name, match.value)
            for match in jsonpath_expr.find(input_object)
        ]
        return result


class ObjectPathParser(BaseParser):
    """ObjectPath parser, requires `objectpath` library.
    Since json input object may be dict / list, _RECURSION_LIST will be False.

        :param input_object: input object, could be str, list, dict.
        :type input_object: [str, list, dict]
        :param param: ObjectPath
        :type param: [str]
        :param value: not to use
        :type value: [Any]

        examples:

            [{'a': {'b': {'c': 1}}}, '$..c', ''] => [1]
    """
    name = 'objectpath'
    doc_url = 'http://github.com/adriank/ObjectPath'
    test_url = 'http://objectpath.org/'
    _RECURSION_LIST = False
    ITER_TYPES_TUPLE = tuple(_lib.ITER_TYPES)

    def _parse(self, input_object, param, value=''):
        if isinstance(input_object, str):
            input_object = GlobalConfig.json_loads(input_object)
        if param.startswith('JSON.'):
            param = '$%s' % param[4:]
        tree = _lib.OP_Tree(input_object)
        result = tree.execute(param)
        # from objectpath.core import ITER_TYPES
        if isinstance(result, self.ITER_TYPES_TUPLE):
            result = list(result)
        return result


class JMESPathParser(BaseParser):
    """JMESPath parser, requires `jmespath` library.
    Since json input object may be dict / list, _RECURSION_LIST will be False.

        :param input_object: input object, could be str, list, dict.
        :type input_object: [str, list, dict]
        :param param: JMESPath
        :type param: [str]
        :param value: not to use
        :type value: [Any]

        examples:

            [{'a': {'b': {'c': 1}}}, 'a.b.c', ''] => 1
    """
    name = 'jmespath'
    doc_url = 'https://github.com/jmespath/jmespath.py'
    test_url = 'http://jmespath.org/'
    _RECURSION_LIST = False

    def _parse(self, input_object, param, value=''):
        if isinstance(input_object, str):
            input_object = GlobalConfig.json_loads(input_object)
        code = getattr(param, 'code', _lib.jmespath_compile(param))
        return code.search(input_object)


class UDFParser(BaseParser):
    """UDFParser. Python source code snippets. globals will contain `input_object` and `context` variables.
    Since python input object may be any type, _RECURSION_LIST will be False.

        param & value:
            param: the python source code to be exec(param), either have the function named `parse`, or will return eval(param)
            value: will be renamed to `context`, which can be used in parser function. `value` often be set as the dict of request & response.
        examples:

            ['a b c d', 'input_object[::-1]', '']                                                       => 'd c b a'
            ['a b c d', 'context["key"]', {'key': 'value'}]                                             => 'value'
            ['a b c d', 'md5(input_object)', '']                                                        => '713f592bd537f7725d491a03e837d64a'
            ['["string"]', 'json_loads(input_object)', '']                                              => ['string']
            ['["string"]', 'json_loads(obj)', '']                                                       => ['string']
            [['string'], 'json_dumps(input_object)', '']                                                => '["string"]'
            ['a b c d', 'parse = lambda input_object: input_object', '']                                => 'a b c d'
            ['a b c d', 'def parse(input_object): context["key"]="new";return context', {'key': 'old'}] => {'key': 'new'}
    """
    name = 'udf'
    doc_url = 'https://docs.python.org/3/'
    # able to import other libs
    _ALLOW_IMPORT = True
    # strict protection
    _FORBIDDEN_FUNCS = {
        "input": NotImplemented,
        "open": NotImplemented,
        "eval": NotImplemented,
        "exec": NotImplemented,
    }
    # Differ from others, treate list as list object
    _RECURSION_LIST = False
    # for udf globals, here could save some module can be used, such as: _GLOBALS_ARGS = {'requests': requests}
    _GLOBALS_ARGS = {
        'md5': md5,
        'json_loads': GlobalConfig.json_loads,
        'json_dumps': GlobalConfig.json_dumps,
        're': re,
        'encode_as_base64': encode_as_base64,
        'decode_as_base64': decode_as_base64,
    }

    @property
    def doc(self):
        return f'{self.__class__.__doc__}\n\n_GLOBALS_ARGS: {list(self._GLOBALS_ARGS.keys())}\n\n{self.doc_url}\n\n{self.test_url}'

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
                context = GlobalConfig.json_loads(value)
            except GlobalConfig.JSONDecodeError:
                context = {}
        else:
            context = value or {}
        if not self._ALLOW_IMPORT and 'import' in param:
            raise RuntimeError(
                'UDFParser._ALLOW_IMPORT is False, so source code should not has `import` strictly. If you really want it, set `UDFParser._ALLOW_IMPORT = True` manually'
            )
        # obj is an alias for input_object
        local_vars = {
            'input_object': input_object,
            'context': context,
            'obj': input_object,
        }
        local_vars.update(self._FORBIDDEN_FUNCS)
        local_vars.update(self._GLOBALS_ARGS)
        # run code
        code = getattr(param, 'code', param)
        if self.get_code_mode(param) is exec:
            exec(code, local_vars, local_vars)
            parse_function = local_vars.get('parse')
            if not parse_function:
                raise ValueError(
                    'UDF snippet should have a function named `parse`')
            return parse_function(input_object)
        else:
            return eval(code, local_vars, local_vars)


class PythonParser(BaseParser):
    r"""PythonParser. Some frequently-used utils.
    Since python input object may be any type, _RECURSION_LIST will be False.

        :param input_object: input object, any object.
        :type input_object: [object]
        param & value:

            1.  param: getitem, alias to get
                value: could be [0] as index, [1:3] as slice, ['key'] for dict
            2.  param: split
                value: return input_object.split(value or None)
            3.  param: join
                value: return value.join(input_object)
            4.  param: chain
                value: nonsense `value` variable. return list(itertools.chain(*input_object))
            5.  param: const
                value: return value if value else input_object.
            6.  param: template
                value: Template.safe_substitute(input_object=input_object, **input_object if isinstance(input_object, dict))
            7.  param: index
                value: value can be number string / key.
            8.  param: sort
                value: value can be asc (default) / desc.
            9.  param: strip
                value: chars. return str(input_object).strip(value)
            10. param: base64_encode, base64_decode
                from string to string.
            11. param: a number for index, will try to get input_object.__getitem__(int(param))
                value: default string
                similar to `param=default` if param is 0

        If not param, return value. (like `const`)
        examples:

            [[1, 2, 3], 'getitem', '[-1]']              => 3
            [[1, 2, 3], 'getitem', '[:2]']              => [1, 2]
            ['abc', 'getitem', '[::-1]']                => 'cba'
            [{'a': '1'}, 'getitem', 'a']                => '1'
            [{'a': '1'}, 'get', 'a']                    => '1'
            ['a b\tc \n \td', 'split', '']              => ['a', 'b', 'c', 'd']
            [['a', 'b', 'c', 'd'], 'join', '']          => 'abcd'
            [['aaa', ['b'], ['c', 'd']], 'chain', '']   => ['a', 'a', 'a', 'b', 'c', 'd']
            ['python', 'template', '1 $input_object 2'] => '1 python 2'
            [[1], 'index', '0']                         => 1
            ['python', 'index', '-1']                   => 'n'
            [{'a': '1'}, 'index', 'a']                  => '1'
            ['adcb', 'sort', '']                        => ['a', 'b', 'c', 'd']
            [[1, 3, 2, 4], 'sort', 'desc']              => [4, 3, 2, 1]
            ['aabbcc', 'strip', 'a']                    => 'bbcc'
            ['aabbcc', 'strip', 'ac']                   => 'bb'
            [' \t a ', 'strip', '']                     => 'a'
            ['a', 'default', 'b']                       => 'a'
            ['', 'default', 'b']                        => 'b'
            [' ', 'default', 'b']                       => 'b'
            ['a', 'base64_encode', '']                  => 'YQ=='
            ['YQ==', 'base64_decode', '']               => 'a'
            ['a', '0', 'b']                             => 'a'
            ['', '0', 'b']                              => 'b'
            [None, '0', 'b']                            => 'b'
            [{0: 'a'}, '0', 'a']                        => 'a'
            [{0: 'a'}, '', 'abc']                        => 'abc'
"""
    name = 'python'
    doc_url = 'https://docs.python.org/3/'
    # Differ from others, treate list as list object
    _RECURSION_LIST = False

    def __init__(self):
        self.param_functions = {
            'getitem': self._handle_getitem,
            'get': self._handle_getitem,
            'split': lambda input_object, param, value: input_object.split(
                value or None),
            'join': lambda input_object, param, value: value.join(input_object),
            'chain': lambda input_object, param, value: list(
                chain(*input_object)),
            'const': lambda input_object, param, value: value or input_object,
            'template': self._handle_template,
            'index': lambda input_object, param, value: input_object[int(
                value) if (value.isdigit() or value.startswith('-') and value[
                    1:].isdigit()) else value],
            'sort': lambda input_object, param, value: sorted(
                input_object,
                reverse=(True if value.lower() == 'desc' else False)),
            'strip': self._handle_strip,
            'default': self._handle_default,
            'base64_encode': self._handle_base64_encode,
            'base64_decode': self._handle_base64_decode,
        }

    @property
    def doc(self):
        return f'{self.__class__.__doc__}\n\nvalid param args: {list(self.param_functions.keys())}\n\n{self.doc_url}\n\n{self.test_url}'

    def _handle_index(self, input_object, param, value):
        try:
            return input_object[int(param)]
        except (IndexError, ValueError, KeyError, TypeError):
            return value

    def _handle_others(self, input_object, param, value):
        if param.isdigit():
            return self._handle_index(input_object, param, value)
        else:
            return value or input_object

    def _parse(self, input_object, param, value):
        function = self.param_functions.get(param, self._handle_others)
        return function(input_object, param, value)

    def _handle_strip(self, input_object, param, value):
        return str(input_object).strip(value or None)

    def _handle_base64_encode(self, input_object, param, value):
        return encode_as_base64(str(input_object))

    def _handle_base64_decode(self, input_object, param, value):
        return decode_as_base64(str(input_object))

    def _handle_default(self, input_object, param, value):
        if isinstance(input_object, str):
            if input_object.strip():
                return input_object
            else:
                return value
        elif input_object:
            return input_object
        else:
            return value

    def _handle_template(self, input_object, param, value):
        if isinstance(input_object, dict):
            return Template(value).safe_substitute(input_object=input_object,
                                                   obj=input_object,
                                                   **input_object)
        else:
            return Template(value).safe_substitute(input_object=input_object,
                                                   obj=input_object)

    def _handle_getitem(self, input_object, param, value):
        if value and (value[0], value[-1]) == ('[', ']'):
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
        else:
            return input_object[value]


class LoaderParser(BaseParser):
    """LoaderParser. Loads string with json / yaml / toml standard format.
    And also b16decode, b16encode, b32decode, b32encode, b64decode, b64encode, b85decode, b85encode.
    Since input object should be string, _RECURSION_LIST will be True.

        :param input_object: str match format of json / yaml / toml
        :type input_object: [str]
        :param param: loader name, such as: json, yaml, toml
        :type param: [str]
        :param value: some kwargs, input as json string
        :type value: [str]

        examples:

            ['{"a": "b"}', 'json', '']   => {'a': 'b'}
            ['a = "a"', 'toml', '']      => {'a': 'a'}
            ['animal: pets', 'yaml', ''] => {'animal': 'pets'}
            ['a', 'b64encode', '']       => 'YQ=='
            ['YQ==', 'b64decode', '']    => 'a'

    """
    name = 'loader'
    _RECURSION_LIST = True

    def __init__(self):
        self.loaders = {
            'json': GlobalConfig.json_loads,
            'toml': _lib.toml_loads,
            'yaml': _lib.yaml_full_load,
            'yaml_safe_load': _lib.yaml_safe_load,
            'yaml_full_load': _lib.yaml_full_load,
            'b16decode': lambda input_object: b16decode(
                input_object.encode(GlobalConfig.__encoding__)).decode(
                    GlobalConfig.__encoding__),
            'b16encode': lambda input_object: b16encode(
                input_object.encode(GlobalConfig.__encoding__)).decode(
                    GlobalConfig.__encoding__),
            'b32decode': lambda input_object: b32decode(
                input_object.encode(GlobalConfig.__encoding__)).decode(
                    GlobalConfig.__encoding__),
            'b32encode': lambda input_object: b32encode(
                input_object.encode(GlobalConfig.__encoding__)).decode(
                    GlobalConfig.__encoding__),
            'b64decode': lambda input_object: b64decode(
                input_object.encode(GlobalConfig.__encoding__)).decode(
                    GlobalConfig.__encoding__),
            'b64encode': lambda input_object: b64encode(
                input_object.encode(GlobalConfig.__encoding__)).decode(
                    GlobalConfig.__encoding__),
            'b85decode': lambda input_object: b85decode(
                input_object.encode(GlobalConfig.__encoding__)).decode(
                    GlobalConfig.__encoding__),
            'b85encode': lambda input_object: b85encode(
                input_object.encode(GlobalConfig.__encoding__)).decode(
                    GlobalConfig.__encoding__),
        }
        super().__init__()

    @property
    def doc(self):
        return f'{self.__class__.__doc__}\n\nvalid param args: {list(self.loaders.keys())}\n\n{self.doc_url}\n\n{self.test_url}'

    def _parse(self, input_object, param, value=''):
        loader = self.loaders.get(param, return_self)
        if value:
            try:
                kwargs = GlobalConfig.json_loads(value)
                return loader(input_object, **kwargs)
            except GlobalConfig.JSONDecodeError as err:
                return err
        else:
            return loader(input_object)


class TimeParser(BaseParser):
    """TimeParser. Parse different format of time. Sometimes time string need a preprocessing with regex.
    Since input object can not be list, _RECURSION_LIST will be True.
        To change time zone:
            uniparser.time.LOCAL_TIME_ZONE = +8

        :param input_object: str
        :type input_object: [str]
        :param param: encode / decode. encode: time string => timestamp; decode: timestamp => time string
        :type param: [str]
        :param value: standard strftime/strptime format
        :type value: [str]

        examples:

            ['2020-02-03 20:29:45', 'encode', '']                  => 1580732985.0
            ['1580732985.1873155', 'decode', '']                   => '2020-02-03 20:29:45'
            ['2020-02-03T20:29:45', 'encode', '%Y-%m-%dT%H:%M:%S'] => 1580732985.0
            ['1580732985.1873155', 'decode', '%b %d %Y %H:%M:%S']  => 'Feb 03 2020 20:29:45'

    WARNING: time.struct_time do not have timezone info, so %z is always the local timezone
    """
    name = 'time'
    match_int_float = re_compile(r'^-?\d+(\.\d+)?$')
    # EAST8 = +8, WEST8 = -8
    _OS_LOCAL_TIME_ZONE: int = -int(timezone / 3600)
    LOCAL_TIME_ZONE: int = _OS_LOCAL_TIME_ZONE

    @property
    def doc(self):
        return f'{self.__class__.__doc__}\n\n_OS_LOCAL_TIME_ZONE: {self._OS_LOCAL_TIME_ZONE}\nLOCAL_TIME_ZONE: {self.LOCAL_TIME_ZONE}\n\n{self.doc_url}\n\n{self.test_url}'

    def _parse(self, input_object, param, value):
        value = value or "%Y-%m-%d %H:%M:%S"
        tz_fix_hours = self.LOCAL_TIME_ZONE - self._OS_LOCAL_TIME_ZONE
        tz_fix_seconds = tz_fix_hours * 3600
        if param == 'encode':
            # time string => timestamp
            if '%z' in value:
                msg = 'TimeParser Warning: time.struct_time do not have timezone info, so %z is nonsense'
                logger.warning(msg)
            return mktime(strptime(input_object, value)) - tz_fix_seconds
        elif param == 'decode':
            if isinstance(input_object,
                          str) and self.match_int_float.match(input_object):
                input_object = float(input_object)
            # timestamp => time string
            return strftime(value, localtime(input_object + tz_fix_seconds))
        else:
            return input_object


class ContextParser(BaseParser):
    """Return a value from input_object with given key(param), input_object often be set with context dict.

        :param input_object: will be ignore
        :param param: the key in context
        :type param: [str]
        :param value: default value if context not contains the key(param)
        :type value: [str]

    """
    name = 'context'

    @property
    def doc(self):
        return f'{self.__class__.__doc__}'

    def _parse(self, input_object, param, value):
        if not input_object or param not in input_object:
            return value
        return input_object[param]


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
            if string.startswith('JSON.'):
                string = string[5:]
            obj.code = _lib.jmespath_compile(string)
        elif mode == 'jsonpath':
            obj.code = _lib.jp_parse(string)
        elif mode == 'udf':
            obj.operator = UDFParser.get_code_mode(string)
            # for higher performance, pre-compile the code
            obj.code = compile(string, string, obj.operator.__name__)
        return obj


class JsonSerializable(dict):
    __slots__ = ()

    def __init__(self, **kwargs):
        super().__init__()
        self.update(kwargs)

    def to_dict(self):
        return dict(self)

    def dumps(self, *args, **kwargs):
        return GlobalConfig.json_dumps(self.to_dict(), *args, **kwargs)

    def to_json(self, *args, **kwargs):
        return self.dumps(*args, **kwargs)

    @classmethod
    def loads(cls, json_string):
        if isinstance(json_string, cls):
            return json_string
        elif isinstance(json_string, str):
            return cls(**GlobalConfig.json_loads(json_string))
        elif isinstance(json_string, dict):
            return cls(**json_string)
        else:
            raise TypeError('Only can be loaded from JSON / cls / dict.')

    @classmethod
    def from_json(cls, json_string):
        return cls.loads(json_string)


class ParseRule(JsonSerializable):
    """ParseRule should contain this params:
    1. a rule name, will be set as result key.
    2. chain_rules: a list of [[parser_name, param, value], ...], will be parse one by one.
    3. child_rules: a list of ParseRule instances, nested to save different values as named.
    4. context: a dict shared values by udf parse of the rules, only when udf value is null. May be shared from upstream CrawlerRule.

    Recursion parsing like a matryoshka doll.

    """
    __slots__ = ('context',)

    def __init__(self,
                 name: str,
                 chain_rules: List[List],
                 child_rules: List['ParseRule'] = None,
                 context: dict = None,
                 iter_parse_child: bool = False,
                 **kwargs):
        chain_rules = self.compile_codes(chain_rules or [])
        # ensure items of child_rules is ParseRule
        child_rules = [
            self.__class__(**parse_rule) for parse_rule in child_rules or []
        ]
        self.context = GlobalConfig.init_context(
        ) if context is None else context

        super().__init__(name=name,
                         chain_rules=chain_rules,
                         child_rules=child_rules,
                         **kwargs)
        if iter_parse_child:
            self['iter_parse_child'] = iter_parse_child

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
            "name": "crawler_rule",
            "request_args": {
                "method": "get",
                "url": "http://example.com",
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"
                }
            },
            "parse_rules": [{
                "name": "parse_rule",
                "chain_rules": [["css", "p", "$text"], ["python", "getitem", "[0]"]],
                "child_rules": [{
                    "name": "rule1",
                    "chain_rules": [["python", "getitem", "[:7]"]],
                    "child_rules": [
                        {
                            "name": "rule2",
                            "chain_rules": [["udf", "input_object[::-1]", ""]],
                            "child_rules": []
                        },
                        {
                            "name": "rule3",
                            "chain_rules": [["udf", "input_object[::-1]", ""]],
                            "child_rules": [{
                                "name": "rule4",
                                "chain_rules": [["udf", "input_object[::-1]", ""]],
                                "child_rules": []
                            }]
                        }
                    ]
                }]
            }],
            "regex": ""
        }

    Parse Result like:
        {'crawler_rule': {'parse_rule': {'rule1': {'rule2': 'od sihT', 'rule3': {'rule4': 'This do'}}}}}
    """
    __slots__ = ('context',)
    CHECK_STRATEGY = 'match'

    def __init__(self,
                 name: str,
                 request_args: Union[dict, str],
                 parse_rules: List[ParseRule] = None,
                 regex: str = None,
                 context: dict = None,
                 **kwargs):
        _request_args: dict = ensure_request(request_args)
        self.context = GlobalConfig.init_context(
        ) if context is None else context
        parse_rules = [
            ParseRule(context=self.context, **parse_rule)
            for parse_rule in parse_rules or []
        ]
        super().__init__(name=name,
                         parse_rules=parse_rules,
                         request_args=_request_args,
                         regex=regex or '',
                         **kwargs)

    def get_request(self, **request):
        if not request:
            return self['request_args']
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

    def check_regex(self, url, strategy=''):
        return getattr(self, strategy or self.CHECK_STRATEGY)(url)


class HostRule(JsonSerializable):
    __slots__ = ()

    def __init__(self,
                 host: str,
                 crawler_rules: Dict[str, CrawlerRule] = None,
                 **kwargs):
        crawler_rules = {
            crawler_rule['name']: CrawlerRule(**crawler_rule)
            for crawler_rule in (crawler_rules or {}).values()
        }
        super().__init__(host=host, crawler_rules=crawler_rules, **kwargs)

    def findall(self, url, strategy=''):
        # find all the rules which matched the given URL, strategy could be: match, search, findall
        return [
            rule for rule in self['crawler_rules'].values()
            if rule.check_regex(url, strategy)
        ]

    def find(self, url, strategy=''):
        # find only one rule which matched the given URL, strategy could be: match, search, findall
        rules = self.findall(url=url, strategy=strategy)
        if len(rules) > 1:
            raise ValueError(f'{url} matched more than 1 rule. {rules}')
        if rules:
            return rules[0]

    def search(self, url):
        return self.find(url, 'search')

    def match(self, url):
        return self.find(url, 'match')

    def add_crawler_rule(self, rule: CrawlerRule):
        if not isinstance(rule, CrawlerRule) and isinstance(rule, str):
            rule = CrawlerRule.loads(rule)
        self['crawler_rules'][rule['name']] = rule
        try:
            assert get_host(rule['request_args']['url']) == self[
                'host'], f'different host: {self["host"]} not match {rule["request_args"]["url"]}'
            assert self.match(rule['request_args']['url']) or self.search(
                rule['request_args']['url']
            ), f'regex {rule["regex"]} not match the given url: {rule["request_args"]["url"]}'
        except (ValueError, KeyError, AssertionError) as e:
            self['crawler_rules'].pop(rule['name'], None)
            raise e

    def pop_crawler_rule(self, rule_name: str):
        return self['crawler_rules'].pop(rule_name, None)


class Uniparser(object):
    """Parsers collection.
    """
    _RECURSION_CRAWL = True
    _DEFAULT_FREQUENCY = Frequency()
    _DEFAULT_ASYNC_FREQUENCY = AsyncFrequency()
    _HOST_FREQUENCIES: Dict[str, Union[Frequency, AsyncFrequency]] = {}

    def __init__(self,
                 request_adapter: Union[AsyncRequestAdapter,
                                        SyncRequestAdapter] = None,
                 parse_callback: Callable = None):
        """
        :param request_adapter: request_adapter for downloading, defaults to None
        :type request_adapter: Union[AsyncRequestAdapter, SyncRequestAdapter], optional
        :param parse_callback: the callback function called while parsing result. Accept 3 args: (rule, result, context)
        :type parse_callback: Callable, optional
        """
        self._prepare_default_parsers()
        self._prepare_custom_parsers()
        self.request_adapter = request_adapter
        self.parse_callback = parse_callback

    def _prepare_default_parsers(self):
        self.css = CSSParser()
        self.css1 = CSSSingleParser()
        self.selectolax = SelectolaxParser()
        self.selectolax1 = SelectolaxSingleParser()
        self.xml = XMLParser()
        self.re = RegexParser()
        self.jsonpath = JSONPathParser()
        self.objectpath = ObjectPathParser()
        self.jmespath = JMESPathParser()
        self.python = PythonParser()
        self.udf = UDFParser()
        self.loader = LoaderParser()
        self.time = TimeParser()
        self.context = ContextParser()

    def _prepare_custom_parsers(self):
        # handle the other sublclasses
        for parser in BaseParser.__subclasses__():
            if parser.name not in self.__dict__:
                self.__dict__[parser.name] = parser()

    # for alias
    @property
    def py(self):
        return self.python

    # for alias
    @property
    def se(self):
        return self.selectolax

    # for alias
    @property
    def se1(self):
        return self.selectolax1

    # for alias
    @property
    def json(self):
        return self.jmespath

    @property
    def parsers(self):
        return [
            parser for parser in self.__dict__.values()
            if isinstance(parser, BaseParser)
        ]

    @property
    def parser_classes(self):
        return BaseParser.__subclasses__()

    def parse_chain(self,
                    input_object,
                    chain_rules: List,
                    context: dict = None):
        context = GlobalConfig.init_context() if context is None else context
        for parser_name, param, value in chain_rules:
            parser: BaseParser = getattr(self, parser_name)
            if parser is None:
                msg = f'Unknown parser name: {parser_name}'
                logger.error(msg)
                raise UnknownParserNameError(msg)
            if parser_name == 'context':
                input_object = context
            elif context and parser_name == 'udf' and not value:
                value = context
            input_object = parser.parse(input_object, param, value)
        return input_object

    def parse_crawler_rule(self, input_object, rule: CrawlerRule, context=None):
        parse_rules = rule['parse_rules']
        parse_result: Dict[str, Any] = {}
        context = rule.context if context is None else context
        context.setdefault('request_args', rule['request_args'])
        # alias name for request_args in context
        context.setdefault('req', context['request_args'])
        context['parse_result'] = parse_result
        for parse_rule in parse_rules:
            parse_result[parse_rule['name']] = self.parse_parse_rule(
                input_object, parse_rule, context).get(parse_rule['name'])
        context.pop('parse_result', None)
        return {rule['name']: parse_result}

    def parse_parse_rule(self, input_object, rule: ParseRule, context=None):
        # if context, use context; else use rule.context
        context = rule.context if context is None else context
        input_object = self.parse_chain(input_object,
                                        rule['chain_rules'],
                                        context=context)
        if rule['name'] == GlobalConfig.__schema__ and input_object is not True:
            raise InvalidSchemaError(
                f'Schema check is not True: {repr(input_object)[:50]}')
        if rule['child_rules']:
            result: Dict[str, Any] = {rule['name']: {}}
            if rule.get('iter_parse_child', False):
                result[rule['name']] = []
                for partial_input_object in input_object:
                    partial_result = {}
                    for sub_rule in rule['child_rules']:
                        partial_result[
                            sub_rule['name']] = self.parse_parse_rule(
                                partial_input_object, sub_rule,
                                context=context).get(sub_rule['name'])
                    result[rule['name']].append(partial_result)
            else:
                for sub_rule in rule['child_rules']:
                    result[rule['name']][
                        sub_rule['name']] = self.parse_parse_rule(
                            input_object, sub_rule,
                            context=context).get(sub_rule['name'])
        else:
            result = {rule['name']: input_object}
        if self.parse_callback:
            return self.parse_callback(rule, result, context)
        return result

    def parse(self,
              input_object,
              rule_object: Union[CrawlerRule, ParseRule],
              context=None):
        context = rule_object.context if context is None else context
        if isinstance(rule_object, CrawlerRule):
            input_object = InputCallbacks.callback(
                text=input_object,
                context=context,
                callback_name=rule_object.get('input_callback'))
            return self.parse_crawler_rule(input_object=input_object,
                                           rule=rule_object,
                                           context=context)
        elif isinstance(rule_object, ParseRule):
            return self.parse_parse_rule(input_object=input_object,
                                         rule=rule_object,
                                         context=context)
        else:
            raise TypeError(
                'rule_object type should be CrawlerRule or ParseRule.')

    async def aparse_crawler_rule(self,
                                  input_object,
                                  rule: CrawlerRule,
                                  context=None):
        parse_rules = rule['parse_rules']
        parse_result: Dict[str, Any] = {}
        context = rule.context if context is None else context
        context.setdefault('request_args', rule['request_args'])
        # alias name for request_args in context
        context.setdefault('req', context['request_args'])
        context['parse_result'] = parse_result
        for parse_rule in parse_rules:
            temp_result = await self.aparse_parse_rule(input_object, parse_rule,
                                                       context)
            parse_result[parse_rule['name']] = temp_result.get(
                parse_rule['name'])
        context.pop('parse_result', None)
        return {rule['name']: parse_result}

    async def aparse_parse_rule(self,
                                input_object,
                                rule: ParseRule,
                                context=None):
        # if context, use context; else use rule.context
        context = rule.context if context is None else context
        input_object = await asyncio.get_event_loop().run_in_executor(
            None, self.parse_chain, input_object, rule['chain_rules'], context)
        input_object = await ensure_await_result(input_object)
        if rule['name'] == GlobalConfig.__schema__ and input_object is not True:
            raise InvalidSchemaError(
                f'Schema check is not True: {repr(input_object)[:50]}')
        if rule['child_rules']:
            result: Dict[str, Any] = {rule['name']: {}}
            if rule.get('iter_parse_child', False):
                result[rule['name']] = []
                for partial_input_object in input_object:
                    partial_result = {}
                    for sub_rule in rule['child_rules']:
                        temp_result = await self.aparse_parse_rule(
                            partial_input_object, sub_rule, context=context)
                        partial_result[sub_rule['name']] = temp_result.get(
                            sub_rule['name'])
                    result[rule['name']].append(partial_result)
            else:
                for sub_rule in rule['child_rules']:
                    temp_result = await self.aparse_parse_rule(input_object,
                                                               sub_rule,
                                                               context=context)
                    result[rule['name']][sub_rule['name']] = temp_result.get(
                        sub_rule['name'])
        else:
            result = {rule['name']: input_object}
        if self.parse_callback:
            if asyncio.iscoroutinefunction(self.parse_callback):
                coro = self.parse_callback(rule, result, context)
            else:
                coro = asyncio.get_event_loop().run_in_executor(
                    None, self.parse_callback, rule, result, context)
            return await coro
        return result

    async def aparse(self,
                     input_object,
                     rule_object: Union[CrawlerRule, ParseRule],
                     context=None):
        context = rule_object.context if context is None else context
        if isinstance(rule_object, CrawlerRule):
            input_object = await InputCallbacks.acallback(
                text=input_object,
                context=context,
                callback_name=rule_object.get('input_callback'))
            return await self.aparse_crawler_rule(input_object=input_object,
                                                  rule=rule_object,
                                                  context=context)
        elif isinstance(rule_object, ParseRule):
            return await self.aparse_parse_rule(input_object=input_object,
                                                rule=rule_object,
                                                context=context)
        else:
            raise TypeError(
                'rule_object type should be CrawlerRule or ParseRule.')

    def ensure_adapter(self, sync=True):
        if self.request_adapter:
            request_adapter = self.request_adapter
            if sync and isinstance(request_adapter, SyncRequestAdapter) or (
                    not sync) and isinstance(request_adapter,
                                             AsyncRequestAdapter):
                return self.request_adapter
        if sync:
            self.request_adapter = get_available_sync_request()()
        else:
            self.request_adapter = get_available_async_request()()
        return self.request_adapter

    def download(self,
                 crawler_rule: CrawlerRule = None,
                 request_adapter=None,
                 **request):
        request_adapter = request_adapter or self.ensure_adapter(sync=True)
        if not isinstance(request_adapter, SyncRequestAdapter):
            raise RuntimeError('bad request_adapter type')
        if isinstance(crawler_rule, CrawlerRule):
            request_args = crawler_rule.get_request(**request)
        else:
            request_args = request
        host = get_host(request_args['url'])
        if request_args['url'].startswith('http'):
            freq = self._HOST_FREQUENCIES.get(host, self._DEFAULT_FREQUENCY)
            with freq:
                with request_adapter as req:
                    input_object, resp = req.request(**request_args)
        else:
            # non-http request will skip the downloading process, request_args as input_object
            input_object, resp = request_args, None
        return input_object, resp

    def crawl(self,
              crawler_rule: CrawlerRule,
              request_adapter=None,
              context=None,
              **request):
        request_args = crawler_rule.get_request(**request)
        input_object, resp = self.download(None, request_adapter,
                                           **request_args)
        if isinstance(resp, Exception):
            return resp
        if context is None:
            context = crawler_rule.context
        else:
            for k, v in crawler_rule.context.items():
                if k not in context:
                    context[k] = v
        context['resp'] = resp
        context['request_args'] = request_args
        return self.parse(input_object, crawler_rule, context)

    async def adownload(self,
                        crawler_rule: CrawlerRule = None,
                        request_adapter=None,
                        **request):
        request_adapter = request_adapter or self.ensure_adapter(sync=False)
        if not isinstance(request_adapter, AsyncRequestAdapter):
            raise RuntimeError('bad request_adapter type')
        if isinstance(crawler_rule, CrawlerRule):
            request_args = crawler_rule.get_request(**request)
        else:
            request_args = request
        host = get_host(request_args['url'])
        if request_args['url'].startswith('http'):
            freq = self._HOST_FREQUENCIES.get(host,
                                              self._DEFAULT_ASYNC_FREQUENCY)
            async with freq:
                async with request_adapter as req:
                    input_object, resp = await req.request(**request_args)
        else:
            # non-http request will skip the downloading process, request_args as text
            input_object, resp = request_args, None
        return input_object, resp

    async def acrawl(self,
                     crawler_rule: CrawlerRule,
                     request_adapter=None,
                     context=None,
                     **request):
        request_args = crawler_rule.get_request(**request)
        input_object, resp = await self.adownload(None, request_adapter,
                                                  **request_args)
        if isinstance(resp, Exception):
            return resp
        if context is None:
            context = crawler_rule.context
        else:
            for k, v in crawler_rule.context.items():
                if k not in context:
                    context[k] = v
        context['resp'] = resp
        context['request_args'] = request_args
        return await self.aparse(input_object, crawler_rule, context)

    @classmethod
    def set_frequency(cls, host_or_url: str, n=0, interval=0):
        host = get_host(host_or_url, host_or_url)
        cls._HOST_FREQUENCIES[host] = Frequency(n, interval)

    @classmethod
    def set_async_frequency(cls, host_or_url: str, n=0, interval=0):
        host = get_host(host_or_url, host_or_url)
        cls._HOST_FREQUENCIES[host] = AsyncFrequency(n, interval)

    @classmethod
    def pop_frequency(cls, host_or_url: str, default=None):
        host = get_host(host_or_url, host_or_url)
        return cls._HOST_FREQUENCIES.pop(host, default)
