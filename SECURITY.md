# Security Policy

## Reporting a vulnerability

Please do not open public GitHub issues for security problems. Instead, open a
**private security advisory** (Security tab → "Report a vulnerability") or send
an email to the repository owner listed in the GitHub profile.

Include as much of the following as possible:

- a description of the issue and its impact,
- the affected version (see the `VERSION` file),
- minimal steps to reproduce,
- the Windows version you tested on.

Reports are acknowledged as soon as possible. Please do not publicly disclose a
suspected vulnerability before it has been investigated and fixed.

## Scope

This policy covers the released Windows application
(`PrayerMusicGuard.exe` / `PrayerMusicGuard-Setup.exe`) and the source in this
repository.

Out of scope: the pinned third-party build toolchain that lives under the
locally kept, non-committed `win7\` environment, and any pre-release or
test build that was never published.

## Build-time secrets

Two kinds of secret material are used when producing a release. **Neither is
ever present in this repository, in the build output, or in the published
application.**

| Secret | Purpose | Where it actually lives |
|---|---|---|
| `pyz_crypto_key.txt` | Encrypts the embedded Python bytecode (PYZ) of the frozen EXE | A local, git-ignored file, read by `PrayerMusicGuard.spec` **at build time only**. It is never listed in `datas`/`hiddenimports`, so it is never bundled into the EXE, and it is excluded from the repository by `.gitignore`. |
| Authenticode signing private key | Signs the EXE, DLLs, and installer | The Windows certificate store (`Cert:\CurrentUser\My`). It is **never exported** into the repository as a `.pfx`/`.pvk`/`.p12` file, and those extensions are blocked by `.gitignore`. |

If you fork this project and build it yourself, generate your own
`pyz_crypto_key.txt` (for example with `secrets.token_urlsafe(32)` written to
that path) and use your own code-signing certificate. A build made with a
different key produces an EXE whose bytecode cannot be read with any other key.

## Signed binaries

Published binaries are Authenticode-signed (SHA-256, RFC 3161 timestamped).
Verify the installer before installing it, for example with:

```powershell
Get-AuthenticodeSignature .\PrayerMusicGuard-Setup.exe | Format-List
Get-FileHash .\PrayerMusicGuard-Setup.exe -Algorithm SHA256
```

Each release folder carries a `SHA256SUMS.txt` with the expected hashes of its
artifacts. Compare the computed hash against that file and reject any binary
that does not match.

> Note: releases are currently signed with a **self-signed** certificate, so
> Windows may show "Unknown publisher" / SmartScreen prompts on machines that
> have not trusted it. Verify the SHA-256 hash against `SHA256SUMS.txt`; that is
> the authoritative integrity check.

## What the application does not do

- It does not collect, transmit, or sell personal data.
- It does not phone home, check for updates, or download anything at runtime.
- Prayer times are computed locally from the bundled `assets/data` datasets; the
  only network access is the optional, user-triggered fetch the user configures.
- Music-player handling suspends the chosen player process by window/media
  commands; it does not inject code into other applications.

## Hardening already in place

- Application Python modules are compiled into the encrypted PYZ archive and are
  **not** shipped as readable `.py` files in the released bundle.
- The PYZ archive is encrypted; without the local build key the embedded
  bytecode is not extractable.
- No source file, build file, or UI file contains the encryption key string.
- Per-user install (no administrator required), with a single-instance guard and
  a clean uninstall that removes its own registry entries.
