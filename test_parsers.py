# -*- coding: utf-8 -*-

from uniparser import Uniparser
from uniparser.parsers import Tag

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

    # test parsing list of input_objects
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

    # test parsing list of input_objects
    tags = uni.xml.parse(XML, 'item', '$self')
    result = uni.xml.parse(tags, 'title', '$text')
    # print(result)
    assert result == [['This is a title'], ['This is a title2']]


def test_re_parser():
    uni = Uniparser()
    # test re findall without ()
    result = uni.re.parse(HTML, 'class="a"', '')
    # print(result)
    assert result == ['class="a"', 'class="a"', 'class="a"']

    # test re findall with ()
    result = uni.re.parse(HTML, 'class="(.*?)"', '')
    # print(result)
    assert result == ['title', 'body', 'a', 'a', 'a', 'body']

    # test re match $0
    result = uni.re.parse(HTML, 'class="(a)"', '$0')
    # print(result)
    assert result == ['class="a"', 'class="a"', 'class="a"']

    # test re match $1
    result = uni.re.parse(HTML, 'class="(a)"', '$1')
    # print(result)
    assert result == ['a', 'a', 'a']

    # test re sub @xxx, with group id \1
    result = uni.re.parse(HTML, '<a.*</a>', '')
    result = uni.re.parse(result, 'class="(a)"', r'@class="\1 b"')
    # print(result)
    assert result == [
        '<a class="a b" id="link1"><!--invisible comment--></a>',
        '<a class="a b" href="http://example.com/2" id="link2">a2</a>',
        '<a class="a b" href="http://example.com/3" id="link3">a3</a>'
    ]


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


def test_udf_parser():
    uni = Uniparser()
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


if __name__ == "__main__":
    test_css_parser()
    test_xml_parser()
    test_re_parser()
    test_jsonpath_parser()
    test_objectpath_parser()
    test_udf_parser()
