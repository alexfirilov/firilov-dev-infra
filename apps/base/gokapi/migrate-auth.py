"""Reconcile native login before Gokapi starts; migrate header users once."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import sys


os.umask(0o077)
state = Path(sys.argv[1])
bootstrap = Path(sys.argv[2])
config_path = state / 'config/config.json'
config = json.loads(config_path.read_text())
auth = config['Authentication']

if auth['Method'] == 2:
    # Keep the existing salts: changing them would invalidate other passwords.
    password = (bootstrap / 'bootstrap-password').read_text().rstrip('\n')
    if len(password) < 8 or not auth['SaltAdmin']:
        raise RuntimeError('Native login requires a valid bootstrap password and salt')
    password_hash = hashlib.sha1((password + auth['SaltAdmin']).encode()).hexdigest()
    backup = state / 'config/native-auth-backup'
    backup.mkdir(mode=0o700, exist_ok=True)
    with sqlite3.connect(state / 'data/gokapi.sqlite') as db:
        if db.execute('SELECT COUNT(*) FROM Users WHERE Name=? AND UserLevel=0',
                      (auth['Username'],)).fetchone()[0] != 1:
            raise RuntimeError('Existing super-admin account is missing; migration aborted')
        if not (backup / 'config.json').exists():
            shutil.copy2(config_path, backup / 'config.json')
        if not (backup / 'gokapi.sqlite').exists():
            temp_backup = backup / 'gokapi.sqlite.tmp'
            with sqlite3.connect(temp_backup) as target:
                db.backup(target)
            temp_backup.replace(backup / 'gokapi.sqlite')
        # These two accounts previously used the same site password in Caddy.
        db.execute('UPDATE Users SET Password=?, ResetPassword=0 WHERE Name IN (?, ?)',
                   (password_hash, auth['Username'], 'alexf'))
    print('Migrated existing accounts to native login; original state backed up')
elif auth['Method'] != 0:
    raise RuntimeError('Unexpected authentication mode; migration aborted')

auth['Method'] = 0
auth['HeaderKey'] = ''
config['Port'] = ':53842'
temporary_config = config_path.with_suffix('.json.tmp')
temporary_config.write_text(json.dumps(config, indent=2) + '\n')
temporary_config.replace(config_path)
print('Native login configuration ready')
