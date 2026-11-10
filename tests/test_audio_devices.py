import subprocess
import unittest
from unittest.mock import patch

from gpt_pi.audio_devices import classify, read_status


def node(name, kind, **props):
    return {'type': 'PipeWire:Interface:Node', 'info': {'props': {
        'node.name': name, 'media.class': kind, **props}}}


class AudioDeviceTests(unittest.TestCase):
    def test_dummy_output_and_monitor_are_not_microphone_or_speaker(self):
        self.assertEqual({'microphone': False, 'speaker': False}, classify([
            node('auto_null', 'Audio/Sink', **{'factory.name': 'support.null-audio-sink'}),
            node('auto_null.monitor', 'Audio/Source'),
            node('browser', 'Stream/Output/Audio')]))

    def test_usb_port_names_do_not_change_availability_or_leak_identifiers(self):
        for port in ('usb-first-private-id', 'usb-second-private-id'):
            self.assertEqual({'microphone': True, 'speaker': True}, classify([
                node(port + '-input', 'Audio/Source'), node(port + '-output', 'Audio/Sink')]))

    def test_missing_tool_or_timeout_reports_unknown(self):
        for error in (FileNotFoundError(), subprocess.TimeoutExpired('pw-dump', 2)):
            with self.subTest(error=type(error).__name__), patch('subprocess.run', side_effect=error):
                self.assertEqual({'microphone': None, 'speaker': None}, read_status())
