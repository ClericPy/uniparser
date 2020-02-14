# -*- coding: utf-8 -*-

from asyncio import ensure_future
from abc import ABC, abstractmethod
from json import dump
from pathlib import Path
from typing import List, Union
from warnings import warn

from .parsers import CrawlerRule, HostRule, JsonSerializable, Uniparser
from .utils import get_available_async_request, get_host


class RuleStorage(ABC):

    @abstractmethod
    def commit(self):
        pass

    @abstractmethod
    def get_crawler_rule(self, url, method='find'):
        pass

    @abstractmethod
    def add_rule(self, rule: Union[HostRule, CrawlerRule]):
        pass

    @abstractmethod
    def remove_rule(self, rule: Union[HostRule, CrawlerRule]):
        pass


class JSONRuleStorage(JsonSerializable, RuleStorage):

    def __init__(self, host_rules: List[HostRule] = None, filt_path=None):
        storage = {
            host_rule['host']: HostRule(**host_rule)
            for host_rule in host_rules or []
        }
        self.filt_path = filt_path or Path.home() / 'host_rules.json'
        if self.filt_path.is_file():
            with open(self.filt_path, 'r') as f:
                json_string = f.read()
                if json_string:
                    self.loads(json_string)
        else:
            warn(f'create storage file at {self.filt_path}.')
            self.filt_path.touch()
        super().__init__(**storage)
        self.commit()

    def commit(self):
        with open(self.filt_path, 'w') as f:
            dump(self, f)

    def get_crawler_rule(self, url, method='find'):
        """return HostRule or None"""
        host = get_host(url)
        host_rule = self.get(host)
        if not host_rule:
            return None
        return getattr(host_rule, method)(url)

    def add_rule(self, rule: Union[HostRule, CrawlerRule]):
        if isinstance(rule, CrawlerRule):
            url = rule.get('request_args', {}).get('url')
            if not url:
                warn(f'invalid url {url} in {rule}, add failed.')
                return False
            host = get_host(url)
            if not host:
                return False
            crawler_rules = self.setdefault(host, [])
            if rule not in crawler_rules:
                crawler_rules.append(rule)
                return True
            return False
        elif isinstance(rule, HostRule):
            host = rule['host']
            if not host:
                warn(f'invalid host {host} in {rule}, add failed.')
                return False
            exist_crawler_rules = self.setdefault(host, [])
            crawler_rules = rule.get('crawler_rules', [])
            for cr in crawler_rules:
                if cr not in exist_crawler_rules:
                    exist_crawler_rules.append(cr)
            return True
        else:
            warn(f'invalid rule type {type(rule)}, add failed.')
            return False
        return True

    def remove_rule(self, rule: Union[HostRule, CrawlerRule]):
        if isinstance(rule, CrawlerRule):
            url = rule.get('request_args', {}).get('url')
            if not url:
                warn(f'invalid url {url} in {rule}, remove failed.')
                return False
            host = get_host(url)
            if not host:
                return False
            crawler_rules = self.setdefault(host, [])
            if rule in crawler_rules:
                crawler_rules.remove(rule)
                return True
            return False
        elif isinstance(rule, HostRule):
            host = rule['host']
            if not host:
                warn(f'invalid host {host} in {rule}, remove failed.')
                return False
            exist_crawler_rules = self.setdefault(host, [])
            crawler_rules = rule.get('crawler_rules', [])
            for cr in crawler_rules:
                if cr in exist_crawler_rules:
                    exist_crawler_rules.remove(cr)
            return True
        else:
            warn(f'invalid rule type {type(rule)}, remove failed.')
            return False
        return True
