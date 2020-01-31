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

    # test re sub @xxx
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
    # test python code without import
    result = uni.udf.parse(JSON, 'parse = lambda item: item.strip()[5:5+9]', '')
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
    test_re_parser()
    test_jsonpath_parser()
    test_objectpath_parser()
    test_udf_parser()
