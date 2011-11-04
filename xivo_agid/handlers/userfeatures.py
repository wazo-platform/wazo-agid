# -*- coding: UTF-8 -*-
from xivo_agid.handlers.Handler import Handler
from xivo_agid import objects


class UserFeatures(Handler):

    def __init__(self, agi, cursor, args):
        Handler.__init__(self, agi, cursor, args)
        self._userid = None
        self._dstid = None
        self._lineid = None
        self._zone = None
        self._bypass_filter = None
        self._srcnum = None
        self._dstnum = None
        self._feature_list = None
        self._caller = None
        self._lines = None

    def _set_members(self):
        self._userid = self._agi.get_variable('XIVO_USERID')
        self._dstid = self._agi.get_variable('XIVO_DSTID')
        self._lineid = self._agi.get_variable('XIVO_LINEID')
        self._zone = self._agi.get_variable('XIVO_CALLORIGIN')
        self._bypass_filter = self._agi.get_variable('XIVO_CALLFILTER_BYPASS')
        self._srcnum = self._agi.get_variable('XIVO_SRCNUM')
        self._dstnum = self._agi.get_variable('XIVO_DSTNUM')
        self._set_feature_list()
        self._set_caller()

    def _set_feature_list(self):
        self._feature_list = objects.ExtenFeatures(self._agi, self._cursor)

    def _set_caller(self):
        if self._userid:
            try:
                self._caller = objects.User(self._agi, self._cursor, int(self._userid))
            except (ValueError, LookupError):
                self._caller = None

    def _set_lines(self):
        if self._dstid:
            try:
                self._lines = objects.Lines(self._agi, self._cursor, int(self._dstid))
            except (ValueError, LookupError), e:
                self._agi.dp_break(str(e))
