## CSSParser (css)

```
CSS selector parser, requires `bs4` and `lxml`(optional).
    Since HTML input object always should be string, _RECURSION_LIST will be True.

    Parse the input object with standard css selector, features from `BeautifulSoup`.

        :param input_object: input object, could be Tag or str.
        :type input_object: [Tag, str]
        :param param: css selector path
        :type param: [str]
        :param value: operation for each item of result
        :type value: [str]

            @attribute: return element.get(xxx)

            $text: return element.text

            $innerHTML, $html: return element.decode_contents()

            $outerHTML, $string: return str(element)

            $self: return element

        :return: list of Tag / str
        :rtype: List[Union[str, Tag]]

        examples:

            ['<a class="url" href="/">title</a>', 'a.url', '@href']      => Expecting value: line 1 column 1 (char 0)
            ['<a class="url" href="/">title</a>', 'a.url', '$text']      => Expecting value: line 1 column 1 (char 0)
            ['<a class="url" href="/">title</a>', 'a.url', '$innerHTML'] => Expecting value: line 1 column 1 (char 0)
            ['<a class="url" href="/">title</a>', 'a.url', '$html']      => Expecting value: line 1 column 1 (char 0)
            ['<a class="url" href="/">title</a>', 'a.url', '$outerHTML'] => Expecting value: line 1 column 1 (char 0)
            ['<a class="url" href="/">title</a>', 'a.url', '$string']    => Expecting value: line 1 column 1 (char 0)
            ['<a class="url" href="/">title</a>', 'a.url', '$self']      => Expecting value: line 1 column 1 (char 0)

            WARNING: $self returns the original Tag object
    
```
## XMLParser (xml)

```
XML parser, requires `bs4` and `lxml`(necessary), but not support `xpath` for now.
    Since XML input object always should be string, _RECURSION_LIST will be True.

    Parse the input object with css selector, `BeautifulSoup` with features='xml'.

        :param input_object: input object, could be Tag or str.
        :type input_object: [Tag, str]
        :param param: css selector path
        :type param: [str]
        :param value: operation for each item of result
        :type value: [str]

            @attribute: return element.get(xxx)

            $text: return element.text

            $innerXML: return element.decode_contents()

            $outerXML: return str(element)

            $self: return element

        :return: list of Tag / str
        :rtype: List[Union[str, Tag]]

        examples:

            ['<dc:creator><![CDATA[author]]></dc:creator>', 'creator', '$text']      => ['author']
            ['<dc:creator><![CDATA[author]]></dc:creator>', 'creator', '$innerHTML'] => [<creator>author</creator>]
            ['<dc:creator><![CDATA[author]]></dc:creator>', 'creator', '$html']      => [<creator>author</creator>]
            ['<dc:creator><![CDATA[author]]></dc:creator>', 'creator', '$outerHTML'] => [<creator>author</creator>]
            ['<dc:creator><![CDATA[author]]></dc:creator>', 'creator', '$string']    => [<creator>author</creator>]
            ['<dc:creator><![CDATA[author]]></dc:creator>', 'creator', '$self']      => [<creator>author</creator>]
            WARNING: $self returns the original Tag object
    
```
## RegexParser (re)

```
RegexParser. Parse the input object with standard regex, features from `re`.
    Since regex input object always should be string, _RECURSION_LIST will be True.

        :param input_object: input object, could be str.
        :type input_object: [str]
        :param param: standard regex
        :type param: [str]
        :param value: operation for each item of result
        :type value: [str]

            @some string: using re.sub

            $0: re.finditer and return list of the whole matched string

            $1: re.finditer, $1 means return list of group 1

            '': null str, means using re.findall method

            -: return re.split(param, input_object)

        :return: list of str
        :rtype: List[Union[str]]

        examples:

            ['a a b b c c', 'a|c', '@b']     => b b b b b b
            ['a a b b c c', 'a', '']         => ['a', 'a']
            ['a a b b c c', 'a (a b)', '$0'] => ['a a b']
            ['a a b b c c', 'a (a b)', '$1'] => ['a b']
            ['a a b b c c', 'b', '-']        => ['a a ', ' ', ' c c']
    
```
## JSONPathParser (jsonpath)

```
JSONPath parser, requires `jsonpath-rw-ext` lib.
    Since json input object may be dict / list, _RECURSION_LIST will be False.

        :param input_object: input object, could be str, list, dict.
        :type input_object: [str, list, dict]
        :param param: JSON path
        :type param: [str]
        :param value: attribute of find result, default to '' as '$value'
        :type value: [str, None]
        :return: list of str
        :rtype: List[Union[str]]

        examples:

            [{'a': {'b': {'c': 1}}}, '$..c', ''] => [1]
    
```
## ObjectPathParser (objectpath)

```
ObjectPath parser, requires `objectpath` lib.
    Since json input object may be dict / list, _RECURSION_LIST will be False.

        :param input_object: input object, could be str, list, dict.
        :type input_object: [str, list, dict]
        :param param: ObjectPath
        :type param: [str]
        :param value: not to use
        :type value: [Any]

        examples:

            [{'a': {'b': {'c': 1}}}, '$..c', ''] => [1]
    
```
## JMESPathParser (jmespath)

```
JMESPath parser, requires `jmespath` lib.
    Since json input object may be dict / list, _RECURSION_LIST will be False.

        :param input_object: input object, could be str, list, dict.
        :type input_object: [str, list, dict]
        :param param: JMESPath
        :type param: [str]
        :param value: not to use
        :type value: [Any]

        examples:

            [{'a': {'b': {'c': 1}}}, 'a.b.c', ''] => 1
    
```
## UDFParser (udf)

```
UDFParser. Python source code snippets. globals will contain `input_object` and `context` variables.
    Since python input object may be any type, _RECURSION_LIST will be False.

        param & value:
            param: the python source code to be exec(param), either have the function named `parse`, or will return eval(param)
            value: will be renamed to `context`, which can be used in parser function. `value` often be set as the dict of request & response.
        examples:

            ['a b c d', 'input_object[::-1]', '']                                                       => d c b a
            ['a b c d', 'context["key"]', {'key': 'value'}]                                             => value
            ['a b c d', 'md5(input_object)', '']                                                        => 713f592bd537f7725d491a03e837d64a
            ['["string"]', 'json_loads(input_object)', '']                                              => ['string']
            [['string'], 'json_dumps(input_object)', '']                                                => ["string"]
            ['a b c d', 'parse = lambda input_object: input_object', '']                                => a b c d
            ['a b c d', 'def parse(input_object): context["key"]="new";return context', {'key': 'old'}] => {'key': 'new'}
    
```
## PythonParser (python)

```
PythonParser. Some frequently-used utils.
    Since python input object may be any type, _RECURSION_LIST will be False.

        :param input_object: input object, any object.
        :type input_object: [object]
        param & value:

            1.  param: getitem, alias to get
                value: could be [0] as index, [1:3] as slice, ['key'] for dict
            2.  param: split
                value: return input_object.split(value or None)
            3.  param: join
                value: return value.join(input_object)
            4.  param: chain
                value: nonsense `value` variable. return list(itertools.chain(*input_object))
            5.  param: const
                value: return value if value else input_object
            6.  param: template
                value: Template.safe_substitute(input_object=input_object, **input_object if isinstance(input_object, dict))
            7.  param: index
                value: value can be number string / key.
            8.  param: sort
                value: value can be asc (default) / desc.
        examples:

            [[1, 2, 3], 'getitem', '[-1]']              => 3
            [[1, 2, 3], 'getitem', '[:2]']              => [1, 2]
            [{'a': '1'}, 'getitem', 'a']                => 1
            ['a b\tc \n \td', 'split', '']              => ['a', 'b', 'c', 'd']
            [['a', 'b', 'c', 'd'], 'join', '']          => abcd
            [['aaa', ['b'], ['c', 'd']], 'chain', '']   => ['a', 'a', 'a', 'b', 'c', 'd']
            ['python', 'template', '1 $input_object 2'] => 1 python 2
            [[1], 'index', '0']                         => 1
            ['python', 'index', '-1']                   => n
            [{'a': '1'}, 'index', 'a']                  => 1
            ['adcb', 'sort', '']                        => ['a', 'b', 'c', 'd']
            [[1, 3, 2, 4], 'sort', 'desc']              => [4, 3, 2, 1]

```
## LoaderParser (loader)

```
LoaderParser. Loads string with json / yaml / toml standard format.
    Since input object should be string, _RECURSION_LIST will be True.

        :param input_object: str match format of json / yaml / toml
        :type input_object: [str]
        :param param: loader name, such as: json, yaml, toml
        :type param: [str]
        :param value: some kwargs, input as json string
        :type value: [str]

        examples:

            ['{"a": "b"}', 'json', '']   => {'a': 'b'}
            ['a = "a"', 'toml', '']      => {'a': 'a'}
            ['animal: pets', 'yaml', ''] => {'animal': 'pets'}
    
```
## TimeParser (time)

```
TimeParser. Parse different format of time. Sometimes time string need a preprocessing with regex.
    Since input object can not be list, _RECURSION_LIST will be True.
        To change time zone:
            uniparser.time.LOCAL_TIME_ZONE = +8

        :param input_object: str
        :type input_object: [str]
        :param param: encode / decode. encode: time string => timestamp; decode: timestamp => time string
        :type param: [str]
        :param value: standard strftime/strptime format
        :type value: [str]

        examples:

            ['2020-02-03 20:29:45', 'encode', '']                  => 1580732985.0
            ['1580732985.1873155', 'decode', '']                   => 2020-02-03 20:29:45
            ['2020-02-03T20:29:45', 'encode', '%Y-%m-%dT%H:%M:%S'] => 1580732985.0
            ['1580732985.1873155', 'decode', '%b %d %Y %H:%M:%S']  => Feb 03 2020 20:29:45

    WARNING: time.struct_time do not have timezone info, so %z is always the local timezone
    
```
