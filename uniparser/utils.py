# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from argparse import ArgumentParser
from functools import partial
from inspect import isawaitable
from logging import getLogger
from re import compile as re_compile
from shlex import split as shlex_split
from typing import Dict, Union
from urllib.parse import urlparse

from .config import GlobalConfig
from .exceptions import InvalidSchemaError

logger = getLogger('uniparser')


class NotSet(object):
    __slots__ = ()

    def __bool__(self):
        return None


def get_host(url, default=None):
    if url and url.startswith('http'):
        return urlparse(url).netloc
    else:
        return default


class _Curl:
    """Curl args parser. **Use curlparse function directly.**
    Copy from torequests.
    """

    parser = ArgumentParser()
    parser.add_argument("curl")
    parser.add_argument("url")
    parser.add_argument("-X", "--method", default="get")
    parser.add_argument("-A", "--user-agent")
    parser.add_argument("-u", "--user")  # <user[:password]>
    parser.add_argument("-x", "--proxy")  # proxy.com:port
    parser.add_argument("-d", "--data")
    parser.add_argument("-F", "--form")
    parser.add_argument("--data-binary")
    parser.add_argument("--connect-timeout", type=float)
    parser.add_argument("-H", "--header", action="append",
                        default=[])  # key: value
    parser.add_argument("--compressed", action="store_true")


def curlparse(string, encoding="utf-8"):
    """Translate curl-string into dict of request.
        :param string: standard curl-string, like `r'''curl ...'''`.
        :param encoding: encoding for post-data encoding.
    Copy from torequests.

    Basic Usage::
      >>> from torequests.utils import curlparse
      >>> curl_string = '''curl 'https://p.3.cn?skuIds=1&nonsense=1&nonce=0' -H 'Pragma: no-cache' -H 'DNT: 1' -H 'Accept-Encoding: gzip, deflate' -H 'Accept-Language: zh-CN,zh;q=0.9' -H 'Upgrade-Insecure-Requests: 1' -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8' -H 'Cache-Control: no-cache' -H 'Referer: https://p.3.cn?skuIds=1&nonsense=1&nonce=0' -H 'Cookie: ASPSESSIONIDSQRRSADB=MLHDPOPCAMBDGPFGBEEJKLAF' -H 'Connection: keep-alive' --compressed'''
      >>> request_args = curlparse(curl_string)
      >>> request_args
      {'url': 'https://p.3.cn?skuIds=1&nonsense=1&nonce=0', 'headers': {'Pragma': 'no-cache', 'Dnt': '1', 'Accept-Encoding': 'gzip, deflate', 'Accept-Language': 'zh-CN,zh;q=0.9', 'Upgrade-Insecure-Requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8', 'Cache-Control': 'no-cache', 'Referer': 'https://p.3.cn?skuIds=1&nonsense=1&nonce=0', 'Cookie': 'ASPSESSIONIDSQRRSADB=MLHDPOPCAMBDGPFGBEEJKLAF', 'Connection': 'keep-alive'}, 'method': 'get'}
      >>> import requests
      >>> requests.request(**request_args)
      <Response [200]>
    """
    assert "\n" not in string, 'curl-string should not contain \\n, try r"...".'
    if string.startswith("http"):
        return {"url": string, "method": "get"}
    try:
        lex_list = shlex_split(string.strip())
    except ValueError as e:
        if str(e) == 'No closing quotation' and string.count("'") % 2 != 0:
            new_err = "If `data` has single-quote ('), the `data` should be quote by double-quote, and add the `backslash`(\\) before original \"."
            e.args += (new_err,)
        raise e
    args, unknown = _Curl.parser.parse_known_args(lex_list)
    requests_args = {}
    headers = {}
    requests_args["url"] = args.url
    for header in args.header:
        key, value = header.split(":", 1)
        headers[key.title()] = value.strip()
    if args.user_agent:
        headers["User-Agent"] = args.user_agent
    if headers:
        requests_args["headers"] = headers
    if args.user:
        requests_args["auth"] = tuple(
            u for u in args.user.split(":", 1) + [""])[:2]
    # if args.proxy:
    # pass
    data = args.data or args.data_binary or args.form
    if data:
        if data.startswith("$"):
            data = data[1:]
        args.method = "post"
        data = data.encode(
            'latin-1',
            'backslashreplace').decode('unicode-escape').encode(encoding)
        requests_args["data"] = data
    requests_args["method"] = args.method.lower()
    if args.connect_timeout:
        requests_args["timeout"] = args.connect_timeout
    return requests_args


def ensure_request(request) -> dict:
    """Used for requests.request / Requests.request with **ensure_request(request)
    :param request: dict or curl-string or url

    Copy from torequests.

    >>> from torequests.utils import ensure_request
    >>> ensure_request('''curl http://test.com''')
    {'url': 'http://test.com', 'method': 'get'}
    >>> ensure_request('http://test.com')
    {'method': 'get', 'url': 'http://test.com'}
    >>> ensure_request({'method': 'get', 'url': 'http://test.com'})
    {'method': 'get', 'url': 'http://test.com'}
    >>> ensure_request({'url': 'http://test.com'})
    {'url': 'http://test.com', 'method': 'get'}
    """
    result = {}
    if isinstance(request, dict):
        result = request
    elif isinstance(request, str):
        request = request.strip()
        if request.startswith("http"):
            result = {"method": "get", "url": request}
        elif request.startswith("curl "):
            result = curlparse(request)
        else:
            try:
                result = GlobalConfig.json_loads(request)
            except GlobalConfig.JSONDecodeError:
                pass
    else:
        return result
    if result:
        result["method"] = result.setdefault("method", "get").lower()
    return result


class SyncRequestAdapter(ABC):
    """Only one purpose: accept request_args, sending request, return Response object or Request Exception.
    Usage:

        with XXAdapter() as req:
            text, resp = req.request(**request_args)
    """

    def request(self, **request_args):
        text, resp = '', None
        retry = request_args.pop('retry', 0)
        encoding = request_args.pop('encoding', None)
        request_args.setdefault('timeout', GlobalConfig.GLOBAL_TIMEOUT)
        for _ in range(retry + 1):
            try:
                resp = self.session.request(**request_args)
                if encoding:
                    text = resp.content.decode(encoding)
                else:
                    text = resp.text
                break
            except self.error as e:
                text = str(e)
                resp = e
                continue
        return text, resp

    @abstractmethod
    def __enter__(self):
        raise NotImplementedError

    @abstractmethod
    def __exit__(self, *args):
        raise NotImplementedError


class AsyncRequestAdapter(ABC):
    """Only one purpose: accept request_args, sending request, return Response object or Request Exception.
    Usage:

        async with XXAdapter() as req:
            text, resp = await req.request(**request_args)
            """

    @abstractmethod
    async def __aenter__(self):
        raise NotImplementedError

    @abstractmethod
    async def __aexit__(self, *args):
        raise NotImplementedError

    async def request(self, **request_args):
        text, resp = '', None
        retry = request_args.pop('retry', 0)
        encoding = request_args.pop('encoding', None)
        request_args.setdefault('timeout', GlobalConfig.GLOBAL_TIMEOUT)
        for _ in range(retry + 1):
            try:
                resp = await self.session.request(**request_args)
                if encoding:
                    text = resp.content.decode(encoding)
                else:
                    text = resp.text
                break
            except self.error as e:
                text = str(e)
                resp = e
                continue
        return text, resp


class RequestsAdapter(SyncRequestAdapter):

    def __init__(self, session=None, **kwargs):
        from requests import RequestException, Session
        if session:
            self.session = session
        else:
            self.session = Session(**kwargs)
        self.error = (RequestException, InvalidSchemaError)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def __del__(self, *args):
        self.session.close()


class HTTPXSyncAdapter(SyncRequestAdapter):

    def __init__(self, session=None, **kwargs):
        self.session = session
        from httpx import Client, HTTPError
        if session:
            self.session = session
        else:
            self.session = Client(**kwargs)
        self.error = (HTTPError, InvalidSchemaError)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def __del__(self):
        if self.session:
            self.session.close()


class TorequestsSyncAdapter(SyncRequestAdapter):

    def __init__(self, session=None, **kwargs):
        from torequests.main import tPool, FailureException
        if session:
            self.session = session
        else:
            self.session = tPool(catch_exception=False, **kwargs)
        self.error = (FailureException, InvalidSchemaError)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class HTTPXAsyncAdapter(AsyncRequestAdapter):

    def __init__(self, session=None, **kwargs):
        from httpx import AsyncClient, HTTPError
        self.session = session
        self.session_class = AsyncClient(**kwargs)
        self.error = (HTTPError, InvalidSchemaError)

    async def __aenter__(self):
        if not self.session:
            self.session = await self.session_class.__aenter__()
        return self

    async def __aexit__(self, *args):
        await self.session.aclose()


class AiohttpAsyncAdapter(AsyncRequestAdapter):

    def __init__(self, session=None, **kwargs):
        from aiohttp import ClientSession, ClientError
        self.session = session
        self.session_class = partial(ClientSession, **kwargs)
        self.error = (ClientError, InvalidSchemaError)

    async def __aenter__(self):
        if not self.session:
            self.session = self.session_class()
        return self

    async def __aexit__(self, *args):
        pass

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    def __del__(self, *args):
        _exhaust_simple_coro(self.close())

    async def request(self, **request_args):
        """non-request-like api"""
        text, resp = '', None
        retry = request_args.pop('retry', 0)
        encoding = request_args.pop('encoding', None)
        request_args.setdefault('timeout', GlobalConfig.GLOBAL_TIMEOUT)
        for _ in range(retry + 1):
            try:
                resp = await self.session.request(**request_args)
                text = await resp.text(encoding=encoding)
                break
            except self.error as e:
                text = str(e)
                resp = e
                continue
        return text, resp


class TorequestsAsyncAdapter(AsyncRequestAdapter):

    def __init__(self, session=None, **kwargs):
        from torequests.dummy import Requests, FailureException
        if session:
            kwargs['session'] = session
        self.req = Requests(catch_exception=False, **kwargs)
        self.error = (FailureException, InvalidSchemaError)

    async def __aenter__(self):
        await self.req.session
        return self

    async def __aexit__(self, *args):
        pass

    async def request(self, **request_args):
        text, resp = '', None
        retry = request_args.pop('retry', 0)
        encoding = request_args.pop('encoding', None)
        request_args.setdefault('timeout', GlobalConfig.GLOBAL_TIMEOUT)
        for _ in range(retry + 1):
            try:
                resp = await self.req.request(**request_args)
                if encoding:
                    text = resp.content.decode(encoding)
                else:
                    text = resp.text
                break
            except self.error as e:
                text = str(e)
                resp = e
                continue
        return text, resp


class TorequestsAiohttpAsyncAdapter(AsyncRequestAdapter):
    """torequests >= 5.0.0.

    WARNING: `torequests.aiohttp_dummy.Requests` is faster than `torequests.dummy.Requests`, but it only can be init in async env."""

    def __init__(self, session=None, **kwargs):
        from torequests.aiohttp_dummy import Requests, FailureException
        if session:
            kwargs['session'] = session
        self.req = Requests(catch_exception=False, **kwargs)
        self.error = (FailureException, InvalidSchemaError)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def request(self, **request_args):
        text, resp = '', None
        retry = request_args.pop('retry', 0)
        encoding = request_args.pop('encoding', None)
        request_args.setdefault('timeout', GlobalConfig.GLOBAL_TIMEOUT)
        for _ in range(retry + 1):
            try:
                resp = await self.req.request(**request_args)
                if encoding:
                    text = resp.content.decode(encoding)
                else:
                    text = resp.text
                break
            except self.error as e:
                text = str(e)
                resp = e
                continue
        return text, resp


def no_adapter():
    return None


def get_available_sync_request():
    """Try to import a lib in ('requests', 'httpx', 'torequests'), return the suitable adapter or None."""
    from importlib import import_module
    choice = {
        'requests': RequestsAdapter,
        'httpx': HTTPXSyncAdapter,
        'torequests': TorequestsSyncAdapter,
    }
    for name, adapter in choice.items():
        try:
            import_module(name)
            return adapter
        except ModuleNotFoundError:
            continue
    return no_adapter


def get_available_async_request():
    """Try to import a lib in ('httpx', 'aiohttp', 'torequests'), return the suitable adapter or None."""
    from importlib import import_module
    choice = {
        'torequests': TorequestsAsyncAdapter,
        'aiohttp': AiohttpAsyncAdapter,
        'httpx': HTTPXAsyncAdapter,
        'torequests_aiohttp': TorequestsAiohttpAsyncAdapter,
    }
    for name, adapter in choice.items():
        try:
            import_module(name)
            return adapter
        except ModuleNotFoundError:
            continue
    return no_adapter


def _exhaust_simple_coro(coro):
    """Run coroutines without event loop, only support simple coroutines which can run without future.
    Or it will raise RuntimeError: await wasn't used with future."""
    while True:
        try:
            coro.send(None)
        except StopIteration as e:
            return e.value


class LazyImporter(object):
    """Lazy import libs while it is really needed.

    Usage::

        >>> from uniparser.utils import LazyImporter
        >>> lib = LazyImporter()
        >>> lib.register('from re import findall')
        True
        >>> lib.findall('a', 'a a a a')
        ['a', 'a', 'a', 'a']
        >>> lib.register('import re')
        True
        >>> lib.re.findall('a', 'a a a a')
        ['a', 'a', 'a', 'a']
        >>> lib.register('from re import findall,    _MAXCACHE')
        True
        >>> lib._MAXCACHE
        512
        >>> lib.register('from re import findall', ('findall',))
        True
        >>> lib.findall('a', 'a a a a')
        ['a', 'a', 'a', 'a']

        from uniparser.utils import LazyImporter

        lib = LazyImporter()

        lib.register('from re import findall')
        print(lib.findall('a', 'a a a a'))
        # ['a', 'a', 'a', 'a']

        lib.register('from re import findall as re_findall', ('re_findall',))
        print(lib.re_findall('a', 'a a a a'))
        # ['a', 'a', 'a', 'a']

        lib.register('import re')
        print(lib.re.findall('a', 'a a a a'))
        # ['a', 'a', 'a', 'a']

        lib.register('import re as regex', 'regex')
        print(lib.regex.findall('a', 'a a a a'))
        # ['a', 'a', 'a', 'a']

        lib.register('from re import findall,    _MAXCACHE')
        print(lib._MAXCACHE)
        # 512

        lib.register('from re import findall', ('findall',))
        print(lib.findall('a', 'a a a a'))
        # ['a', 'a', 'a', 'a']

        lib.register('from re import findall, match', ('findall',))
        try:
            lib.match
        except Exception as err:
            print(repr(err))
        # AttributeError("LazyImporter object has no attribute 'match'")

        try:
            lib.register('from re import findall as reg_findall')
        except Exception as err:
            print(repr(err))
        # ValueError('Can not use `import var as var1` while names is None')
    """
    sub_import_patter = re_compile(r'.* ?import ')
    find_import_names_pattern = re_compile(r'[a-zA-Z0-9_]+')

    def __init__(self):
        self.container: Dict[str, tuple] = {}
        self.inverted_container: Dict[str, str] = {}

    def __getattr__(self, name):
        if name not in self.inverted_container:
            raise AttributeError(
                f"LazyImporter object has no attribute '{name}'")
        value = self.lazy_import(name)
        return value

    def lazy_import(self, name):
        # make `old_keys` in locals
        old_keys = None
        import_str = self.inverted_container[name]
        # clean dict
        names = self.container.pop(import_str)
        for _name in names:
            self.inverted_container.pop(_name, None)
        old_keys = set(locals().keys())
        # ! dangerous operation
        exec(import_str)
        current_locals = locals()
        new_vars = current_locals.keys() - old_keys
        for imported_var in new_vars:
            if imported_var in names:
                setattr(self, imported_var, current_locals[imported_var])
        return getattr(self, name, NotSet)

    def register(self, import_string, names: Union[tuple, str, None] = None):
        if not names:
            if ' as ' in import_string:
                raise ValueError(
                    'Can not use `import var as var1` while names is None')
            names_string = self.sub_import_patter.sub('', import_string)
            name_list = self.find_import_names_pattern.findall(names_string)
            if not name_list:
                return False
            names = tuple(name_list)
        elif isinstance(names, str):
            names = (names,)
        self.container[import_string] = names
        for name in names:
            if name in self.inverted_container:
                old_import_str = self.inverted_container[name]
                logger.warning(
                    f'name `{name}` is registered, updated `{old_import_str}` -> `{import_string}`'
                )
            self.inverted_container[name] = import_string
        return True

    def add(self, import_string, names: Union[tuple, str, None] = None):
        return self.register(import_string, names=names)


async def ensure_await_result(result):
    if isawaitable(result):
        return await result
    return result
