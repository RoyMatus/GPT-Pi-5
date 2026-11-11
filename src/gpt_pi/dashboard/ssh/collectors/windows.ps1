$work = {
$ErrorActionPreference='Stop'
$cpu=Get-CimInstance -OperationTimeoutSec 3 Win32_Processor
$os=Get-CimInstance -OperationTimeoutSec 3 Win32_OperatingSystem
$drive=Get-CimInstance -OperationTimeoutSec 3 Win32_LogicalDisk -Filter "DeviceID='$env:SystemDrive'"
# Counter-provider WMI queries can time out even for the desktop owner. Read the
# built-in IP interface byte counters instead; no performance-counter group needed.
$rx=$null;$tx=$null
try {
 $stats=@(foreach($interface in [System.Net.NetworkInformation.NetworkInterface]::GetAllNetworkInterfaces()) {
  if($interface.NetworkInterfaceType -ne [System.Net.NetworkInformation.NetworkInterfaceType]::Loopback) {
   try {$interface.GetIPStatistics()} catch { } # Unsupported adapter, not zero traffic.
  }
 })
 if($stats.Count -gt 0) {
  $rx=($stats|Measure-Object BytesReceived -Sum).Sum
  $tx=($stats|Measure-Object BytesSent -Sum).Sum
 }
} catch { } # Missing network statistics must not discard CPU/RAM/disk.
Add-Type -TypeDefinition 'public static class GptPiClock { [System.Runtime.InteropServices.DllImport("kernel32.dll")] public static extern ulong GetTickCount64(); }'
$uptime=[GptPiClock]::GetTickCount64()/1000.0
$data=[ordered]@{schema=1;cpuPct=($cpu|Measure-Object LoadPercentage -Average).Average;cpuGHz=(($cpu|Measure-Object CurrentClockSpeed -Average).Average/1000);cpuTemp=$null;gpuPct=$null;gpuTemp=$null;gpuMemoryUsed=$null;gpuMemoryTotal=$null;gpuWatts=$null;ramUsed=([double]$os.TotalVisibleMemorySize-[double]$os.FreePhysicalMemory)*1024;ramTotal=[double]$os.TotalVisibleMemorySize*1024;diskUsed=[double]$drive.Size-[double]$drive.FreeSpace;diskTotal=[double]$drive.Size;netRxBytes=$rx;netTxBytes=$tx;netRxBitsPerSecond=$null;netTxBitsPerSecond=$null;uptime=$uptime;fanRpm=$null}
$data|ConvertTo-Json -Compress

}
$job=Start-Job -ScriptBlock $work
try {
 $job | Wait-Job -Timeout 8 | Out-Null
 if ($job.State -eq "Failed") { Receive-Job $job -ErrorAction Stop | Out-Null }
 if ($job.State -ne "Completed") { throw "Collector deadline or failure" }
 Receive-Job $job -ErrorAction Stop
} finally {
 Remove-Job $job -Force -ErrorAction SilentlyContinue
}
