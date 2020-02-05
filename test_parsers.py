# -*- coding: utf-8 -*-
import requests
from uniparser import CrawlerRule, HostRules, ParseRule, Uniparser
from uniparser.parsers import Tag
import warnings

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

    # test get innerHTML
    result = uni.css.parse(HTML, 'a', '$innerHTML')
    # print(result)
    assert result == ['<!--invisible comment-->', 'a2', 'a3']

    # test get outerHTML
    result = uni.css.parse(HTML, 'a', '$outerHTML')
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


def test_python_parser():
    uni = Uniparser()
    # ===================== test getitem =====================
    # getitem with index
    result = uni.python.parse([1, 2, 3], 'getitem', '[-1]')
    # print(result)
    assert result == 3

    # getitem with slice
    result = uni.python.parse([1, 2, 3], 'getitem', '[:2]')
    # print(result)
    assert result == [1, 2]
    result = uni.python.parse([1, 2, 3, 4, 5], 'getitem', '[1::2]')
    # print(result)
    assert result == [2, 4]

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


def test_udf_parser():
    uni = Uniparser()
    context = {'a': 1}
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
    assert isinstance(result, Exception)

    # test python code with import, no raise RuntimeError
    uni.udf._ALLOW_IMPORT = True
    result = uni.udf.parse(JSON, scode, '')
    # print(result)
    assert result == 'John'

    # test python code without parse function, using eval
    result = uni.udf.parse('hello', 'input_object + " world."', '')
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


def test_crawler_rules():
    # Simple usage of Uniparser and CrawlerRule
    uni = Uniparser()
    crawler_rule = CrawlerRule('test', {
        'url': 'http://httpbin.org/get',
        'method': 'get'
    }, [{
        "name": "rule1",
        "rules_chain": [
            ['objectpath', 'JSON.url', ''],
            ['python', 'getitem', '[:4]'],
            ['udf', '(context.url, input_object)', ''],
        ],
        "child_rules": []
    }], '')
    resp = requests.request(timeout=3, **crawler_rule['request_args'])
    result = uni.parse(resp.text, crawler_rule, context=resp)
    # print(result)
    assert result == {'test': {'rule1': ('http://httpbin.org/get', 'http')}}
    crawler_rule_json = crawler_rule.to_json()
    # print(crawler_rule_json)
    assert crawler_rule_json == r'{"name": "test", "parse_rules": [{"name": "rule1", "rules_chain": [["objectpath", "JSON.url", ""], ["python", "getitem", "[:4]"], ["udf", "(context.url, input_object)", ""]], "child_rules": []}], "request_args": {"url": "http://httpbin.org/get", "method": "get"}, "regex": ""}'
    crawler_rule_dict = crawler_rule.to_dict()
    # print(crawler_rule_dict)
    assert crawler_rule_dict == {
        'name': 'test',
        'parse_rules': [{
            'name': 'rule1',
            'rules_chain': [['objectpath', 'JSON.url', ''],
                            ['python', 'getitem', '[:4]'],
                            ['udf', '(context.url, input_object)', '']],
            'child_rules': []
        }],
        'request_args': {
            'url': 'http://httpbin.org/get',
            'method': 'get'
        },
        'regex': ''
    }


def test_default_usage():
    from urllib.parse import urlparse

    # 1. prepare for storage to save {'host': HostRules}
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
            "rules_chain": [
                ['objectpath', 'JSON.url', ''],
                ['python', 'getitem', '[:4]'],
                ['udf', '(context.url, input_object)', ''],
            ],
            "child_rules": []
        }],
        'https?://httpbin.org/get',
    )
    host = urlparse(test_url).netloc
    hrs = HostRules(host=host)
    hrs.add(crawler_rule)
    # same as: json_string = hrs.to_json()
    json_string = hrs.dumps()
    # print(json_string)
    assert json_string == r'{"host": "httpbin.org", "crawler_rules": [{"name": "test_crawler_rule", "parse_rules": [{"name": "rule1", "rules_chain": [["objectpath", "JSON.url", ""], ["python", "getitem", "[:4]"], ["udf", "(context.url, input_object)", ""]], "child_rules": []}], "request_args": {"url": "http://httpbin.org/get", "method": "get"}, "regex": "https?://httpbin.org/get"}]}'
    # 2. add HostRules to storage, sometimes save on redis
    storage[hrs['host']] = json_string
    # ============================================
    # start to crawl
    # 1. set a example url
    test_url1 = test_url
    # 2. find the HostRules
    json_string = storage.get(host)
    # 3. HostRules init: load from json
    # same as: hrs = HostRules.from_json(json_string)
    hrs = HostRules.loads(json_string)
    # print(crawler_rule)
    # 4. now search / match the url with existing rules
    crawler_rule = hrs.search(test_url1)
    # print(crawler_rule)
    assert crawler_rule == {
        'name': 'test_crawler_rule',
        'parse_rules': [{
            'name': 'rule1',
            'rules_chain': [['objectpath', 'JSON.url', ''],
                            ['python', 'getitem', '[:4]'],
                            ['udf', '(context.url, input_object)', '']],
            'child_rules': []
        }],
        'request_args': {
            'url': 'http://httpbin.org/get',
            'method': 'get'
        },
        'regex': 'https?://httpbin.org/get'
    }
    # print(hrs.match(test_url1))
    assert crawler_rule == hrs.match(test_url1)
    # 5. send request as crawler_rule's request_args, download the page source code
    resp = requests.request(**crawler_rule['request_args'])
    source_code = resp.text
    # 6. parse the whole crawler_rule as crawler_rule's with uniparser. set context with resp
    assert isinstance(crawler_rule, CrawlerRule)
    result = uni.parse(source_code, crawler_rule, context=resp)
    # print(result)
    assert result == {
        'test_crawler_rule': {
            'rule1': ('http://httpbin.org/get', 'http')
        }
    }
    # ===================== while search failed =====================
    # given a url not matched the pattern
    test_url2 = 'http://notmatch.com'
    crawler_rule = hrs.search(test_url2)
    assert crawler_rule is None


def test_uni_parser():
    uni = Uniparser()
    # ===================================================
    # 1. test Uniparser's parse_parse_rule
    rule1 = ParseRule(
        'rule1',
        [['python', 'getitem', '[:7]'],
         ['udf', 'str(input_object)+" "+context', '']],
        [],
    )
    result = uni.parse(HTML, rule1, 'hello world')
    # print(result)
    assert result == {'rule1': '\n<html> hello world'}
    json_string = r'{"name": "rule1", "rules_chain": [["python", "getitem", "[:7]"], ["udf", "str(input_object)+\" \"+context", ""]], "child_rules": []}'
    assert rule1.dumps() == rule1.to_json() == json_string
    loaded_rule = ParseRule.from_json(json_string)
    assert isinstance(loaded_rule, ParseRule)
    assert loaded_rule == ParseRule.loads(json_string)
    # print(loaded_rule)
    # ===================================================
    # # 2. test Uniparser's nested parse_parse_rule
    rule2 = ParseRule('rule2', [['udf', 'input_object[::-1]', '']], [])
    rule1['child_rules'].append(rule2)
    parse_rule = ParseRule(
        'parse_rule',
        [['css', 'p', '$outerHTML'], ['css', 'b', '$text'],
         ['python', 'getitem', '[0]'], ['python', 'getitem', '[0]']], [rule1])
    result = uni.parse(HTML, parse_rule, 'hello world')
    # print(result)
    assert result == {
        'parse_rule': 'This is article title',
        '__child__': {
            'rule1': 'This is hello world',
            '__child__': {
                'rule2': 'dlrow olleh si sihT'
            }
        }
    }
    # ===================================================
    # 3. test Uniparser's nested parse_crawler_rule
    crawler_rule = CrawlerRule('crawler_rule', 'http://example.com',
                               [parse_rule], '')
    result = uni.parse(HTML, crawler_rule, 'hello world')
    # print(result)
    assert result == {
        'crawler_rule': {
            'parse_rule': 'This is article title',
            '__child__': {
                'rule1': 'This is hello world',
                '__child__': {
                    'rule2': 'dlrow olleh si sihT'
                }
            }
        }
    }
    json_string = r'{"name": "crawler_rule", "parse_rules": [{"name": "parse_rule", "rules_chain": [["css", "p", "$outerHTML"], ["css", "b", "$text"], ["python", "getitem", "[0]"], ["python", "getitem", "[0]"]], "child_rules": [{"name": "rule1", "rules_chain": [["python", "getitem", "[:7]"], ["udf", "str(input_object)+\" \"+context", ""]], "child_rules": [{"name": "rule2", "rules_chain": [["udf", "input_object[::-1]", ""]], "child_rules": []}]}]}], "request_args": {"method": "get", "url": "http://example.com", "headers": {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"}}, "regex": ""}'
    assert crawler_rule.dumps() == crawler_rule.to_json() == json_string
    loaded_rule = CrawlerRule.from_json(json_string)
    assert CrawlerRule.loads(json_string) == CrawlerRule.from_json(
        json_string) == crawler_rule == loaded_rule
    assert isinstance(loaded_rule['parse_rules'][0], ParseRule)


if __name__ == "__main__":
    test_css_parser()
    test_xml_parser()
    test_re_parser()
    test_jsonpath_parser()
    test_objectpath_parser()
    test_python_parser()
    test_udf_parser()
    test_loader_parser()
    test_time_parser()
    test_uni_parser()
    test_crawler_rules()
    test_default_usage()
