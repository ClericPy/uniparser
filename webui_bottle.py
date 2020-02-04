# -*- coding: utf-8 -*-
"""
Uniparser Test Console Demo
"""
import json

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

TEMPLATE = r'''<!DOCTYPE html>
<html>

<head>
    <meta charset="utf-8" />
    <meta name="referrer" content="never">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <link rel="shortcut icon" type="image/ico" href="/icon.png" />
    <title>Uniparser Test Console</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="{{cdn_urls['VUE_JS_CDN']}}"></script>
    <script src="{{cdn_urls['ELEMENT_JS_CDN']}}"></script>
    <script src="{{cdn_urls['VUE_RESOURCE_CDN']}}"></script>
    <style>
        @import url("{{cdn_urls['ELEMENT_CSS_CDN']}}");

        html>body {
            width: 60%;
            height: 98%;
            margin: 0 0 0 20%;
            background-color: #eceff1;
            word-wrap: break-word;
        }
    </style>
</head>

<body>
    <div id="app">
        <el-container>
            <el-header>Uniparser Test Console</el-header>
            <el-main>
                <el-form :model="crawler_rule">
                    <el-form-item label="Rule Name">
                        <el-input v-model="crawler_rule.name" placeholder="Rule Name"></el-input>
                    </el-form-item>
                    <el-form-item label="Request Args">
                        <el-input v-model="crawler_rule.request_args" placeholder="Json dict for Requests"
                            type="textarea" autosize></el-input>
                    </el-form-item>
                    <el-form-item>
                        <el-button type="primary" @click="download">Send HTTP</el-button>
                    </el-form-item>
                    <el-form-item label="Response Body">
                        <el-input type="textarea" :autosize="{ minRows: 2, maxRows: 5}" placeholder="" width="50%"
                            v-model="input_object">
                        </el-input>
                    </el-form-item>
                    <el-form-item label="Rules">
                        <span style="font-size: 0.7em;color: #606266;">Ctrl+Enter = Parse, Alt+Enter = New rule</span>
                        <br>
                        <div v-for="(rule, index) in crawler_rule.parse_rules" class="rule">
                            <el-button size="mini" type="info" icon="el-icon-info" circle @click="get_doc(index)">
                            </el-button>
                            <el-select filterable v-model="rule.parser_name" style="width: 20%;display:inline-block;"
                                placeholder="Parser Name">
                                <el-option v-for="item in options" :key="item.value" :label="item.value"
                                    :value="item.value">
                                </el-option>
                            </el-select>
                            <el-input @keyup.ctrl.13.native="parse" @keyup.alt.13.native="add_new_rule" type="textarea" style="width: 35%;zoom: 120%;display:inline-block;" :rows="1"
                                autosize placeholder="Param" v-model="rule.param"></el-input>
                            <el-input @keyup.ctrl.13.native="parse" @keyup.alt.13.native="add_new_rule" type="textarea" style="width: 35%;zoom: 120%;display:inline-block;" :rows="1"
                                autosize placeholder="Value" v-model="rule.value"></el-input>
                            <el-button size="mini" type="danger" icon="el-icon-delete" circle @click="del_rule(index)">
                            </el-button>


                        </div>
                        <el-button size="mini" @click="add_new_rule" style="margin: 0.5em 0 0.5em 45%;"
                            icon="el-icon-plus" circle>
                        </el-button>
                    </el-form-item>
                    <el-form-item>
                        <el-button type="primary" @click="parse">Parse</el-button>
                    </el-form-item>
                    <el-drawer title="Parse Result" :visible.sync="drawer" size="50%" direction="ttb">
                        <b>${parse_result.type}</b>
                        <textarea name="doc" id="show_parse_result" style="width: 100%; height: 100%;">${parse_result.data}</textarea>
                    </el-drawer>

                    <el-drawer title="Doc" :visible.sync="doc_drawer" size="50%" direction="ttb">
                        <textarea name="doc" id="show_doc" style="width: 100%; height: 100%;">${current_doc}</textarea>
                    </el-drawer>
                </el-form>

            </el-main>
        </el-container>
    </div>

    <script>
        var Main = {
            data() {
                return {
                    drawer: false,
                    options: '',
                    docs: '',
                    crawler_rule: {
                        name: 'HelloWorld',
                        parse_rules: [],
                        request_args: JSON.stringify({
                            "method": "get",
                            "url": "http://httpbin.org/forms/post",
                            "headers": {
                                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"
                            }
                        }, null, 2),
                    },
                    input_object: '',
                    parse_result: '',
                    current_doc: '',
                    doc_drawer: false,
                }
            },
            methods: {
                openAlert(body, title) {
                    this.$alert(body, title, {
                        confirmButtonText: 'Ok',
                        distinguishCancelAndClose: true,
                        closeOnPressEscape: true,
                        closeOnClickModal: true,
                    });
                },
                download() {
                    var data = this.crawler_rule.request_args
                    this.$http.post('/request', data).then(
                        r => {
                            this.input_object = r.bodyText
                        }, r => {
                            this.status = 'testTask failed, Bad request (' + r.status + ') :' + r
                                .statusText
                            this.status_icon_flag = 'error'
                        }
                    )
                },
                parse() {
                    var data = {
                        'name': this.crawler_rule.name,
                        'parse_rules': this.crawler_rule.parse_rules,
                        'request_args': this.crawler_rule.request_args,
                        'input_object': this.input_object,
                    }
                    if (!this.crawler_rule.parse_rules || !this.input_object) {
                        this.openAlert('Send request and fill the parse_rules before parsing.')
                        return
                    }
                    this.$http.post('/parse', JSON.stringify(data)).then(
                        r => {
                            this.parse_result = r.body
                            this.drawer = true
                        }, r => {
                            this.status = 'testTask failed, Bad request (' + r.status + ') :' + r.statusText
                            this.status_icon_flag = 'error'
                        }
                    )
                },
                add_new_rule() {
                    this.crawler_rule.parse_rules.push({
                        parser_name: '',
                        param: '',
                        value: '',
                    })
                },
                del_rule(index) {
                    this.crawler_rule.parse_rules.splice(index, 1)
                },
                get_doc(index) {
                    var name = this.crawler_rule.parse_rules[index].parser_name
                    this.current_doc = this.docs[name]
                    this.doc_drawer = true
                }
            },
            watch: {

            },
            computed: {

            }
        }

        function init_app(app) {
            app.add_new_rule()
            app.$http.get('/init_app').then(
                r => {
                    result = r.body
                    app.docs = result.parser_name_docs
                    app.options = result.parser_name_choices
                }, r => {}
            )
        }
        var vue_app = Vue.extend(Main)
        var app = new vue_app({
            delimiters: ['${', '}']
        }).$mount('#app')
        init_app(app)
    </script>
</body>

</html>
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
    parse_rules = [[i['parser_name'], i['param'], i['value']]
                   for i in kwargs['parse_rules']
                   if any(i.values())]
    rule = CrawlerRule(
        name=kwargs['name'],
        request_args=kwargs['request_args'],
        parse_rules=parse_rules)
    # print(rule)
    result = uni.parse(input_object, rule, GLOBAL_RESP)
    return {'type': str(type(result)), 'data': repr(result)}


if __name__ == "__main__":
    app.run(port=8080)
