# -*- coding: utf-8 -*-
"""
Uniparser Test Console Demo
"""

from pathlib import Path

import requests
from bottle import BaseRequest, Bottle, request, template

from . import CrawlerRule, Uniparser, __version__

# 10MB
BaseRequest.MEMFILE_MAX = 10 * 1024 * 1024
app = Bottle()
uni = Uniparser()
GLOBAL_RESP = None

cdn_urls = dict(
    VUE_JS_CDN='https://cdn.staticfile.org/vue/2.6.11/vue.min.js',
    ELEMENT_CSS_CDN=
    'https://cdn.staticfile.org/element-ui/2.13.0/theme-chalk/index.css',
    ELEMENT_JS_CDN='https://cdn.staticfile.org/element-ui/2.13.0/index.js',
    VUE_RESOURCE_CDN=
    'https://cdn.staticfile.org/vue-resource/1.5.1/vue-resource.min.js')

index_tpl_path = Path(__file__).parent / 'templates' / 'index.html'
index_tpl_path = index_tpl_path.as_posix()


@app.get('/init_app')
def init_app():
    parser_name_choices = [{'value': i.name} for i in uni.parser_classes]
    parser_name_docs = {i.name: i.__doc__ for i in uni.parser_classes}
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
    encoding = rule.get('encoding')
    try:
        request_args = rule['request_args']
        r = requests.request(**request_args)
        GLOBAL_RESP = r
        if encoding:
            r.encoding = encoding
        return {
            'text': r.text,
            'status': f'[{r.status_code}]',
            'ok': r.status_code in range(200, 300)
        }
    except requests.RequestException as e:
        return {'text': str(e), 'status': '[-1]', 'ok': False}


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
    result = uni.parse(input_object, rule, GLOBAL_RESP)
    return {'type': str(type(result)), 'data': repr(result)}


if __name__ == "__main__":
    app.run(port=8080)
