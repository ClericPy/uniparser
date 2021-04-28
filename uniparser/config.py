from json import JSONDecodeError, dumps, loads


class GlobalConfig:
    GLOBAL_TIMEOUT = 60
    # can be set as orjson / ujson
    JSONDecodeError = JSONDecodeError
    json_dumps = dumps
    json_loads = loads
    __schema__ = '__schema__'
    __request__ = '__request__'
    __result__ = '__result__'
    __encoding__ = 'utf-8'
    cdn_urls = {
        'VUE_JS_CDN': 'https://cdnjs.cloudflare.com/ajax/libs/vue/2.6.12/vue.min.js',
        'ELEMENT_CSS_CDN': 'https://cdnjs.cloudflare.com/ajax/libs/element-ui/2.13.2/theme-chalk/index.css',
        'ELEMENT_JS_CDN': 'https://cdnjs.cloudflare.com/ajax/libs/element-ui/2.13.2/index.js',
        'VUE_RESOURCE_CDN': 'https://cdnjs.cloudflare.com/ajax/libs/vue-resource/1.5.1/vue-resource.min.js',
        'CLIPBOARDJS_CDN': 'https://cdnjs.cloudflare.com/ajax/libs/clipboard.js/2.0.6/clipboard.min.js',
    }
    FAVICON = ''
    DEFAULT_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'
    demo_choices = [
        [
            'CSS',
            r'{"name":"CSS demo","request_args":{"method":"get","url":"http://httpbin.org/forms/post","headers":{"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"}},"parse_rules":[{"name":"Tag attribute","chain_rules":[["css","form","@method"],["py","index","0"]],"child_rules":[]},{"name":"Tag text","chain_rules":[["css","legend","$text"]],"child_rules":[],"iter_parse_child":false},{"name":"Tag outerHTML","chain_rules":[["css","[name=\"custname\"]","$string"],["py","index","0"]],"child_rules":[],"iter_parse_child":false},{"name":"context demo","chain_rules":[["context","resp",""],["udf","obj.url == context[\"resp\"].url",""]],"child_rules":[],"iter_parse_child":false}],"regex":"^http://httpbin\\.org/forms/post$","input_callback":"css"}'
        ],
        [
            'Selectolax',
            r'{"name":"Selectolax demo","request_args":{"method":"get","url":"http://httpbin.org/forms/post","headers":{"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"}},"parse_rules":[{"name":"Node attribute","chain_rules":[["se","form","@method"],["py","index","0"]],"child_rules":[]},{"name":"Node text","chain_rules":[["se","legend","$text"]],"child_rules":[],"iter_parse_child":false},{"name":"Node outerHTML","chain_rules":[["se","[name=\"custname\"]","$string"],["py","index","0"]],"child_rules":[],"iter_parse_child":false}],"regex":"^http://httpbin\\.org/forms/post$","input_callback":"se"}'
        ],
        [
            "XML(RSS)",
            r'{"name":"XML(RSS) demo","request_args":{"method":"get","url":"https://lucumr.pocoo.org/feed.atom","headers":{"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"}},"parse_rules":[{"name":"text","chain_rules":[["xml","feed>title","$text"],["py","0",""]],"child_rules":[]},{"name":"titles","chain_rules":[["xml","entry >title","$text"]],"child_rules":[]}],"regex":"^https?://lucumr\\.pocoo\\.org/feed\\.atom$","input_callback":"xml"}'
        ],
        [
            'Regex',
            '{"name":"Regex demo","request_args":{"method":"get","url":"http://myip.ipip.net/","headers":{"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"}},"parse_rules":[{"name":"find one","chain_rules":[["re","(\\\\d+\\\\.){3}\\\\d+","$0"]],"child_rules":[]},{"name":"findall","chain_rules":[["re","\\\\d+",""]],"child_rules":[],"iter_parse_child":false},{"name":"find group","chain_rules":[["re","(\\\\d+\\\\.){3}\\\\d+","$1"]],"child_rules":[],"iter_parse_child":false},{"name":"Zero-Length Assertions: find the aa not a or aaa","chain_rules":[["py","const","aaababaaccc"],["re","(?<=[^a])aa(?=[^a])",""]],"child_rules":[],"iter_parse_child":false},{"name":"re.sub","chain_rules":[["re","(\\\\d+)","@\\\\1+"]],"child_rules":[],"iter_parse_child":false},{"name":"re.split","chain_rules":[["re","\\\\s","-"]],"child_rules":[],"iter_parse_child":false}],"regex":"^http://myip\\\\.ipip\\\\.net/$"}'
        ],
        [
            'JSON',
            r'{"name":"JSON demo","request_args":{"method":"get","url":"http://httpbin.org/json","headers":{"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"}},"parse_rules":[{"name":"jmes_demo","chain_rules":[["jmespath","JSON.slideshow.slides[1].title",""]],"child_rules":[],"iter_parse_child":false},{"name":"jsonpath_demo","chain_rules":[["jsonpath","JSON.slideshow.slides[1].title",""]],"child_rules":[],"iter_parse_child":false},{"name":"jsonpath_demo2","chain_rules":[["jsonpath","$.slideshow.slides[1].title",""]],"child_rules":[],"iter_parse_child":false},{"name":"objectpath_demo","chain_rules":[["objectpath","$.slideshow.slides[1].title",""]],"child_rules":[],"iter_parse_child":false},{"name":"objectpath_demo2","chain_rules":[["objectpath","JSON.slideshow.slides[1].title",""]],"child_rules":[],"iter_parse_child":false}],"regex":"^http://httpbin\\.org/json$","input_callback":"json"}'
        ],
        [
            'UDF',
            '''{"name":"UDF demo","request_args":{"method":"get","url":"http://httpbin.org/json","headers":{"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"}},"parse_rules":[{"name":"context_resp_demo","chain_rules":[["udf","context['resp'].url",""]],"child_rules":[],"iter_parse_child":false},{"name":"context_parse_result_demo","chain_rules":[["udf","context['parse_result']['context_resp_demo']",""]],"child_rules":[],"iter_parse_child":false},{"name":"lambda_demo","chain_rules":[["udf","parse = lambda input_object: 123",""]],"child_rules":[],"iter_parse_child":false},{"name":"context_and_function_demo","chain_rules":[["udf","def parse(input_object):\\n    context['a'] = 1\\n    return 2",""],["udf","context['a'] + input_object",""]],"child_rules":[],"iter_parse_child":false},{"name":"obj_alias_demo","chain_rules":[["udf","1",""],["udf","int(obj)",""]],"child_rules":[],"iter_parse_child":false}],"regex":"^http://httpbin\\\\.org/json$"}'''
        ],
        [
            'Null',
            '{"name":"Null demo","request_args":"{}","parse_rules":[],"regex":""}'
        ],
    ]

    @staticmethod
    def init_context() -> dict:
        """Make a default context for uniparser. you can rewrite this method as you wish"""
        return {}
