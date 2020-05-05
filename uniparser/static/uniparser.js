var Main = {
    data() {
        return {
            downloading: false,
            pretty_json: false,
            drawer: false,
            options: "",
            encoding: "",
            docs: "",
            current_template: "",
            crawler_rule: {
                name: "",
                regex: "^https://httpbin.org/html$",
                parse_rules: [
                    {
                        name: "title",
                        chain_rules: [
                            ["css", "title,h1", "$text"],
                            ["py", "index", "0"],
                        ],
                        child_rules: "[]",
                        iter_parse_child: false,
                    },
                ],
                request_args: JSON.stringify(
                    {
                        method: "get",
                        url: "https://httpbin.org/html",
                        headers: {
                            "User-Agent":
                                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36",
                        },
                    },
                    null,
                    2
                ),
            },
            input_object: "",
            request_status: "",
            parse_result: "",
            current_doc: "",
            doc_drawer: false,
            new_rule_visible: false,
            new_rule_json: "",
            parse_rule_idx_to_send: null,
            send_child_rule_visible: false,
            template_visible: false,
            request_template_values: {},
        }
    },
    methods: {
        querySearch(queryString, cb) {
            var options = this.options
            var results = queryString
                ? options.filter(this.createFilter(queryString))
                : options
            cb(results)
        },
        createFilter(queryString) {
            return (item) => {
                return (
                    item.value
                        .toLowerCase()
                        .indexOf(queryString.toLowerCase()) === 0
                )
            }
        },
        openAlert(body, title) {
            this.$alert(body, title, {
                confirmButtonText: "Ok",
                distinguishCancelAndClose: true,
                closeOnPressEscape: true,
                closeOnClickModal: true,
            })
        },
        download() {
            var data = this.current_crawler_rule_json
            this.downloading = true
            this.request_status = "(Downloading)"
            this.input_object = ""
            this.$http.post("request", data).then(
                (r) => {
                    let scode = r.body.text
                    this.input_object = scode.replace(/^\s+/, "")
                    if (!this.crawler_rule.name) {
                        let default_name =
                            "U-" + new Date().getTime().toString().slice(0, -3)
                        try {
                            // get title as name
                            var el = new DOMParser().parseFromString(
                                scode,
                                "text/html"
                            )
                            let title = (
                                el.getElementsByTagName("title")[0] ||
                                el.getElementsByTagName("h1")[0] ||
                                el.getElementsByTagName("h2")[0] ||
                                ""
                            ).innerText
                            title = title.replace(/-.*/g, "")
                            let name =
                                title ||
                                this.crawler_rule.request_args.url ||
                                default_name
                            this.crawler_rule.name = name
                        } catch (error) {
                            this.crawler_rule.name = default_name
                        }
                    }
                    this.request_status = r.body.status
                    let color = r.body.ok ? "green" : "red"
                    document.querySelector(
                        "#request_status>label"
                    ).style.color = color
                    this.downloading = false
                },
                (r) => {
                    this.status =
                        "testTask failed, Bad request (" +
                        r.status +
                        ") :" +
                        r.statusText
                    this.status_icon_flag = "error"
                    this.downloading = false
                    this.openAlert(this.status)
                }
            )
        },
        parse() {
            var data = {
                rule: this.current_crawler_rule_json,
                input_object: this.input_object,
            }
            if (!this.crawler_rule.parse_rules || !this.input_object) {
                this.openAlert(
                    "Send request and fill the parse_rules before parsing"
                )
                return
            }
            this.$http.post("parse", JSON.stringify(data)).then(
                (r) => {
                    this.parse_result = r.body
                    this.drawer = true
                },
                (r) => {
                    this.openAlert(r.body, "Request Error")
                }
            )
        },
        add_new_rule_chain(index) {
            this.crawler_rule.parse_rules[index].chain_rules.push(["", "", ""])
        },
        add_new_rule() {
            this.crawler_rule.parse_rules.push({
                name: "",
                chain_rules: [["", "", ""]],
                child_rules: "",
                iter_parse_child: false,
            })
        },
        tail_rule() {
            this.send_child_rule_visible = false
            if (this.parse_rule_idx_to_send != null) {
                let rule = this.crawler_rule.parse_rules.splice(
                    this.parse_rule_idx_to_send,
                    1
                )[0]
                this.crawler_rule.parse_rules.push(rule)
            }
            this.parse_rule_idx_to_send = null
        },
        send_child(rule, receiver_index) {
            this.send_child_rule_visible = false
            let child_rules = JSON.parse(rule.child_rules || "[]")
            let sender_rule = this.crawler_rule.parse_rules[
                this.parse_rule_idx_to_send
            ]
            sender_rule.child_rules = JSON.parse(
                sender_rule.child_rules || "[]"
            )
            child_rules.push(sender_rule)
            this.crawler_rule.parse_rules[
                receiver_index
            ].child_rules = JSON.stringify(child_rules)
            this.crawler_rule.parse_rules.splice(
                this.parse_rule_idx_to_send,
                1
            )[0]
            this.parse_rule_idx_to_send = null
            setTimeout(() => {
                for (const text of document.getElementsByTagName(
                    ".child-rules-input>textarea"
                )) {
                    text.style.height = "auto"
                    text.style.height = text.scrollHeight + "px"
                }
                this.iframe_loaded = true
            }, 0)
        },
        open_send_child_dialog(index) {
            this.parse_rule_idx_to_send = index
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
            this.current_doc = this.docs[name] || "Not found parser: " + name
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
                    new_rule.request_args = JSON.stringify(
                        new_rule.request_args,
                        null,
                        2
                    )
                }
                if (new_rule.request_template) {
                    new_rule.request_template = JSON.stringify(
                        new_rule.request_template,
                        null,
                        2
                    )
                }
                new_rule.parse_rules.forEach((rule) => {
                    if (rule.child_rules) {
                        rule.child_rules = JSON.stringify(rule.child_rules)
                    }
                })
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
            }, 0)
            if (!this.new_rule_json) {
                this.new_rule_json = this.current_crawler_rule_json
            }
        },
        show_request_template() {
            this.template_visible = true
            this.current_template =
                this.crawler_rule.request_template ||
                this.crawler_rule.request_args
            this.request_template_values = {}
        },
        update_template() {
            try {
                JSON.parse(this.current_template)
                this.$set(
                    this.crawler_rule,
                    "request_template",
                    this.current_template
                )
            } catch (error) {
                this.openAlert(error, "Error")
            }
        },
        add_to_request_args() {
            try {
                new Set(this.current_template.match(/\$\{.*?\}/g)).forEach(
                    (key) => {
                        if (!this.request_template_values[key]) {
                            throw key + " should not be null"
                        }
                    }
                )
                let temp = this.current_template
                Object.keys(this.request_template_values).forEach((key) => {
                    let max_tries = 1000
                    let i = 0
                    while (i < max_tries) {
                        i += 1
                        let new_temp = temp.replace(
                            key,
                            this.request_template_values[key]
                        )
                        if (new_temp == temp) {
                            break
                        }
                        temp = new_temp
                    }
                })
                this.$set(
                    this.crawler_rule,
                    "request_args",
                    JSON.stringify(JSON.parse(temp), null, 2)
                )
                this.template_visible = false
            } catch (error) {
                this.openAlert(error, "Error")
                this.template_visible = true
            }
        },
        demo_handle_click(choice) {
            let choices = {
                CSS:
                    '{"name":"","request_args":{"method":"get","url":"http://httpbin.org/html","headers":{"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"}},"parse_rules":[{"name":"text","chain_rules":[["css","body h1","$text"],["python","getitem","[0]"]],"child_rules":""}],"regex":"^http://httpbin.org/html$","encoding":""}',
                "XML(RSS)":
                    '{"name":"","request_args":{"method":"get","url":"https://importpython.com/blog/feed/","headers":{"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"}},"parse_rules":[{"name":"text","chain_rules":[["xml","channel>item>title","$text"],["python","getitem","[0]"]],"child_rules":""},{"name":"url","chain_rules":[["xml","channel>item>link","$text"],["python","getitem","[0]"]],"child_rules":""}],"regex":"^https?://importpython.com/blog/feed/$","encoding":""}',
                Regex:
                    '{"name":"","request_args":{"method":"get","url":"http://myip.ipip.net/","headers":{"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"}},"parse_rules":[{"name":"find one","chain_rules":[["re","(\\\\d+\\\\.){3}\\\\d+","$0"]],"child_rules":[]},{"name":"findall","chain_rules":[["re","\\\\d+",""]],"child_rules":[],"iter_parse_child":false},{"name":"find group","chain_rules":[["re","(\\\\d+\\\\.){3}\\\\d+","$1"]],"child_rules":[],"iter_parse_child":false},{"name":"Zero-Length Assertions: find the aa not a or aaa","chain_rules":[["py","const","aaababaaccc"],["re","(?<=[^a])aa(?=[^a])",""]],"child_rules":[],"iter_parse_child":false},{"name":"re.sub","chain_rules":[["re","(\\\\d+)","@\\\\1+"]],"child_rules":[],"iter_parse_child":false},{"name":"re.split","chain_rules":[["re","\\\\s","-"]],"child_rules":[],"iter_parse_child":false}],"regex":"^http://myip\\\\.ipip\\\\.net/$"}',
                JSON: `{"name":"U-1588672624","request_args":{"method":"get","url":"http://httpbin.org/json","headers":{"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"}},"parse_rules":[{"name":"jmes_demo","chain_rules":[["jmespath","JSON.slideshow.slides[1].title",""]],"child_rules":[],"iter_parse_child":false},{"name":"jsonpath_demo","chain_rules":[["jsonpath","JSON.slideshow.slides[1].title",""]],"child_rules":[],"iter_parse_child":false},{"name":"jsonpath_demo2","chain_rules":[["jsonpath","$.slideshow.slides[1].title",""]],"child_rules":[],"iter_parse_child":false},{"name":"objectpath_demo","chain_rules":[["objectpath","$.slideshow.slides[1].title",""]],"child_rules":[],"iter_parse_child":false},{"name":"objectpath_demo2","chain_rules":[["objectpath","JSON.slideshow.slides[1].title",""]],"child_rules":[],"iter_parse_child":false}],"regex":"^http://httpbin\\\\.org/json$"}`,
                UDF: `{"name":"","request_args":{"method":"get","url":"http://httpbin.org/json","headers":{"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"}},"parse_rules":[{"name":"context_resp_demo","chain_rules":[["udf","context['resp'].url",""]],"child_rules":[],"iter_parse_child":false},{"name":"context_parse_result_demo","chain_rules":[["udf","context['parse_result']['context_resp_demo']",""]],"child_rules":[],"iter_parse_child":false},{"name":"lambda_demo","chain_rules":[["udf","parse = lambda input_object: 123",""]],"child_rules":[],"iter_parse_child":false},{"name":"context_and_function_demo","chain_rules":[["udf","def parse(input_object):\\n    context['a'] = 1\\n    return 2",""],["udf","context['a'] + input_object",""]],"child_rules":[],"iter_parse_child":false},{"name":"obj_alias_demo","chain_rules":[["udf","1",""],["udf","int(obj)",""]],"child_rules":[],"iter_parse_child":false}],"regex":"^http://httpbin\\\\.org/json$"}`,
                Null:
                    '{"name":"","request_args":"{}","parse_rules":[],"regex":"","encoding":""}',
            }
            this.new_rule_json = choices[choice]
            this.input_object = ""
            this.request_status = ""
            this.load_rule()
        },
        input_curl() {
            this.$prompt("Input cURL string (or URL)", "", {
                confirmButtonText: "OK",
                cancelButtonText: "Cancel",
                inputPattern: /^(curl |http).*/,
                inputErrorMessage:
                    "cURL string should start with curl, or url should start with http",
            })
                .then(({ value }) => {
                    this.$http.post("curl_parse", value).then(
                        (r) => {
                            let result = r.body
                            if (result.ok) {
                                this.crawler_rule.request_args = JSON.stringify(
                                    result.result,
                                    null,
                                    2
                                )
                                let url = result.result.url
                                if (url) {
                                    this.crawler_rule.regex =
                                        "^" +
                                        url.replace(
                                            /([\.\?\+\*\^\$])/g,
                                            "\\$1"
                                        ) +
                                        "$"
                                }
                            } else {
                                this.$message({
                                    type: "error",
                                    message:
                                        "cURL parse failed: " + result.result,
                                })
                            }
                        },
                        () => {
                            this.$message({
                                type: "error",
                                message: "cURL parse failed",
                            })
                        }
                    )
                })
                .catch(() => {})
        },
    },
    watch: {
        encoding() {
            let args = JSON.parse(this.crawler_rule.request_args)
            args.encoding = this.encoding
            this.crawler_rule.request_args = JSON.stringify(args, null, 2)
        },
    },
    computed: {
        current_request_url: function () {
            try {
                return JSON.parse(this.crawler_rule.request_args).url || ""
            } catch (error) {
                return ""
            }
        },
        current_crawler_rule_json: function () {
            try {
                var rules = []
                this.crawler_rule.parse_rules.forEach((item) => {
                    if (item.name) {
                        try {
                            var child_rules = JSON.parse(
                                item.child_rules || "[]"
                            )
                        } catch (error) {
                            var child_rules = item.child_rules
                        }
                        var chain_rules = []
                        item.chain_rules.forEach((i) => {
                            if (i[0] && i[1]) {
                                chain_rules.push([i[0], i[1], i[2]])
                            }
                        })
                        rules.push({
                            name: item.name,
                            chain_rules: chain_rules,
                            child_rules: child_rules,
                            iter_parse_child: item.iter_parse_child,
                        })
                    }
                })
                var data = {
                    name: this.crawler_rule.name,
                    request_args: JSON.parse(this.crawler_rule.request_args),
                    parse_rules: rules,
                    regex: this.crawler_rule.regex,
                }
                if (this.crawler_rule.request_template) {
                    data.request_template = JSON.parse(
                        this.crawler_rule.request_template
                    )
                }
                this.crawler_rule.request_args = JSON.stringify(
                    data.request_args,
                    null,
                    2
                )
                if (this.pretty_json) {
                    return JSON.stringify(data, null, 2)
                } else {
                    return JSON.stringify(data)
                }
            } catch (error) {
                return error
            }
        },
    },
}

function init_app(app) {
    //   init vars
    let node = document.getElementById("init_vars")
    let args = JSON.parse(window.atob(node.innerHTML))
    console.log(args)
    Object.keys(args).forEach((name) => {
        app[name] = args[name]
    })
    node.parentNode.removeChild(node)
    //   init clip
    var clipboard = new ClipboardJS(".cp-button")
    clipboard.on("success", function () {
        app.$message({
            message: "Copy success",
            type: "success",
        })
    })
}
var vue_app = Vue.extend(Main)
var app = new vue_app({
    delimiters: ["${", "}"],
}).$mount("#app")
init_app(app)
