# [uniparser](https://github.com/ClericPy/uniparser)

[![PyPI](https://img.shields.io/pypi/v/uniparser?style=plastic)](https://pypi.org/project/uniparser/)[![GitHub Workflow Status](https://img.shields.io/github/workflow/status/clericpy/uniparser/Python%20package?style=plastic)](https://github.com/ClericPy/uniparser/actions?query=workflow%3A%22Python+package%22)![PyPI - Wheel](https://img.shields.io/pypi/wheel/uniparser?style=plastic)![PyPI - Python Version](https://img.shields.io/pypi/pyversions/uniparser?style=plastic)![PyPI - Downloads](https://img.shields.io/pypi/dm/uniparser?style=plastic)![PyPI - License](https://img.shields.io/pypi/l/uniparser?style=plastic)

Provides a general low-code page parsing solution.

> Backwards Compatibility Breaking Warning:
> 
> `uniparser` will not install any default parsers after version v3.0.0. You can install some of them manually ('selectolax', 'jsonpath-rw-ext', 'objectpath', 'bs4', 'toml', 'pyyaml>=5.3', 'lxml', 'jmespath'). This warning will keep 2 versions.

## Install

> `pip install uniparser -U`
> 
> or
> 
> `pip install uniparser[parsers]` with default 3rd parsers

## Why?

1. Reduced the code quantity from plenty of similar crawlers & parsers.  Don't Repeat Yourself.
2. Make the parsing process of different parsers persistent.
3. Separating the crawler code from main app code, no need to redeploy app when adding a new crawler.
4. Provide a universal solution for crawler platforms.
5. Summarize common string parsing tools on the market.
6. The implementation of web views is to be plug-in and portable, which means it can be mounted on other web apps as a [sub_app](https://fastapi.tiangolo.com/advanced/sub-applications-proxy/#mount-the-sub-application):
    1. `app.mount("/uniparser", uniparser_app)`
7. Here is the **low-code** web UI screenshot.

![demo.png](https://raw.githubusercontent.com/ClericPy/uniparser/master/imgs/demo.png)

## Feature List

1. Support most of popular parsers for HTML / XML / JSON / AnyString / Python object
   1. [Parser docs](https://github.com/ClericPy/uniparser/blob/master/parsers.md)
   2. <details>
        <summary>parser list</summary>
      
            1. css (HTML)
                1. bs4
            2. xml
                1. lxml
            3. regex
            4. jsonpath
                1. jsonpath-rw-ext
            5. objectpath
                1. objectpath
            6. jmespath
                1. jmespath
            7. time
            8. loader
                1. json / yaml / toml
                    1. toml
                    2. pyyaml
            9. udf
                1. source code for exec & eval which named as **parse**
            10. python
                1. some  common python methods, getitem, split, join...
            11. *waiting for new ones...*
      
      </details>
      
2. Request args persistence, support curl-string, single-url, dict, json.
3. A simple Web UI for generate & test CrawlerRule.
4. Serializable JSON rule class for saving the whole parsing process.
    1. Each ParseRule / CrawlerRule / HostRule subclass can be json.dumps to JSON for persistence.
    2. Therefore, they also can be loaded from JSON string.
    3. Nest relation of rule names will be treat as the result format. (Rule's result will be ignore if has childs.)
5. Rule Classes
    1. **JsonSerializable** is the base class for all the rules.
        1. dumps classmethod can dump self as a standard JSON string.
        1. loads classmethod can load self from a standard JSON string, which means the new object will has the methods as a rule.
    1. **ParseRule** is the lowest level for a parse mission, which contains how to parse a input_object. Sometimes it also has a list of ParseRule as child rules.
        1. Parse result is a dict that rule_name as key and result as value.
    1. **CrawlerRule** contains some ParseRules, which has 3 attributes besides the rule name:
        1. request_args tell the http-downloader how to send the request.
        2. parse_rules is a list of ParseRule, and the parsing result format is like {CrawlerRule_name: {ParseRule1['name']: ParseRule1_result, ParseRule2['name']: ParseRule2_result}}.
        3. regex tells how to find the crawler_rule with a given url.
    1. **HostRule** contains a dict like: {CrawlerRule['name']: CrawlerRule}, with the *find* method it can get the specified CrawlerRule with a given url.
    1. **JSONRuleStorage** is a simple storage way, which saved the HostRules in a JSON file. On the production environment this is not a good choice, maybe redis / mysql / mongodb can give a hand. 
6. **Uniparser** is the center console for the entire crawler process. It handled download middleware, parse middleware. Detail usage can be find at *uniparser.crawler.Crawler*, or have a loot at [Quick Start].
7. For custom settings, such as json loader, please update the uniparser.config.GlobalConfig.

## Quick Start

> Mission: Crawl python [Meta-PEPs](https://www.python.org/dev/peps/#id6)
>
> Only less than 25 lines necessary code besides the rules(which can be saved outside and auto loaded).
> 
> HostRules will be saved at `$HOME/host_rules.json` by default, not need to init every time.

<details>
    <summary>CrawlerRule JSON & Expected Result</summary>

```python
# These rules will be saved at `$HOME/host_rules.json`
crawler = Crawler(
    storage=JSONRuleStorage.loads(
        r'{"www.python.org": {"host": "www.python.org", "crawler_rules": {"main": {"name":"list","request_args":{"method":"get","url":"https://www.python.org/dev/peps/","headers":{"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"}},"parse_rules":[{"name":"__request__","chain_rules":[["css","#index-by-category #meta-peps-peps-about-peps-or-processes td.num>a","@href"],["re","^/","@https://www.python.org/"],["python","getitem","[:3]"]],"childs":""}],"regex":"^https://www.python.org/dev/peps/$","encoding":""}, "subs": {"name":"detail","request_args":{"method":"get","url":"https://www.python.org/dev/peps/pep-0001/","headers":{"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"}},"parse_rules":[{"name":"title","chain_rules":[["css","h1.page-title","$text"],["python","getitem","[0]"]],"childs":""}],"regex":"^https://www.python.org/dev/peps/pep-\\d+$","encoding":""}}}}'
    ))
expected_result = {
    'list': {
        '__request__': [
            'https://www.python.org/dev/peps/pep-0001',
            'https://www.python.org/dev/peps/pep-0004',
            'https://www.python.org/dev/peps/pep-0005'
        ],
        '__result__': [{
            'detail': {
                'title': 'PEP 1 -- PEP Purpose and Guidelines'
            }
        }, {
            'detail': {
                'title': 'PEP 4 -- Deprecation of Standard Modules'
            }
        }, {
            'detail': {
                'title': 'PEP 5 -- Guidelines for Language Evolution'
            }
        }]
    }
}

```

</details>

<details>
  <summary>The Whole Source Code</summary>

```python
from uniparser import Crawler, JSONRuleStorage
import asyncio

crawler = Crawler(
    storage=JSONRuleStorage.loads(
        r'{"www.python.org": {"host": "www.python.org", "crawler_rules": {"main": {"name":"list","request_args":{"method":"get","url":"https://www.python.org/dev/peps/","headers":{"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"}},"parse_rules":[{"name":"__request__","chain_rules":[["css","#index-by-category #meta-peps-peps-about-peps-or-processes td.num>a","@href"],["re","^/","@https://www.python.org/"],["python","getitem","[:3]"]],"childs":""}],"regex":"^https://www.python.org/dev/peps/$","encoding":""}, "subs": {"name":"detail","request_args":{"method":"get","url":"https://www.python.org/dev/peps/pep-0001/","headers":{"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"}},"parse_rules":[{"name":"title","chain_rules":[["css","h1.page-title","$text"],["python","getitem","[0]"]],"childs":""}],"regex":"^https://www.python.org/dev/peps/pep-\\d+$","encoding":""}}}}'
    ))
expected_result = {
    'list': {
        '__request__': [
            'https://www.python.org/dev/peps/pep-0001',
            'https://www.python.org/dev/peps/pep-0004',
            'https://www.python.org/dev/peps/pep-0005'
        ],
        '__result__': [{
            'detail': {
                'title': 'PEP 1 -- PEP Purpose and Guidelines'
            }
        }, {
            'detail': {
                'title': 'PEP 4 -- Deprecation of Standard Modules'
            }
        }, {
            'detail': {
                'title': 'PEP 5 -- Guidelines for Language Evolution'
            }
        }]
    }
}


def test_sync_crawler():
    result = crawler.crawl('https://www.python.org/dev/peps/')
    print('sync result:', result)
    assert result == expected_result


def test_async_crawler():

    async def _test():
        result = await crawler.acrawl('https://www.python.org/dev/peps/')
        print('sync result:', result)
        assert result == expected_result

    asyncio.run(_test())


test_sync_crawler()
test_async_crawler()

```

</details>


## Uniparser Rule Test Console (Web UI)

> 1. pip install bottle uniparser
> 2. python -m uniparser 8080
> 3. open browser => http://127.0.0.1:8080/

- Download URL

![1.png](https://raw.githubusercontent.com/ClericPy/uniparser/master/imgs/1.png)

- Parse HTML

![2.png](https://raw.githubusercontent.com/ClericPy/uniparser/master/imgs/2.png)

Show result as JSON

> {"CSS demo":{"Tag attribute":"post"}}

As we can see, CrawlerRule's name is the root key, and ParseRule's name as the others.

### Async environment usage: [Fastapi](https://github.com/tiangolo/fastapi)

```python
import uvicorn
from uniparser.fastapi_ui import app

if __name__ == "__main__":
    uvicorn.run(app, port=8080)
    # http://127.0.0.1:8080
```

### or Fastapi subapp usage

```python
import uvicorn
from fastapi import FastAPI
from uniparser.fastapi_ui import app as sub_app

app = FastAPI()

app.mount('/uniparser', sub_app)

if __name__ == "__main__":
    uvicorn.run(app, port=8080)
    # http://127.0.0.1:8080/uniparser/

```

## More Usage


Some Demos: **Click the dropdown buttons on top of the Web UI**

Test Code: [test_parsers.py](https://github.com/ClericPy/uniparser/blob/master/test_parsers.py)

Advanced Usage: [Create crawler rule](https://github.com/ClericPy/watchdogs/blob/master/quick_start.md#create-a-crawlerrule) for  [watchdogs](https://github.com/ClericPy/watchdogs)


> Generate parsers doc

```python
from uniparser import Uniparser

for i in Uniparser().parsers:
    print(f'## {i.__class__.__name__} ({i.name})\n\n```\n{i.doc}\n```')
```

## Benchmark

> Compare parsers and choose a faster one

```python
css:         2558 calls / sec, ['<a class="url" href="/">title</a>', 'a.url', '@href']
css:         2491 calls / sec, ['<a class="url" href="/">title</a>', 'a.url', '$text']
css:         2385 calls / sec, ['<a class="url" href="/">title</a>', 'a.url', '$innerHTML']
css:         2495 calls / sec, ['<a class="url" href="/">title</a>', 'a.url', '$html']
css:         2296 calls / sec, ['<a class="url" href="/">title</a>', 'a.url', '$outerHTML']
css:         2182 calls / sec, ['<a class="url" href="/">title</a>', 'a.url', '$string']
css:         2130 calls / sec, ['<a class="url" href="/">title</a>', 'a.url', '$self']
=================================================================================
css1:        2525 calls / sec, ['<a class="url" href="/">title</a>', 'a.url', '@href']
css1:        2402 calls / sec, ['<a class="url" href="/">title</a>', 'a.url', '$text']
css1:        2321 calls / sec, ['<a class="url" href="/">title</a>', 'a.url', '$innerHTML']
css1:        2256 calls / sec, ['<a class="url" href="/">title</a>', 'a.url', '$html']
css1:        2122 calls / sec, ['<a class="url" href="/">title</a>', 'a.url', '$outerHTML']
css1:        2142 calls / sec, ['<a class="url" href="/">title</a>', 'a.url', '$string']
css1:        2483 calls / sec, ['<a class="url" href="/">title</a>', 'a.url', '$self']
=================================================================================
selectolax:  15187 calls / sec, ['<a class="url" href="/">title</a>', 'a.url', '@href']
selectolax:  19164 calls / sec, ['<a class="url" href="/">title</a>', 'a.url', '$text']
selectolax:  19699 calls / sec, ['<a class="url" href="/">title</a>', 'a.url', '$html']
selectolax:  20659 calls / sec, ['<a class="url" href="/">title</a>', 'a.url', '$outerHTML']
selectolax:  20369 calls / sec, ['<a class="url" href="/">title</a>', 'a.url', '$self']
=================================================================================
selectolax1: 17572 calls / sec, ['<a class="url" href="/">title</a>', 'a.url', '@href']
selectolax1: 19096 calls / sec, ['<a class="url" href="/">title</a>', 'a.url', '$text']
selectolax1: 17997 calls / sec, ['<a class="url" href="/">title</a>', 'a.url', '$html']
selectolax1: 18100 calls / sec, ['<a class="url" href="/">title</a>', 'a.url', '$outerHTML']
selectolax1: 19137 calls / sec, ['<a class="url" href="/">title</a>', 'a.url', '$self']
=================================================================================
xml:         3171 calls / sec, ['<dc:creator><![CDATA[author]]></dc:creator>', 'creator', '$text']
=================================================================================
re:          220240 calls / sec, ['a a b b c c', 'a|c', '@b']
re:          334206 calls / sec, ['a a b b c c', 'a', '']
re:          199572 calls / sec, ['a a b b c c', 'a (a b)', '$0']
re:          203122 calls / sec, ['a a b b c c', 'a (a b)', '$1']
re:          256544 calls / sec, ['a a b b c c', 'b', '-']
=================================================================================
jsonpath:    28  calls / sec, [{'a': {'b': {'c': 1}}}, '$..c', '']
=================================================================================
objectpath:  42331 calls / sec, [{'a': {'b': {'c': 1}}}, '$..c', '']
=================================================================================
jmespath:    95449 calls / sec, [{'a': {'b': {'c': 1}}}, 'a.b.c', '']
=================================================================================
udf:         58236 calls / sec, ['a b c d', 'input_object[::-1]', '']
udf:         64846 calls / sec, ['a b c d', 'context["key"]', {'key': 'value'}]
udf:         55169 calls / sec, ['a b c d', 'md5(input_object)', '']
udf:         45388 calls / sec, ['["string"]', 'json_loads(input_object)', '']
udf:         50741 calls / sec, ['["string"]', 'json_loads(obj)', '']
udf:         48974 calls / sec, [['string'], 'json_dumps(input_object)', '']
udf:         41670 calls / sec, ['a b c d', 'parse = lambda input_object: input_object', '']
udf:         31930 calls / sec, ['a b c d', 'def parse(input_object): context["key"]="new";return context', {'key': 'new'}]
=================================================================================
python:      383293 calls / sec, [[1, 2, 3], 'getitem', '[-1]']
python:      350290 calls / sec, [[1, 2, 3], 'getitem', '[:2]']
python:      325668 calls / sec, ['abc', 'getitem', '[::-1]']
python:      634737 calls / sec, [{'a': '1'}, 'getitem', 'a']
python:      654257 calls / sec, [{'a': '1'}, 'get', 'a']
python:      642111 calls / sec, ['a b\tc \n \td', 'split', '']
python:      674048 calls / sec, [['a', 'b', 'c', 'd'], 'join', '']
python:      478239 calls / sec, [['aaa', ['b'], ['c', 'd']], 'chain', '']
python:      191430 calls / sec, ['python', 'template', '1 $input_object 2']
python:      556022 calls / sec, [[1], 'index', '0']
python:      474540 calls / sec, ['python', 'index', '-1']
python:      619489 calls / sec, [{'a': '1'}, 'index', 'a']
python:      457317 calls / sec, ['adcb', 'sort', '']
python:      494608 calls / sec, [[1, 3, 2, 4], 'sort', 'desc']
python:      581480 calls / sec, ['aabbcc', 'strip', 'a']
python:      419745 calls / sec, ['aabbcc', 'strip', 'ac']
python:      615518 calls / sec, [' \t a ', 'strip', '']
python:      632536 calls / sec, ['a', 'default', 'b']
python:      655448 calls / sec, ['', 'default', 'b']
python:      654189 calls / sec, [' ', 'default', 'b']
python:      373153 calls / sec, ['a', 'base64_encode', '']
python:      339589 calls / sec, ['YQ==', 'base64_decode', '']
python:      495246 calls / sec, ['a', '0', 'b']
python:      358796 calls / sec, ['', '0', 'b']
python:      356988 calls / sec, [None, '0', 'b']
python:      532092 calls / sec, [{0: 'a'}, '0', 'a']
=================================================================================
loader:      159737 calls / sec, ['{"a": "b"}', 'json', '']
loader:       38540 calls / sec, ['a = "a"', 'toml', '']
loader:        3972 calls / sec, ['animal: pets', 'yaml', '']
loader:      461297 calls / sec, ['a', 'b64encode', '']
loader:      412507 calls / sec, ['YQ==', 'b64decode', '']
=================================================================================
time:        39241 calls / sec, ['2020-02-03 20:29:45', 'encode', '']
time:        83251 calls / sec, ['1580732985.1873155', 'decode', '']
time:        48469 calls / sec, ['2020-02-03T20:29:45', 'encode', '%Y-%m-%dT%H:%M:%S']
time:        74481 calls / sec, ['1580732985.1873155', 'decode', '%b %d %Y %H:%M:%S']
```

## Tasks

- [x] Release to pypi.org
  - [x] Upload dist with Web UI
- [x] Add **github actions** for testing package
- [x] Web UI for testing rules
- [x] Complete the doc in detail
- [x] Compare each parser's performance
