var Main = {
    data() {
        return {
            downloading: false,
            pretty_json: true,
            drawer: false,
            options: '',
            encoding: "",
            docs: '',
            crawler_rule: {
                name: '',
                regex: '^https://httpbin.org/html$',
                parse_rules: [{
                    "name": "title",
                    "chain_rules": [
                        ["css", "title,h1", "$text"],
                        ["py", "index", "0"]
                    ],
                    "child_rules": '[]',
                    "iter_parse_child": false
                }],
                request_args: JSON.stringify({
                    "method": "get",
                    "url": "https://httpbin.org/html",
                    "headers": {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"
                    }
                }, null, 2),
            },
            input_object: '',
            request_status: '',
            parse_result: '',
            current_doc: '',
            doc_drawer: false,
            new_rule_visible: false,
            new_rule_json: '',
            parse_rules_to_be_send: [],
            send_child_rule_visible: false,
        }
    },
    methods: {
        querySearch(queryString, cb) {
            var options = this.options;
            var results = queryString ? options.filter(this.createFilter(queryString)) : options;
            cb(results);
        },
        createFilter(queryString) {
            return (item) => {
                return (item.value.toLowerCase().indexOf(queryString.toLowerCase()) === 0);
            };
        },
        openAlert(body, title) {
            this.$alert(body, title, {
                confirmButtonText: 'Ok',
                distinguishCancelAndClose: true,
                closeOnPressEscape: true,
                closeOnClickModal: true,
            });
        },
        download() {
            var data = this.current_crawler_rule_json
            this.downloading = true
            this.request_status = '(Downloading)'
            this.input_object = ''
            this.$http.post('request', data).then(
                r => {
                    let scode = r.body.text
                    this.input_object = scode.replace(/^\s+/, '')
                    if (!this.crawler_rule.name) {
                        let default_name = 'U-' + new Date().getTime().toString().slice(0, -3)
                        try {
                            // get title as name
                            var el = new DOMParser().parseFromString(scode, "text/html");
                            let title = (el.getElementsByTagName('title')[0] || el.getElementsByTagName(
                                'h1')[0] || el.getElementsByTagName('h2')[0] || '').innerText
                            title = title.replace(/-.*/g, '')
                            let h1 = (el.getElementsByTagName('h1')[0] || '').innerText
                            let name = title || this.crawler_rule.request_args.url || default_name
                            this.crawler_rule.name = name
                        } catch (error) {
                            this.crawler_rule.name = default_name
                        }
                    }
                    this.request_status = r.body.status
                    let color = r.body.ok ? 'green' : 'red'
                    document.querySelector('#request_status>label').style.color = color
                    this.downloading = false
                }, r => {
                    this.status = 'testTask failed, Bad request (' + r.status + ') :' + r
                        .statusText
                    this.status_icon_flag = 'error'
                    this.downloading = false
                    this.openAlert(this.status)
                }
            )
        },
        parse() {
            var data = {
                'rule': this.current_crawler_rule_json,
                'input_object': this.input_object,
            }
            if (!this.crawler_rule.parse_rules || !this.input_object) {
                this.openAlert('Send request and fill the parse_rules before parsing')
                return
            }
            this.$http.post('parse', JSON.stringify(data)).then(
                r => {
                    this.parse_result = r.body
                    this.drawer = true
                }, r => {
                    this.status = 'testTask failed, Bad request (' + r.status + ') :' + r.statusText
                    this.status_icon_flag = 'error'
                }
            )
        },
        add_new_rule_chain(index) {
            this.crawler_rule.parse_rules[index].chain_rules.push(['', '', ''])
        },
        add_new_rule() {
            this.crawler_rule.parse_rules.push({
                name: '',
                chain_rules: [
                    ['', '', '']
                ],
                child_rules: "",
                iter_parse_child: false,
            })
        },
        send_child(item) {
            this.send_child_rule_visible = false
            let child_rules = JSON.parse(item.rule.child_rules || '[]')
            let sender_rule = this.crawler_rule.parse_rules[item.sender_index]
            sender_rule.child_rules = JSON.parse(sender_rule.child_rules || "[]")
            child_rules.push(sender_rule)
            this.crawler_rule.parse_rules[item.receiver_index].child_rules = JSON.stringify(child_rules)
            this.crawler_rule.parse_rules.splice(item.sender_index, 1)[0]
            this.parse_rules_to_be_send = []
            setTimeout(() => {
                for (const text of document.getElementsByTagName('.child-rules-input>textarea')) {
                    text.style.height = 'auto';
                    text.style.height = text.scrollHeight + 'px';
                };
                this.iframe_loaded = true
            }, 0);
        },
        open_send_child_dialog(index) {
            this.parse_rules_to_be_send = []
            this.crawler_rule.parse_rules.forEach((rule, idx) => {
                if (idx != index) {
                    this.parse_rules_to_be_send.push({
                        rule: rule,
                        receiver_index: idx,
                        sender_index: index,
                    })
                }
            });
            this.send_child_rule_visible = true
            // this.crawler_rule.parse_rules.splice(index, 1)
        },
        del_rule(index) {
            this.crawler_rule.parse_rules.splice(index, 1)
        },
        del_rule_chain(index, i) {
            this.crawler_rule.parse_rules[index].chain_rules.splice(i, 1)
        },
        get_doc(name) {
            this.current_doc = this.docs[name] || 'Not found parser: ' + name
            this.doc_drawer = true
        },
        load_rule() {
            if (!this.new_rule_json) {
                this.new_rule_visible = false
                return
            }
            try {
                var new_rule = JSON.parse(this.new_rule_json)
                if (new_rule.request_args && new_rule.request_args.url) {
                    new_rule.request_args = JSON.stringify(new_rule.request_args, null, 2)
                }
                new_rule.parse_rules.forEach(rule => {
                    if (rule.child_rules) {
                        rule.child_rules = JSON.stringify(rule.child_rules)
                    }
                });
                this.crawler_rule = new_rule
                this.new_rule_visible = false
            } catch (err) {
                alert(err)
            }
        },
        load_rule_popup() {
            this.new_rule_visible = true
            setTimeout(() => {
                this.$refs.load_json_input.focus()
            }, 0);
            if (!this.new_rule_json) {
                this.new_rule_json = this.current_crawler_rule_json
            }
        },
        input_curl() {
            this.$prompt('Input cURL string (or url)', '', {
                confirmButtonText: 'OK',
                cancelButtonText: 'Cancel',
                inputPattern: /^(curl |http).*/,
                inputErrorMessage: 'cURL string should start with curl, or url should start with http'
            }).then(({
                value
            }) => {
                this.$http.post('curl_parse', value).then(
                    r => {
                        let result = r.body
                        if (result.ok) {
                            this.crawler_rule.request_args = JSON.stringify(result.result, null,
                                2)
                            let url = result.result.url
                            if (url) {
                                this.crawler_rule.regex = '^' + url.replace(/([\.\?\+\*\^\$])/g,
                                    '\\$1') + '$'
                            }
                        } else {
                            this.$message({
                                type: 'error',
                                message: 'cURL parse failed: ' + result.result
                            });
                        }
                    }, r => {
                        this.$message({
                            type: 'error',
                            message: 'cURL parse failed'
                        });
                    }
                );
            }).catch(() => {
                this.$message({
                    type: 'info',
                    message: 'Cancel'
                });
            });
        }
    },
    watch: {
        encoding() {
            let args = JSON.parse(this.crawler_rule.request_args)
            args.encoding = this.encoding
            this.crawler_rule.request_args = JSON.stringify(args, null, 2)
        }
    },
    computed: {
        current_request_url: function () {
            try {
                return JSON.parse(this.crawler_rule.request_args).url || ''
            } catch (error) {
                return ''
            }
        },
        current_crawler_rule_json: function () {
            try {
                var rules = []
                this.crawler_rule.parse_rules.forEach(item => {
                    if (item.name) {
                        try {
                            var child_rules = JSON.parse(item.child_rules || "[]")
                        } catch (error) {
                            var child_rules = item.child_rules
                        }
                        var chain_rules = []
                        item.chain_rules.forEach(i => {
                            if (i[0] && i[1]) {
                                chain_rules.push([i[0], i[1], i[2]])
                            }
                        });
                        rules.push({
                            'name': item.name,
                            'chain_rules': chain_rules,
                            'child_rules': child_rules,
                            'iter_parse_child': item.iter_parse_child
                        })
                    }
                });
                var data = {
                    name: this.crawler_rule.name,
                    request_args: JSON.parse(this.crawler_rule.request_args),
                    parse_rules: rules,
                    regex: this.crawler_rule.regex,
                }
                this.crawler_rule.request_args = JSON.stringify(data.request_args, null, 2)
                if (this.pretty_json) {
                    return JSON.stringify(data, null, 2)
                } else {
                    return JSON.stringify(data)
                }
            } catch (error) {
                return error
            }

        }
    }
}

function init_app(app) {
    app.add_new_rule()
    app.$http.get('init_app').then(
        r => {
            result = r.body
            app.docs = result.parser_name_docs
            let options = []
            result.parser_name_choices.forEach(item => {
                options.push(item)
            });
            app.options = options
        }, r => {}
    )
}
var vue_app = Vue.extend(Main)
var app = new vue_app({
    delimiters: ['${', '}']
}).$mount('#app')
init_app(app)
var clipboard = new ClipboardJS('#copy');
clipboard.on('success', function (e) {
    app.$message({
        message: 'Copy success',
        type: 'success'
    });
});
