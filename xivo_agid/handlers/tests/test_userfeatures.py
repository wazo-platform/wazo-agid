import unittest
from mock import Mock, patch

from xivo_agid.handlers.userfeatures import UserFeatures
from xivo_agid import objects


class TestUserFeatures(unittest.TestCase):

    def setUp(self):
        self._variables = {'XIVO_USERID': 42,
                           'XIVO_DSTID': 33,
                           'XIVO_LINEID': 5,
                           'XIVO_CALLORIGIN' : 'my_origin',
                           'XIVO_CALLFILTER_BYPASS': 'my_filter',
                           'XIVO_SRCNUM': '1000',
                           'XIVO_DSTNUM': '1003',}

        def get_variable(key):
            return self._variables[key]

        self._agi = Mock()
        self._agi.get_variable = get_variable
        self._cursor = Mock()
        self._args = Mock()
        self._old_extenfeatures = objects.ExtenFeatures
        objects.ExtenFeatures = Mock

    def tearDown(self):
        objects.ExtenFeatures = self._old_extenfeatures
        self._old_extenfeatures = None


    def test_userfeatures(self):
        userfeatures = UserFeatures(self._agi, self._cursor, self._args)

        self.assertEqual(userfeatures._agi, self._agi)
        self.assertEqual(userfeatures._cursor, self._cursor)
        self.assertEqual(userfeatures._args, self._args)

    def test_set_members(self):
        userfeatures = UserFeatures(self._agi, self._cursor, self._args)
        userfeatures._set_feature_list = Mock()
        userfeatures._set_caller = Mock()

        userfeatures._set_members()

        objects.ExtenFeatures = Mock()
        objects.User = Mock()

        self.assertEqual(userfeatures._userid, self._variables['XIVO_USERID'])
        self.assertEqual(userfeatures._dstid, self._variables['XIVO_DSTID'])
        self.assertEqual(userfeatures._lineid, self._variables['XIVO_LINEID'])
        self.assertEqual(userfeatures._zone, self._variables['XIVO_CALLORIGIN'])
        self.assertEqual(userfeatures._bypass_filter, self._variables['XIVO_CALLFILTER_BYPASS'])
        self.assertEqual(userfeatures._srcnum, self._variables['XIVO_SRCNUM'])
        self.assertEqual(userfeatures._dstnum, self._variables['XIVO_DSTNUM'])
        self.assertTrue(userfeatures._set_feature_list.called)
        self.assertTrue(userfeatures._set_caller.called)

    def test_set_feature_list(self):
        userfeatures = UserFeatures(self._agi, self._cursor, self._args)
        
        with patch.object(objects.ExtenFeatures, '__init__') as extenfeatures_init:
            extenfeatures_init.return_value = None
            userfeatures._set_feature_list()
            extenfeatures_init.assert_called_with(self._agi, self._cursor)
        self.assertNotEqual(userfeatures._feature_list, None)
        self.assertTrue(isinstance(userfeatures._feature_list, objects.ExtenFeatures))

    def test_set_caller(self):
        userfeatures = UserFeatures(self._agi, self._cursor, self._args)

        userfeatures._set_caller()

        self.assertTrue(userfeatures._caller is None)

        userfeatures._userid = self._variables['XIVO_USERID']

        with patch.object(objects.User, '__init__') as user_init:
            user_init.return_value = None

            userfeatures._set_caller()

            user_init.assert_called_with(self._agi, self._cursor, self._variables['XIVO_USERID'])
        self.assertTrue(userfeatures._caller is not None)
        self.assertTrue(isinstance(userfeatures._caller, objects.User))

    def test_set_lines(self):
        userfeatures = UserFeatures(self._agi, self._cursor, self._args)

        userfeatures._set_lines()

        self.assertEqual(userfeatures._lines, None)

        userfeatures._dstid = self._variables['XIVO_DSTID']
        with patch.object(objects.Lines, '__init__') as lines_init:
            lines_init.return_value = None

            userfeatures._set_lines()

            lines_init.assert_called_with(self._agi, self._cursor, int(self._variables['XIVO_DSTID']))
        self.assertNotEqual(userfeatures._lines, None)
        self.assertTrue(isinstance(userfeatures._lines, objects.Lines))


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.test_']
    unittest.main()