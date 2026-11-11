"""Mocked Windows worker failures must survive the bounded collector wrapper."""
import os
from pathlib import Path
import shutil
import subprocess
import unittest

SHELL=shutil.which('powershell.exe') if os.name=='nt' else None
COLLECTOR=Path(__file__).resolve().parents[1]/'src/gpt_pi/dashboard/ssh/collectors/windows.ps1'


@unittest.skipUnless(SHELL,'Windows PowerShell required')
class WindowsCollectorFailureTests(unittest.TestCase):
    def test_network_wmi_timeout_does_not_discard_core_metrics(self):
        script=r'''
function Get-CimInstance {
 param([string]$ClassName,[int]$OperationTimeoutSec,[string]$Filter)
 switch ($ClassName) {
  'Win32_Processor' {[pscustomobject]@{LoadPercentage=12;CurrentClockSpeed=3200}}
  'Win32_OperatingSystem' {[pscustomobject]@{TotalVisibleMemorySize=1000;FreePhysicalMemory=400}}
  'Win32_LogicalDisk' {[pscustomobject]@{Size=10000;FreeSpace=3000}}
  default {throw 'synthetic network WMI timeout'}
 }
}
function Start-Job {
 param($ScriptBlock)
 try {$value=& $ScriptBlock; [pscustomobject]@{State='Completed';Value=$value}}
 catch {[pscustomobject]@{State='Failed';Reason=$_.Exception.Message}}
}
function Wait-Job { param([Parameter(ValueFromPipeline)]$InputObject,[int]$Timeout); process {$InputObject} }
function Receive-Job { param($Job,[string]$ErrorAction); if($Job.State -eq 'Failed'){throw $Job.Reason};$Job.Value }
function Remove-Job { param($Job,[switch]$Force,[string]$ErrorAction) }
. 'COLLECTOR'
'''.replace('COLLECTOR',str(COLLECTOR).replace("'","''"))
        result=subprocess.run([SHELL,'-NoProfile','-ExecutionPolicy','RemoteSigned','-Command',script],
                              capture_output=True,timeout=15)
        self.assertEqual(result.returncode,0,result.stderr.decode(errors='replace'))
        import json
        data=json.loads(result.stdout.decode('utf-8-sig'))
        self.assertEqual(data['cpuPct'],12)
        self.assertEqual(data['ramTotal'],1000*1024)
        self.assertEqual(data['diskTotal'],10000)
        self.assertIsNone(data['netRxBitsPerSecond'])
        self.assertGreater(data['uptime'],0)

    def test_failed_worker_reason_is_not_hidden_and_job_is_removed(self):
        script=r'''
function Start-Job { param($ScriptBlock); [pscustomobject]@{State='Failed'} }
function Wait-Job { param([Parameter(ValueFromPipeline)]$InputObject,[int]$Timeout); process { $InputObject } }
function Receive-Job { param($Job,[string]$ErrorAction); throw 'synthetic provider failure' }
function Remove-Job { param($Job,[switch]$Force,[string]$ErrorAction); $global:removed=$true }
try { . 'COLLECTOR'; exit 21 }
catch {
 if (!$global:removed) {exit 22}
 if ($_.Exception.Message -ne 'synthetic provider failure') {exit 23}
 exit 0
}
'''.replace('COLLECTOR',str(COLLECTOR).replace("'","''"))
        result=subprocess.run([SHELL,'-NoProfile','-ExecutionPolicy','RemoteSigned','-Command',script],
                              capture_output=True,timeout=15)
        self.assertEqual(result.returncode,0,result.stderr.decode(errors='replace'))
