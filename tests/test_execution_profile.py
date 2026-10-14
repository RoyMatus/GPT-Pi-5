import subprocess
import unittest
from unittest.mock import patch

from tools.execution_profile import collect, linux_memory, probe


class ExecutionProfileTests(unittest.TestCase):
    def test_linux_memory_units_and_missing_available(self):
        self.assertEqual({'total_bytes': 2048, 'available_bytes': 1024},
                         linux_memory('MemTotal: 2 kB\nMemAvailable: 1 kB'))
        self.assertIsNone(linux_memory('MemTotal: 2 kB')['available_bytes'])

    def test_missing_audio_tool_is_unknown_not_success(self):
        with patch('tools.execution_profile.shutil.which', return_value=None), patch('subprocess.run') as run:
            self.assertEqual({'status': 'unavailable'}, probe(['arecord', '-l']))
            run.assert_not_called()

    def test_probe_has_timeout_and_no_shell(self):
        with patch('tools.execution_profile.shutil.which', return_value='/synthetic/aplay'), patch('subprocess.run') as run:
            run.side_effect = subprocess.TimeoutExpired(['aplay', '-l'], 5)
            self.assertEqual({'status': 'timeout'}, probe(['aplay', '-l']))
            self.assertEqual(5, run.call_args.kwargs['timeout'])
            self.assertFalse(run.call_args.kwargs.get('shell', False))

    def test_device_probe_does_not_run_linux_commands_on_windows(self):
        with patch('tools.execution_profile.platform.system', return_value='Windows'), \
                patch('tools.execution_profile.memory', return_value={}), \
                patch('tools.execution_profile.probe') as run:
            result = collect(device=True)
            self.assertEqual('unsupported_host', result['device']['status'])
            self.assertFalse(result['hardware_verified'])
            run.assert_not_called()

    def test_default_does_not_enumerate_audio(self):
        with patch('tools.execution_profile.probe') as run:
            result = collect()
            self.assertNotIn('device', result)
            self.assertNotIn('hostname', result)
            run.assert_not_called()
