from json import JSONDecodeError, dumps, loads


class GlobalConfig:
    GLOBAL_TIMEOUT = 60
    # can be set as orjson / ujson
    JSONDecodeError = JSONDecodeError
    json_dumps = dumps
    json_loads = loads
