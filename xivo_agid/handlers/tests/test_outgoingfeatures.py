import unittest
from mock import Mock

from xivo_agid.handlers.outgoingfeatures import OutgoingFeatures
from xivo_agid import objects


class Test(unittest.TestCase):

    def setUp(self):
        self._agi = Mock()
        self._cursor = Mock()
        self._args = Mock()
        self.outgoing_features = OutgoingFeatures(self._agi, self._cursor, self._args)

    def tearDown(self):
        pass

    def test_set_caller_id(self):
        outcall = Mock(objects.Outcall)
        outcall.callerid = '27857218'
        self.outgoing_features.outcall = outcall

        self.outgoing_features._set_caller_id()
        self.assertEqual(self.outgoing_features.callerid, '27857218')

    def test_set_caller_id_no_forced_caller_id(self):
        outcall = Mock(objects.Outcall)
        outcall.callerid = ''
        self.outgoing_features.outcall = outcall

        self.outgoing_features._set_caller_id()
        self.assertEqual(self.outgoing_features.callerid, None)


    def test_retreive_outcall(self):
        outcall = Mock(objects.Outcall)
        self.outgoing_features.outcall = outcall
        self.outgoing_features.dstid = 23
        
        self.outgoing_features._retrieve_outcall()
        
        outcall.retrieve_values.assert_called_once_with(23)
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.test_set_caller_id']
    unittest.main()
