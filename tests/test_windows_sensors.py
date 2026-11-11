"""Offline sensor fixtures: units, unavailable fields, adapter and cache boundaries."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SHELL = shutil.which('powershell.exe') if os.name == 'nt' else None
SOURCE = Path(__file__).resolve().parents[1] / 'src/gpt_pi/dashboard/ssh/collectors/windows-sensors.ps1'


class WindowsCollectorPackagingTests(unittest.TestCase):
    def test_encoded_collector_contains_optional_providers_without_remote_sidecar(self):
        from gpt_pi.dashboard.ssh.service import windows_collector_script
        script = windows_collector_script()
        self.assertIn('function Get-GptPiHardware', script)
        self.assertIn('function ConvertFrom-GptPiNvidiaCsv', script)
        # Windows CreateProcess limit; leave space for the fixed PowerShell arguments.
        import base64
        self.assertLess(len(base64.b64encode(script.encode('utf-16le'))), 30000)


@unittest.skipUnless(SHELL, 'Windows PowerShell required')
class WindowsSensorsTests(unittest.TestCase):
    def run_ps(self, body):
        script = ". '" + str(SOURCE).replace("'", "''") + "'\n" + body
        result = subprocess.run([SHELL, '-NoProfile', '-ExecutionPolicy', 'RemoteSigned',
                                 '-Command', script], capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))
        return json.loads(result.stdout.decode('utf-8-sig'))

    def test_packaged_encoded_worker_runs_without_a_remote_sidecar(self):
        import base64
        from gpt_pi.dashboard.ssh.service import windows_collector_script
        script = windows_collector_script().replace(
            "$ErrorActionPreference='Stop'",
            "function Get-GptPiHardware { ConvertFrom-GptPiNvidiaCsv '17, 42.5, 1024, 8192, 39.75' }\n$ErrorActionPreference='Stop'", 1)
        with tempfile.TemporaryDirectory() as folder:
            result = subprocess.run([SHELL, '-NoProfile', '-EncodedCommand',
                                     base64.b64encode(script.encode('utf-16le')).decode()],
                                    cwd=folder, capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))
        sample = json.loads(result.stdout.decode('utf-8-sig'))
        self.assertEqual(sample['gpuPct'], 17)
        self.assertEqual(sample['gpuMemoryUsed'], 1073741824)
        self.assertGreater(sample['ramTotal'], 0)
        self.assertIsNone(sample['cpuTemp'])

    def test_gpu_units_and_unavailable_values(self):
        data = self.run_ps("ConvertFrom-GptPiNvidiaCsv '17, 42.5, 1024, 8192, 39.75' | ConvertTo-Json -Compress")
        self.assertEqual(data.get('gpuPct'), 17)
        self.assertEqual(data.get('gpuTemp'), 42.5)
        self.assertEqual(data.get('gpuMemoryUsed'), 1024 * 1048576)
        self.assertEqual(data.get('gpuMemoryTotal'), 8192 * 1048576)
        self.assertEqual(data.get('gpuWatts'), 39.75)
        data = self.run_ps("ConvertFrom-GptPiNvidiaCsv 'N/A, [Not Supported], 1, 8, N/A' | ConvertTo-Json -Compress")
        self.assertIsNone(data.get('gpuPct'))
        self.assertIsNone(data.get('gpuTemp'))
        self.assertIsNone(data.get('gpuWatts'))
        self.assertEqual(data.get('gpuMemoryUsed'), 1048576)

    def test_gpu_invalid_and_multiple_adapters_fail_closed(self):
        for fixture in ['101, -1, 10, 8, NaN', '0, 40, 0, 8, 20\n0, 50, 0, 16, 30', 'bad,csv']:
            escaped = fixture.replace("'", "''").replace('\n', '`n')
            data = self.run_ps(f'ConvertFrom-GptPiNvidiaCsv "{escaped}" | ConvertTo-Json -Compress')
            self.assertFalse(any(v is not None for v in data.values()))

    def test_cpu_uses_package_temperature_and_mean_core_clock(self):
        body = r'''
$hw=@([pscustomobject]@{HardwareType='Cpu'; Sensors=@(
 [pscustomobject]@{SensorType='Clock';Name='Bus Speed';Value=100},
 [pscustomobject]@{SensorType='Clock';Name='CPU Core #1';Value=4200},
 [pscustomobject]@{SensorType='Clock';Name='CPU Core #2';Value=4400},
 [pscustomobject]@{SensorType='Temperature';Name='CPU Core #1';Value=61},
 [pscustomobject]@{SensorType='Temperature';Name='CPU Package';Value=65})},
 [pscustomobject]@{HardwareType='GpuNvidia'; Sensors=@(
 [pscustomobject]@{SensorType='Temperature';Name='GPU Core';Value=99})})
ConvertFrom-GptPiCpuSensors $hw | ConvertTo-Json -Compress
'''
        data = self.run_ps(body)
        self.assertAlmostEqual(data.get('cpuGHz', 0), 4.3)
        self.assertEqual(data.get('cpuTemp'), 65)

    def test_cache_expired_future_or_malformed_is_not_current(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'sample.json'
            for stamp, expected in [(10000, 4.3), (1, None), (20000, None)]:
                path.write_text(json.dumps(dict(schema=1, sampledAt=stamp, cpuGHz=4.3, cpuTemp=65)))
                data = self.run_ps(f"Read-GptPiCpuSample '{path}' 11000 | ConvertTo-Json -Compress")
                self.assertEqual(data.get('cpuGHz'), expected)
            path.write_text('{broken')
            data = self.run_ps(f"Read-GptPiCpuSample '{path}' 11000 | ConvertTo-Json -Compress")
            self.assertFalse(any(v is not None for v in data.values()))

    def test_cache_can_be_published_repeatedly_without_partial_or_temp_files(self):
        with tempfile.TemporaryDirectory() as folder:
            body = f"""
$ErrorActionPreference='Stop'
Write-GptPiCpuSample '{folder}' @{{schema=1;sampledAt=10000;cpuGHz=4.2;cpuTemp=60}}
Write-GptPiCpuSample '{folder}' @{{schema=1;sampledAt=11000;cpuGHz=4.3;cpuTemp=65}}
Read-GptPiCpuSample '{folder}/cpu.json' 11000 | ConvertTo-Json -Compress
"""
            data = self.run_ps(body)
            self.assertEqual(data.get('cpuGHz'), 4.3)
            self.assertEqual(data.get('cpuTemp'), 65)
            self.assertEqual([p.name for p in Path(folder).iterdir()], ['cpu.json'])
