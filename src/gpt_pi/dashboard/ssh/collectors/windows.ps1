$work = {
$ErrorActionPreference='Stop'
# CIM providers can time out in SSH sessions. All collection uses local, read-only
# kernel/.NET APIs; no WMI, performance-counter group or external sensor driver.
Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Threading;
public static class GptPiNative {
 [StructLayout(LayoutKind.Sequential)]
 public struct FileTime { public uint Low, High; }
 [StructLayout(LayoutKind.Sequential)]
 public struct MemoryStatus {
  public uint Length, Load;
  public ulong TotalPhys, AvailPhys, TotalPage, AvailPage, TotalVirtual, AvailVirtual, AvailExtended;
 }
 [DllImport("kernel32.dll", SetLastError=true)]
 static extern bool GetSystemTimes(out FileTime idle, out FileTime kernel, out FileTime user);
 [DllImport("kernel32.dll", SetLastError=true)]
 static extern bool GlobalMemoryStatusEx(ref MemoryStatus memory);
 [DllImport("kernel32.dll")]
 public static extern ulong GetTickCount64();
 [DllImport("kernel32.dll")]
 static extern uint GetActiveProcessorCount(ushort group);
 static ulong T(FileTime t) { return ((ulong)t.High << 32) | t.Low; }
 public static MemoryStatus Memory() {
  MemoryStatus m = new MemoryStatus();
  m.Length = (uint)Marshal.SizeOf(typeof(MemoryStatus));
  if (!GlobalMemoryStatusEx(ref m)) throw new Win32Exception(Marshal.GetLastWin32Error());
  return m;
 }
 public static double? Cpu() {
  // Do not present the primary processor group as a whole machine >64 CPUs.
  if (GetActiveProcessorCount(0xffff) > 64) return null;
  FileTime i1,k1,u1,i2,k2,u2;
  if (!GetSystemTimes(out i1,out k1,out u1)) return null;
  Thread.Sleep(250);
  if (!GetSystemTimes(out i2,out k2,out u2)) return null;
  if (T(i2)<T(i1) || T(k2)<T(k1) || T(u2)<T(u1)) return null;
  ulong total=(T(k2)-T(k1))+(T(u2)-T(u1)), idle=T(i2)-T(i1);
  if (total==0 || idle>total) return null;
  return 100.0*(total-idle)/total;
 }
}
'@
$cpuPct=[GptPiNative]::Cpu()
$memory=[GptPiNative]::Memory()
$drive=New-Object System.IO.DriveInfo($env:SystemDrive)
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
$uptime=[GptPiNative]::GetTickCount64()/1000.0
$data=[ordered]@{schema=1;cpuPct=$cpuPct;cpuGHz=$null;cpuTemp=$null;gpuPct=$null;gpuTemp=$null;gpuMemoryUsed=$null;gpuMemoryTotal=$null;gpuWatts=$null;ramUsed=$memory.TotalPhys-$memory.AvailPhys;ramTotal=$memory.TotalPhys;diskUsed=$drive.TotalSize-$drive.TotalFreeSpace;diskTotal=$drive.TotalSize;netRxBytes=$rx;netTxBytes=$tx;netRxBitsPerSecond=$null;netTxBitsPerSecond=$null;uptime=$uptime;fanRpm=$null}
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
