"""Offline module scope checks; real keyboard/compositor acceptance remains separate."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.name == 'posix' and shutil.which('cc') and shutil.which('pkg-config'),
                     'Linux C compiler and GLib development headers are required')
class KeyboardOverlayTests(unittest.TestCase):
    def test_only_keyboard_surface_in_keyboard_process_is_raised(self):
        flags = subprocess.run(['pkg-config', '--cflags', '--libs', 'gobject-2.0'],
                               capture_output=True, text=True, timeout=10)
        if flags.returncode:
            self.skipTest('GLib development headers are not installed')
        import shlex
        with tempfile.TemporaryDirectory() as directory:
            binary = str(Path(directory)/'osk-overlay-test')
            subprocess.run(['cc', '-Wall', '-Wextra', '-Werror',
                            str(ROOT/'tests/osk_overlay_test.c'),
                            *shlex.split(flags.stdout), '-o', binary],
                           check=True, capture_output=True, timeout=30)
            for args in [[], ['unrelated-application']]:
                runtime=Path(directory)/('keyboard' if not args else 'other')
                runtime.mkdir()
                subprocess.run([binary, *args], check=True, capture_output=True, timeout=10,
                               env={**os.environ, 'G_DEBUG': 'fatal-warnings', 'XDG_RUNTIME_DIR':str(runtime)})
                geometry=runtime/'gpt-pi-osk/geometry.json'
                if args:
                    self.assertFalse(geometry.exists())
                else:
                    import json
                    data=json.loads(geometry.read_text())
                    self.assertTrue(data['visible'])
                    self.assertEqual(data['height'],420)
