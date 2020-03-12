# [uniparser](https://github.com/ClericPy/uniparser) [![PyPI](https://img.shields.io/pypi/v/uniparser?style=plastic)](https://pypi.org/project/uniparser/)[![GitHub Workflow Status](https://img.shields.io/github/workflow/status/clericpy/uniparser/Python%20package?style=plastic)](https://github.com/ClericPy/uniparser/actions?query=workflow%3A%22Python+package%22)![PyPI - Wheel](https://img.shields.io/pypi/wheel/uniparser?style=plastic)![PyPI - Python Version](https://img.shields.io/pypi/pyversions/uniparser?style=plastic)![PyPI - Downloads](https://img.shields.io/pypi/dm/uniparser?style=plastic)![PyPI - License](https://img.shields.io/pypi/l/uniparser?style=plastic)

Provide a universal solution for crawler.

## Install

> pip install uniparser -U

## Why?

1. Reduced the code quantity from plenty of similar crawlers & parsers.  Don't Repeat Yourself.
2. Make the parsing process of different parsers persistent.
3. Separating the crawler code from main app code, no need to redeploy app when adding a new crawler.
4. Provide a universal solution for crawler platforms.
5. Summarize common string parsing tools on the market.
6. The implementation of web views is to be plug-in and portable, which means it can be mounted on other web apps as a [sub_app](https://fastapi.tiangolo.com/advanced/sub-applications-proxy/#mount-the-sub-application):
    1. `app.mount("/uniparser", uniparser_app)`

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

<details>
    <summary>Start page</summary>

![1.png](https://raw.githubusercontent.com/ClericPy/uniparser/master/imgs/1.png)

</details>

<details>
    <summary>Prepare the rules</summary>

![2.png](https://raw.githubusercontent.com/ClericPy/uniparser/master/imgs/2.png)

</details>

<details>
    <summary>Read the parse result</summary>

Show result as repr(result)

> {'HelloWorld': {'rule1-get-first-p': 'Customer name: ', 'rule2-get-legends': [' Pizza Size ', ' Pizza Toppings ']}}

As we can see, CrawlerRule's name is the root key, and ParseRule's name as the others.

</details>

### Async environment usage: [Fastapi](https://github.com/tiangolo/fastapi)

```python
import uvicorn
from uniparser.fastapi_ui import app

if __name__ == "__main__":
    uvicorn.run(app, port=8080)
    # http://127.0.0.1:8080
```

### Fastapi subapp usage

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

> Doc is on the way.

Test code: [test_parsers.py](https://github.com/ClericPy/uniparser/blob/master/test_parsers.py)

Advanced Usage Demo: [watchdogs](https://github.com/ClericPy/watchdogs)

> Generate parsers doc

```python
from uniparser import Uniparser

for i in Uniparser().parser_classes:
    print(f'## {i.__name__} ({i.name})\n\n```\n{i.__doc__}\n```')
```

## TODO

- [x] Release to pypi.org
  - [x] Upload dist with Web UI
- [x] Add **github actions** for testing package
- [x] Web UI for testing rules
- [ ] Complete the doc in detail
