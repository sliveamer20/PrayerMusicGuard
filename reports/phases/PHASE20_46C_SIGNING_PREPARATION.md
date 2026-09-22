# Phase 20.46.C — Authenticode Code Signing Preparation (Audit Only)

**Scope:** READ / AUDIT / PREPARE ONLY. No EXE or DLL was signed. No certificate was
requested or purchased. No source, build, UI, updater, or release logic was modified.
No previous build or release was overwritten or deleted. No private key, password, or
certificate secret was exported or logged.

**Date of audit:** 2026-09-22
**Machine audited:** the Windows build host for this project (Windows 11 Pro x64).

---

## 1. Operating System and Architecture

| Item | Value |
|---|---|
| OS | Microsoft Windows 11 Pro |
| OS version | 10.0.26200 (Windows 11) |
| 64-bit OS | Yes |
| Process architecture | AMD64 (x64) |
| .NET Framework | present (system) |

> Note: the **build host** is Windows 11, but the **release target** is Windows 7 SP1
> x64 (see §7). Signing on Windows 11 for a Windows 7 target is fully supported; see
> §8 for the constraints that matter.

---

## 2. Signing Tools Found

| Tool | Available? | Path / Notes |
|---|---|---|
| **signtool.exe** | **YES** | `C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64\signtool.exe` (not on PATH) |
| signtool (x86) | Yes | `...\bin\10.0.26100.0\x86\signtool.exe` |
| signtool (arm64) | Yes | `...\bin\10.0.26100.0\arm64\signtool.exe` |
| signtool (App Certification Kit) | Yes | `C:\Program Files (x86)\Windows Kits\10\App Certification Kit\signtool.exe` |
| certutil.exe | Yes | `C:\WINDOWS\system32\certutil.exe` (cert store import/inspect) |
| certmgr.msc | Yes | `C:\WINDOWS\system32\certmgr.msc` (GUI) |
| PowerShell `Get-AuthenticodeSignature` | Yes | Built-in cmdlet — used for this audit |
| PowerShell `Set-AuthenticodeSignature` | Yes | Built-in cmdlet — available as an alternative to signtool |
| makecert / pvk2pfx | **NO** | Not found — deprecated SDK tools are not installed |
| osslsigncode | **NO** | Not found |
| Inno Setup compiler (ISCC) | Yes (not on PATH) | `C:\Program Files (x86)\Inno Setup 6\ISCC.exe` |

### signtool version and path (detail)

```
Path            : C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64\signtool.exe
Product version : 10.0.26100.8249
File version    : 4.00 (WinBuild.160101.0800)
```

`signtool sign /?` runs successfully. The tool supports the modern command set,
including `-fd` / `/fd` (digest algorithm), `-tr` / `/tr` (RFC 3161 timestamp),
`-td` / `/td` (timestamp digest), and certificate-store selection via `/sha1` or
`/f` + `/p` for PFX.

---

## 3. Windows SDK Installation

Windows Kits root: `C:\Program Files (x86)\Windows Kits\10\`

Installed SDK versions under `bin\`:

```
10.0.14393.0   (from Windows 10 Anniversary SDK era)
10.0.15063.0   (Windows 10 Creators Update SDK)
10.0.16299.0   (Windows 10 Fall Creators Update SDK)
10.0.17134.0   (Windows 10 April 2018 SDK)
10.0.26100.0   (Windows 11 24H2 SDK)   <-- latest, contains the signtool to use
```

Registry `KitsRoot10` = `C:\Program Files (x86)\Windows Kits\10\`

**Selected for signing:** the **x64** `signtool.exe` from **10.0.26100.0**
(product 10.0.26100.8249). It is the newest available and is the one this audit
recommends for the actual signing step.

---

## 4. Existing Authenticode Signatures on Current Builds

### 4a. EXE and installer signature state

Checked with `Get-AuthenticodeSignature` (PowerShell):

| File | Signature status | Signer |
|---|---|---|
| `dist\Phase20-46A-Verification\PrayerMusicGuard\PrayerMusicGuard.exe` | **NotSigned** | none |
| `dist\Phase20-46B-Verification\PrayerMusicGuard\PrayerMusicGuard.exe` (latest) | **NotSigned** | none |
| `releases\v1.2.6\PrayerMusicGuard.exe` | **NotSigned** | none |
| `releases\v1.2.6\PrayerMusicGuard-Setup.exe` | **NotSigned** | none |
| `releases\v1.2.7\PrayerMusicGuard.exe` | **NotSigned** | none |
| `releases\v1.2.7\PrayerMusicGuard-Setup.exe` | **NotSigned** | none |

Also checked earlier build folders (`dist\Phase20-28-Release`,
`Phase20-36/38/42/44-Visual-Review`) — same result: all `PrayerMusicGuard.exe`
instances are unsigned. The latest build is
* `dist\Phase20-46B-Verification\PrayerMusicGuard\PrayerMusicGuard.exe` (with PYZ
  encryption + no source bundle — the Phase 20.46.A/B verification build).

All report **`Status = NotSigned`**, with no signer certificate and no timestamp
counter-signature. Nothing in the current pipeline is signed. (This is expected: no
signing step exists in the build/release scripts — see §5.)

### 4b. DLL / PYD signature state

A spot check of the native binaries in the latest build directory
(`dist\Phase20-46B-Verification\PrayerMusicGuard\`) shows all DLL/PYD files are
**unsigned** (no embedded Authenticode signature), consistent with the unsigned EXE.

---

## 5. Current Build / Release Scripts — Signing Hooks

Audited: `PrayerMusicGuard.spec`, `release.ps1`, `build_exe.bat`,
`PrayerMusicGuard.iss`.

**Result: there are NO signing hooks anywhere in the project.**

* `PrayerMusicGuard.spec:107` — PyInstaller `EXE(..., codesign_identity=None, ...)`.
  Explicitly disabled (the default). PyInstaller will not sign the bootloader EXE.
* `release.ps1` — 200 lines. Steps: version read → preflight → EXE build (PyInstaller)
  → Inno Setup → archive to `releases\vX.Y.Z\` → SHA256SUMS → manifest.
  **Zero references** to `signtool`, `codesign`, `authenticode`, or `timestamp`.
* `build_exe.bat` — plain PyInstaller one-dir build. No signing step.
* `PrayerMusicGuard.iss` — Inno Setup script. **No `SignTool` directive** and no
  `signonce`/`sign` flag on `[Files]` entries, so the installer EXE is not signed and
  the payload is not signed at install time.

A repo-wide search for `signtool`, `codesign`, `authenticode`, `timestamp` across
`*.spec`, `*.iss`, `*.ps1`, `*.bat`, `*.py`, `*.md`, `*.json`, `*.txt` found only the
single `codesign_identity=None` line in the spec. **No signing hook exists to enable —
one must be added in Phase 20.46.D/E.**

---

## 6. Code Signing Certificate Availability

### 6a. Windows certificate stores

All stores were enumerated for both `CurrentUser` and `LocalMachine` across
`My`, `Root`, `CA`, `TrustedPublisher`, `AuthRoot`, `TrustedPeople`.

**Result: NO valid Authenticode code-signing certificate exists in any store.**

Full inventory of `CurrentUser\My` (the personal store, where a signing cert would
live) — 6 certificates, **none usable for code signing**:

| Subject | Issuer | Valid to | Private key | Code Signing EKU? |
|---|---|---|---|---|
| `CN=e8d28f0f-242d-4415-84e4-5e320cca6c61` | self | 2027-03-12 | Yes | **No** (no EKU) |
| `CN=Adobe Intermediate CA 10-15` | Adobe Root CA 10-3 | 2068-08-04 | No | **No** |
| `CN=Adobe Intermediate CA 10-19` | Adobe Root CA 10-3 | 2068-08-04 | No | **No** |
| `CN=Adobe Content Certificate 10-8` | Adobe Intermediate CA 10-19 | 2030-08-05 | No | **No** |
| `CN=Adobe Content Certificate 10-7` | Adobe Intermediate CA 10-15 | 2030-08-05 | No | **No** |
| `CN=0223d222-f93b-44b6-a000-3e1873ebe727` | self | 2026-09-06 | Yes | **No** (no EKU) |

* `LocalMachine\My` is **empty** (0 certificates).
* The two self-signed GUID-named certs have no EKU at all and no organization identity —
  they are machine/app-generated, not a purchased code-signing identity.
* The Adobe certificates are content/document certificates unrelated to this project,
  and none of them carries a private key.
* No certificate in any store carries the **Code Signing** OID
  (`1.3.6.1.5.5.7.3.3`) or the **Windows System Component Verification** /
  **Kernel-Mode Code Signing** OIDs.

### 6b. Certificate files on disk

Searched the project tree and the user profile (`Desktop`, `Documents`, `Downloads`,
`Pictures`, temp workspace) for `*.pfx`, `*.p12`, `*.pem`, `*.cer`:
**No Authenticode certificate file was found.** (Only unrelated Python `cacert.pem`
CA bundles from `pip`/`certifi`.)

### 6c. Findings

> **No code-signing certificate is available on this machine.**
> No signing identity has been invented or assumed. The two self-signed GUID
> certificates in `CurrentUser\My` are NOT a code-signing identity and MUST NOT be
> used as one.

**SHA-256 thumbprints of the certificates that ARE present** (public metadata only;
no private key was exported or exposed):

| Thumbprint (SHA-1 store key) | Identity |
|---|---|
| `E4D21F1ACE4D4933B4303B2552AD47DDD5F74209` | self-signed `CN=e8d28f0f-...` (not code signing) |
| `55749B90566BCBCF441C5B6D6986CFDE69CCE062` | self-signed `CN=0223d222-...` (not code signing) |

These are listed only to document that they were inspected and rejected; neither is a
basis for signing this product.

---

## 7. Build Toolchain (context for the signed release)

The release pipeline is pinned (enforced by `release.ps1` preflight) to:

| Component | Version | Path |
|---|---|---|
| Python | **3.8.10 x64** (MSC v.1928, 64-bit AMD64, WindowsPE) | `win7\venv\Scripts\python.exe` |
| PyInstaller | **5.13.2** | same venv |
| Build mode | one-dir (`COLLECT`) | `dist\<tag>\PrayerMusicGuard\` |
| Installer | Inno Setup 6 | `C:\Program Files (x86)\Inno Setup 6\ISCC.exe` |

Verified live during this audit: Python reports `3.8.10 ... 64 bit (AMD64)` and
PyInstaller reports `5.13.2`. The target platform for the release is **Windows 7 SP1
x64** (`requirements-win7.txt`; the v1.2.2 build was rejected for leaving this
toolchain — see `release.ps1` Phase 46 comment).

Current version: `1.2.7` (VERSION file and `PrayerMusicGuard.iss` `MyAppVersion`).
Existing archived releases: `v1.2.5`, `v1.2.6`, `v1.2.7` — all untouched by this audit.

---

## 8. Windows 7 Compatibility — Signing Considerations

These are the constraints the future signed release must satisfy. They are
requirements to plan against, not changes made in this phase.

1. **SHA-256 is the minimum, and SHA-1 must be avoided as primary.** Windows 7 SP1
   without updates cannot verify SHA-256 Authenticode signatures. Windows 7 SP1 with
   the 2019+ servicing updates *can*. Since Windows 7 is out of support, the only
   robust answer is **dual-signing** (`/fd sha1` + `/fd sha256` is not possible in one
   pass; use `signtool sign /fd sha256 /tr <TSA> /td sha256` and then a second
   `signtool sign /fd sha1` pass, in that order) OR ship SHA-256 only and require an
   updated Win7 SP1. **Recommendation: dual SHA-1 + SHA-256, SHA-256 last (outermost),
   so SmartScreen and modern Windows see SHA-256.**
   *Note:* a certificate valid for SHA-256 signing must be used for the SHA-256 pass.
2. **The timestamp must also be SHA-256** (`/td sha256`) if the signature digest is
   SHA-256, otherwise the signature can break chain validation after the certificate
   expires.
3. **No SHA-256-only dependency in the signature verification path.** For Windows 7
   without the SHA-2 updates, the SHA-1 pass is what makes the file usable.
4. **Do not sign with a certificate whose validity window is shorter than the intended
   release lifetime without a timestamp.** An untimestamped signature becomes invalid
   the day the certificate expires — this is what makes Windows show "Unknown
   Publisher" for old builds. **Always timestamp.**
5. **Windows 7 does not support the newer `signtool` Azure Key Vault / device
   signing** flows without additional runtime support; classic `/f <pfx>` or
   `/sha1 <thumbprint>` (certificate store) signing is the Win7-safe path.
6. **Installer signing matters as much as EXE signing on Windows 7.** Inno Setup's
   `SignTool` directive signs the generated `Setup.exe` outer binary. On Windows 7,
   UAC and IE/Edge "unknown publisher" warnings are triggered by the **installer**
   first, so it must be signed and timestamped too.
7. **The EXE is more trusted than its DLLs, but signing the DLLs is still required for
   a fully trusted deployment** (and for `SigCheck -e`-style verification). DLLs are
   not loaded any differently on Win7 if unsigned, but SmartScreen reputation and
   antivirus heuristics treat an unsigned DLL load chain as suspicious.
8. **PE architecture**: the build is x64 AMD64 (`platform.architecture()` =
   `64bit (WindowsPE)`), matching the x64 `signtool`. No WOW64 mismatch.
9. **The signed file must still be built with the same pinned toolchain**
   (Python 3.8.10 x64 + PyInstaller 5.13.2). Signing does not change the Win7
   runtime compatibility of the binary itself — that comes from the build.
10. **Version/manifest**: `PrayerMusicGuard.exe` has no embedded application manifest
    directives beyond the default. A future signed release may optionally add
    `requestedExecutionLevel` (this is a Phase 20.46.D/E decision, not made here).

---

## 9. Recommended Signing Order

For a one-dir PyInstaller bundle there is a strict order. **EXE first, then its
dependencies, then the installer last.**

### Step 1 — Main EXE (first)

```
signtool sign /fd sha256 /tr <TSA_URL> /td sha256 PrayerMusicGuard.exe
```

*Why first:* this is the primary executable that SmartScreen, UAC, and the user see.
Everything else is validated relative to it. Signing it first also means the EXE's
hash is fixed before the installer embeds it.

### Step 2 — DLL and PYD payloads (second, in dependency order)

The list below is the complete PE set in the current build
(`dist\Phase20-46B-Verification\PrayerMusicGuard\`), grouped by role. Files in
**bold** are the ones that matter most for trust and should be signed first within
this step.

| Priority | File (relative to `PrayerMusicGuard\`) | Role |
|---|---|---|
| **1** | **`python38.dll`** | Python runtime — loaded by everything |
| **2** | **`webview\lib\Microsoft.Web.WebView2.Core.dll`** | WebView2 runtime binding |
| 3 | `webview\lib\Microsoft.Web.WebView2.WinForms.dll` | WebView2 WinForms host |
| 4 | `webview\lib\WebBrowserInterop.x64.dll` | pywebview IE/Edge interop |
| 5 | `webview\lib\WebBrowserInterop.x86.dll` | pywebview interop (x86) |
| 6 | `webview\lib\runtimes\win-x64\native\WebView2Loader.dll` | WebView2 loader (x64) |
| 7 | `webview\lib\runtimes\win-x86\native\WebView2Loader.dll` | WebView2 loader (x86) |
| 8 | `webview\lib\runtimes\win-arm64\native\WebView2Loader.dll` | WebView2 loader (arm64) |
| 9 | `pythonnet\runtime\Python.Runtime.dll` | pythonnet / CLR bridge |
| 10 | `clr_loader\ffi\dlls\amd64\ClrLoader.dll` | CLR loader (amd64) |
| 11 | `clr_loader\ffi\dlls\x86\ClrLoader.dll` | CLR loader (x86) |
| 12 | `libcrypto-1_1.dll` | OpenSSL crypto |
| 13 | `libssl-1_1.dll` | OpenSSL TLS |
| 17 `.pyd` files | `_asyncio.pyd`, `_bz2.pyd`, `_ctypes.pyd`, `_decimal.pyd`, `_elementtree.pyd`, `_hashlib.pyd`, `_lzma.pyd`, `_multiprocessing.pyd`, `_overlapped.pyd`, `_queue.pyd`, `_socket.pyd`, `_ssl.pyd`, `_tkinter.pyd`, `pyexpat.pyd`, `select.pyd`, `unicodedata.pyd`, `winsound.pyd`, `_cffi_backend.cp38-win_amd64.pyd`, `tinyaes.cp38-win_amd64.pyd` | Python extension modules |

*Third-party Microsoft DLLs (`WebView2*.dll`, `WebBrowserInterop.*.dll`) are already
Microsoft-signed in the source package; re-signing them is optional and generally
**not** recommended — see §13.*

### Step 3 — Installer (last)

```
signtool sign /fd sha256 /tr <TSA_URL> /td sha256 dist\PrayerMusicGuard-Setup.exe
```

*Why last:* the Inno Setup `Setup.exe` embeds the payload at compile time. Signing it
**after** ISCC runs guarantees the signature covers the final bytes of the installer,
and its embedded copy of the EXE is already the signed copy.

> **Critical sequencing note:** `release.ps1` currently runs PyInstaller → ISCC →
> archive. The signing steps must be inserted **between** the PyInstaller output and
> the ISCC compile (for EXE/DLL) and **after** the ISCC compile (for the installer).
> Inserting signing before ISCC is what makes the installer embed the *signed* EXE.

---

## 10. Timestamping Capability

RFC 3161 timestamp servers were probed from this machine with a real
`application/timestamp-query` POST (not just a HEAD ping).

| Timestamp server | Reachable from this host | Latency | Notes |
|---|---|---|---|
| `http://ts.ssl.com` | **YES** | ~350 ms | Recommended primary (SSL.com) |
| `http://timestamp.globalsign.com/tsa/r6advanced1` | **YES** | ~395 ms | Recommended secondary (GlobalSign) |
| `http://rfc3161timestamp.globalsign.com/advanced` | **YES** | ~401 ms | Alternate GlobalSign TSA |
| `http://timestamp.digicert.com` | No | — | 400 Bad Request on probe |
| `http://timestamp.sectigo.com` | No | — | 404 on probe (Sectigo retired this legacy endpoint) |

> **Timestamping is fully available.** Three RFC 3161 TSA endpoints answered a valid
> timestamp query in under half a second each. No timestamp *configuration* exists yet
> in the project (there is no `/tr` anywhere), so the TSA URL must be chosen and
> recorded when Phase 20.46.D implements signing.

**Which TSA to use depends on the certificate vendor** — the correct choice in
Phase 20.46.D is **the TSA operated by the certificate's issuer** (Sectigo certs with
Sectigo's current TSA, DigiCert with DigiCert's, SSL.com with `ts.ssl.com`, GlobalSign
with GlobalSign). Using a mismatched vendor TSA is technically valid but can confuse
some verification tools. The three reachable TSAs above cover SSL.com and GlobalSign;
if the certificate comes from DigiCert or Sectigo, that vendor's current TSA endpoint
must be re-verified at signing time (both vendors operate working TSAs; the legacy
endpoints probed here are the ones that have been retired).

---

## 11. Files That Would Eventually Need Signing

Complete inventory for a release, in signing order. Paths are relative to the
build output directory.

**A. Main executable (1 file)**
1. `PrayerMusicGuard.exe`

**B. Native payloads (41 PE files)**
2. `python38.dll`
3. `libcrypto-1_1.dll`
4. `libssl-1_1.dll`
5. `libffi-7.dll`
6. `tcl86t.dll`
7. `tk86t.dll`
8. `VCRUNTIME140.dll`
9. `webview\lib\Microsoft.Web.WebView2.Core.dll`
10. `webview\lib\Microsoft.Web.WebView2.WinForms.dll`
11. `webview\lib\WebBrowserInterop.x64.dll`
12. `webview\lib\WebBrowserInterop.x86.dll`
13. `webview\lib\runtimes\win-x64\native\WebView2Loader.dll`
14. `webview\lib\runtimes\win-x86\native\WebView2Loader.dll`
15. `webview\lib\runtimes\win-arm64\native\WebView2Loader.dll`
16. `pythonnet\runtime\Python.Runtime.dll`
17. `clr_loader\ffi\dlls\amd64\ClrLoader.dll`
18. `clr_loader\ffi\dlls\x86\ClrLoader.dll`
19–37. 19 `.pyd` extension modules (listed in §9 Step 2)

**C. Installer (1 file)**
38. `dist\PrayerMusicGuard-Setup.exe` (Inno Setup output)

**D. Not PE — do not sign:** `base_library.zip`, `webview\js\*.js`,
`webview\lib\pywebview-android.jar`, `assets\*`, `webview_app\frontend\*`,
`*.dist-info\*`. These are not PE images and cannot carry an embedded Authenticode
signature.

**Totals for the future signed release:** **1 EXE + 41 native payloads + 1 installer
= 43 files** (1 EXE + 17 DLL + 24 PYD + 1 Setup).

---

## 12. Exact Prerequisites for Actual Signing (Checklist)

Ordered. Nothing below has been done; this is what Phase 20.46.D requires.

1. **Obtain a Code Signing certificate** — OV (Organization Validation) or EV
   (Extended Validation) from a CA whose root is in the Windows 7 trusted root store.
   The certificate MUST have the **Code Signing EKU (`1.3.6.1.5.5.7.3.3`)**.
   *This is the single hard blocker — see §13.*
2. **Decide private-key custody.** Either:
   - install the certificate + private key into `CurrentUser\My` (then sign with
     `/sha1 <thumbprint>`), or
   - keep a `.pfx`/`.p12` on removable/encrypted media and sign with
     `/f cert.pfx /p <password>`.
   Never store the PFX password in the repo, in `release.ps1`, or in any build log.
3. **Install the full CA chain** (root + any intermediates) into
   `LocalMachine\CA` / `LocalMachine\Root` so signtool can build the chain at signing
   time. Missing intermediates are the #1 cause of "signature cannot be verified"
   after a signed release ships.
4. **Confirm the certificate's algorithm support.** If the cert is SHA-256 capable
   (any modern cert is), plan the SHA-256 pass; if dual-signing for legacy Win7, also
   confirm the SHA-1 pass is permitted by the CA's policy.
5. **Pick the TSA** — the certificate issuer's RFC 3161 endpoint. §10 lists the three
   endpoints already verified reachable from this host.
6. **Add a signing step to the release pipeline**, inserted between the PyInstaller
   build and the Inno Setup compile (EXE + DLLs/PYDs), and after ISCC (installer).
   `release.ps1` currently has **no** hook for this.
7. **Add `SignTool` to `PrayerMusicGuard.iss`** so the installer itself is signed
   (`SignTool` directive + a `signtool` configured via ISCC's
   `SetupSigning.SignTool`/`signtool` setting). Currently absent.
8. **Set `codesign_identity` in `PrayerMusicGuard.spec`** (currently `None` at line
   107) **only if** you want PyInstaller to sign the bootloader EXE itself. This is
   optional — the outer EXE can be signed after the build with plain `signtool`.
9. **Verify after signing** with `Get-AuthenticodeSignature` (PowerShell) and
   `signtool verify /v /all` — checking `Status = Valid`, the signer subject matches
   the intended identity, and `TimeNotarizedOperator`/timestamp is present.
10. **Test on a real Windows 7 SP1 x64 machine** (or a VM) — both the signed EXE and
    the signed installer — to confirm the signature validates there, not just on this
    Windows 11 host.
11. **Record the signing identity in the release manifest** (`RELEASE_MANIFEST.txt`)
    so future releases are attributable. Subject + thumbprint + TSA used. Not a secret.
12. **Keep SmartScreen reputation in mind.** A newly purchased cert has no reputation.
    EV certificates build reputation immediately; OV certificates build it over
    download volume. This is informational for release planning, not a blocker.

---

## 13. Status

**Status: BLOCKED** (on certificate) / **READY** (on tooling)

The tooling side is fully ready. The single blocker is that **no code-signing
certificate exists on this machine or in the project**, and none may be invented.

| Item | State |
|---|---|
| `signtool.exe` present and working | **READY** — 10.0.26100.8249, x64, at `C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64\signtool.exe` |
| Windows SDK installed | **READY** — 5 SDK versions, latest 10.0.26100.0 |
| Inno Setup compiler | **READY** — `C:\Program Files (x86)\Inno Setup 6\ISCC.exe` (not on PATH; `release.ps1` already resolves it) |
| Build toolchain pinned for Win7 | **READY** — Python 3.8.10 x64 + PyInstaller 5.13.2, enforced by `release.ps1` preflight |
| RFC 3161 timestamping | **READY** — 3 TSA endpoints verified reachable (~350–400 ms) |
| Candidate files identified | **READY** — 43 files (1 EXE + 41 native payloads + 1 installer) |
| Signing hook in build/release scripts | **MISSING** — must be added in Phase 20.46.D (currently zero signing logic) |
| Code-signing certificate | **BLOCKED** — none present, none in any store, no PFX on disk |
| Code Signing EKU on any cert | **BLOCKED** — no certificate has `1.3.6.1.5.5.7.3.3` |

**Bottom line:** signing can proceed technically the moment a valid Code Signing
certificate is in hand — every tool, path, and timestamp endpoint required is already
present and verified. Until that certificate exists, actual signing is **BLOCKED**.

---

## 14. Security Notes (this audit)

* No private key, PFX password, or certificate secret was exported, displayed, or
  logged. Only public certificate metadata (subject, issuer, validity, thumbprint,
  EKU) was read.
* `pyz_crypto_key.txt` (the Phase 20.46B PYZ encryption key) was not opened or read.
* No EXE, DLL, PYD, or installer was signed, modified, or deleted.
* No source file, spec, build script, or installer script was modified.
* No previous build in `dist\` or release in `releases\` was touched.

---

## 15. Audit Trail — Commands Executed

All commands were read-only: `Get-AuthenticodeSignature`, `Get-ChildItem` on
`Cert:\` and disk, `Get-Item ... .VersionInfo`, `signtool sign /?` (help text only,
**never** a `sign` operation), `Invoke-WebRequest` to TSA endpoints, and file reads.
No file was written by any command. No file was modified.
