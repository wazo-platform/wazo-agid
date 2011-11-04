# -*- coding: UTF-8 -*-

class Handler(object):

    def __init__(self, agi, cursor, args):
        self._agi = agi
        self._cursor = cursor
        self._args = args
