import unittest
from mock import Mock

from xivo_agid.handlers.outgoingfeatures import OutgoingFeatures
from xivo_agid import objects


class OutCallBuilder():

    def __init__(self):
        self._internal = 0
        self.callerId = ''

    def withCallerId(self, callerId):
        self.callerId = callerId
        return self

    def internal(self):
        self._internal = 1
        return self

    def external(self):
        self._internal = 0
        return self

    def build(self):
        outcall = Mock(objects.Outcall)
        outcall.callerid = self.callerId
        outcall.internal = self._internal
        return outcall


def an_outcall():
    return OutCallBuilder()


class Test(unittest.TestCase):

    def setUp(self):
        self._agi = Mock()
        self._cursor = Mock()
        self._args = Mock()
        self.outgoing_features = OutgoingFeatures(self._agi, self._cursor, self._args)

    def tearDown(self):
        pass

    def test_set_caller_id(self):

        outcall = (an_outcall()
                   .external()
                   .withCallerId('27857218')
                   .build())

        self.outgoing_features.outcall = outcall
        self.outgoing_features.callerid = None

        self.outgoing_features._set_caller_id()

        self.assertEqual(self.outgoing_features.callerid, '27857218', 'caller id should be set for external interconnexions')

    def test_do_not_set_caller_id_for_internal_outcall(self):

        outcall = (an_outcall()
                   .internal()
                   .withCallerId('23456'))

        self.outgoing_features.outcall = outcall
        self.outgoing_features.callerid = None

        self.outgoing_features._set_caller_id()

        self.assertEqual(None, self.outgoing_features.callerid, 'caller id should not be set for internal interconnexions')

    def test_set_caller_id_no_forced_caller_id(self):

        outcall = (an_outcall()
                   .external()
                   .withCallerId(''))

        self.outgoing_features.outcall = outcall
        self.outgoing_features.callerid = None

        self.outgoing_features._set_caller_id()
        self.assertEqual(self.outgoing_features.callerid, None)

    def test_retreive_outcall(self):
        outcall = Mock(objects.Outcall)
        self.outgoing_features.outcall = outcall
        self.outgoing_features.dialpattern_id = 23

        self.outgoing_features._retrieve_outcall()

        outcall.retrieve_values.assert_called_once_with(23)


if __name__ == "__main__":
    unittest.main()
