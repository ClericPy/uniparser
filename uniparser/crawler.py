# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from asyncio import ensure_future, wait
from json import dump
from pathlib import Path
from typing import List, Union
from warnings import warn

from .parsers import CrawlerRule, HostRule, JsonSerializable, Uniparser, json_loads
from .utils import (get_available_async_request, get_available_sync_request,
                    ensure_request, get_host, NotSet)


class RuleStorage(ABC):

    @abstractmethod
    def commit(self):
        pass

    @abstractmethod
    def get_crawler_rule(self, url, method='find'):
        pass

    @abstractmethod
    def add_crawler_rule(self, rule: CrawlerRule, commit=False):
        pass

    @abstractmethod
    def pop_crawler_rule(self, host: str, rule_name: str, commit=False):
        pass

    @abstractmethod
    def add_host_rule(self, rule: HostRule, commit=False):
        pass

    @abstractmethod
    def pop_host_rule(self, host: str, commit=False):
        pass


class JSONRuleStorage(JsonSerializable, RuleStorage):

    def __init__(self, host_rules: List[HostRule] = None, file_path=NotSet):
        super().__init__()
        host_rules = host_rules or []
        if file_path is None:
            self.file_path = None
        elif file_path is NotSet:
            self.file_path = Path.home() / 'host_rules.json'
        else:
            self.file_path = file_path
        if self.file_path:
            if self.file_path.is_file():
                with open(self.file_path, 'r') as f:
                    json_string = f.read()
                    if json_string:
                        for k, v in json_loads(json_string).items():
                            self[k] = HostRule(**v)
            else:
                warn(f'create storage file at {self.file_path}.')
                self.file_path.touch()
        for host_rule in host_rules or []:
            self[host_rule['host']] = HostRule(**host_rule)
        self.commit()

    def commit(self):
        if self.file_path:
            with open(self.file_path, 'w') as f:
                dump(self, f)

    def get_crawler_rule(self, url, method='find'):
        """return HostRule or None"""
        host = get_host(url)
        host_rule = self.get(host)
        if not host_rule:
            return None
        return getattr(host_rule, method)(url)

    def add_crawler_rule(self, rule: CrawlerRule, commit=False):
        url = rule.get('request_args', {}).get('url')
        if not url:
            warn(f'invalid url {url} in {rule}, add failed.')
            return False
        host = get_host(url)
        if not host:
            return False
        host_rule = self.setdefault(host, HostRule(host))
        host_rule.add_crawler_rule(rule)
        if commit:
            self.commit()
        return True

    def pop_crawler_rule(self, host: str, rule_name: str, commit=False):
        host_rule = self.get(host)
        if host_rule:
            crawler_rule = host_rule.pop_crawler_rule(rule_name, None)
            if commit:
                self.commit()
            return crawler_rule
        else:
            return None

    def add_host_rule(self, rule: HostRule, commit=False):
        self[rule['host']] = rule
        if commit:
            self.commit()

    def pop_host_rule(self, host: str, commit=False):
        rule = self.pop(host, None)
        if commit:
            self.commit()
        return rule


class Crawler(object):
    """
    Constraint Schema:

        1. If result has key name as `__link__`, will recursively call crawl/acrawl (_RECURSION_CRAWL=True).
            1.1 If __link__ type is tuple / list, will do [self.crawl(url) if url else None for url in __link__]
            1.2 New crawl result will be set in same level as __link__ named `__result__`
            1.3 Besides url, other request_args will use crawler_rule's
        2. If same url has different post-data, use nonsense param in url's tail to distinguish, like http://xxx.com#nonsense?nonsense=1
    """

    def __init__(self, uniparser: Uniparser = None,
                 storage: RuleStorage = None):
        self.uniparser = uniparser or Uniparser()
        self.storage = storage or JSONRuleStorage()

    def ensure_adapter(self, sync=True):
        if self.uniparser.request_adapter:
            return True
        if sync:
            self.uniparser.request_adapter = get_available_sync_request()()
        else:
            self.uniparser.request_adapter = get_available_async_request()()
        return bool(self.uniparser.request_adapter)

    def crawl(self, url, context=None, **request):
        """
        1. Input url.
        2. Find the rule.
        3. Return result or None.
        """
        assert self.ensure_adapter(sync=True)
        crawler_rule = self.storage.get_crawler_rule(url)
        if not crawler_rule:
            return
        result = self.uniparser.crawl(
            crawler_rule, url=url, context=context, **request)
        __link__ = result[crawler_rule['name']].pop('__link__', None)
        if __link__:
            if isinstance(__link__, (list, tuple)):
                result[crawler_rule['name']]['__result__'] = [
                    self.crawl(url) if url else None for url in __link__
                ]
            else:
                result[crawler_rule['name']]['__result__'] = self.crawl(
                    __link__)
        return result

    async def acrawl(self, url):
        """
        1. Input url.
        2. Find the rule.
        3. Return result or None.
        """
        assert self.ensure_adapter(sync=True)
        crawler_rule = self.storage.get_crawler_rule(url)
        if not crawler_rule:
            return
        result = await self.uniparser.acrawl(crawler_rule, url=url)
        __link__ = result[crawler_rule['name']].get('__link__')
        if __link__:
            if isinstance(__link__, (list, tuple)):
                tasks = [
                    ensure_future(self.acrawl(url)) if url else None
                    for url in __link__
                ]
                result[crawler_rule['name']]['request_result'] = [
                    (await task) if task else None for task in tasks
                ]
            else:
                result[crawler_rule['name']][
                    'request_result'] = await self.acrawl(__link__)
        return result
