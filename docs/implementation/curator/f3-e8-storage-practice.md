# Public encryption, backup and restore practice — future supervised steps

Not executed on the curator's device in E8. No genuine evaluation key or case may
be used. Start with `public-report.json` only, in a new curator-owned directory.
Stop if any destination already exists; do not overwrite/delete evidence. Keep
checksums separately so a corrupted backup cannot replace its own expected hash.

Encryption at rest, restricted viewers and an independently controlled plaintext
workspace are different requirements. Do not use automatic cloud sync, shared
folders, clipboard sharing, remote support or developer/AI indexing. No current
guide proves OS isolation, full-volume encryption, secure deletion, power-loss
durability or protection from an OS administrator. No global security change is
authorized here. Genuine custody needs actual owner/witness review later.

## Windows — built-in user-bound public practice

DPAPI CurrentUser needs no extra service or new evaluation secret. It uses existing
Windows protection; this practice does not generate a commitment key. This sample
protects the report bytes, **not its filename, unencrypted original or whole disk**.
Public plaintext is intentional in practice. Future private plaintext must reside
only in the independently approved encrypted environment.

In the new public directory, after the earlier public runner and checksum:

```powershell
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Security
foreach ($p in @('public-report.dpapi', 'backup-report.dpapi', 'restored-report.json')) {
    if (Test-Path -LiteralPath $p) { throw 'Existing destination; stop' }
}
$plain = [System.IO.File]::ReadAllBytes((Join-Path $PWD 'public-report.json'))
$expected = (Get-FileHash -Algorithm SHA256 .\public-report.json).Hash
$encrypted = [System.Security.Cryptography.ProtectedData]::Protect($plain, $null, [System.Security.Cryptography.DataProtectionScope]::CurrentUser)
[System.IO.File]::WriteAllBytes((Join-Path $PWD 'public-report.dpapi'), $encrypted)
Copy-Item -LiteralPath .\public-report.dpapi -Destination .\backup-report.dpapi -ErrorAction Stop
if ((Get-FileHash .\public-report.dpapi -Algorithm SHA256).Hash -cne (Get-FileHash .\backup-report.dpapi -Algorithm SHA256).Hash) { throw 'Backup checksum mismatch' }
$restored = [System.Security.Cryptography.ProtectedData]::Unprotect([System.IO.File]::ReadAllBytes((Join-Path $PWD 'backup-report.dpapi')), $null, [System.Security.Cryptography.DataProtectionScope]::CurrentUser)
[System.IO.File]::WriteAllBytes((Join-Path $PWD 'restored-report.json'), $restored)
if ((Get-FileHash .\restored-report.json -Algorithm SHA256).Hash -cne $expected) { throw 'Restore checksum mismatch' }
'public_storage_practice_verified_same_windows_user_only'
```

This is a same-user restore test, not a disaster-recovery plan. A fresh computer,
lost Windows profile or unavailable DPAPI recovery material may prevent recovery.
A copied ciphertext without the required recovery context is not a portable backup.
Before genuine work choose and independently rehearse a recoverable encrypted
storage arrangement. Existing supported Device Encryption/BitLocker may help if
actually available/verified, but Windows Home is not assumed to support every
feature; no enablement, recovery-key access or administrator command is included.
Do not copy Windows secrets to make a test pass.

## macOS — public encrypted disk-image option

Only after separate setup approval, using existing Disk Utility: File → New Image
→ Blank Image; save a new `public-practice.dmg`,64MB, APFS, read/write image,
AES-256 encryption. Confirm the target is a **new image file**, never a physical
disk or existing volume. For public practice use an explicitly nonsecret dummy
passphrase entered interactively, not in shell history. Do not save it in a shared
keychain. If those options are unavailable, stop rather than reformat anything.

Mount and copy only the public report into the image. Record its plaintext SHA-256
with `shasum -a 256`. Eject normally; copy the closed image to a distinct approved
backup location, and compare both image SHA-256 values. Open the backup image,
extract to a fresh restore directory and compare the restored report checksum to
the original. A matching ciphertext alone is insufficient; verify successful
decryption too. Finder/OS encryption, access and recovery are not attested by E8.
No APFS image command was tested on this Windows development host.

## Linux — existing GnuPG public-only option

If GnuPG is already available and separately approved (`gpg --version`), use
password-based symmetric encryption, not private-key generation. Enter an explicitly
nonsecret dummy passphrase interactively for practice. Do not use a real evaluation
key or passphrase argument/environment variable. If GnuPG is absent, stop and seek
a setup decision; do not install it as an automatic test dependency.

```sh
# Confirm every output is absent before proceeding; never use --yes.
sha256sum public-report.json
gpg --no-symkey-cache --symmetric --cipher-algo AES256 --output public-report.json.gpg public-report.json
cp -n public-report.json.gpg backup-report.json.gpg
sha256sum public-report.json.gpg backup-report.json.gpg
gpg --no-symkey-cache --output restored-report.json --decrypt backup-report.json.gpg
sha256sum restored-report.json
```

Stop on any failed command, existing output, unexpected prompt or checksum mismatch.
Ciphertext copies must match; restored plaintext must match the original hash.
The passphrase and protected backup are both needed for future portable recovery.
This is not a tested Linux LUKS/full-disk setup or guarantee of memory erasure.

## Recovery, retention and sanitized reporting

The same-volume backup above exercises recovery mechanics only. Later genuine
custody requires one independently controlled, encrypted recovery copy in another
failure domain, named authorized viewers, recovery custodian, retention/deletion
policy and a witnessed dummy restore on the chosen arrangement. Do not transfer
genuine content/key to the developer or make them the sole recovery custodian.

After a future public rehearsal, report only OS category, public runner pass/stop,
encryption method, ciphertext match, decrypt/restore match, scope/limitations and
unresolved setup. Leave unperformed items null, not true. Never attach device
identifiers, recovery secrets, paths, screenshots or actual private material.
Do not edit the runner's JSON to fabricate these checks; keep a separately dated
human observation. No actual curator observation is filled out in this package.

Cleanup is manual after owner review and only of the known public-practice files.
No recursive cleanup command or secure-deletion claim is supplied. A compromised
genuine population needs incident/invalidation review, not deletion and recreation.
