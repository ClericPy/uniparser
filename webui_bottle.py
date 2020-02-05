# -*- coding: utf-8 -*-
"""
Uniparser Test Console Demo
"""
raise NotImplementedError
import requests
from bottle import Bottle, request, template
from uniparser import CrawlerRule, Uniparser

app = Bottle()
uni = Uniparser()
GLOBAL_RESP = None

cdn_urls = dict(
    VUE_JS_CDN='https://cdn.staticfile.org/vue/2.6.10/vue.min.js',
    ELEMENT_CSS_CDN=
    'https://cdn.staticfile.org/element-ui/2.11.1/theme-chalk/index.css',
    ELEMENT_JS_CDN='https://cdn.staticfile.org/element-ui/2.11.1/index.js',
    VUE_RESOURCE_CDN=
    'https://cdn.staticfile.org/vue-resource/1.5.1/vue-resource.min.js')

TEMPLATE = r'''
'''


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
    with open('index.html', encoding='u8') as f:
        TEMPLATE = f.read()
    return template(
        TEMPLATE,
        cdn_urls=cdn_urls,
    )


@app.post("/request")
def send_request():
    global GLOBAL_RESP
    # kwargs = request.body.read().decode('u8')
    kwargs = request.json
    encoding = kwargs.pop('encoding', None)
    try:
        r = requests.request(**kwargs)
        GLOBAL_RESP = r
        if encoding:
            r.encoding = encoding
        return r.text
    except requests.RequestException as e:
        return str(e)


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
