[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$PublicKeyPath,
    [Parameter(Mandatory)][string]$HostKeyPath,
    [Parameter(Mandatory)][string]$DeviceAddress,
    [Parameter(Mandatory)][string]$ListenAddress,
    [switch]$Apply
)
# Explicit administrator setup; this is not called by the dashboard or model.
$ErrorActionPreference = 'Stop'
foreach ($address in @($DeviceAddress, $ListenAddress)) {
    $parsed = $null
    if (![Net.IPAddress]::TryParse($address, [ref]$parsed) -or
        $parsed.AddressFamily -ne [Net.Sockets.AddressFamily]::InterNetwork -or
        $parsed.Equals([Net.IPAddress]::Any) -or [Net.IPAddress]::IsLoopback($parsed)) {
        throw 'Expected explicit non-loopback IPv4 addresses'
    }
}
$publicKey = [IO.File]::ReadAllText((Resolve-Path -LiteralPath $PublicKeyPath)).Trim()
if ($publicKey -notmatch '^ssh-ed25519 [A-Za-z0-9+/]{68}={0,2}( [^\r\n]*)?$') {
    throw 'Expected one plain Ed25519 public key without authorized_keys options'
}
$hostKey = (Resolve-Path -LiteralPath $HostKeyPath).Path
$collector = Join-Path $PSScriptRoot '../src/gpt_pi/dashboard/ssh/collectors/windows.ps1'
if (!(Test-Path -LiteralPath $collector -PathType Leaf)) { throw 'Bundled collector is missing' }
if (!$Apply) {
    Write-Output 'Plan: install Windows OpenSSH Server; dedicated standard telemetry account; key-only forced collector; no shell/forwarding/SFTP; firewall restricted to the device.'
    return
}
$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (!$principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Administrator elevation is required' }
$account = 'gptpi-monitor'
$root = Join-Path $env:ProgramData 'GPT-Pi/telemetry-ssh'
$marker = Join-Path $root 'managed-by-gpt-pi.txt'
$existing = Get-Service sshd -ErrorAction SilentlyContinue
if (($existing -or (Get-LocalUser -Name $account -ErrorAction SilentlyContinue)) -and !(Test-Path -LiteralPath $marker)) {
    throw 'Existing SSH service/account is not owned by this installer; refusing to overwrite it'
}
function Set-ProtectedAcl([string]$Path, [bool]$Directory, [bool]$AccountRead) {
    $acl = if ($Directory) { New-Object Security.AccessControl.DirectorySecurity } else { New-Object Security.AccessControl.FileSecurity }
    $acl.SetAccessRuleProtection($true, $false)
    $admins = New-Object Security.Principal.SecurityIdentifier('S-1-5-32-544')
    $system = New-Object Security.Principal.SecurityIdentifier('S-1-5-18')
    $acl.SetOwner($admins)
    $inherit = if ($Directory) { [Security.AccessControl.InheritanceFlags]'ContainerInherit,ObjectInherit' } else { [Security.AccessControl.InheritanceFlags]::None }
    foreach ($sid in @($admins, $system)) {
        $acl.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule($sid, 'FullControl', $inherit, 'None', 'Allow')))
    }
    if ($AccountRead) {
        $sid = (Get-LocalUser -Name $account).SID
        $acl.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule($sid, 'ReadAndExecute', $inherit, 'None', 'Allow')))
    }
    Set-Acl -LiteralPath $Path -AclObject $acl
}
New-Item -ItemType Directory -Path $root -Force | Out-Null
Set-ProtectedAcl $root $true $false
if (!(Test-Path -LiteralPath $marker)) { [IO.File]::WriteAllText($marker, 'GPT-Pi telemetry SSH v1') }
try {
    if (!$existing) {
        Add-WindowsCapability -Online -Name 'OpenSSH.Server~~~~0.0.1.0' | Out-Null
        # The capability creates a broad default firewall rule; it is never used here.
        Get-NetFirewallRule -Name 'OpenSSH-Server-In-TCP' -ErrorAction SilentlyContinue | Disable-NetFirewallRule | Out-Null
    }
    Stop-Service sshd -ErrorAction SilentlyContinue
    if (!(Get-LocalUser -Name $account -ErrorAction SilentlyContinue)) {
        $randomPassword = ConvertTo-SecureString (([Guid]::NewGuid().ToString('N')) + ([Guid]::NewGuid().ToString('N')) + 'aA!9') -AsPlainText -Force
        New-LocalUser -Name $account -Password $randomPassword -PasswordNeverExpires -UserMayNotChangePassword -Description 'GPT-Pi fixed read-only telemetry over SSH' | Out-Null
        $randomPassword.Dispose()
        Add-LocalGroupMember -SID 'S-1-5-32-545' -Member $account
    }
    Set-ProtectedAcl $root $true $true
    $keyFile = Join-Path $root 'authorized_keys'
    [IO.File]::WriteAllText($keyFile, $publicKey + "`n", (New-Object Text.UTF8Encoding($false)))
    $installedCollector = Join-Path $root 'collect.ps1'
    Copy-Item -LiteralPath $collector -Destination $installedCollector -Force
    $installedHost = Join-Path $root 'host_ed25519'
    if (!(Test-Path -LiteralPath $installedHost)) { Copy-Item -LiteralPath $hostKey -Destination $installedHost }
    if ((Get-FileHash -LiteralPath $hostKey).Hash -ne (Get-FileHash -LiteralPath $installedHost).Hash) { throw 'Host key changed; explicit review required' }
    foreach ($path in @($installedCollector, $keyFile)) { Set-ProtectedAcl $path $false $true }
    Set-ProtectedAcl $installedHost $false $false
    $config = Join-Path $env:ProgramData 'ssh/sshd_config'
    if (!(Test-Path -LiteralPath (Split-Path $config))) { New-Item -ItemType Directory -Path (Split-Path $config) | Out-Null }
    if ((Test-Path -LiteralPath $config) -and !(Test-Path -LiteralPath (Join-Path $root 'sshd_config.before'))) {
        Copy-Item -LiteralPath $config -Destination (Join-Path $root 'sshd_config.before')
    }
    $hostPosix = $installedHost.Replace('\','/')
    $keysPosix = $keyFile.Replace('\','/')
    $collectorPosix = $installedCollector.Replace('\','/')
    $shell = "$env:WINDIR/System32/WindowsPowerShell/v1.0/powershell.exe".Replace('\','/')
    $content = @"
# Managed by GPT-Pi setup-windows-telemetry.ps1. No interactive shell is granted.
Port 22
AddressFamily inet
ListenAddress $ListenAddress
HostKey $hostPosix
PubkeyAuthentication yes
PasswordAuthentication no
AuthenticationMethods publickey
PermitEmptyPasswords no
AllowUsers $account@$DeviceAddress
AuthorizedKeysFile $keysPosix
AllowTcpForwarding no
AllowAgentForwarding no
PermitTTY no
PermitTunnel no
X11Forwarding no
MaxAuthTries 3
LoginGraceTime 20
ForceCommand $shell -NoLogo -NoProfile -NonInteractive -ExecutionPolicy RemoteSigned -File "$collectorPosix"
"@
    [IO.File]::WriteAllText($config, $content + "`n", (New-Object Text.UTF8Encoding($false)))
    Set-ProtectedAcl $config $false $false
    $sshd = Join-Path $env:WINDIR 'System32/OpenSSH/sshd.exe'
    & $sshd -t -f $config
    if ($LASTEXITCODE -ne 0) { throw 'sshd configuration validation failed' }
    $ruleName = 'GPT-Pi-Telemetry-SSH'
    Get-NetFirewallRule -Name $ruleName -ErrorAction SilentlyContinue | Remove-NetFirewallRule
    New-NetFirewallRule -Name $ruleName -DisplayName 'GPT-Pi telemetry from paired device' -Direction Inbound -Action Allow -Protocol TCP -LocalPort 22 -LocalAddress $ListenAddress -RemoteAddress $DeviceAddress -Profile Any | Out-Null
    Set-Service sshd -StartupType Automatic
    Start-Service sshd
    if ((Get-Service sshd).Status -ne 'Running') { throw 'SSH service did not start' }
    Write-Output 'Installed: key-only SSH, fixed telemetry command, dedicated standard account, device-only firewall.'
} catch {
    # Fail closed. Preserve the previous config and all user data for review/rollback.
    Stop-Service sshd -ErrorAction SilentlyContinue
    Get-NetFirewallRule -Name 'GPT-Pi-Telemetry-SSH' -ErrorAction SilentlyContinue | Disable-NetFirewallRule | Out-Null
    throw
}
