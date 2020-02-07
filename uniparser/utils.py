# -*- coding: utf-8 -*-
from argparse import ArgumentParser
from json import JSONDecodeError
from json import loads as json_loads
from shlex import split as shlex_split


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
