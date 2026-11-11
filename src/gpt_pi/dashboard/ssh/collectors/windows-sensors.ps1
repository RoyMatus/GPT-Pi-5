function ConvertTo-GptPiNumber($Value, [double]$Maximum) {
    $number = 0.0
    if ($null -ne $Value -and [double]::TryParse([string]$Value,
        [Globalization.NumberStyles]::Float, [Globalization.CultureInfo]::InvariantCulture,
        [ref]$number) -and ![double]::IsNaN($number) -and ![double]::IsInfinity($number) -and
        $number -ge 0 -and $number -le $Maximum) { return $number }
    return $null
}

function ConvertFrom-GptPiNvidiaCsv([string]$Text) {
    $data = @{gpuPct=$null;gpuTemp=$null;gpuMemoryUsed=$null;gpuMemoryTotal=$null;gpuWatts=$null}
    # Exactly one physical NVIDIA adapter (index 0); never combine different GPUs.
    $parts = $Text.Trim().Split(',')
    if ($parts.Count -ne 5 -or $Text.Trim() -match '[\r\n]') { return $data }
    $data.gpuPct = ConvertTo-GptPiNumber $parts[0].Trim() 100
    $data.gpuTemp = ConvertTo-GptPiNumber $parts[1].Trim() 200
    $used = ConvertTo-GptPiNumber $parts[2].Trim() 10000000
    $total = ConvertTo-GptPiNumber $parts[3].Trim() 10000000
    if ($null -ne $used -and $null -ne $total -and $total -gt 0 -and $used -le $total) {
        $data.gpuMemoryUsed = $used * 1048576
        $data.gpuMemoryTotal = $total * 1048576
    }
    $data.gpuWatts = ConvertTo-GptPiNumber $parts[4].Trim() 10000
    return $data
}

function ConvertFrom-GptPiCpuSensors($Hardware) {
    $clocks = @(); $packages = @(); $cores = @()
    foreach ($cpu in $Hardware) {
        if ([string]$cpu.HardwareType -ne 'Cpu') { continue }
        foreach ($sensor in $cpu.Sensors) {
            if ([string]$sensor.SensorType -eq 'Clock' -and $sensor.Name -match '^CPU Core #') {
                $value = ConvertTo-GptPiNumber $sensor.Value 20000
                if ($null -ne $value -and $value -gt 0) { $clocks += $value }
            }
            if ([string]$sensor.SensorType -eq 'Temperature') {
                $value = ConvertTo-GptPiNumber $sensor.Value 200
                if ($null -ne $value) {
                    if ($sensor.Name -eq 'CPU Package') { $packages += $value }
                    elseif ($sensor.Name -match '^CPU Core #') { $cores += $value }
                }
            }
        }
    }
    $data = @{cpuGHz=$null;cpuTemp=$null}
    if ($clocks.Count) { $data.cpuGHz = ($clocks | Measure-Object -Average).Average / 1000.0 }
    if ($packages.Count) { $data.cpuTemp = ($packages | Measure-Object -Maximum).Maximum }
    elseif ($cores.Count) { $data.cpuTemp = ($cores | Measure-Object -Maximum).Maximum }
    return $data
}

function Read-GptPiCpuSample([string]$Path, [long]$Now) {
    $empty = @{cpuGHz=$null;cpuTemp=$null}
    try {
        $file = Get-Item -LiteralPath $Path -ErrorAction Stop
        if ($file.Length -gt 1024) { return $empty }
        $sample = [IO.File]::ReadAllText($Path) | ConvertFrom-Json -ErrorAction Stop
        if ($sample.schema -ne 1 -or $sample.sampledAt -isnot [long] -and $sample.sampledAt -isnot [int]) { return $empty }
        $age = $Now - $sample.sampledAt
        if ($age -lt 0 -or $age -gt 5000) { return $empty }
        return @{cpuGHz=(ConvertTo-GptPiNumber $sample.cpuGHz 20);cpuTemp=(ConvertTo-GptPiNumber $sample.cpuTemp 200)}
    } catch { return $empty }
}

function Write-GptPiCpuSample([string]$Directory, $Data) {
    $path = Join-Path $Directory 'cpu.json'
    $temporary = Join-Path $Directory ([Guid]::NewGuid().ToString('N') + '.tmp')
    try {
        [IO.File]::WriteAllText($temporary, ($Data | ConvertTo-Json -Compress), (New-Object Text.UTF8Encoding($false)))
        # PS 5.1 converts $null to an empty path for a .NET string parameter.
        if (Test-Path -LiteralPath $path) { [IO.File]::Replace($temporary, $path, [NullString]::Value) }
        else { [IO.File]::Move($temporary, $path) }
    } finally {
        if (Test-Path -LiteralPath $temporary) { [IO.File]::Delete($temporary) }
    }
}

function Get-GptPiHardware {
    $data = @{}
    $process = $null
    try {
        $exe = Join-Path $env:WINDIR 'System32/nvidia-smi.exe'
        if (Test-Path -LiteralPath $exe -PathType Leaf) {
            $info = New-Object Diagnostics.ProcessStartInfo
            $info.FileName = $exe
            $info.Arguments = '--id=0 --query-gpu=utilization.gpu,temperature.gpu,memory.used,memory.total,power.draw --format=csv,noheader,nounits'
            $info.UseShellExecute = $false; $info.CreateNoWindow = $true
            $info.RedirectStandardOutput = $true; $info.RedirectStandardError = $true
            $process = [Diagnostics.Process]::Start($info)
            $output = $process.StandardOutput.ReadToEndAsync()
            $errors = $process.StandardError.ReadToEndAsync()
            if ($process.WaitForExit(1200) -and $process.ExitCode -eq 0 -and $output.Result.Length -le 4096) {
                $data = ConvertFrom-GptPiNvidiaCsv $output.Result
            }
        }
    } catch { } finally {
        if ($null -ne $process) {
            if (!$process.HasExited) { $process.Kill() }
            $process.Dispose()
        }
    }
    try {
        $stage = 'scheduler'
        $scheduler = New-Object -ComObject 'Schedule.Service'
        $scheduler.Connect()
        $task = $scheduler.GetFolder('\GPT-Pi').GetTask('CpuSensors')
        $stage = 'run'
        $null = $task.Run($null)
        $stage = 'sample'
        $path = Join-Path $env:ProgramData 'GPT-Pi/telemetry-ssh/sensors/cpu.json'
        $timer = [Diagnostics.Stopwatch]::StartNew()
        do {
            Start-Sleep -Milliseconds 100
            $cpu = Read-GptPiCpuSample $path ([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds())
            if ($null -ne $cpu.cpuGHz -or $null -ne $cpu.cpuTemp) {
                foreach ($key in $cpu.Keys) { $data[$key] = $cpu[$key] }
                break
            }
        } while ($timer.ElapsedMilliseconds -lt 2500)
    } catch {
        # Fixed stage/HRESULT only, never exception text or machine/user identifiers.
        [Console]::Error.WriteLine(('CPU sensor {0}: 0x{1:X8}' -f $stage, $_.Exception.HResult))
    } # Optional hardware access must never discard the kernel metrics.
    return $data
}
