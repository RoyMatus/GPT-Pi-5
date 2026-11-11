"""Safe preview/input rejection of the elevated Windows setup, without installing SSH."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SHELL = shutil.which('powershell.exe') if os.name == 'nt' else None
SCRIPT = Path(__file__).resolve().parents[1] / 'deploy/setup-windows-telemetry.ps1'


@unittest.skipUnless(SHELL, 'Windows PowerShell is required')
class WindowsSetupPreviewTests(unittest.TestCase):
    def test_sensor_setup_rejects_unpinned_packages_before_elevation_or_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / 'untrusted.bin'
            package.write_bytes(b'synthetic invalid sensor package')
            script = SCRIPT.with_name('setup-windows-sensors.ps1')
            result = subprocess.run([SHELL, '-NoProfile', '-ExecutionPolicy', 'RemoteSigned',
                                     '-File', str(script), '-LhmArchive', str(package),
                                     '-PawnInstaller', str(package), '-Apply'],
                                    capture_output=True, timeout=15)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(b'SHA256 does not match', result.stderr)

    def run_preview(self, key, device='192.0.2.10', listen='192.0.2.20'):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'key.pub').write_text(key, encoding='ascii')
            (root/'host').write_text('synthetic preview only', encoding='ascii')
            return subprocess.run([SHELL, '-NoLogo', '-NoProfile', '-ExecutionPolicy',
                                   'RemoteSigned', '-File', str(SCRIPT), '-PublicKeyPath',
                                   str(root/'key.pub'), '-HostKeyPath', str(root/'host'),
                                   '-DeviceAddress', device, '-ListenAddress', listen],
                                  capture_output=True, timeout=20)

    def test_preview_needs_no_administrator_or_system_changes(self):
        result = self.run_preview('ssh-ed25519 ' + 'A'*68)
        self.assertEqual(result.returncode, 0)
        self.assertIn(b'Plan:', result.stdout)

    def test_public_key_options_and_extra_lines_are_rejected(self):
        for key in ['command="cmd" ssh-ed25519 ' + 'A'*68,
                    'ssh-ed25519 ' + 'A'*68 + '\nssh-ed25519 ' + 'B'*68]:
            self.assertNotEqual(self.run_preview(key).returncode, 0)

    def test_unspecified_loopback_and_injected_addresses_are_rejected(self):
        for address in ['0.0.0.0', '127.0.0.1', '::1', '192.0.2.1\nAllowUsers *']:
            self.assertNotEqual(self.run_preview('ssh-ed25519 '+'A'*68, device=address).returncode, 0)


if __name__ == '__main__':
    unittest.main()
