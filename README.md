# uniparser [![PyPI version](https://badge.fury.io/py/uniparser.svg)](https://badge.fury.io/py/uniparser)

Provide a universal solution for crawler, **Python3.6+**.

## Install

> pip install uniparser -U

## Why?

1. Reduced the code quantity from plenty of similar crawlers & parsers.  Don't Repeat Yourself.
2. Make the parsing process of different parsers persistent.
3. Separating parsing processes from the downloading.
4. Provide a universal solution for crawler platforms.
5. Summarize common string parsing tools on the market.

## Feature List

1. Support most of popular parsers for HTML / XML / JSON / AnyString / Python object
   1. css (HTML)
      1. bs4
   2. xml
      1. lxml
   3. regex
   4. jsonpath
      1. jsonpath_ng
   5. objectpath
      1. objectpath
   6. jmespath
      1. jmespath
   7. time
   8. loader
      1. json / yaml / toml
         1. toml
         2. pyyaml
   9. *waiting for new ones...*
2. Request args persistence, support curl-string, single-url, dict, json.
3. A simple Web UI for generate & test CrawlerRule.
4. Serializable JSON rule class for saving the whole parsing process.
   1. Each ParseRule / CrawlerRule / HostRule subclass can be json.dumps to JSON for persistence.
   2. Therefore, they also can be loaded from JSON string.
   3. Nest relation of rule names will be treat as the result format. (Rule's result will be ignore if has childs.)

## Quick Start

> Crawl python [Meta-PEPs](https://www.python.org/dev/peps/#id6)

```python
# -*- coding: utf-8 -*-

import asyncio

import httpx
from uniparser import CrawlerRule, Uniparser, HTTPXAsyncAdapter

try:
    import uvloop
    uvloop.install()
except ImportError:
    pass

list_crawler_json = r'''
{
    "name": "SeedParser",
    "request_args": {
        "method": "get",
        "url": "https://www.python.org/dev/peps/",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"
        }
    },
    "parse_rules": [{
        "name": "links",
        "chain_rules": [[
            "css",
            "#index-by-category #meta-peps-peps-about-peps-or-processes td.num>a",
            "@href"
        ], ["re", "^/", "@https://www.python.org/"]],
        "childs": ""
    }],
    "regex": "^https?://www.python.org/dev/peps/$"
}

'''

detail_crawler_json = r'''
{
  "name": "SeedParser",
  "request_args": {
    "method": "get",
    "url": "https://www.python.org/dev/peps/pep-0001/",
    "headers": {
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"
    }
  },
  "parse_rules": [
    {
      "name": "title",
      "chain_rules": [
        [
          "css",
          "h1.page-title",
          "$text"
        ],
        [
          "python",
          "getitem",
          "[0]"
        ]
      ],
      "childs": ""
    },
    {
      "name": "author",
      "chain_rules": [
        [
          "css",
          "#content > div > section > article > table > tbody > tr:nth-child(3) > td",
          "$text"
        ],
        [
          "python",
          "getitem",
          "[0]"
        ]
      ],
      "childs": ""
    }
  ],
  "regex": "^https?://www.python.org/dev/peps/pep-\\d+/?$"
}
'''


class CrawlerTask(object):

    def __init__(self, uniparser: Uniparser, list_crawler_json,
                 detail_crawler_json):
        self.uni = uniparser
        self.list_crawler_rule = CrawlerRule.loads(list_crawler_json)
        self.detail_crawler_rule = CrawlerRule.loads(detail_crawler_json)

    async def crawl(self):
        # 1. get url list
        result = await self.uni.acrawl(self.list_crawler_rule)
        # print(result)
        # {'SeedParser': {'links': ['https://www.python.org/dev/peps/pep-0001', 'https://www.python.org/dev/peps/pep-0004', 'https://www.python.org/dev/peps/pep-0005', 'https://www.python.org/dev/peps/pep-0006', 'https://www.python.org/dev/peps/pep-0007', 'https://www.python.org/dev/peps/pep-0008', 'https://www.python.org/dev/peps/pep-0010', 'https://www.python.org/dev/peps/pep-0011', 'https://www.python.org/dev/peps/pep-0012']}}
        links = result['SeedParser']['links']
        tasks = [
            asyncio.ensure_future(
                self.uni.acrawl(self.detail_crawler_rule, url=link))
            for link in links
            if self.detail_crawler_rule.match(link)
        ]
        # print(tasks)
        results = [await task for task in tasks]
        return results


async def main():
    uni = Uniparser(HTTPXAsyncAdapter())
    crawler = CrawlerTask(uni, list_crawler_json, detail_crawler_json)
    results = await crawler.crawl()
    for result in results:
        print('Title :', result['SeedParser']['title'])
        print('Author:', result['SeedParser']['author'].strip())
        print('=' * 30)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

```

#### Print result

> Title : PEP 1 -- PEP Purpose and Guidelines
>
> Author: Barry Warsaw, Jeremy Hylton, David Goodger, Nick Coghlan
>
> ==============================
>
> Title : PEP 4 -- Deprecation of Standard Modules
>
> Author: Brett Cannon <brett at python.org>, Martin von LÃ¶wis <martin at v.loewis.de>
>
> ==============================
>
> ...

## Uniparser Test Console Demo (Web UI)

### 1. Prepare Environment

1. pip install bottle uniparser
2. python -m uniparser 8080

### 2. open browser  http://127.0.0.1:8080/ 

#### 2.1 Start page

![1.png](1.png)

#### 2.2 Prepare the rules

![2.png](2.png)

#### 2.3 Read the parse result

Show result as repr(result)

> {'HelloWorld': {'rule1-get-first-p': 'Customer name: ', 'rule2-get-legends': [' Pizza Size ', ' Pizza Toppings ']}}

As you see, Crawler Rule's name is the root key, and ParseRule's name as the others.

## More Usage

> Talk is cheap, code is doc. Poor time to write...

Watch the examples: [test_parsers.py](https://github.com/ClericPy/uniparser/blob/master/test_parsers.py)

## TODO

- [x] Release to pypi.org
  - [x] Upload dist with Web UI
- [x] Add **github actions** for testing package
- [x] Web UI for testing rules
- [ ] Complete the whole doc
