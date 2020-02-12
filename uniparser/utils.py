# -*- coding: utf-8 -*-

from argparse import ArgumentParser
from json import JSONDecodeError
from json import loads as json_loads
from shlex import split as shlex_split
from abc import ABC, abstractmethod


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
    parser.add_argument(
        "-H", "--header", action="append", default=[])  # key: value
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


def ensure_request(request):
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
                result = json_loads(request)
            except JSONDecodeError:
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
        for _ in range(retry + 1):
            try:
                resp = self.session.request(**request_args)
                if encoding:
                    text = resp.content.decode(encoding)
                else:
                    text = resp.text
                break
            except self.error:
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
        for _ in range(retry + 1):
            try:
                resp = await self.session.request(**request_args)
                if encoding:
                    text = resp.content.decode(encoding)
                else:
                    text = resp.text
                break
            except self.error:
                continue
        return text, resp


class RequestsAdapter(SyncRequestAdapter):

    def __init__(self, session=None, **kwargs):
        self.session = session
        from requests import RequestException, Session
        if session:
            self.session = session
        else:
            self.session = Session(**kwargs)
        self.error = RequestException

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.session.close()


class HTTPXSyncAdapter(SyncRequestAdapter):

    def __init__(self, session=None, **kwargs):
        self.session = session
        from httpx import Client, HTTPError
        if session:
            self.session = session
        else:
            self.session = Client(**kwargs)
        self.error = HTTPError

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.session.close()


class TorequestsSyncAdapter(SyncRequestAdapter):

    def __init__(self, session=None, **kwargs):
        self.session = session
        from torequests.main import tPool, FailureException
        if session:
            self.session = session
        else:
            self.session = tPool(**kwargs)
        self.error = FailureException

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.session.close()


class HTTPXAsyncAdapter(AsyncRequestAdapter):

    def __init__(self, session=None, **kwargs):
        from httpx import AsyncClient, HTTPError
        self.session = session
        self.session_class = AsyncClient(**kwargs)
        self.error = HTTPError

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
        self.session_class = ClientSession(**kwargs)
        self.error = ClientError

    async def __aenter__(self):
        if not self.session:
            self.session = await self.session_class.__aenter__()
        return self

    async def __aexit__(self, *args):
        await self.session.close()

    async def request(self, **request_args):
        """non-request-like api"""
        text, resp = '', None
        retry = request_args.pop('retry', 0)
        encoding = request_args.pop('encoding', None)
        for _ in range(retry + 1):
            try:
                resp = await self.session.request(**request_args)
                text = await resp.text(encoding=encoding)
                break
            except self.error:
                continue
        return text, resp


class TorequestsAsyncAdapter(AsyncRequestAdapter):

    def __init__(self, session=None, **kwargs):
        from torequests.dummy import Requests, FailureException
        self.session = session
        self.session_class = Requests(**kwargs)
        self.error = FailureException

    async def __aenter__(self):
        if not self.session:
            self.session = await self.session_class.__aenter__()
        return self

    async def __aexit__(self, *args):
        await self.session.close()
