# Phase 20.47 — Final Stable Build + Setup

**Status:** COMPLETE — **PASS**
**Date:** 2026-09-22
**Version:** 1.2.7

The final stable Windows release built from the verified 20.46.A/B/C/D state:
source-stripped, PYZ-encrypted, Authenticode-signed, and packaged with a working
installer. No application UI or behavior was modified, and no encryption or signing
design was changed.

---

## 1. Build Result

**Toolchain (pinned, verified before build):**

| Component | Version | Verified |
|---|---|---|
| Python | 3.8.10 x64 (MSC v.1928, AMD64) | ✓ (`win7\venv\Scripts\python.exe`) |
| PyInstaller | 5.13.2 | ✓ |
| tinyaes | 1.1.2 (PYZ crypto backend) | ✓ importable |
| Inno Setup | 6 | ✓ (`C:\Program Files (x86)\Inno Setup 6\ISCC.exe`) |

**Build command:**
```
win7\venv\Scripts\python.exe -m PyInstaller --noconfirm --clean ^
    --distpath dist\Phase20-47-Final-Stable PrayerMusicGuard.spec
```

**Result:** exit 0 in **20 seconds**. `Building COLLECT COLLECT-00.toc completed successfully`.

> **Note on output location:** the initial `--distpath` created the tree at the project
> root (`E:\prayer-music-guard\Phase20-47-Final-Stable\`) instead of under `dist\`. The
> completed build was **relocated** with `Move-Item` (no rebuild, no recompile) to
> `dist\Phase20-47-Final-Stable\`, so the built bytes are exactly what PyInstaller
> produced. Pre-relocation EXE SHA-256 `2002F8B3…DB7DF87` matches the bundle now at the
> final path.

**Pre-build static gate:** the Phase 20.46.B spec validation
(`_validate_pyz.py`) passed **18/18** *before* building — encryption wired, datas clean,
key isolated.

### Bundle inventory

| Metric | Value |
|---|---|
| Bundle folder | `dist\Phase20-47-Final-Stable\PrayerMusicGuard\` |
| Total files | **1,022** |
| Total size | **31.0 MB** |
| DLLs / PYDs | 17 / 24 |
| Uncompressed EXE (before signing) | 4,264,687 B |
| Signed EXE | 4,270,360 B |

---

## 2. EXE Path, Hash, Signature

### Main executable

| Field | Value |
|---|---|
| **Path** | `dist\Phase20-47-Final-Stable\PrayerMusicGuard\PrayerMusicGuard.exe` |
| **Size** | 4,270,360 B (4.07 MB) |
| **SHA-256 (signed)** | **`E3B0D69D3073E1805BDD36AD1750B6823426F8FF6FF6F99EBA6B1095283E3DB9`** |
| SHA-256 (unsigned, as built) | `2002F8B3C6DAA380C0E198E9A94F12F53B7C7FE6F1106EFA3109EAD22DB7DF87` |
| Signer | **`CN=Ayman Alaa Abu Leila`** |
| Cert thumbprint | `E62474D0BE183AA95876BC5464B319D54B248E1F` |
| Signature algorithm | SHA-256 |
| Timestamp | RFC 3161, `SSL.com Timestamping Unit 2025 E1` |

`signtool verify /pa /v` resolves the primary signature, recomputes the SHA-256 file hash
(`EB697BB8…DCBB56E0`), and reports the full chain to the self-signed root. The only
verification error is the expected **untrusted root** condition inherent to a self-signed
certificate (see §9).

### Installer

| Field | Value |
|---|---|
| **Path** | `dist\Phase20-47-Final-Stable\PrayerMusicGuard-Setup.exe` |
| **Size** | 14,648,840 B (13.97 MB) |
| **SHA-256 (signed)** | **`FF589DCC0628D99BDE297E43492F5E185E3C8A0B41AD5854EDE1F21A7ED6C65F`** |
| SHA-256 (unsigned, as built) | `4EA3FA5819F4669F11D075E3579B02D845BF8068C841DD11E46D443C44BAFDB8` |
| Signer | **`CN=Ayman Alaa Abu Leila`** |
| Timestamp | RFC 3161, `SSL.com Timestamping Unit 2025 E1` |

### Signed binaries (12 total, in signing order)

Signing used `signtool sign /fd sha256 /sha1 <tp> /tr http://ts.ssl.com /td sha256`.
First-party load chain signed; Microsoft's own WebView2 runtime DLLs were deliberately
left Microsoft-signed (industry practice).

| # | Binary | Signer |
|---|---|---|
| 1 | `PrayerMusicGuard.exe` | Ayman Alaa Abu Leila |
| 2 | `python38.dll` | Ayman Alaa Abu Leila |
| 3 | `libcrypto-1_1.dll` | Ayman Alaa Abu Leila |
| 4 | `libssl-1_1.dll` | Ayman Alaa Abu Leila |
| 5 | `libffi-7.dll` | Ayman Alaa Abu Leila |
| 6 | `tcl86t.dll` | Ayman Alaa Abu Leila |
| 7 | `tk86t.dll` | Ayman Alaa Abu Leila |
| 8 | `VCRUNTIME140.dll` | Ayman Alaa Abu Leila |
| 9 | `pythonnet\runtime\Python.Runtime.dll` | Ayman Alaa Abu Leila |
| 10 | `clr_loader\ffi\dlls\amd64\ClrLoader.dll` | Ayman Alaa Abu Leila |
| 11 | `clr_loader\ffi\dlls\x86\ClrLoader.dll` | Ayman Alaa Abu Leila |
| 12 | `PrayerMusicGuard-Setup.exe` (installer, signed last) | Ayman Alaa Abu Leila |

All 12 confirmed via `Get-AuthenticodeSignature` (11 in-bundle + installer).---

## 3. Installer Result

Built from the **corrected** `PrayerMusicGuard.iss` (Phase 20.46.D paths), consuming the
**signed** bundle.

```
ISCC /Q PrayerMusicGuard.iss   ->  exit 0, 10 s
  OutputDir           = dist
  OutputBaseFilename  = PrayerMusicGuard-Setup
  Source              = dist\PrayerMusicGuard\*   (staged signed 20.47 bundle)
```

The signed bundle was staged to `dist\PrayerMusicGuard\` (the path the corrected `.iss`
expects) so the installer embeds the *signed* EXE and DLLs. The resulting Setup was then
signed and copied into the isolated release folder, so
`dist\Phase20-47-Final-Stable\PrayerMusicGuard-Setup.exe` is the authoritative installer.

The staging folder `dist\PrayerMusicGuard\` and the intermediate
`dist\PrayerMusicGuard-Setup.exe` were left in place as build byproducts; they are
byte-copies of the isolated release artifacts. No historical build or release was
overwritten — the only `dist\` additions this phase are `Phase20-47-Final-Stable\`,
`PrayerMusicGuard\`, and `PrayerMusicGuard-Setup.exe`.

---

## 4. Encryption Verification (Phase 20.46.B intact)

Harness: `reports\phases\phase20_47_evidence\_verify_pyz.py` (adapted from 20.46.B),
run with the pinned Win7 venv against the fresh build.

**Result: 26 / 26 checks PASS.**

- Embedded CArchive TOC contains `PYZ-00.pyz` (typecode `z`); CArchive TOC size 15.
- **Embedded PYZ encryption flag byte == 1** (header offset 12).
- Standalone workpath PYZ (`build\PrayerMusicGuard\PYZ-00.pyz`) has the same flag == 1.
- **Without the key:** extracting `backend_api` / `main` FAILS
  (`incorrect header check`).
- **With a wrong key:** extraction still FAILS (`invalid block type`).
- **With the real key:** all **7 application modules** extract and are provably the real
  modules by code-object names — `backend_api` (`BackendAPI`, `get_state`, `save_settings`),
  `main` (`acquire_single_instance`), `launcher` (`main`), `webview_main` (`run`),
  `platform_check` (`can_use_html_frontend`), `uiverse_combobox`
  (`CountryCitySelector`), `app_entry` (`main`).
- `tinyaes.cp38-win_amd64.pyd` bundled (runtime decryption backend).
- `pyimod00_crypto_key` present in the EXE's CArchive (bootloader requirement); **no
  readable crypto-key file shipped** in the bundle.

Evidence: `phase20_47_evidence\pyz_encryption_result.json`.

### Key protection

- `pyz_crypto_key.txt` present (43 B), still git-ignored, hash unchanged this phase
  (`83DA49E5…CE433B9C`), and **not** in `datas`/`hiddenimports` — never bundled.
- Key string absent from every application/UI/build source (validated by the 20.46.B
  harness, §4 check "key string absent from all app/UI/build sources").

---

## 5. Source-Removal Verification (Phase 20.46.A intact)

Scanned the entire fresh bundle for the eight files that must never ship as readable data
(`main.py`, `uiverse_combobox.py`, `backend_api.py`, `launcher.py`, `platform_check.py`,
`webview_main.py`, `app_entry.py`, `pyz_crypto_key.txt`):

**Violations: 0.**

The only `.py` files in the bundle are the 13 **pystray public-library** dependency files
(`pystray\_base.py`, `pystray\_win32.py`, `pystray\_util\win32.py`, …) — third-party
dependencies, not application source. Zero `.py` files exist outside `pystray\`. This
matches the documented 20.46.A scope (application modules only; pystray dependency `.py`
cleanup was scoped out in 20.46.B/D).

**Asset / frontend verification (all required runtime resources present):**

| Resource | Status |
|---|---|
| `assets\icons\prayer_music_guard.ico` | OK |
| `assets\data\cities.json` (45,751 B) | OK |
| `assets\data\countries.json` (14,166 B) | OK |
| `webview_app\splash.html` | OK |
| `webview_app\frontend\index.html` | OK |
| `webview_app\frontend\js\app.js` | OK |
| `webview_app\frontend\css\{theme,layout,components,skins}.css` | OK (4 files) |
| `webview\lib\Microsoft.Web.WebView2.Core.dll` | OK |
| `tinyaes.cp38-win_amd64.pyd` | OK |
| `python38.dll` | OK |

---

## 6. Runtime QA Results

Harness: `reports\phases\phase20_47_evidence\_runtime.js` — live CDP against the running
WebView2 frontend. Screenshots: `final_light.png`, `final_dark.png`.

**Standalone signed EXE: 25 / 25 PASS**, 0 CDP exceptions, 0 console errors.

| Area | Checks | Result |
|---|---|---|
| Clean startup / WebView2 frontend | 1a–1d (target reachable, title صلاة وسكون, `readyState=complete`, 553 chars rendered) | PASS |
| WebView2 bridge (PYZ decrypted) | 2a–2c (`window.pywebview` present, **16** api methods, all required present) | PASS |
| Prayer data | 3a–3e (`get_state()` ok in 4 ms, version 1.2.7, 5 prayers with real times, exactly one next flagged) | PASS |
| Prayer UI | 4a–4d (5 cards keyed Fajr..Isha, Arabic names + 12h times, next-prayer ring populated) | PASS |
| Save animation | 5a–5d (Arabic label حفظ الإعدادات, icon hidden at rest, `.is-saving` applied 64 ms after real click, removed after 967 ms) | PASS |
| Themes | 6a–6b (light and dark both applied) | PASS |
| RTL | 7a (`dir=rtl`, `lang=ar`) | PASS |
| Errors | 8a–8b (0 exceptions, 0 console.error) | PASS |

The signature did not disturb the bootloader, CArchive, PYZ decryption, WebView2 runtime,
or any application behavior.

---

## 7. Install / Uninstall QA

Installed per-user to `%LOCALAPPDATA%\PrayerMusicGuard-InstallTest` via
`/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /CURRENTUSER /DIR=...`.

> A first attempt at an unelevated silent install to `%ProgramFiles%` returned exit 2
> (that path requires UAC elevation, which is not interactively available in this
> environment, and a stale empty folder pre-existed there). Per-user install is the
> equivalent functional test and requires no elevation. The `.iss` already declares
> `PrivilegesRequiredOverridesAllowed=dialog`, so per-user is a supported mode.

### Install

| Check | Result |
|---|---|
| Installer exit code | **0** (3 s) |
| Files installed | **1,024** (1,022 bundle + `unins000.exe` + `unins000.dat`) |
| `PrayerMusicGuard.exe` installed | **OK** |
| Installed EXE SHA-256 | `E3B0D69D…3E3DB9` — **identical to the released signed EXE** |
| Installed EXE signer | **`CN=Ayman Alaa Abu Leila`** (signature survived packaging) |
| Source-removal in installed app | **0 violations** |
| Uninstall key written | **OK** — `HKCU\…\Uninstall\{B7C4A5D1-…}_is1`, DisplayName "صلاة وسكون" |

### Installed-app runtime QA

Ran the same CDP harness against the **installed** copy:
**25 / 25 PASS** (startup, bridge with 16 methods, prayer data, 5 cards, save animation
applied 67 ms / cleared 948 ms, both themes, RTL, zero errors).
Evidence: `runtime_result_installed.json`, `installed_light.png`, `installed_dark.png`.

### Launch from install

| Check | Result |
|---|---|
| Launched installed EXE | **OK** — running after 9 s |
| CDP page target | `http://127.0.0.1:26263/index.html` |
| Page title | صلاة وسكون (rendered correctly) |

### Uninstall

| Check | Result |
|---|---|
| `unins000.exe /VERYSILENT` exit code | **0** (1 s) |
| Install directory removed | **OK** (0 residual files) |
| Uninstall registry key removed | **OK** |
| Leftover uninstall entries anywhere (HKLM/HKLM-32/HKCU) | **none (clean)** |

---

## 8. Previous-Release Integrity

| Artifact | Verification | Result |
|---|---|---|
| `releases\` (all 15 files: v1.2.5, v1.2.6, v1.2.7) | Full SHA-256 manifest vs pre-phase baseline | **0 differences — ALL UNCHANGED** |
| `dist\Phase20-46B-Verification\…\PrayerMusicGuard.exe` | SHA-256 | `5984502F…70CF48F` — unchanged |
| `dist\Phase20-46C-SelfSigned\…\PrayerMusicGuard.exe` | SHA-256 + signature | `4BA1D9DB…BFC4C2`, still signed by Ayman Alaa Abu Leila — unchanged |
| `dist\Phase20-46A-Verification\…` | Signature status + mtime | Still `NotSigned`, mtime frozen 2026-09-22 11:23 — untouched |
| `dist\Phase20-28/36/38/42/44-*` | Folder mtimes | All frozen at their original dates — untouched |
| Signing certificate in `Cert:\CurrentUser\My` | Subject/EKU/validity | `CN=Ayman Alaa Abu Leila`, Code Signing, valid to 2028-09-22 — unchanged |

### Source/release files unchanged this phase

Backed up **before** any work to `backup\phase20_47_final_stable_20260922\`, then compared
after — **all identical**:

`PrayerMusicGuard.spec`, `release.ps1`, `PrayerMusicGuard.iss`, `build_exe.bat`,
`VERSION`, `.gitignore` — **unchanged=True** for all six.

No application source (`main.py`, `webview_app\*.py`), UI, frontend, encryption, or
signing design was modified. No historical build, release, report, or backup was deleted
or overwritten.

---

## 9. Important: Self-Signed Certificate Status

> The certificate signing this release is **SELF-SIGNED** and is **not publicly trusted**.
> It identifies the developer (**Ayman Alaa Abu Leila**) but is not chained to a public
> Certificate Authority. On machines that have not explicitly trusted it, Windows shows
> "Unknown publisher" / SmartScreen warnings and signature verification reports an
> untrusted root. This is expected and is the same status carried over from Phase 20.46.C.
> A public release still requires a CA-issued certificate.

---

## 10. Release Artifacts Summary

```
dist\Phase20-47-Final-Stable\
├── PrayerMusicGuard\                      1,022 files, 31.0 MB
│   ├── PrayerMusicGuard.exe               4,270,360 B  SHA256 E3B0D69D…3E3DB9  [SIGNED]
│   ├── python38.dll + 16 other DLL/PYD    first-party load chain [SIGNED where applicable]
│   ├── assets\                            icons + cities.json + countries.json
│   ├── webview_app\frontend\              index.html + app.js + 5 CSS
│   └── (no application .py, no key file)
└── PrayerMusicGuard-Setup.exe            14,648,840 B  SHA256 FF589DCC…6C65F  [SIGNED]
```

Evidence folder: `reports\phases\phase20_47_evidence\`
(`_runtime.js`, `_runtime_installed.js`, `_verify_pyz.py`,
`runtime_result.json`, `runtime_result_installed.json`, `pyz_encryption_result.json`,
`final_light.png`, `final_dark.png`, `installed_light.png`, `installed_dark.png`).

Backups: `backup\phase20_47_final_stable_20260922\` (spec, `.iss`, `build_exe.bat`,
`release.ps1`, `VERSION`, `.gitignore`).

---

## 11. FINAL STATUS

| Gate | Result |
|---|---|
| Build (pinned toolchain, isolated output) | **PASS** — exit 0, 20 s, 1,022 files |
| Source-removal (zero readable application `.py`) | **PASS** — 0 violations |
| PYZ encryption | **PASS** — 26/26 |
| Assets / frontend shipped | **PASS** — all required present |
| Signing (EXE + 10 payloads + installer) | **PASS** — all 12 signed by Ayman Alaa Abu Leila, timestamped |
| Runtime QA (standalone signed EXE) | **PASS** — 25/25, 0 errors |
| Installer build | **PASS** — exit 0, 10 s |
| Install QA | **PASS** — exit 0, 1,024 files, signature preserved |
| Installed-app runtime QA | **PASS** — 25/25, 0 errors |
| Uninstall QA | **PASS** — exit 0, clean removal, registry cleared |
| Previous releases / builds unchanged | **PASS** — 0 differences |
| Source / release scripts unchanged | **PASS** — all 6 identical to pre-phase backups |

# **FINAL: PASS**

No GitHub files, releases, or updater were created. Phase 20.48 not started.

**STOP — Phase 20.47 complete.**
