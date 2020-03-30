# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from asyncio import ensure_future
from concurrent.futures import ThreadPoolExecutor
from json import dump
from logging import getLogger
from pathlib import Path
from warnings import warn

from .config import GlobalConfig
from .exceptions import RuleNotFoundError
from .parsers import CrawlerRule, HostRule, JsonSerializable, Uniparser
from .utils import (AsyncRequestAdapter, NotSet, SyncRequestAdapter,
                    ensure_await_result, ensure_request, get_host)

logger = getLogger('uniparser')


class RuleStorage(ABC):

    @abstractmethod
    def commit(self):
        pass

    @abstractmethod
    def find_crawler_rule(self, url, method='find'):
        pass

    @abstractmethod
    def add_crawler_rule(self, rule: CrawlerRule, commit=False):
        pass

    @abstractmethod
    def pop_crawler_rule(self, rule: CrawlerRule, commit=False):
        pass

    @abstractmethod
    def add_host_rule(self, rule: HostRule, commit=False):
        pass

    @abstractmethod
    def pop_host_rule(self, host: str, commit=False):
        pass


class JSONRuleStorage(JsonSerializable, RuleStorage):

    def __init__(self, file_path=NotSet, **kwargs):
        super().__init__()
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
                        for host, host_rule in GlobalConfig.json_loads(
                                json_string).items():
                            self[host] = HostRule(**host_rule)
            else:
                msg = f'create storage file at {self.file_path}.'
                warn(msg)
                logger.warning(msg)
        for host, host_rule in kwargs.items():
            self[host] = HostRule(**host_rule)
        self.commit()

    def commit(self):
        if self.file_path:
            with open(self.file_path, 'w') as f:
                dump(self, f)

    def find_crawler_rule(self, url, method='find'):
        """return HostRule or None"""
        host = get_host(url)
        host_rule = self.get(host)
        if not host_rule:
            return None
        return getattr(host_rule, method)(url)

    def add_crawler_rule(self, rule: CrawlerRule, commit=False):
        url = rule.get('request_args', {}).get('url')
        if not url:
            msg = f'invalid url {url} in {rule}, add failed.'
            warn(msg)
            logger.warning(msg)
            return False
        host = get_host(url)
        if not host:
            return False
        host_rule = self.setdefault(host, HostRule(host))
        host_rule.add_crawler_rule(rule)
        if commit:
            self.commit()
        return True

    def pop_crawler_rule(self, rule: CrawlerRule, commit=False):
        host = get_host(rule['request_args'].get('url'))
        if host:
            host_rules = [self.get(host)]
        else:
            host_rules = list(self.values())
        for host_rule in host_rules:
            if host_rule:
                crawler_rule = host_rule.pop_crawler_rule(rule['name'])
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

        1. If result has key name as `__request__`, will recursively call crawl/acrawl (_RECURSION_CRAWL=True).
            1.1 If __request__ type is tuple / list, will do [self.crawl(url) if url else None for url in __request__]
            1.2 New crawl result will be set in same level as __request__ named `__result__`
            1.3 Besides url, other request_args will use crawler_rule's
        2. If same url has different post-data, use nonsense param in url's tail to distinguish, like http://xxx.com#nonsense?nonsense=1

    PS: __request__ can be reset by GlobalConfig.__request__ = '__new_request__'
    """

    def __init__(self, uniparser: Uniparser = None,
                 storage: RuleStorage = None):
        self.uniparser = uniparser or Uniparser()
        self.storage = storage or JSONRuleStorage()

    def ensure_adapter(self, sync=True):
        self.uniparser.ensure_adapter(sync=sync)
        if sync:
            return isinstance(self.uniparser.request_adapter,
                              SyncRequestAdapter)
        else:
            return isinstance(self.uniparser.request_adapter,
                              AsyncRequestAdapter)

    def crawl(self, request, context=None):
        """
        1. Input url.
        2. Find the rule.
        3. Return result or None.
        """
        if not request:
            return
        assert self.ensure_adapter(sync=True)
        request_args = ensure_request(request)
        url = request_args['url']
        crawler_rule = self.storage.find_crawler_rule(url)
        if not crawler_rule:
            return RuleNotFoundError(f'No rule matched the given url: {url}')
        result = self.uniparser.crawl(
            crawler_rule, context=context, **request_args)
        if isinstance(result, BaseException):
            return result
        __request__ = result[crawler_rule['name']].get(GlobalConfig.__request__)
        if __request__ and self.uniparser._RECURSION_CRAWL:
            if isinstance(__request__, (list, tuple)):
                with ThreadPoolExecutor() as pool:
                    tasks = [
                        pool.submit(self.crawl, request, context=context)
                        for request in __request__
                    ]
                    result[crawler_rule['name']][GlobalConfig.__result__] = [
                        task.result() for task in tasks
                    ]
            else:
                result[crawler_rule['name']][GlobalConfig.
                                             __result__] = self.crawl(
                                                 __request__, context=context)
        return result

    async def acrawl(self, request, context=None):
        """
        1. Input url.
        2. Find the rule.
        3. Return result or None.
        """
        if not request:
            return
        assert self.ensure_adapter(sync=False)
        request_args = ensure_request(request)
        url = request_args['url']
        crawler_rule = await ensure_await_result(
            self.storage.find_crawler_rule(url))
        if not crawler_rule:
            return RuleNotFoundError(f'No rule matched the given url: {url}')
        result = await self.uniparser.acrawl(
            crawler_rule, context=context, **request_args)
        if isinstance(result, BaseException):
            return result
        __request__ = result[crawler_rule['name']].get(GlobalConfig.__request__)
        if __request__ and self.uniparser._RECURSION_CRAWL:
            if isinstance(__request__, (list, tuple)):
                tasks = [
                    ensure_future(self.acrawl(request, context=context))
                    for request in __request__
                ]
                result[crawler_rule['name']][GlobalConfig.__result__] = [
                    (await task) if task else None for task in tasks
                ]
            else:
                result[crawler_rule['name']][GlobalConfig.
                                             __result__] = await self.acrawl(
                                                 __request__, context=context)
        return result
