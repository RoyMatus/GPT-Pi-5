$ErrorActionPreference='Stop'
$cpu=Get-CimInstance Win32_Processor
$os=Get-CimInstance Win32_OperatingSystem
$drive=Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='$env:SystemDrive'"
$net=Get-CimInstance Win32_PerfFormattedData_Tcpip_NetworkInterface
$data=[ordered]@{schema=1;cpuPct=($cpu|Measure-Object LoadPercentage -Average).Average;cpuGHz=(($cpu|Measure-Object CurrentClockSpeed -Average).Average/1000);cpuTemp=$null;gpuPct=$null;gpuTemp=$null;gpuMemoryUsed=$null;gpuMemoryTotal=$null;gpuWatts=$null;ramUsed=([double]$os.TotalVisibleMemorySize-[double]$os.FreePhysicalMemory)*1024;ramTotal=[double]$os.TotalVisibleMemorySize*1024;diskUsed=[double]$drive.Size-[double]$drive.FreeSpace;diskTotal=[double]$drive.Size;netRxBytes=$null;netTxBytes=$null;netRxBitsPerSecond=($net|Measure-Object BytesReceivedPersec -Sum).Sum*8;netTxBitsPerSecond=($net|Measure-Object BytesSentPersec -Sum).Sum*8;uptime=0;fanRpm=$null}
$data|ConvertTo-Json -Compress
