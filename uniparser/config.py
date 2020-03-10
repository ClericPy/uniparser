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
