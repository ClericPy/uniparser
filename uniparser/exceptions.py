# -*- coding: utf-8 -*-


class RuleNotFoundError(BaseException):
    pass


class InvalidSchemaError(BaseException):
    pass


class UnknownParserNameError(ValueError):
    pass
