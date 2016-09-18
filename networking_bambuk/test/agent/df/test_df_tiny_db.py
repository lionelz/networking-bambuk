#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#

import unittest

from networking_bambuk.agent.df import df_tiny_db

from tinydb import TinyDB
from tinydb.storages import MemoryStorage


class TinyDbDriver(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        TinyDbDriver.tiny_db_driver = df_tiny_db.TinyDbDriver()
        TinyDbDriver.tiny_db_driver._db = TinyDB(storage=MemoryStorage)

    @classmethod
    def tearDownClass(cls):
        pass

    def test_table(self):
        TinyDbDriver.tiny_db_driver.create_table('lport')
        self.assertSetEqual({'lport', '_default'},
                            TinyDbDriver.tiny_db_driver._db.tables())
        TinyDbDriver.tiny_db_driver.delete_table('lport')
        self.assertSetEqual({'_default'},
                            TinyDbDriver.tiny_db_driver._db.tables())

    def test_key(self):
        value = {'id': 'xxx'}
        value2 = {'id': 'yyy'}
        table = 'lport'
        key = '123'
        TinyDbDriver.tiny_db_driver.create_key(table, key, value)
        res = TinyDbDriver.tiny_db_driver.get_key(table, key)
        self.assertDictEqual(value, res)
        TinyDbDriver.tiny_db_driver.set_key(table, key, value2)
        res = TinyDbDriver.tiny_db_driver.get_key(table, key)
        self.assertDictEqual(value2, res)
        TinyDbDriver.tiny_db_driver.delete_key(table, key)
        res = TinyDbDriver.tiny_db_driver.get_key(table, key)
        self.assertEqual(res, None)

    def test_all(self):
        entries = [
            {'key': '2', 'value': {'id': 'xxx'}},
            {'key': '3', 'value': {'id': 'yyy'}},
            {'key': '4', 'value': {'id': 'zzz'}},
        ]
        for entry in entries:
            TinyDbDriver.tiny_db_driver.create_key(
                'lp', entry['key'], entry['value'])
            TinyDbDriver.tiny_db_driver.create_key(
                'ln', entry['key'], entry['value'])
        self.assertListEqual([e['key'] for e in entries],
                             TinyDbDriver.tiny_db_driver.get_all_keys('lp'))
        self.assertListEqual([e['value'] for e in entries],
                             TinyDbDriver.tiny_db_driver.get_all_entries('lp'))
        TinyDbDriver.tiny_db_driver.delete_table('lp')
        TinyDbDriver.tiny_db_driver.delete_table('ln')


if __name__ == '__main__':
    unittest.main()
