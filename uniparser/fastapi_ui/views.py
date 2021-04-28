# -*- coding: utf-8 -*-

from base64 import b64encode
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
from ..utils import (GlobalConfig, InputCallbacks, ensure_await_result,
                     ensure_request, get_available_async_request)

app = FastAPI(title="Uniparser", version=__version__)
logger = getLogger('uniparser')
adapter = get_available_async_request()
if not adapter:
    raise RuntimeError(
        "one of these libs should be installed: ('requests', 'httpx', 'torequests')"
    )
uni = Uniparser(adapter())
CONTEXT = {'request_args': None, 'resp': None}
templates_directory = str(
    (Path(__file__).parent.parent / 'templates').absolute())
templates = Jinja2Templates(directory=templates_directory)
static_directory = str((Path(__file__).parent.parent / 'static').absolute())
app.mount("/static", StaticFiles(directory=static_directory), name="static")
cdn_urls = GlobalConfig.cdn_urls


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


@app.get("/")
def index(request: Request):
    parser_name_docs = {i.name: i.doc for i in uni.parsers}
    parser_name_choices = [{'value': name} for name in parser_name_docs]
    parser_name_docs[''] = 'Choose a parser_name'
    parser_name_docs['py'] = parser_name_docs['python']
    init_vars = {
        'options': parser_name_choices,
        'docs': parser_name_docs,
        'demo_choices': GlobalConfig.demo_choices,
        'cb_names': ' | '.join(map(str, InputCallbacks._CALLBACKS.keys()))
    }
    init_vars_b64 = b64encode(
        GlobalConfig.json_dumps(init_vars).encode('u8')).decode('u8')
    return templates.TemplateResponse(
        'index.html',
        dict(cdn_urls=cdn_urls,
             version=__version__,
             FAVICON=GlobalConfig.FAVICON,
             init_vars_b64=init_vars_b64,
             request=request))


@app.post("/request")
async def send_request(request_args: dict):
    rule = CrawlerRule(**request_args)
    regex = rule['regex']
    url = rule['request_args']['url']
    if not regex or not rule.check_regex(url):
        msg = f'Download completed, but the regex `{regex}` does not match the given url: {url}'
    else:
        msg = ''
    input_object, resp = await uni.adownload(rule)
    CONTEXT.clear()
    CONTEXT.update(await ensure_await_result(GlobalConfig.init_context()))
    CONTEXT['request_args'] = rule['request_args']
    CONTEXT['resp'] = resp
    return {
        'text': str(input_object),
        'status': f'[{getattr(resp, "status_code", 0)}] - ({type(input_object)!r})',
        'ok': getattr(resp, "status_code", 0) in range(200, 300),
        'msg': msg
    }


@app.post("/curl_parse")
async def curl_parse(request: Request):
    curl = (await request.body()).decode('u8')
    result = ensure_request(curl)
    if isinstance(curl, str) and curl.startswith('http'):
        result.setdefault('headers', {"User-Agent": GlobalConfig.DEFAULT_UA})
    return {'result': result, 'ok': True}


@app.post("/parse")
async def parse_rule(kwargs: dict):
    input_object = kwargs['input_object']
    rule_json = kwargs['rule']
    json_result = ""
    try:
        rule = CrawlerRule.loads(rule_json)
        # print(rule)
        result = await uni.aparse(input_object, rule, context=CONTEXT)
        try:
            json_result = GlobalConfig.json_dumps(result,
                                                  default=repr,
                                                  indent=2,
                                                  ensure_ascii=False)
        except Exception as e:
            json_result = repr(e)
        return {
            'type': str(type(result)),
            'data': repr(result),
            'json': json_result
        }
    except BaseException as err:
        return {'type': str(type(err)), 'data': repr(err), 'json': format_exc()}
