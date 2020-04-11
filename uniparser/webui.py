# -*- coding: utf-8 -*-
"""
Uniparser Test Console Demo
"""

from logging import getLogger
from pathlib import Path
from time import time
from traceback import format_exc

from bottle import BaseRequest, Bottle, request, static_file, template

from . import CrawlerRule, Uniparser, __version__
from .utils import ensure_request, get_available_sync_request

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
GLOBAL_RESP = None
cdn_urls = {
    'VUE_JS_CDN': 'https://cdn.staticfile.org/vue/2.6.11/vue.min.js',
    'ELEMENT_CSS_CDN': 'https://cdn.staticfile.org/element-ui/2.13.0/theme-chalk/index.css',
    'ELEMENT_JS_CDN': 'https://cdn.staticfile.org/element-ui/2.13.0/index.js',
    'VUE_RESOURCE_CDN': 'https://cdn.staticfile.org/vue-resource/1.5.1/vue-resource.min.js',
    'CLIPBOARDJS_CDN': 'https://cdn.staticfile.org/clipboard.js/2.0.4/clipboard.min.js',
}
root_path = Path(__file__).parent
index_tpl_path = root_path / 'templates' / 'index.html'
index_tpl_path = index_tpl_path.as_posix()
static_path = (root_path / 'static').as_posix()


def exception_handler(exc):
    trace_id = str(int(time() * 1000))
    err_name = exc.__class__.__name__
    err_value = str(exc)
    msg = f'{err_name}({err_value}) trace_id: {trace_id}:\n{format_exc()}'
    logger.error(msg)
    return f'Oops! {err_name}, trace_id: {trace_id}'


app.error_handler[500] = exception_handler


@app.get('/init_app')
def init_app():
    parser_name_choices = [{'value': i.name} for i in uni.parser_classes]
    parser_name_docs = {
        i.name: f'{i.__doc__}\n{i.doc_url}\n\n{i.test_url}'
        for i in uni.parser_classes
    }
    parser_name_docs[''] = 'Choose a parser_name'
    return {
        'parser_name_choices': parser_name_choices,
        'parser_name_docs': parser_name_docs,
    }


@app.get("/")
def index():
    return template(index_tpl_path, cdn_urls=cdn_urls, version=__version__)


@app.post("/request")
def send_request():
    global GLOBAL_RESP
    rule = CrawlerRule(**request.json)
    regex = rule['regex']
    url = rule['request_args']['url']
    if not regex or not rule.check_regex(url):
        return {
            'text': f'regex `{regex}` not match url: {url}',
            'status': -1,
            'ok': False
        }
    body, r = uni.download(rule)
    GLOBAL_RESP = r
    return {
        'text': body,
        'status': f'[{getattr(r, "status_code", 0)}]',
        'ok': getattr(r, "status_code", 0) in range(200, 300)
    }


@app.post("/curl_parse")
def curl_parse():
    curl = request.body.read().decode('u8')
    result = ensure_request(curl)
    if isinstance(curl, str) and curl.startswith('http'):
        result.setdefault(
            'headers', {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"
            })
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
    rule = CrawlerRule.loads(rule_json)
    # print(rule)
    result = uni.parse(input_object, rule, {
        'resp': GLOBAL_RESP,
        'request_args': rule['request_args']
    })
    return {'type': str(type(result)), 'data': repr(result)}


if __name__ == "__main__":
    app.run(port=8080)
