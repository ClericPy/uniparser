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
        'VUE_JS_CDN': 'https://cdn.staticfile.org/vue/2.6.11/vue.min.js',
        'ELEMENT_CSS_CDN': 'https://cdn.staticfile.org/element-ui/2.13.0/theme-chalk/index.css',
        'ELEMENT_JS_CDN': 'https://cdn.staticfile.org/element-ui/2.13.0/index.js',
        'VUE_RESOURCE_CDN': 'https://cdn.staticfile.org/vue-resource/1.5.1/vue-resource.min.js',
        'CLIPBOARDJS_CDN': 'https://cdn.staticfile.org/clipboard.js/2.0.4/clipboard.min.js',
    }
