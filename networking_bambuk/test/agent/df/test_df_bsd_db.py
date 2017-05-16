import os
import unittest

from networking_bambuk.agent.df import df_bsd_db


class BSDDbDriver(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        BSDDbDriver.bsd_db_driver = df_bsd_db.BSDDbDriver()
        BSDDbDriver.bsd_db_driver._db_dir = '/tmp/dbtest'
        BSDDbDriver.bsd_db_driver._tables = {}
        if os.path.exists(BSDDbDriver.bsd_db_driver._db_dir):
            for f in os.listdir(BSDDbDriver.bsd_db_driver._db_dir):
                os.remove(os.path.join(BSDDbDriver.bsd_db_driver._db_dir, f))
        else:
            os.makedirs(BSDDbDriver.bsd_db_driver._db_dir)

    @classmethod
    def tearDownClass(cls):
        pass

    def _assert_list(self, l1, l2):
        list.sort(l1)
        list.sort(l2)
        self.assertListEqual(l1, l2)

    def test_table(self):
        BSDDbDriver.bsd_db_driver.create_table('lport')
        self._assert_list(['lport'],
                          BSDDbDriver.bsd_db_driver._tables.keys())
        BSDDbDriver.bsd_db_driver.delete_table('lport')
        self._assert_list([],
                          BSDDbDriver.bsd_db_driver._tables.keys())

    def test_key(self):
        value = {'id': 'xxx'}
        value2 = {'id': 'yyy'}
        table = 'lport'
        key = '123'
        BSDDbDriver.bsd_db_driver.create_key(table, key, value)
        res = BSDDbDriver.bsd_db_driver.get_key(table, key)
        self.assertDictEqual(value, res)
        BSDDbDriver.bsd_db_driver.set_key(table, key, value2)
        res = BSDDbDriver.bsd_db_driver.get_key(table, key)
        self.assertDictEqual(value2, res)
        BSDDbDriver.bsd_db_driver.delete_key(table, key)
        res = BSDDbDriver.bsd_db_driver.get_key(table, key)
        self.assertEqual(res, None)

    def test_all(self):
        entries = [
            {'key': '2', 'value': {'id': 'xxx'}},
            {'key': '3', 'value': {'id': 'yyy'}},
            {'key': '4', 'value': {'id': 'zzz'}},
        ]
        try:
            for entry in entries:
                BSDDbDriver.bsd_db_driver.create_key(
                    'lp', entry['key'], entry['value'])
                BSDDbDriver.bsd_db_driver.create_key(
                    'ln', entry['key'], entry['value'])
            self._assert_list([e['key'] for e in entries],
                              BSDDbDriver.bsd_db_driver.get_all_keys('lp'))
            self._assert_list([e['value'] for e in entries],
                              BSDDbDriver.bsd_db_driver.get_all_entries('lp'))
        finally:
            BSDDbDriver.bsd_db_driver.delete_table('lp')
            BSDDbDriver.bsd_db_driver.delete_table('ln')


if __name__ == '__main__':
    unittest.main()
