# -*- coding: utf-8 -*-

from logging import getLogger
# pip install fastapi uvicorn
from pathlib import Path
from time import time
from traceback import format_exc

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.templating import Jinja2Templates

from .. import CrawlerRule, Uniparser, __version__
from ..utils import ensure_request, get_available_async_request

app = FastAPI(title="Uniparser", version=__version__)
logger = getLogger('uniparser')
adapter = get_available_async_request()
if not adapter:
    raise RuntimeError(
        "one of these libs should be installed: ('requests', 'httpx', 'torequests')"
    )
uni = Uniparser(adapter())
GLOBAL_RESP = None
templates = Jinja2Templates(
    directory=str((Path(__file__).parent.parent / 'templates').absolute()))
app.mount(
    "/static",
    StaticFiles(directory=str((Path(__file__).parent.parent / 'static').absolute())),
    name="static")
cdn_urls = {
    'VUE_JS_CDN': 'https://cdn.staticfile.org/vue/2.6.11/vue.min.js',
    'ELEMENT_CSS_CDN': 'https://cdn.staticfile.org/element-ui/2.13.0/theme-chalk/index.css',
    'ELEMENT_JS_CDN': 'https://cdn.staticfile.org/element-ui/2.13.0/index.js',
    'VUE_RESOURCE_CDN': 'https://cdn.staticfile.org/vue-resource/1.5.1/vue-resource.min.js',
    'CLIPBOARDJS_CDN': 'https://cdn.staticfile.org/clipboard.js/2.0.4/clipboard.min.js',
}


@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    trace_id = str(int(time() * 1000))
    err_name = exc.__class__.__name__
    err_value = str(exc)
    msg = f'{err_name}({err_value}) trace_id: {trace_id}:\n{format_exc()}'
    logger.error(msg)
    return JSONResponse(
        status_code=500,
        content={
            "message": f"Oops! {err_name}.",
            "trace_id": trace_id
        },
    )


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
def index(request: Request):
    return templates.TemplateResponse(
        'index.html',
        dict(cdn_urls=cdn_urls, version=__version__, request=request))


@app.post("/request")
async def send_request(request_args: dict):
    global GLOBAL_RESP
    rule = CrawlerRule(**request_args)
    regex = rule['regex']
    url = rule['request_args']['url']
    if not regex or not rule.check_regex(url):
        return {
            'text': f'regex `{regex}` not match url: {url}',
            'status': -1,
            'ok': False
        }
    body, r = await uni.adownload(rule)
    GLOBAL_RESP = r
    return {
        'text': body,
        'status': f'[{getattr(r, "status_code", 0)}]',
        'ok': getattr(r, "status_code", 0) in range(200, 300)
    }


@app.post("/curl_parse")
async def curl_parse(request: Request):
    curl = (await request.body()).decode('u8')
    result = ensure_request(curl)
    if isinstance(curl, str) and curl.startswith('http'):
        result.setdefault(
            'headers', {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"
            })
    return {'result': result, 'ok': True}


@app.post("/parse")
def parse_rule(kwargs: dict):
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
