# -*- coding: utf-8 -*-


class RuleNotFoundError(Exception):

    def __bool__(self):
        return False


class InvalidSchemaError(Exception):

    def __bool__(self):
        return False


class UnknownParserNameError(ValueError):

    def __bool__(self):
        return False
