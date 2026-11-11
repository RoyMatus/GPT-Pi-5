[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$LhmArchive,
    [Parameter(Mandatory)][string]$PawnInstaller,
    [switch]$Apply
)
$ErrorActionPreference = 'Stop'
$lhmHash = '086d9f1b5a99e643edc2cfaaac16051685b551e4c5ac0b32a57c58c0e529c001'
$pawnHash = '1f519a22e47187f70a1379a48ca604981c4fcf694f4e65b734aaa74a9fba3032'
function Assert-Package([string]$Path, [string]$Expected) {
    $stream = [IO.File]::OpenRead((Resolve-Path -LiteralPath $Path).Path)
    $sha = [Security.Cryptography.SHA256]::Create()
    try { $actual = [BitConverter]::ToString($sha.ComputeHash($stream)).Replace('-','').ToLowerInvariant() }
    finally { $sha.Dispose(); $stream.Dispose() }
    if ($actual -ne $Expected) {
        throw 'Sensor package SHA256 does not match the pinned official release'
    }
}
Assert-Package $LhmArchive $lhmHash
Assert-Package $PawnInstaller $pawnHash
if (!$Apply) {
    Write-Output 'Plan: LibreHardwareMonitor 0.9.6 CPU-only library; signed PawnIO 2.2.0; fixed on-demand SYSTEM task; telemetry role has read/run only. No network listener or periodic sensor process.'
    return
}
$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (!$principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Administrator elevation is required' }
$root = Join-Path $env:ProgramData 'GPT-Pi/telemetry-ssh'
if (!(Test-Path -LiteralPath (Join-Path $root 'managed-by-gpt-pi.txt'))) { throw 'Configure the managed telemetry SSH endpoint first' }
$sid = (Get-LocalUser -Name 'gptpi-monitor').SID.Value
$sensors = Join-Path $root 'sensors'
function Protect-Sensors([string]$Path, [bool]$Read) {
    $acl = New-Object Security.AccessControl.DirectorySecurity
    $acl.SetAccessRuleProtection($true, $false)
    $acl.SetOwner((New-Object Security.Principal.SecurityIdentifier('S-1-5-32-544')))
    foreach ($identity in @('S-1-5-18','S-1-5-32-544')) {
        $acl.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule(
            (New-Object Security.Principal.SecurityIdentifier($identity)), 'FullControl', 'ContainerInherit,ObjectInherit', 'None', 'Allow')))
    }
    if ($Read) {
        $acl.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule(
            (New-Object Security.Principal.SecurityIdentifier($sid)), 'ReadAndExecute', 'ContainerInherit,ObjectInherit', 'None', 'Allow')))
    }
    Set-Acl -LiteralPath $Path -AclObject $acl
}
New-Item -ItemType Directory -Path $sensors -Force | Out-Null
Protect-Sensors $sensors $true
$staging = Join-Path $sensors ([Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $staging | Out-Null
Protect-Sensors $staging $false
try {
    # Validate the protected copies actually used, avoiding a user-writable input race.
    $zip = Join-Path $staging 'lhm.zip'; $installer = Join-Path $staging 'PawnIO_setup.exe'
    Copy-Item -LiteralPath $LhmArchive -Destination $zip
    Copy-Item -LiteralPath $PawnInstaller -Destination $installer
    Assert-Package $zip $lhmHash; Assert-Package $installer $pawnHash
    if ((Get-AuthenticodeSignature -LiteralPath $installer).Status -ne 'Valid') { throw 'PawnIO installer signature is not valid' }
    $process = Start-Process -FilePath $installer -ArgumentList '-install -silent' -Wait -PassThru -WindowStyle Hidden
    if ($process.ExitCode -eq 3010) { throw 'PawnIO installed but requires a Windows restart before verification' }
    if ($process.ExitCode -ne 0) { throw ('PawnIO installation failed: ' + $process.ExitCode) }
    Expand-Archive -LiteralPath $zip -DestinationPath (Join-Path $staging 'expanded')
    $lib = Join-Path $sensors 'lib'
    New-Item -ItemType Directory -Path $lib -Force | Out-Null
    Get-ChildItem -LiteralPath (Join-Path $staging 'expanded') -Filter '*.dll' -File | Copy-Item -Destination $lib -Force
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'windows-cpu-sensors.ps1') -Destination (Join-Path $sensors 'read-cpu.ps1') -Force
    $scheduler = New-Object -ComObject 'Schedule.Service'
    $scheduler.Connect()
    $security = "D:P(A;;FA;;;SY)(A;;FA;;;BA)(A;;GRGX;;;$sid)"
    $folder = $null
    try { $folder = $scheduler.GetFolder('\GPT-Pi') } catch { }
    if ($null -eq $folder) { $folder = $scheduler.GetFolder('\').CreateFolder('GPT-Pi', $security) }
    $existing = $null
    try { $existing = $folder.GetTask('CpuSensors') } catch { }
    if ($null -ne $existing -and $existing.Definition.RegistrationInfo.Description -ne 'GPT-Pi fixed read-only CPU sensors v1') {
        throw 'Refusing to replace an unowned sensor task'
    }
    $definition = $scheduler.NewTask(0)
    $definition.RegistrationInfo.Description = 'GPT-Pi fixed read-only CPU sensors v1'
    $definition.Principal.UserId = 'S-1-5-18'
    $definition.Principal.LogonType = 5
    $definition.Settings.AllowDemandStart = $true
    $definition.Settings.DisallowStartIfOnBatteries = $false
    $definition.Settings.StopIfGoingOnBatteries = $false
    $definition.Settings.ExecutionTimeLimit = 'PT5S'
    $definition.Settings.MultipleInstances = 2 # IgnoreNew; no unbounded queue.
    $definition.Settings.Hidden = $true
    $action = $definition.Actions.Create(0)
    $action.Path = Join-Path $env:WINDIR 'System32/WindowsPowerShell/v1.0/powershell.exe'
    # No $(ArgN) substitutions: Run arguments cannot become executable code or paths.
    $action.Arguments = '-NoLogo -NoProfile -NonInteractive -ExecutionPolicy RemoteSigned -File "' + (Join-Path $sensors 'read-cpu.ps1') + '"'
    $action.WorkingDirectory = $sensors
    $task = $folder.RegisterTaskDefinition('CpuSensors', $definition, 6, 'S-1-5-18', $null, 5, $security)
    $samplePath = Join-Path $sensors 'cpu.json'
    if (Test-Path -LiteralPath $samplePath) { Remove-Item -LiteralPath $samplePath -Force }
    $null = $task.Run($null)
    $timer = [Diagnostics.Stopwatch]::StartNew()
    do { Start-Sleep -Milliseconds 100 } while (!(Test-Path -LiteralPath $samplePath) -and $timer.ElapsedMilliseconds -lt 6000)
    if (!(Test-Path -LiteralPath $samplePath)) {
        throw ('CPU sensor self-check failed: ' + $task.LastTaskResult)
    }
    $sample = [IO.File]::ReadAllText($samplePath) | ConvertFrom-Json
    if ($null -eq $sample.cpuGHz -or $null -eq $sample.cpuTemp) { throw 'CPU sensor self-check returned unavailable readings' }
    Write-Output 'Installed: pinned sensor packages; fixed SYSTEM task, telemetry role read/run only.'
} finally {
    # Staging is a newly created GUID child of the fixed protected sensor directory.
    $resolvedStaging = [IO.Path]::GetFullPath($staging)
    if (!$resolvedStaging.StartsWith([IO.Path]::GetFullPath($sensors) + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe staging cleanup path' }
    Remove-Item -LiteralPath $resolvedStaging -Recurse -Force
}
