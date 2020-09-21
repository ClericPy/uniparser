# -*- coding: utf-8 -*-
"""
Uniparser Test Console Demo
"""

from base64 import b64encode
from logging import getLogger
from pathlib import Path
from time import time
from traceback import format_exc

from bottle import BaseRequest, Bottle, request, static_file, template

from . import CrawlerRule, Uniparser, __version__
from .utils import (GlobalConfig, ResponseCallbacks, ensure_request,
                    get_available_sync_request)

logger = getLogger('uniparser')
# 10MB
BaseRequest.MEMFILE_MAX = 10 * 1024 * 1024
app = Bottle()
adapter = get_available_sync_request()
if not adapter:
    raise RuntimeError(
        "one of these libs should be installed: ('requests', 'httpx', 'torequests')"
    )
uni = Uniparser(adapter())
GLOBAL_REQ = None
GLOBAL_RESP = None
cdn_urls = GlobalConfig.cdn_urls
root_path = Path(__file__).parent
index_tpl_path = root_path / 'templates' / 'index.html'
index_tpl_path_str = index_tpl_path.as_posix()
static_path = (root_path / 'static').as_posix()


def exception_handler(exc):
    trace_id = str(int(time() * 1000))
    err_name = exc.__class__.__name__
    err_value = str(exc)
    msg = f'{err_name}({err_value}) trace_id: {trace_id}:\n{format_exc()}'
    logger.error(msg)
    return f'Oops! {err_name}, trace_id: {trace_id}'


app.error_handler[500] = exception_handler


@app.get("/")
def index():
    parser_name_docs = {i.name: i.doc for i in uni.parsers}
    parser_name_choices = [{'value': name} for name in parser_name_docs]
    parser_name_docs[''] = 'Choose a parser_name'
    parser_name_docs['py'] = parser_name_docs['python']
    init_vars = {
        'options': parser_name_choices,
        'docs': parser_name_docs,
        'demo_choices': GlobalConfig.demo_choices,
        'cb_names': ' / '.join(map(str, ResponseCallbacks._CALLBACKS.keys()))
    }
    init_vars_b64 = b64encode(
        GlobalConfig.json_dumps(init_vars).encode('u8')).decode('u8')
    return template(index_tpl_path_str,
                    cdn_urls=cdn_urls,
                    init_vars_b64=init_vars_b64,
                    version=__version__)


@app.post("/request")
def send_request():
    global GLOBAL_RESP, GLOBAL_REQ
    rule = CrawlerRule(**request.json)
    regex = rule['regex']
    url = rule['request_args']['url']
    if not regex or not rule.check_regex(url):
        msg = f'Download completed, but the regex `{regex}` does not match the given url: {url}'
    else:
        msg = ''
    body, r = uni.download(rule)
    GLOBAL_RESP = r
    GLOBAL_REQ = rule['request_args']
    return {
        'text': body,
        'status': f'[{getattr(r, "status_code", 0)}]',
        'ok': getattr(r, "status_code", 0) in range(200, 300),
        'msg': msg
    }


@app.post("/curl_parse")
def curl_parse():
    curl = request.body.read().decode('u8')
    result = ensure_request(curl)
    if isinstance(curl, str) and curl.startswith('http'):
        result.setdefault('headers', {"User-Agent": GlobalConfig.DEFAULT_UA})
    return {'result': result, 'ok': True}


@app.get('/static/<path:path>')
def callback(path):
    return static_file(path, root=static_path)


@app.post("/parse")
def parse_rule():
    # kwargs = request.body.read().decode('u8')
    kwargs = request.json
    # print(kwargs)
    input_object = kwargs['input_object']
    if not input_object:
        return 'Null input_object?'
    rule_json = kwargs['rule']
    json_result = ""
    try:
        rule = CrawlerRule.loads(rule_json)
        # print(rule)
        result = uni.parse(input_object, rule, {
            'resp': GLOBAL_RESP,
            'request_args': GLOBAL_REQ
        })
        try:
            json_result = GlobalConfig.json_dumps(result, default=repr)
        except Exception as e:
            json_result = repr(e)
        return {
            'type': str(type(result)),
            'data': repr(result),
            'json': json_result
        }
    except BaseException as err:
        return {'type': str(type(err)), 'data': repr(err), 'json': json_result}


if __name__ == "__main__":
    app.run(port=8080)
