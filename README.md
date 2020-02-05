# uniparser [![PyPI version](https://badge.fury.io/py/uniparser.svg)](https://badge.fury.io/py/uniparser)

Provide a universal solution for crawler platforms. Python3.6+ is needed.

## Install

> pip install uniparser -U

## Why?

1. Reduced the code quantity from plenty of similar crawlers & parsers.  Don't Repeat Yourself.
2. Make the parsing process of different parsers persistent.
3. Separating parsing processes from the downloading.
4. Provide a universal solution for crawler platforms.
5. Summarize common string parsing tools on the market.

## Quick Start

```python
# -*- coding: utf-8 -*-
import requests
from uniparser import Uniparser, CrawlerRule, HostRules
from urllib.parse import urlparse


def test_default_usage():
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


if __name__ == "__main__":
    test_default_usage()
```

## Parsers Collections

> to be finished...

## More Usage

> Talk is cheap, code == doc.  ^_^

Watch the examples: [test_parsers.py](https://github.com/ClericPy/uniparser/blob/master/test_parsers.py)

**Online Web UI for testing is coming soon...**

<!-- 

## Uniparser Test Console Demo

1. pip install bottle uniparser
2. python webui_bottle.py
3. open browser:  http://127.0.0.1:8080/ 

![1.png](1.png)

![2.png](2.png)

 -->

## TODO

- [x] Release to **pypi.org**
- [x] Add **github actions** for testing package
- [ ] Web UI for testing rules
- [ ] Complete the whole doc
