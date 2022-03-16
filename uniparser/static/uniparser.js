Date.prototype.Format = function (fmt) {
    var o = {
        "M+": this.getMonth() + 1,
        "d+": this.getDate(),
        "H+": this.getHours(),
        "m+": this.getMinutes(),
        "s+": this.getSeconds(),
        "q+": Math.floor((this.getMonth() + 3) / 3),
        S: this.getMilliseconds(),
    }
    if (/(y+)/.test(fmt))
        fmt = fmt.replace(
            RegExp.$1,
            (this.getFullYear() + "").substr(4 - RegExp.$1.length)
        )
    for (var k in o)
        if (new RegExp("(" + k + ")").test(fmt))
            fmt = fmt.replace(
                RegExp.$1,
                RegExp.$1.length == 1
                    ? o[k]
                    : ("00" + o[k]).substr(("" + o[k]).length)
            )
    return fmt
}
var Main = {
    data() {
        return {
            downloading: false,
            pretty_json: false,
            drawer: false,
            options: "",
            docs: "",
            current_template: "",
            crawler_rule: {
                name: "",
                description: "",
                input_callback: "",
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
            show_parse_result_as_json: true,
            custom_args: "",
            demo_choices: [],
            cb_names: "",
            show_toc: true,
        }
    },
    methods: {
        jump_rule(index) {
            switch (index) {
                case 0:
                    document.getElementById("app").scrollIntoView()
                    break
                case 1:
                    this.download()
                    break
                case 2:
                    this.parse()
                    break
                case 3:
                    this.load_rule_popup()
                    break
                default:
                    document
                        .querySelectorAll(".rule")
                        [index - 4].scrollIntoView()
                    break
            }
        },
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
                            "Rule (" +
                            new Date().Format("yyyy-MM-dd HH:mm:ss") +
                            ")"
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
                    if (r.body.msg) {
                        const h = this.$createElement
                        this.$notify({
                            title: "Warning",
                            message: h("b", r.body.msg),
                            type: "warning",
                            position: "top-left",
                        })
                    }
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
                this.download()
                this.openAlert(
                    "Can not parse it before downloading, now wait for downloading finished."
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
        prepose_rule() {
            this.send_child_rule_visible = false
            if (this.parse_rule_idx_to_send != null) {
                let rule = this.crawler_rule.parse_rules.splice(
                    this.parse_rule_idx_to_send,
                    1
                )[0]
                this.crawler_rule.parse_rules.unshift(rule)
            }
            this.parse_rule_idx_to_send = null
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
            let sender_rule =
                this.crawler_rule.parse_rules[this.parse_rule_idx_to_send]
            sender_rule.child_rules = JSON.parse(
                sender_rule.child_rules || "[]"
            )
            child_rules.push(sender_rule)
            this.crawler_rule.parse_rules[receiver_index].child_rules =
                JSON.stringify(child_rules)
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
                var known_keys = [
                    "name",
                    "description",
                    "regex",
                    "parse_rules",
                    "request_args",
                    "input_callback",
                ]
                var custom_args = {}
                for (key in new_rule) {
                    if (known_keys.indexOf(key) < 0) {
                        custom_args[key] = new_rule[key]
                    }
                }
                if (Object.keys(custom_args)[0]) {
                    this.custom_args = JSON.stringify(custom_args)
                } else {
                    this.custom_args = ""
                }
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
            this.new_rule_json = this.demo_choices[choice * 1][1]
            this.input_object = ""
            this.request_status = ""
            this.load_rule()
        },
        input_encoding() {
            this.$prompt("Input the encoding of response", "", {
                confirmButtonText: "OK",
                cancelButtonText: "Cancel",
            })
                .then(({ value }) => {
                    let args = JSON.parse(this.crawler_rule.request_args)
                    args.encoding = value
                    this.crawler_rule.request_args = JSON.stringify(
                        args,
                        null,
                        2
                    )
                })
                .catch(() => {})
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
                    fill_regex = (url) => {
                        if (url && !this.crawler_rule.regex) {
                            this.crawler_rule.regex =
                                "^" +
                                url
                                    .replace(/([\.\?\+\*\^\$])/g, "\\$1")
                                    .replace(/^https?:\/\//, "https?://") +
                                "$"
                        }
                    }
                    if (/^https?:\/\/.*/.test(value)) {
                        try {
                            let _old_args
                            try {
                                _old_args = JSON.parse(
                                    this.crawler_rule.request_args
                                )
                            } catch (error) {
                                _old_args = {
                                    method: "get",
                                    url: value,
                                    headers: {
                                        "User-Agent": "Chrome",
                                    },
                                }
                            }

                            _old_args.url = value
                            this.crawler_rule.request_args = JSON.stringify(
                                _old_args,
                                null,
                                2
                            )
                            fill_regex(value)
                            return
                        } catch (error) {}
                        return
                    }
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
                                fill_regex(url)
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
        handle_cache(action) {
            switch (action) {
                case "save":
                    localStorage.setItem(
                        "uniparser_cache",
                        this.current_crawler_rule_json
                    )
                    this.openAlert("Cache saved")
                    break
                case "load":
                    var rule = localStorage.getItem("uniparser_cache")
                    if (rule) {
                        this.new_rule_json = rule
                        this.load_rule()
                        this.openAlert("Cache loaded")
                    }
                    break
                case "clear":
                    localStorage.clear("uniparser_cache")
                    this.openAlert("Cache cleared")
                    break
                default:
                    break
            }
        },
    },
    watch: {},
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
                            if (i[0] || i[1] || i[2]) {
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
                    description: this.crawler_rule.description,
                    request_args: JSON.parse(this.crawler_rule.request_args),
                    parse_rules: rules,
                    regex: this.crawler_rule.regex,
                    input_callback: this.crawler_rule.input_callback,
                }
                var custom_args = this.custom_args
                    ? JSON.parse(this.custom_args)
                    : {}
                for (const key in custom_args) {
                    if (custom_args.hasOwnProperty(key)) {
                        data[key] = custom_args[key]
                    }
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
    // console.log(args)
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
    // init demo[0]
    app.demo_handle_click(0)
    app.handle_cache("load")
}
var vue_app = Vue.extend(Main)
var app = new vue_app({
    delimiters: ["${", "}"],
}).$mount("#app")
init_app(app)
