import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / 'apps/base/gokapi/migrate-auth.py'


class AuthMigrationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.state = self.root / 'state'
        self.bootstrap = self.root / 'bootstrap'
        (self.state / 'config').mkdir(parents=True)
        (self.state / 'data').mkdir()
        self.bootstrap.mkdir()
        (self.bootstrap / 'bootstrap-password').write_text('existing-site-password')
        self.config_path = self.state / 'config/config.json'
        self.config = {'Authentication': {'Method': 2, 'Username': 'admin',
                       'HeaderKey': 'X-Gokapi-User', 'SaltAdmin': 'keep-admin-salt',
                       'SaltFiles': 'keep-file-salt', 'OnlyRegisteredUsers': True},
                       'Port': '127.0.0.1:53842', 'DatabaseUrl': 'sqlite://./data/gokapi.sqlite',
                       'ChunkSize': 2, 'Encryption': {'Level': 0}}
        self.config_path.write_text(json.dumps(self.config))
        self.db_path = self.state / 'data/gokapi.sqlite'
        with sqlite3.connect(self.db_path) as db:
            db.execute('CREATE TABLE Users (Id INTEGER PRIMARY KEY, Name TEXT, Password TEXT, '
                       'Permissions INTEGER, UserLevel INTEGER, LastOnline INTEGER, ResetPassword INTEGER)')
            db.executemany('INSERT INTO Users VALUES (?, ?, ?, ?, ?, ?, ?)', [
                (1, 'admin', 'old-bootstrap-hash', 511, 0, 123, 0),
                (2, 'alexf', '', 511, 1, 456, 0),
                (3, 'other', 'keep-other-password', 0, 2, 789, 0)])
            db.execute('CREATE TABLE Files (Id TEXT PRIMARY KEY, Owner INTEGER)')
            db.execute("INSERT INTO Files VALUES ('existing-share', 2)")

    def migrate(self, success=True):
        result = subprocess.run([sys.executable, str(SCRIPT), str(self.state), str(self.bootstrap)],
                                capture_output=True, text=True)
        if success:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0)
        return result

    def test_migration_keeps_files_users_permissions_salts_and_backup(self):
        self.migrate()
        config = json.loads(self.config_path.read_text())
        self.assertEqual(config['Authentication']['Method'], 0)
        self.assertEqual(config['Authentication']['HeaderKey'], '')
        self.assertEqual(config['Authentication']['SaltAdmin'], 'keep-admin-salt')
        self.assertEqual(config['Authentication']['SaltFiles'], 'keep-file-salt')
        self.assertEqual(config['Encryption'], self.config['Encryption'])
        self.assertEqual(config['Port'], ':53842')
        password_hash = hashlib.sha1(b'existing-site-passwordkeep-admin-salt').hexdigest()
        with sqlite3.connect(self.db_path) as db:
            self.assertEqual(db.execute('SELECT * FROM Files').fetchall(), [('existing-share', 2)])
            self.assertEqual(db.execute('SELECT Id, Name, Permissions, UserLevel FROM Users').fetchall(),
                             [(1, 'admin', 511, 0), (2, 'alexf', 511, 1), (3, 'other', 0, 2)])
            self.assertEqual(db.execute('SELECT Password FROM Users WHERE Id IN (1,2)').fetchall(),
                             [(password_hash,), (password_hash,)])
            self.assertEqual(db.execute('SELECT Password FROM Users WHERE Id=3').fetchone(),
                             ('keep-other-password',))
        backup = self.state / 'config/native-auth-backup'
        self.assertEqual(json.loads((backup / 'config.json').read_text()), self.config)
        with sqlite3.connect(backup / 'gokapi.sqlite') as db:
            self.assertEqual(db.execute('SELECT Password FROM Users WHERE Id=1').fetchone(),
                             ('old-bootstrap-hash',))

    def test_restart_preserves_changed_password_and_original_backup(self):
        self.migrate()
        with sqlite3.connect(self.db_path) as db:
            db.execute("UPDATE Users SET Password='user-changed-password' WHERE Id=2")
        (self.bootstrap / 'bootstrap-password').write_text('rotated-bootstrap-password')
        self.migrate()
        with sqlite3.connect(self.db_path) as db:
            self.assertEqual(db.execute('SELECT Password FROM Users WHERE Id=2').fetchone(),
                             ('user-changed-password',))
        backup = self.state / 'config/native-auth-backup/config.json'
        self.assertEqual(json.loads(backup.read_text())['Authentication']['Method'], 2)

    def test_missing_admin_fails_before_exposing_native_login(self):
        with sqlite3.connect(self.db_path) as db:
            db.execute('DELETE FROM Users WHERE Id=1')
        self.migrate(success=False)
        self.assertEqual(json.loads(self.config_path.read_text()), self.config)
        with sqlite3.connect(self.db_path) as db:
            self.assertEqual(db.execute('SELECT Password FROM Users WHERE Id=2').fetchone(), ('',))

    def test_already_native_accounts_keep_passwords(self):
        self.config['Authentication']['Method'] = 0
        self.config_path.write_text(json.dumps(self.config))
        self.migrate()
        with sqlite3.connect(self.db_path) as db:
            self.assertEqual(db.execute('SELECT Password FROM Users WHERE Id=1').fetchone(),
                             ('old-bootstrap-hash',))


if __name__ == '__main__':
    unittest.main()
