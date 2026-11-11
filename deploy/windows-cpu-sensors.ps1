# Fixed, argument-free, on-demand scheduled task. SYSTEM reads CPU sensors;
# the SSH role can only run this task and read its small, expiring result.
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
. (Join-Path $PSScriptRoot '../windows-sensors.ps1')
$computer = $null
try {
    $null = [Reflection.Assembly]::LoadFrom((Join-Path $PSScriptRoot 'lib/LibreHardwareMonitorLib.dll'))
    $computer = New-Object LibreHardwareMonitor.Hardware.Computer
    $computer.IsCpuEnabled = $true
    $computer.Open()
    foreach ($hardware in $computer.Hardware) { $hardware.Update() }
    Start-Sleep -Milliseconds 100
    foreach ($hardware in $computer.Hardware) { $hardware.Update() }
    $data = ConvertFrom-GptPiCpuSensors $computer.Hardware
    $data.schema = 1
    $data.sampledAt = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
    Write-GptPiCpuSample $PSScriptRoot $data
} finally {
    if ($null -ne $computer) { $computer.Close() }
}
