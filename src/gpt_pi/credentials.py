"""Owner-only backend credentials, indexed by a hash of the browser session secret."""
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile

from .cloud import Connection, ISSUER


class CredentialStore:
    def __init__(self, data_dir):
        self.root = Path(data_dir) / 'credentials'
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        if os.name == 'posix':
            self.root.chmod(0o700)
        self.lock_file = None

    def acquire(self):
        self.lock_file = os.fdopen(os.open(self.root / 'runtime.lock', os.O_CREAT | os.O_RDWR, 0o600), 'r+b')
        try:
            if os.name == 'posix':
                import fcntl
                fcntl.flock(self.lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            else:
                import msvcrt
                self.lock_file.seek(0)
                msvcrt.locking(self.lock_file.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            self.lock_file.close()
            self.lock_file = None
            raise RuntimeError('Another GPT-Pi instance is using this data directory') from None

    def release(self):
        if self.lock_file:
            self.lock_file.close()
            self.lock_file = None

    def path(self, key):
        if not isinstance(key, str) or not re.fullmatch(r'[A-Za-z0-9_-]{43}', key):
            return None
        return self.root / (hashlib.sha256(key.encode()).hexdigest() + '.json')

    def save(self, key, connection):
        target = self.path(key)
        if target is None:
            raise ValueError('Invalid local session')
        record = {'version': 1, 'issuer': ISSUER, 'client_id': connection.client_id,
                  'subject': connection.subject, 'name': connection.name, 'token': connection.token}
        fd, filename = tempfile.mkstemp(prefix='.write-', dir=self.root)
        temporary = Path(filename)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as output:
                json.dump(record, output)
                output.flush()
                os.fsync(output.fileno())
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)

    def load(self, key):
        path = self.path(key)
        if path is None:
            return None
        try:
            flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0)
            with os.fdopen(os.open(path, flags), 'r', encoding='utf-8') as source:
                mode = os.fstat(source.fileno())
                if not stat.S_ISREG(mode.st_mode) or mode.st_size > 256000:
                    return None
                if os.name == 'posix' and (mode.st_uid != os.getuid() or mode.st_mode & 0o077):
                    return None
                record = json.load(source)
            if record.get('version') != 1 or record.get('issuer') != ISSUER:
                return None
            if not all(isinstance(record.get(field), str) and record[field]
                       for field in ('client_id', 'subject', 'name')):
                return None
            token = record['token']
            if not isinstance(token, dict) or not token.get('access_token'):
                return None
            return Connection(record['client_id'], record['subject'], record['name'], token)
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            return None

    def delete(self, key):
        path = self.path(key)
        if path is not None:
            path.unlink(missing_ok=True)
