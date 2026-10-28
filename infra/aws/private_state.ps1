# Local filesystem preparation only. This file never invokes AWS or Terraform.
# Target Windows PowerShell 5.1, whose Directory.CreateDirectory overload accepts
# a DACL at creation rather than exposing an inherited directory before locking it.
param([ValidateSet('Functions', 'Check')][string]$Mode = 'Functions', [string]$Path)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($PSVersionTable.PSVersion.Major -ne 5) { throw 'windows_powershell_5_1_required' }

function Assert-FataCachePath([string]$Path) {
    $root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
    $cache = [IO.Path]::GetFullPath((Join-Path $root '.cache'))
    $resolved = [IO.Path]::GetFullPath($Path)
    if (-not $resolved.StartsWith($cache + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'private_cache_path_required'
    }
    $node = $resolved
    while ($node -and $node.Length -ge $root.Length) {
        if (Test-Path -LiteralPath $node) {
            $item = Get-Item -LiteralPath $node -Force
            if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'private_link_rejected' }
        }
        $node = [IO.Path]::GetDirectoryName($node)
    }
    return $resolved
}

function Assert-FataPrivateAccess([string]$Path, [switch]$DirectoryRoot) {
    $target = Assert-FataCachePath $Path
    $sid = [Security.Principal.WindowsIdentity]::GetCurrent().User
    # Python 3.14 mkdir(0700) uses OWNER RIGHTS and local Administrators.
    # Neither ordinary Users, Authenticated Users nor Everyone is acceptable.
    $allowed = @($sid.Value, 'S-1-3-4', 'S-1-5-18', 'S-1-5-32-544')
    $acl = Get-Acl -LiteralPath $target
    if ($acl.GetOwner([Security.Principal.SecurityIdentifier]).Value -ne $sid.Value) { throw 'private_owner_required' }
    if ($DirectoryRoot -and -not $acl.AreAccessRulesProtected) { throw 'private_inheritance_not_blocked' }
    $rules = @($acl.GetAccessRules($true, $true, [Security.Principal.SecurityIdentifier]))
    if ($rules.Count -eq 0) { throw 'private_access_rules_missing' }
    $ownerFull = $false
    foreach ($rule in $rules) {
        if ($rule.AccessControlType -ne [Security.AccessControl.AccessControlType]::Allow -or
            $rule.IdentityReference.Value -notin $allowed) { throw 'private_access_too_broad' }
        if ($rule.IdentityReference.Value -in @($sid.Value, 'S-1-3-4') -and
            ($rule.FileSystemRights -band [Security.AccessControl.FileSystemRights]::FullControl) -eq [Security.AccessControl.FileSystemRights]::FullControl) { $ownerFull = $true }
    }
    if (-not $ownerFull) { throw 'private_owner_full_control_required' }
}

function New-FataPrivateDirectory([string]$Path) {
    $target = Assert-FataCachePath $Path
    if (-not (Test-Path -LiteralPath $target)) {
        $sid = [Security.Principal.WindowsIdentity]::GetCurrent().User
        $acl = New-Object Security.AccessControl.DirectorySecurity
        $acl.SetOwner($sid)
        $acl.SetAccessRuleProtection($true, $false)
        foreach ($principal in @($sid, (New-Object Security.Principal.SecurityIdentifier('S-1-5-18')))) {
            $rule = New-Object Security.AccessControl.FileSystemAccessRule($principal, 'FullControl', 'ContainerInherit,ObjectInherit', 'None', 'Allow')
            $acl.AddAccessRule($rule)
        }
        [void][IO.Directory]::CreateDirectory($target, $acl)
    }
    # Existing directories are verified, never silently re-ACL'd or overwritten.
    Assert-FataPrivateAccess $target -DirectoryRoot
    return $target
}

function Read-FataPrivateValue([string]$Prompt) {
    $secure = Read-Host $Prompt -AsSecureString
    $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try { return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer); $secure.Dispose() }
}

function Assert-FataPermissionWindow($Spec) {
    try {
        foreach ($field in @('permission_starts_at', 'permission_expires_at')) {
            if ($Spec[$field] -notmatch '^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$') { throw 'invalid' }
        }
        $start = [DateTimeOffset]::Parse($Spec.permission_starts_at, [Globalization.CultureInfo]::InvariantCulture)
        $end = [DateTimeOffset]::Parse($Spec.permission_expires_at, [Globalization.CultureInfo]::InvariantCulture)
    } catch { throw 'permission_window_invalid' }
    $now = [DateTimeOffset]::UtcNow
    if ($end -le $start -or ($end - $start).TotalHours -gt 2 -or $now -lt $start -or $now.AddMinutes(5) -gt $end) {
        throw 'permission_window_inactive_or_insufficient'
    }
    # A time precondition only: this function does not grant execution approval.
}

if ($Mode -eq 'Check') { Assert-FataPrivateAccess $Path }
