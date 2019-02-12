from pytd.client import Client
import pandas as pd

import unittest
try:
    from unittest.mock import MagicMock
    from unittest.mock import patch
except ImportError:
    from mock import MagicMock
    from mock import patch


class ClientTestCase(unittest.TestCase):

    @patch.object(Client, '_connect_td_hive', return_value=MagicMock())
    @patch.object(Client, '_connect_td_presto', return_value=MagicMock())
    def setUp(self, _connect_td_presto, _connect_td_hive):
        self.client = Client(apikey='APIKEY', database='sample_datasets')

        cursor = MagicMock(return_value=MagicMock())
        cursor.description = [('col1', 'int'), ('col2', 'string')]
        cursor.fetchall.return_value = [[1, 'a'], [2, 'b']]

        self.client.get_cursor = MagicMock(return_value=cursor)

        self._connect_td_presto = _connect_td_presto
        self._connect_td_hive = _connect_td_hive

    def test_close(self):
        self._connect_td_presto.assert_called_with('APIKEY', 'sample_datasets')
        self._connect_td_hive.assert_called_with('APIKEY', 'sample_datasets')
        self.assertTrue(self.client.writer is None)
        self.client.writer = MagicMock()
        self.client.close()
        self.assertTrue(self.client.td_presto.close.called)
        self.assertTrue(self.client.td_hive.close.called)
        self.assertTrue(self.client.writer.close.called)

    def test_query(self):
        d = self.client.query('select * from tbl')
        self.assertListEqual(d['columns'], ['col1', 'col2'])
        self.assertListEqual(d['data'], [[1, 'a'], [2, 'b']])

    def test_load_table_from_dataframe(self):
        df = pd.DataFrame([[1, 2], [3, 4]])
        self.assertTrue(self.client.writer is None)
        self.client.writer = MagicMock()
        self.client.load_table_from_dataframe(df, 'foo', 'error')
        self.assertTrue(self.client.writer.write_dataframe.called)


def test_client_context():
    with patch.object(Client, '_connect_td_presto', return_value=MagicMock()):
        with patch.object(Client, '_connect_td_hive', return_value=MagicMock()):
            with Client(apikey='APIKEY', database='sample_datasets') as client:
                client.close = MagicMock()
                client.close.assert_not_called()
            client.close.assert_called_with()
