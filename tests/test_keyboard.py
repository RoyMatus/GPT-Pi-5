import json
import os
from pathlib import Path
import tempfile
import time
import unittest

from gpt_pi.keyboard import read_geometry


class KeyboardGeometryTests(unittest.TestCase):
    def test_guest_endpoint_exposes_geometry_only(self):
        from unittest.mock import patch
        from starlette.testclient import TestClient
        from gpt_pi.config import Settings
        from gpt_pi.webapp import create_app
        from test_webapp import FakeCloud
        with tempfile.TemporaryDirectory() as directory:
            settings=Settings(data_dir=Path(directory))
            with TestClient(create_app(settings,FakeCloud()),base_url=settings.origin) as client:
                with patch('gpt_pi.webapp.read_geometry',return_value={'visible':True,'height':420}):
                    response=client.get('/api/keyboard')
                self.assertEqual(response.status_code,200)
                self.assertEqual(response.json(),{'visible':True,'height':420})

    def test_fresh_geometry_has_no_input_or_process_information(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'geometry.json'
            path.write_text(json.dumps({'visible':True,'height':420,'updated':time.monotonic(),
                                        'text':'must never be exposed'}))
            path.chmod(0o600)
            self.assertEqual(read_geometry(path), {'visible':True,'height':420})

    def test_stale_untrusted_and_unbounded_records_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'geometry.json'
            for data in [{'visible':True,'height':420,'updated':time.monotonic()-10},
                         {'visible':True,'height':90000,'updated':time.monotonic()},
                         {'visible':True,'height':True,'updated':time.monotonic()},
                         {'visible':True,'height':420,'updated':time.monotonic()+100},
                         {'visible':True,'height':420,'updated':'bad'}]:
                path.write_text(json.dumps(data));path.chmod(0o600)
                self.assertEqual(read_geometry(path), {'visible':False,'height':0})
            path.write_text('x'*300);self.assertEqual(read_geometry(path),{'visible':False,'height':0})
            if os.name=='posix':
                path.write_text(json.dumps({'visible':True,'height':420,'updated':time.monotonic()}))
                path.chmod(0o666);self.assertEqual(read_geometry(path),{'visible':False,'height':0})
                path.chmod(0o600);link=path.with_name('link');link.symlink_to(path)
                self.assertEqual(read_geometry(link),{'visible':False,'height':0})

    def test_absent_or_hidden_keyboard_reserves_no_space(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'geometry.json'
            self.assertEqual(read_geometry(path),{'visible':False,'height':0})
            path.write_text(json.dumps({'visible':False,'height':420,'updated':time.monotonic()}));path.chmod(0o600)
            self.assertEqual(read_geometry(path),{'visible':False,'height':0})
