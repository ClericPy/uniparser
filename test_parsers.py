# -*- coding: utf-8 -*-
import asyncio
import time
import warnings
from urllib.parse import urlparse

import requests
from bs4 import Tag

from uniparser import (Crawler, CrawlerRule, HostRule, JSONRuleStorage,
                       ParseRule, Uniparser)
from uniparser.crawler import RuleNotFoundError
from uniparser.exceptions import InvalidSchemaError
from uniparser.utils import (AiohttpAsyncAdapter, HTTPXAsyncAdapter,
                             HTTPXSyncAdapter, RequestsAdapter,
                             TorequestsAsyncAdapter, TorequestsSyncAdapter)

warnings.filterwarnings('ignore', 'TimeParser')

HTML = '''
<html><head><title >This is HTML title</title></head>
<body>
<p class="title" name="dromouse"><b>This is article title</b></p>
<p class="body">
first part
<a class="a" id="link1"><!--invisible comment--></a>
<a class="a" href="http://example.com/2" id="link2">a2</a>
<a class="a" href="http://example.com/3" id="link3">a3</a>
and they lived at the bottom of a well.</p>
<p class="body">...</p>
<div>
<span>d1</span>
</div>
<div>
<span>d2</span>
</div>
'''
JSON = '''
{
  "firstName": "John",
  "lastName" : "doe",
  "age"      : 26,
  "address"  : {
    "streetAddress": "naist street",
    "city"         : "Nara",
    "postalCode"   : "630-0192"
  },
  "prices": [
    {
      "price": 1
    },
    {
      "price": 2
    },
    {
      "price": 3
    }
  ],
  "phoneNums": [
    {
      "type"  : "iPhone",
      "number": "0123-4567-8888"
    },
    {
      "type"  : "home",
      "number": "0123-4567-8910"
    }
  ]
}
'''
XML = r'''
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>Channel title</title>
        <atom:link href="https://www.example.com/feed/" rel="self" type="application/rss+xml" />
        <link>https://www.example.com</link>
        <description>XML example</description>
        <lastBuildDate>Fri, 31 Jan 2020 08:02:33 +0000</lastBuildDate>
        <language>zh-CN</language>
        <sy:updatePeriod>
            hourly </sy:updatePeriod>
        <sy:updateFrequency>1</sy:updateFrequency>
        <item>
            <title>This is a title</title>
            <link>https://example.com/1/</link>
            <comments>https://example.com/1/#comments</comments>
            <pubDate>Fri, 31 Jan 2020 08:02:12 +0000</pubDate>
            <dc:creator>
                <![CDATA[creator]]>
            </dc:creator>
            <category>
                <![CDATA[category]]>
            </category>
            <guid isPermaLink="false">https://www.example.com/?p=35293</guid>
            <description>
                <![CDATA[ description ]]>
            </description>
            <content:encoded>
                <![CDATA[ <p><a href="https://example.com" class="home">homepage</a> some words </p>]]>
            </content:encoded>
        </item>
        <item>
            <title>This is a title2</title>
            <link>https://example.com/2/</link>
            <comments>https://example.com/1/#comments</comments>
            <pubDate>Fri, 31 Jan 2020 08:02:12 +0000</pubDate>
            <dc:creator>
                <![CDATA[creator]]>
            </dc:creator>
            <category>
                <![CDATA[category]]>
            </category>
            <guid isPermaLink="false">https://www.example.com/?p=35293</guid>
            <description>
                <![CDATA[ description ]]>
            </description>
            <content:encoded>
                <![CDATA[ <p><a href="https://example.com" class="home">homepage</a> some words </p>]]>
            </content:encoded>
        </item>
    </channel>
</rss>
'''
YAML = r'''
user1:
  name: a
  pwd: 123
user2:
  name: b
  pwd: 456
'''
TOML = """
# This is a TOML document.
title = "TOML Example"
[owner]
name = "ClericPy" # some comments
[example]
ports = [ 8001, 8001, 8002 ]
connection_max = 5000
enabled = true
"""


def test_css_parser():
    uni = Uniparser()
    # test get attribute
    result = uni.css.parse(HTML, 'a', '@href')
    # print(result)
    assert result == ['', 'http://example.com/2', 'http://example.com/3']

    # test get text
    result = uni.css.parse(HTML, 'a.a', '$text')
    # print(result)
    assert result == ['', 'a2', 'a3']

    # test get innerHTML, html
    result = uni.css.parse(HTML, 'a', '$innerHTML')
    # print(result)
    assert result == ['<!--invisible comment-->', 'a2', 'a3']
    result = uni.css.parse(HTML, 'a', '$html')
    # print(result)
    assert result == ['<!--invisible comment-->', 'a2', 'a3']

    # test get outerHTML, string
    result = uni.css.parse(HTML, 'a', '$outerHTML')
    # print(result)
    assert result == [
        '<a class="a" id="link1"><!--invisible comment--></a>',
        '<a class="a" href="http://example.com/2" id="link2">a2</a>',
        '<a class="a" href="http://example.com/3" id="link3">a3</a>'
    ]
    result = uni.css.parse(HTML, 'a', '$string')
    # print(result)
    assert result == [
        '<a class="a" id="link1"><!--invisible comment--></a>',
        '<a class="a" href="http://example.com/2" id="link2">a2</a>',
        '<a class="a" href="http://example.com/3" id="link3">a3</a>'
    ]

    # test get Tag object self
    result = uni.css.parse(HTML, 'a', '$self')
    # print(result)
    assert all([isinstance(i, Tag) for i in result])

    # test parsing Tag object
    tag = uni.css.parse(HTML, 'p.body', '$self')[0]
    result = uni.css.parse(tag, 'a', '$text')
    # print(result)
    assert result == ['', 'a2', 'a3']

    # test parsing list of input_object
    tags = uni.css.parse(HTML, 'div', '$self')
    result = uni.css.parse(tags, 'span', '$text')
    # print(result)
    assert result == [['d1'], ['d2']]


def test_xml_parser():
    uni = Uniparser()
    # test get attribute
    result = uni.xml.parse(XML, 'link', '@href')
    # print(result)
    assert result == ['https://www.example.com/feed/', '', '', '']

    # test get text
    result = uni.xml.parse(XML, 'creator', '$text')
    # print(result)
    assert result == [
        '\n                creator\n            ',
        '\n                creator\n            '
    ]

    # test get innerXML
    result = uni.xml.parse(XML, 'description', '$innerXML')
    # print(result)
    assert result == [
        'XML example', '\n                 description \n            ',
        '\n                 description \n            '
    ]

    # test get outerXML
    result = uni.xml.parse(XML, 'encoded', '$outerXML')
    # print(result)
    assert result == [
        '<encoded>\n                 &lt;p&gt;&lt;a href="https://example.com" class="home"&gt;homepage&lt;/a&gt; some words &lt;/p&gt;\n            </encoded>',
        '<encoded>\n                 &lt;p&gt;&lt;a href="https://example.com" class="home"&gt;homepage&lt;/a&gt; some words &lt;/p&gt;\n            </encoded>'
    ]

    # test get Tag object self
    result = uni.xml.parse(XML, 'link', '$self')
    # print(result)
    assert all([isinstance(i, Tag) for i in result])

    # test parsing Tag object
    tag = uni.xml.parse(XML, 'item', '$self')[0]
    result = uni.xml.parse(tag, 'title', '$text')
    # print(result)
    assert result == ['This is a title']

    # test parsing list of input_object
    tags = uni.xml.parse(XML, 'item', '$self')
    result = uni.xml.parse(tags, 'title', '$text')
    # print(result)
    assert result == [['This is a title'], ['This is a title2']]


def test_re_parser():
    uni = Uniparser()
    # ======================
    # test re findall without () group
    result = uni.re.parse(HTML, 'class="a"', '')
    # print(result)
    assert result == ['class="a"', 'class="a"', 'class="a"']

    # test re findall with () group
    result = uni.re.parse(HTML, 'class="(.*?)"', '')
    # print(result)
    assert result == ['title', 'body', 'a', 'a', 'a', 'body']

    # ======================
    # test re match $0
    result = uni.re.parse(HTML, 'class="(a)"', '$0')
    # print(result)
    assert result == ['class="a"', 'class="a"', 'class="a"']

    # test re match $1
    result = uni.re.parse(HTML, 'class="(a)"', '$1')
    # print(result)
    assert result == ['a', 'a', 'a']

    # ======================
    # test re sub @xxx, with group id \1
    result = uni.re.parse(HTML, '<a.*</a>', '')
    result = uni.re.parse(result, 'class="(a)"', r'@class="\1 b"')
    # print(result)
    assert result == [
        '<a class="a b" id="link1"><!--invisible comment--></a>',
        '<a class="a b" href="http://example.com/2" id="link2">a2</a>',
        '<a class="a b" href="http://example.com/3" id="link3">a3</a>'
    ]
    # ======================
    # test re.split
    result = uni.re.parse('a\t \nb  c', r'\s+', '-')
    # print(result)
    assert result == ['a', 'b', 'c']


def test_jsonpath_parser():
    uni = Uniparser()
    # test default value ''
    result = uni.jsonpath.parse(JSON, 'firstName', '')
    # print(result)
    assert result == ['John']

    # test value=$value
    result = uni.jsonpath.parse(JSON, 'firstName', '$value')
    # print(result)
    assert result == ['John']

    # test absolute path
    result = uni.jsonpath.parse(JSON, '$.address.city', '')
    # print(result)
    assert result == ['Nara']

    # test slice
    result = uni.jsonpath.parse(JSON, '$.phoneNums[1:]', '')
    # print(result)
    assert result == [{'type': 'home', 'number': '0123-4567-8910'}]

    # test filter large than
    result = uni.jsonpath.parse(JSON, '$.prices[?(@.price > 1)]', '')
    # print(result)
    assert result == [{'price': 2}, {'price': 3}]

    # test filter2
    result = uni.jsonpath.parse(JSON, '$.phoneNums[?(@.type = "iPhone")]', '')
    # print(result)
    assert result == [{'type': 'iPhone', 'number': '0123-4567-8888'}]

    # test other attributes, full_path
    result = uni.jsonpath.parse(JSON, 'firstName', '$full_path')
    # print(result)
    assert str(result) == "[Fields('firstName')]"


def test_objectpath_parser():
    uni = Uniparser()
    # test default value ''
    result = uni.objectpath.parse(JSON, '$.firstName', '')
    # print(result)
    assert result == 'John'

    # test absolute path
    result = uni.objectpath.parse(JSON, '$.address.city', '')
    # print(result)
    assert result == 'Nara'

    # test slice, not support...........
    # result = uni.objectpath.parse(JSON, '$.phoneNums[0:1]', '')
    # print(result)
    # assert result == [{'type': 'home', 'number': '0123-4567-8910'}]

    # test filter large than
    result = uni.objectpath.parse(JSON, '$.prices[@.price > 1]', '')
    # print(result)
    assert result == [{'price': 2}, {'price': 3}]

    # test filter2
    result = uni.objectpath.parse(JSON, '$.phoneNums[@.type is "iPhone"]', '')
    # print(result)
    assert result == [{'type': 'iPhone', 'number': '0123-4567-8888'}]


def test_jmespath_parser():
    uni = Uniparser()
    # test default value ''
    result = uni.jmespath.parse(JSON, 'firstName', '')
    # print(result)
    assert result == 'John'

    # test absolute path
    result = uni.jmespath.parse(JSON, 'address.city', '')
    # print(result)
    assert result == 'Nara'

    # test filter index
    result = uni.jmespath.parse(JSON, "prices[1].price", '')
    # print(result)
    assert result == 2

    # test filter slice
    result = uni.jmespath.parse(JSON, "prices[1:3].price", '')
    # print(result)
    assert result == [2, 3]

    # test attribute equals filter, use single-quote is ok, double-quote is invalid!
    result = uni.jmespath.parse(JSON, "phoneNums[?type == 'iPhone'].number", '')
    # print(result)
    assert result == ['0123-4567-8888']

    # filt by number, use ``
    result = uni.jmespath.parse(JSON, "prices[?price > `1`].price", '')
    # print(result)
    assert result == [2, 3]


def test_python_parser():
    uni = Uniparser()
    # ===================== test getitem =====================
    # getitem with index
    result = uni.python.parse([1, 2, 3], 'getitem', '[-1]')
    # print(result)
    assert result == 3
    # getitem with index
    result = uni.python.parse([1, 2, 3], 'get', '[-1]')
    # print(result)
    assert result == 3

    # getitem with slice
    result = uni.python.parse([1, 2, 3], 'getitem', '[:2]')
    # print(result)
    assert result == [1, 2]
    result = uni.python.parse([1, 2, 3, 4, 5], 'getitem', '[1::2]')
    # print(result)
    assert result == [2, 4]
    result = uni.python.parse({'a': '1'}, 'getitem', 'a')
    # print(result)
    assert result == '1'
    result = uni.python.parse({'a': '1'}, 'getitem', 'b')
    # print(result)
    # key error returns the bad key
    assert str(result) == "'b'" and isinstance(result, KeyError)

    # ===================== test split =====================
    # split by None
    result = uni.python.parse('a b\tc \n \td', 'split', '')
    # print(result)
    assert result == ['a', 'b', 'c', 'd']

    # split by 's'
    result = uni.python.parse('asbscsd', 'split', 's')
    # print(result)
    assert result == ['a', 'b', 'c', 'd']

    # ===================== test join =====================
    # join by ''
    result = uni.python.parse(['a', 'b', 'c', 'd'], 'join', '')
    # print(result)
    assert result == 'abcd'

    # ===================== test const =====================
    # const as input_object
    result = uni.python.parse(['a', 'b', 'c', 'd'], 'const', '')
    # print(result)
    assert result == ['a', 'b', 'c', 'd']
    # const as value
    result = uni.python.parse(['a', 'b', 'c', 'd'], 'const', 'abcd')
    # print(result)
    assert result == 'abcd'

    # ===================== test template =====================
    # const as input_object
    result = uni.python.parse(['a', 'b', 'c', 'd'], 'template',
                              '1 $input_object 2')
    # print(result)
    assert result == "1 ['a', 'b', 'c', 'd'] 2"
    # const as value
    result = uni.python.parse({
        'a': 'aaaa',
        'b': 'bbbb'
    }, 'template', '$a + $b = ?')
    # print(result)
    assert result == 'aaaa + bbbb = ?'
    # ===================== test index =====================
    result = uni.python.parse(['a', 'b', 'c', 'd'], 'index', '-1')
    # print(result)
    assert result == 'd'
    result = uni.python.parse({'a': 1}, 'index', 'a')
    # print(result)
    assert result == 1
    # ===================== test chain =====================
    result = uni.python.parse(['a', 'b', ['c', 'd']], 'chain', '')
    # print(result)
    assert result == ['a', 'b', 'c', 'd']
    result = uni.python.parse(['aaa', ['b'], ['c', 'd']], 'chain', '')
    # print(result)
    assert result == ['a', 'a', 'a', 'b', 'c', 'd']
    # ===================== test sort =====================
    result = uni.python.parse(*['adcb', 'sort', ''])
    # print(result)
    assert result == ['a', 'b', 'c', 'd']
    result = uni.python.parse(*[[1, 3, 2, 4], 'sort', 'desc'])
    # print(result)
    assert result == [4, 3, 2, 1]
    # ===================== test strip =====================
    result = uni.python.parse(*['aabbcc', 'strip', 'ac'])
    # print(result)
    assert result == 'bb'
    result = uni.python.parse(*['  bb\t\n', 'strip', ''])
    # print(result)
    assert result == 'bb'
    result = uni.python.parse(*['  \t\n', 'default', 'default'])
    # print(result)
    assert result == 'default'
    result = uni.python.parse(*['', 'default', 'default'])
    # print(result)
    assert result == 'default'
    result = uni.python.parse(*['a', 'default', 'default'])
    # print(result)
    assert result == 'a'

    # ===================== test base64 =====================
    result = uni.python.parse('abc', 'base64_encode', '')
    # print(result)
    assert result == 'YWJj'
    result = uni.python.parse('YWJj', 'base64_decode', '')
    # print(result)
    assert result == 'abc'

    # ===================== test parser.__call__() =====================
    result = uni.python('abc', 'base64_encode', '')
    # print(result)
    assert result == 'YWJj'
    result = uni.python('YWJj', 'base64_decode', '')
    # print(result)
    assert result == 'abc'

    # test index int
    assert uni.python(*['a', '0', 'b']) == 'a'
    assert uni.python(*['', '0', 'b']) == 'b'
    assert uni.python(*[None, '0', 'b']) == 'b'
    assert uni.python(*[{0: 'a'}, '0', 'a']) == 'a'
    assert uni.python(*[['a'], '0', 'b']) == 'a'


def test_udf_parser():
    uni = Uniparser()
    context = {'a': 1}
    # ===================== test dangerous words =====================
    assert uni.udf.parse('abcd', 'open', context) is NotImplemented
    assert uni.udf.parse('abcd', 'input', context) is NotImplemented
    assert uni.udf.parse('abcd', 'input_object', context) is not NotImplemented
    assert uni.udf.parse('abcd', 'exec', context) is NotImplemented
    assert uni.udf.parse('abcd', 'eval', context) is NotImplemented

    # ===================== test udf with context=====================
    # return a variable like context, one line code.
    result = uni.udf.parse('abcd', 'context', context)
    # print(result)
    assert result == context

    # return a variable like context(json), one line code.
    result = uni.udf.parse('abcd', 'context["a"]', '{"a": 1}')
    # print(result)
    assert result == 1

    # return a variable like context, lambda function.
    # context will be set to exec's globals
    result = uni.udf.parse(
        'abcd', 'parse = lambda input_object: (input_object, context)', context)
    # print(result)
    assert result == ('abcd', context)

    # return a variable like context, `def` function.
    # context will be set to exec's globals
    scode = '''
def parse(item):
    return (item, context)
'''
    result = uni.udf.parse('abcd', scode, context)
    # print(result)
    assert result == ('abcd', context)

    # ===================== test udf without context=====================
    # test python code without import; use `lambda` and `def`
    result = uni.udf.parse(JSON, 'parse = lambda item: item.strip()[5:5+9]', '')
    # print(result)
    assert result == 'firstName'
    # test python code without import; use `lambda` and `def`
    result = uni.udf.parse(JSON, 'def parse(item): return item.strip()[5:5+9]',
                           '')
    # print(result)
    assert result == 'firstName'

    # test python code with import, raise RuntimeError
    scode = '''
def parse(item):
    import json
    return json.loads(item)['firstName']
'''
    result = uni.udf.parse(JSON, scode, '')
    # print(result)
    assert result == 'John'

    # test python code with import, no raise RuntimeError
    uni.udf._ALLOW_IMPORT = True
    result = uni.udf.parse(JSON, scode, '')
    # print(result)
    assert result == 'John'

    # test python code without parse function, using eval
    result = uni.udf.parse('hello', 'input_object + " world."', '')
    # print(result)
    assert result == 'hello world.'

    # test alias obj
    result = uni.udf.parse('hello', 'obj + " world."', '')
    # print(result)
    assert result == 'hello world.'


def test_loader_parser():
    uni = Uniparser()
    # ===================== test getitem =====================
    # yaml
    result = uni.loader.parse(YAML, 'yaml', '')
    # print(result)
    assert result == {
        'user1': {
            'name': 'a',
            'pwd': 123
        },
        'user2': {
            'name': 'b',
            'pwd': 456
        }
    }

    # toml
    result = uni.loader.parse(TOML, 'toml', '{"decoder": null}')
    # print(result)
    assert result == {
        'title': 'TOML Example',
        'owner': {
            'name': 'ClericPy'
        },
        'example': {
            'ports': [8001, 8001, 8002],
            'connection_max': 5000,
            'enabled': True
        }
    }

    # json
    result = uni.loader.parse(JSON, 'json', '{"encoding": null}')
    # print(result)
    assert result['age'] == 26
    # base64 lib
    result = uni.loader.parse('a', 'b64encode', '')
    # print(result)
    assert result == 'YQ=='
    result = uni.loader.parse('YQ==', 'b64decode', '')
    # print(result)
    assert result == 'a'
    result = uni.loader.parse('a', 'b16encode', '')
    # print(result)
    assert uni.loader.parse(result, 'b16decode', '') == 'a'
    result = uni.loader.parse('a', 'b32encode', '')
    # print(result)
    assert uni.loader.parse(result, 'b32decode', '') == 'a'
    result = uni.loader.parse('a', 'b85encode', '')
    # print(result)
    assert uni.loader.parse(result, 'b85decode', '') == 'a'


def test_time_parser():
    timestamp = '1580732985.1873155'
    time_string = '2020-02-03 20:29:45'
    time_string_timezone = '2020-02-03T20:29:45 +0000'

    uni = Uniparser()
    uni.time.LOCAL_TIME_ZONE = +8

    # translate time_string into timestamp float
    result = uni.time.parse(time_string, 'encode', '')
    # print(result)
    assert int(result) == int(float(timestamp))

    result = uni.time.parse(timestamp, 'decode', '')
    # print(result)
    assert result == time_string

    result = uni.time.parse(result, 'encode', '')
    # print(result)
    assert int(result) == int(float(timestamp))

    result_time_zone = uni.time.parse(time_string_timezone, 'encode',
                                      '%Y-%m-%dT%H:%M:%S %z')
    # print(result_time_zone)
    assert int(result_time_zone) == int(float(timestamp))

    # =============================================
    # set a new timezone as local timezone +1, time will be 1 hour earlier than local.
    uni.time.LOCAL_TIME_ZONE += 1

    # same timestamp, different tz, earlier time_string will be larger than the old one.
    new_result = uni.time.parse(timestamp, 'decode', '')
    # print(new_result)
    # print(time_string)
    assert new_result > time_string

    # same time_string, different tz, earlier timestamp is less than the old one.
    new_result = uni.time.parse(time_string, 'encode', '')
    # print(new_result - int(float(timestamp)))
    assert new_result - int(float(timestamp)) == -1 * 3600


def test_crawler_rule():
    # Simple usage of Uniparser and CrawlerRule
    uni = Uniparser()
    crawler_rule = CrawlerRule('test', {
        'url': 'http://httpbin.org/get',
        'method': 'get'
    }, [{
        "name": "rule1",
        "chain_rules": [
            ['objectpath', 'JSON.url', ''],
            ['python', 'getitem', '[:4]'],
            [
                'udf',
                '(context["resp"].url, context["request_args"]["url"], input_object)',
                ''
            ],
        ],
        "child_rules": []
    }], '')
    resp = requests.request(timeout=3, **crawler_rule['request_args'])
    result = uni.parse(resp.text, crawler_rule, context={'resp': resp})
    # print(result)
    assert result == {
        'test': {
            'rule1':
                ('http://httpbin.org/get', 'http://httpbin.org/get', 'http')
        }
    }
    crawler_rule_json = crawler_rule.to_json()
    # print(crawler_rule_json)
    assert crawler_rule_json == r'{"name": "test", "parse_rules": [{"name": "rule1", "chain_rules": [["objectpath", "JSON.url", ""], ["python", "getitem", "[:4]"], ["udf", "(context[\"resp\"].url, context[\"request_args\"][\"url\"], input_object)", ""]], "child_rules": []}], "request_args": {"url": "http://httpbin.org/get", "method": "get"}, "regex": ""}'
    crawler_rule_dict = crawler_rule.to_dict()
    # print(crawler_rule_dict)
    # yapf: disable
    assert crawler_rule_dict == {'name': 'test', 'parse_rules': [{'name': 'rule1', 'chain_rules': [['objectpath', 'JSON.url', ''], ['python', 'getitem', '[:4]'], ['udf', '(context["resp"].url, context["request_args"]["url"], input_object)', '']], 'child_rules': []}], 'request_args': {'url': 'http://httpbin.org/get', 'method': 'get'}, 'regex': ''}
    # yapf: enable
    # saving some custom kwargs to crawler_rule
    crawler_rule['context'] = {'a': 1, 'b': {'c': 2}}
    # print(crawler_rule)
    # yapf: disable
    assert crawler_rule == {'name': 'test', 'parse_rules': [{'name': 'rule1', 'chain_rules': [['objectpath', 'JSON.url', ''], ['python', 'getitem', '[:4]'], ['udf', '(context["resp"].url, context["request_args"]["url"], input_object)', '']], 'child_rules': []}], 'request_args': {'url': 'http://httpbin.org/get', 'method': 'get'}, 'regex': '', 'context': {'a': 1, 'b': {'c': 2}}}
    # yapf: enable
    host_rule = HostRule('importpython.com')
    crawler_rule_json = '{"name":"C-1583501370","request_args":{"method":"get","url":"https://importpython.com/blog/feed/"},"parse_rules":[{"name":"text","chain_rules":[["xml","channel>item>title","$text"],["python","getitem","[0]"]],"childs":""},{"name":"url","chain_rules":[["xml","channel>item>link","$text"],["python","getitem","[0]"]],"childs":""}],"regex":"https://bad_url_host.com/blog/feed/$","encoding":""}'
    try:
        host_rule.add_crawler_rule(crawler_rule_json)
        assert NotImplementedError
    except AssertionError as err:
        assert err
    assert host_rule['crawler_rules'] == {}
    crawler_rule = CrawlerRule.loads(crawler_rule_json)
    crawler_rule['regex'] = r'https?://importpython\.com/.*'
    host_rule.add_crawler_rule(crawler_rule)
    assert host_rule['crawler_rules']
    assert not host_rule.findall('https://bad_url_host.com/')
    assert host_rule.findall('https://importpython.com/')


def test_default_usage():
    # 1. prepare for storage to save {'host': HostRule}
    uni = Uniparser()
    storage = {}
    test_url = 'http://httpbin.org/get'
    crawler_rule = CrawlerRule(
        'test_crawler_rule',
        {
            'url': 'http://httpbin.org/get',
            'method': 'get'
        },
        [{
            "name": "rule1",
            "chain_rules": [
                ['objectpath', 'JSON.url', ''],
                ['python', 'getitem', '[:4]'],
                ['udf', '(context["resp"].url, input_object)', ''],
            ],
            "child_rules": []
        }],
        'https?://httpbin.org/get',
    )
    host = urlparse(test_url).netloc
    host_rule = HostRule(host=host)
    host_rule.add_crawler_rule(crawler_rule)
    # same as: json_string = host_rule.to_json()
    json_string = host_rule.dumps()
    # print(json_string)
    assert json_string == r'{"host": "httpbin.org", "crawler_rules": {"test_crawler_rule": {"name": "test_crawler_rule", "parse_rules": [{"name": "rule1", "chain_rules": [["objectpath", "JSON.url", ""], ["python", "getitem", "[:4]"], ["udf", "(context[\"resp\"].url, input_object)", ""]], "child_rules": []}], "request_args": {"url": "http://httpbin.org/get", "method": "get"}, "regex": "https?://httpbin.org/get"}}}'
    # 2. add HostRule to storage, sometimes save on redis
    storage[host_rule['host']] = json_string
    # ============================================
    # start to crawl
    # 1. set a example url
    test_url1 = test_url
    # 2. find the HostRule
    json_string = storage.get(host)
    # 3. HostRule init: load from json
    # same as: host_rule = HostRule.from_json(json_string)
    host_rule = HostRule.loads(json_string)
    # print(crawler_rule)
    # 4. now search / match the url with existing rules
    crawler_rule = host_rule.search(test_url1)
    # print(crawler_rule)
    # yapf: disable
    assert crawler_rule == {'name': 'test_crawler_rule', 'parse_rules': [{'name': 'rule1', 'chain_rules': [['objectpath', 'JSON.url', ''], ['python', 'getitem', '[:4]'], ['udf', '(context["resp"].url, input_object)', '']], 'child_rules': []}], 'request_args': {'url': 'http://httpbin.org/get', 'method': 'get'}, 'regex': 'https?://httpbin.org/get'}
    # yapf: enable
    # print(host_rule.match(test_url1))
    assert crawler_rule == host_rule.match(test_url1)
    # 5. send request as crawler_rule's request_args, download the page source code
    resp = requests.request(**crawler_rule['request_args'])
    source_code = resp.text
    # 6. parse the whole crawler_rule as crawler_rule's with uniparser. set context with resp
    assert isinstance(crawler_rule, CrawlerRule)
    result = uni.parse(source_code, crawler_rule, context={'resp': resp})
    # print(result)
    assert result == {
        'test_crawler_rule': {
            'rule1': ('http://httpbin.org/get', 'http')
        }
    }
    # ===================== while search failed =====================
    # given a url not matched the pattern
    test_url2 = 'http://notmatch.com'
    crawler_rule2 = host_rule.search(test_url2)
    assert crawler_rule2 is None
    # ===================== shared context =====================
    # !!! use context by updating rule.context variable
    new_parse = '''
def parse(input_object):
    context['new_key'] = 'cleared'
    return 'ok'
    '''
    crawler_rule.context.update({'new_key': 'new_value'})
    crawler_rule.clear_parse_rules()
    crawler_rule.add_parse_rule({
        'name': 'rule1',
        'chain_rules': [['objectpath', 'JSON.url', ''],
                        ['python', 'getitem', '[:4]'], ['udf', new_parse, '']],
        'child_rules': []
    })
    result = uni.parse(source_code, crawler_rule)
    # print(result)
    assert result == {'test_crawler_rule': {'rule1': 'ok'}}
    # print(crawler_rule.context)
    # now the crawler_rule.context has been updated as 'cleared'.
    assert crawler_rule.context['new_key'] == 'cleared'


def test_uni_parser():
    uni = Uniparser()
    # ===================================================
    # 1. test Uniparser's parse_parse_rule
    rule1 = ParseRule(
        'rule1',
        [['python', 'getitem', '[:7]'],
         ['udf', 'str(input_object)+" "+context["key"]', '']],
        [],
    )
    result = uni.parse(HTML, rule1, {'key': 'hello world'})
    # print(result)
    assert result == {'rule1': '\n<html> hello world'}
    json_string = r'{"name": "rule1", "chain_rules": [["python", "getitem", "[:7]"], ["udf", "str(input_object)+\" \"+context[\"key\"]", ""]], "child_rules": []}'
    # print(rule1.dumps(), rule1.to_json(), json_string)
    assert rule1.dumps() == rule1.to_json() == json_string
    loaded_rule = ParseRule.from_json(json_string)
    assert isinstance(loaded_rule, ParseRule)
    assert loaded_rule == ParseRule.loads(json_string)
    # print(loaded_rule)
    # ===================================================
    # # 2. test Uniparser's nested parse_parse_rule
    rule2 = ParseRule('rule2', [['udf', 'input_object[::-1]', '']], [])
    rule1['child_rules'].append(rule2)
    rule3 = ParseRule(
        'rule3', [['udf', 'input_object[::-1]', '']],
        [ParseRule('rule4', [['udf', 'input_object[::-1]', '']], [])])
    rule1['child_rules'].append(rule3)
    # init parse rule
    parse_rule = ParseRule(
        'parse_rule',
        [['css', 'p', '$outerHTML'], ['css', 'b', '$text'],
         ['python', 'getitem', '[0]'], ['python', 'getitem', '[0]']],
        child_rules=[rule1])
    # print(parse_rule)
    result = uni.parse(HTML, parse_rule, {'key': 'hello world'})
    # print(result)
    # yapf: disable
    assert result == {'parse_rule': {'rule1': {'rule2': 'dlrow olleh si sihT', 'rule3': {'rule4': 'This is hello world'}}}}
    # yapf: enable

    # ===================================================
    # 3. test Uniparser's nested parse_crawler_rule
    crawler_rule = CrawlerRule('crawler_rule', 'http://example.com',
                               [parse_rule], '')
    result = uni.parse(HTML, crawler_rule, {'key': 'hello world'})
    # print(result)
    # yapf: disable
    assert result == {'crawler_rule': {'parse_rule': {'rule1': {'rule2': 'dlrow olleh si sihT', 'rule3': {'rule4': 'This is hello world'}}}}}
    # yapf: enable
    # print(crawler_rule.dumps())
    json_string = r'{"name": "crawler_rule", "parse_rules": [{"name": "parse_rule", "chain_rules": [["css", "p", "$outerHTML"], ["css", "b", "$text"], ["python", "getitem", "[0]"], ["python", "getitem", "[0]"]], "child_rules": [{"name": "rule1", "chain_rules": [["python", "getitem", "[:7]"], ["udf", "str(input_object)+\" \"+context[\"key\"]", ""]], "child_rules": [{"name": "rule2", "chain_rules": [["udf", "input_object[::-1]", ""]], "child_rules": []}, {"name": "rule3", "chain_rules": [["udf", "input_object[::-1]", ""]], "child_rules": [{"name": "rule4", "chain_rules": [["udf", "input_object[::-1]", ""]], "child_rules": []}]}]}]}], "request_args": {"method": "get", "url": "http://example.com"}, "regex": ""}'
    # print(crawler_rule.dumps(), crawler_rule.to_json(), json_string, sep='\n')
    assert crawler_rule.dumps() == crawler_rule.to_json() == json_string
    loaded_rule = CrawlerRule.from_json(json_string)
    assert CrawlerRule.loads(json_string) == CrawlerRule.from_json(
        json_string) == crawler_rule == loaded_rule
    assert isinstance(loaded_rule['parse_rules'][0], ParseRule)
    # test iter_parse_child
    parse_rule = ParseRule(
        'test_iter_parse', [['python', 'const', '']],
        iter_parse_child=True,
        child_rules=[ParseRule('child', [['udf', 'input_object * 2', '']])])
    result = uni.parse([1, 2, 3], parse_rule)
    # print(result)
    # yapf: disable
    assert result == {'test_iter_parse': [{'child': 2}, {'child': 4}, {'child': 6}]}
    # yapf: enable
    parse_rule = ParseRule(
        'test_iter_parse', [['python', 'const', '']],
        child_rules=[ParseRule('child', [['udf', 'input_object * 2', '']])])
    result = uni.parse([1, 2, 3], parse_rule)
    # print(result)
    assert result == {'test_iter_parse': {'child': [1, 2, 3, 1, 2, 3]}}

    # ===================================================
    # 4. test Uniparser.crawl & Uniparser.acrawl
    crawler_rule = CrawlerRule(
        **{
            'name': 'test_crawler_rule',
            'parse_rules': [{
                'name': 'rule1',
                'chain_rules': [
                    ['objectpath', 'JSON.url', ''
                    ], ['python', 'getitem', '[:4]'],
                    [
                        'udf',
                        '(context["resp"].url==context["request_args"]["url"], input_object)',
                        ''
                    ]
                ],
                'child_rules': []
            }],
            'request_args': {
                'url': 'http://httpbin.org/get',
                'method': 'get',
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'
                }
            },
            'regex': 'https?://httpbin.org/get.*'
        })
    result = uni.crawl(crawler_rule,
                       RequestsAdapter(),
                       url='http://httpbin.org/get?a=1')
    # print(result)
    assert result == {'test_crawler_rule': {'rule1': (True, 'http')}}

    async def _a_test():
        result = await uni.acrawl(crawler_rule,
                                  HTTPXAsyncAdapter(),
                                  url='http://httpbin.org/get?a=1')
        # print(result)
        assert result['test_crawler_rule']['rule1'][0]

    asyncio.get_event_loop().run_until_complete(_a_test())
    # 5. test the parse_result variable in context usage
    # yapf: disable
    crawler_rule = CrawlerRule.loads(r'''{"name":"HelloWorld","request_args":{"method":"get","url":"http://httpbin.org/get","headers":{"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"}},"parse_rules":[{"name":"rule1","chain_rules":[["objectpath","$.url",""]],"child_rules":[],"iter_parse_child":false},{"name":"rule2","chain_rules":[["udf","context['parse_result']['rule1']",""]],"child_rules":[],"iter_parse_child":false}],"regex":"http://httpbin.org/get$","encoding":""}''')
    result = uni.crawl(crawler_rule, RequestsAdapter(), None)
    # print(result)
    assert result == {'HelloWorld': {'rule1': 'http://httpbin.org/get', 'rule2': 'http://httpbin.org/get'}}
    # yapf: enable

    # 6. test url with non-http scheme, will ignore download
    # yapf: disable
    crawler_rule = CrawlerRule.loads(r'''{"name":"HelloWorld","request_args":{"method":"get","url":"http://httpbin.org/get","headers":{"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"}},"parse_rules":[{"name":"only_req","chain_rules":[["udf","obj['url'].startswith('ftp://')",""]],"child_rules":[],"iter_parse_child":false}],"regex":".*://httpbin.org/get$","encoding":""}''')
    # yapf: enable
    result = uni.crawl(crawler_rule, url='ftp://httpbin.org/get')
    # print(result)
    assert result == {'HelloWorld': {'only_req': True}}

    async def _test():
        return await uni.acrawl(crawler_rule, url='ftp://httpbin.org/get')

    assert asyncio.get_event_loop().run_until_complete(_test()) == {
        'HelloWorld': {
            'only_req': True
        }
    }

    # 7. test result parse_callback
    def parse_callback(rule, result) -> bool:
        return rule['name'] == 'A' and result == {"A": 'a'}

    uni = Uniparser(parse_callback=parse_callback)
    result = uni.parse('A', ParseRule('A', [['udf', 'obj.lower()', '']]))
    # print(result)
    assert result
    try:
        result = uni.parse('A', ParseRule('a', [['udf', 'obj.lower()', '']]))
        # print(result)
        assert result is False
    except InvalidSchemaError:
        pass


def test_sync_adapters():
    with RequestsAdapter() as req:
        text, r = req.request(method='get', url='http://httpbin.org/get')
        assert 'url' in text
        assert r.status_code == 200
    with HTTPXSyncAdapter() as req:
        text, r = req.request(method='get', url='http://httpbin.org/get')
        assert 'url' in text
        assert r.status_code == 200
    with TorequestsSyncAdapter() as req:
        text, r = req.request(method='get', url='http://httpbin.org/get')
        assert 'url' in text
        assert r.status_code == 200


def test_async_adapters():

    async def _a_test():
        async with HTTPXAsyncAdapter() as req:
            text, r = await req.request(method='get',
                                        url='http://httpbin.org/get')
            assert 'url' in text
            assert r.status_code == 200
        async with AiohttpAsyncAdapter() as req:
            text, r = await req.request(method='get',
                                        url='http://httpbin.org/get')
            assert 'url' in text
            assert r.status == 200
        async with TorequestsAsyncAdapter() as req:
            text, r = await req.request(method='get',
                                        url='http://httpbin.org/get')
            assert 'url' in text
            assert r.status == 200

    asyncio.get_event_loop().run_until_complete(_a_test())


def test_crawler_storage():
    crawler = Crawler()
    crawler_rule = CrawlerRule(
        **{
            'name': 'test_crawler_rule',
            'parse_rules': [{
                'name': 'rule1',
                'chain_rules': [[
                    'objectpath', 'JSON.url', ''
                ], ['python', 'getitem', '[:4]'
                   ], ['udf', '(context["resp"].url, input_object)', '']],
                'child_rules': []
            }],
            'request_args': {
                'url': 'http://httpbin.org/get',
                'method': 'get',
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'
                }
            },
            'regex': 'https?://httpbin.org/get'
        })
    crawler.storage.add_crawler_rule(crawler_rule, commit=1)
    new_crawler = Crawler()
    assert new_crawler.storage['httpbin.org']


def test_crawler():
    crawler = Crawler(storage=JSONRuleStorage.loads(
        r'{"www.python.org": {"host": "www.python.org", "crawler_rules": {"list": {"name":"list","request_args":{"method":"get","retry":3,"timeout":8,"url":"https://www.python.org/dev/peps/","headers":{"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"}},"parse_rules":[{"name":"__request__","chain_rules":[["css","#index-by-category #meta-peps-peps-about-peps-or-processes td.num>a","@href"],["re","^/","@https://www.python.org/"],["python","getitem","[:3]"]],"childs":""}],"regex":"^https://www.python.org/dev/peps/$","encoding":""}, "subs": {"name":"detail","request_args":{"method":"get","retry":3,"timeout":8,"url":"https://www.python.org/dev/peps/pep-0001/","headers":{"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"}},"parse_rules":[{"name":"title","chain_rules":[["css","h1.page-title","$text"],["python","getitem","[0]"]],"childs":""}],"regex":"^https://www.python.org/dev/peps/pep-\\d+$","encoding":""}}}}'
    ))
    # yapf: disable
    expected_result = {'list': {'__request__': ['https://www.python.org/dev/peps/pep-0001', 'https://www.python.org/dev/peps/pep-0004', 'https://www.python.org/dev/peps/pep-0005'], '__result__': [{'detail': {'title': 'PEP 1 -- PEP Purpose and Guidelines'}}, {'detail': {'title': 'PEP 4 -- Deprecation of Standard Modules'}}, {'detail': {'title': 'PEP 5 -- Guidelines for Language Evolution'}}]}}
    # yapf: enable

    def test_sync_crawler():
        # JSON will be saved if file_path!=None

        result = crawler.crawl('https://www.python.org/dev/peps/')
        # print(result)
        assert result == expected_result

    def test_async_crawler():

        async def _test():
            result = await crawler.acrawl('https://www.python.org/dev/peps/')
            # print(result)
            assert result == expected_result

        asyncio.get_event_loop().run_until_complete(_test())

    test_sync_crawler()
    test_async_crawler()

    # test crawl return Exception
    crawler = Crawler(storage=JSONRuleStorage.loads(
        r'{"www.python.org": {"host": "www.python.org", "crawler_rules": {"list": {"name":"list","request_args":{"method":"get","retry":3,"timeout":8,"url":"https://www.python.org/dev/peps/","headers":{"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"}},"parse_rules":[{"name":"list","chain_rules":[["css","#index-by-category #meta-peps-peps-about-peps-or-processes td.num>a","@href"],["re","^/","@https://www.python.org/"],["python","getitem","[:3]"]],"childs":""}],"regex":"^https://www.python.org/dev/peps/$","encoding":""}, "detail": {"name":"detail","request_args":{"method":"get","retry":3,"timeout":8,"url":"https://www.python.org/dev/peps/pep-0001/","headers":{"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"}},"parse_rules":[{"name":"title","chain_rules":[["css","h1.page-title","$text"],["python","getitem","[0]"]],"childs":""}],"regex":"^https://www.python.org/dev/peps/pep-\\d+$","encoding":""}}}}'
    ))
    result = crawler.crawl('https://www.python.org/')
    # print(result)
    assert isinstance(result, RuleNotFoundError)
    assert str(
        result) == 'No rule matched the given url: https://www.python.org/'
    crawler = Crawler(storage=JSONRuleStorage.loads(
        r'{"clericpyclericpyclericpyclericpy.com.cn": {"host": "clericpyclericpyclericpyclericpy.com.cn", "crawler_rules": {"list": {"name":"list","request_args":{"method":"get","retry":3,"timeout":8,"url":"https://clericpyclericpyclericpyclericpy.com.cn/dev/peps/","headers":{"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"}},"parse_rules":[{"name":"list","chain_rules":[["css","#index-by-category #meta-peps-peps-about-peps-or-processes td.num>a","@href"],["re","^/","@https://clericpyclericpyclericpyclericpy.com.cn/"],["python","getitem","[:3]"]],"childs":""}],"regex":"^https://clericpyclericpyclericpyclericpy.com.cn/dev/peps/$","encoding":""}}}}'
    ))
    result = crawler.crawl(
        'https://clericpyclericpyclericpyclericpy.com.cn/dev/peps/')
    # print(result)
    assert isinstance(result, BaseException)
    assert str(result).startswith('HTTPSConnectionPool')


def test_uni_parser_frequency():

    def test_sync_crawl():
        from concurrent.futures import ThreadPoolExecutor
        Uniparser.pop_frequency('https://www.baidu.com/robots.txt')
        uni = Uniparser()
        crawler_rule = CrawlerRule.loads(
            r'''{"name":"Test Frequency","request_args":{"method":"get","url":"https://www.baidu.com/robots.txt","headers":{"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"}},"parse_rules":[{"name":"__request__","chain_rules":[["udf","['https://www.baidu.com/robots.txt'] * 4",""]],"childs":""}],"regex":"^https://www.baidu.com/robots.txt","encoding":""}'''
        )
        start_time = time.time()
        pool = ThreadPoolExecutor()
        tasks = [pool.submit(uni.download, crawler_rule) for _ in range(5)]
        [task.result() for task in tasks]
        cost_time = time.time() - start_time
        # print(cost_time)
        assert cost_time < 2
        # set Frequency, download 2 times each 1 sec
        uni.set_frequency('https://www.baidu.com/robots.txt', 2, 1)
        start_time = time.time()
        pool = ThreadPoolExecutor()
        tasks = [pool.submit(uni.download, crawler_rule) for _ in range(5)]
        [task.result() for task in tasks]
        cost_time = time.time() - start_time
        # print(cost_time)
        assert cost_time > 2

    async def test_async_crawl():
        uni = Uniparser()
        uni.pop_frequency('https://www.baidu.com/robots.txt')
        crawler_rule = CrawlerRule.loads(
            r'''{"name":"Test Frequency","request_args":{"method":"get","url":"https://www.baidu.com/robots.txt","headers":{"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"}},"parse_rules":[{"name":"nonsense","chain_rules":[["udf","['https://www.baidu.com/robots.txt'] * 4",""]],"childs":""}],"regex":"^https://www.baidu.com/robots.txt","encoding":""}'''
        )
        start_time = time.time()
        tasks = [
            asyncio.ensure_future(uni.adownload(crawler_rule)) for _ in range(5)
        ]
        [await task for task in tasks]
        cost_time = time.time() - start_time
        # print(cost_time)
        assert cost_time < 2
        # set Frequency, download 2 times each 1 sec
        uni.set_async_frequency('https://www.baidu.com/robots.txt', 2, 1)
        start_time = time.time()
        tasks = [
            asyncio.ensure_future(uni.adownload(crawler_rule)) for _ in range(5)
        ]
        [await task for task in tasks]
        cost_time = time.time() - start_time
        # print(cost_time)
        assert cost_time > 2

    test_sync_crawl()
    asyncio.get_event_loop().run_until_complete(test_async_crawl())


def _partial_test_parser():
    from uniparser import Uniparser

    uni = Uniparser()
    args = [
        ['adcb', 'sort', ''],
    ]
    max_len = max([len(str(i)) for i in args])
    for i in args:
        print(f'{str(i):<{max_len}} => {uni.python.parse(*i)}')


if __name__ == "__main__":
    from uniparser.config import GlobalConfig
    GlobalConfig.GLOBAL_TIMEOUT = 5
    for case in (
            test_css_parser,
            test_xml_parser,
            test_re_parser,
            test_jsonpath_parser,
            test_objectpath_parser,
            test_jmespath_parser,
            test_python_parser,
            test_udf_parser,
            test_loader_parser,
            test_time_parser,
            test_uni_parser,
            test_crawler_rule,
            test_default_usage,
            test_crawler_storage,
            test_uni_parser_frequency,
            test_crawler,
    ):
        case()
        print(case.__name__, 'ok')
