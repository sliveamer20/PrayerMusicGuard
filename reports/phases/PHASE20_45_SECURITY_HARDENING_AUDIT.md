# PHASE 20.45 — SECURITY + RELEASE HARDENING AUDIT

**Project:** `E:\prayer-music-guard`
**Date:** 2026-09-22
**Phase:** 20.45 — READ-ONLY security audit preparing Prayer Music Guard for safe public distribution and better source-code protection.
**Mode:** **Audit only.** No files modified, no build performed, no packages installed. No attempt to bypass Defender/antivirus, no weakening of Windows security, no packers or aggressive obfuscation, no architecture changes, no UI changes, no existing builds/releases touched.

Audited scope: `PrayerMusicGuard.spec`, `build_exe.bat`, `release.ps1`, `PrayerMusicGuard.iss`, `main.py`, `uiverse_combobox.py`, `webview_app\{backend_api, webview_main, platform_check, launcher, app_entry}.py`, `webview_app\frontend\*`, and the frozen OneDir bundle `dist\Phase20-44-Visual-Review\PrayerMusicGuard` (1,028 files).

---

## 0. Executive Summary

| Area | Verdict |
|---|---|
| Malicious / unsafe behavior | **NONE** — no injection, no memory access, no download-and-execute, no shell injection |
| Secrets / credentials | **NONE** in shipped application code |
| Network | **SAFE** — HTTPS-only, cert verification on, minimal data sent |
| Process / media control | **SAFE** — media commands only, lowest-privilege handles |
| Autostart | **SAFE** — per-user HKCU, no admin, idempotent |
| **Source-code protection** | **CRITICAL — all application source ships as readable plain text** |
| **Code signing** | **HIGH — nothing is signed (EXE nor installer)** |
| Build hygiene | **MEDIUM — path leakage, stale build references, stray files** |

The application logic itself is conservatively and safely written. The dominant risk for public distribution is **IP protection and trust signaling**, not malicious behavior: the entire backend ships as readable `.py`, and no Authenticode signature exists anywhere, which is the single biggest driver of SmartScreen/AV friction for a new, unknown publisher.

---

## 1. Windows Defender / Antivirus False-Positive Risk

### Findings

| # | Severity | File / module | Exact reason | Recommended safe fix | Compatibility risk |
|---|---|---|---|---|---|
| 1.1 | **HIGH** | Entire EXE (unresolved) | Unsigned binary from an unknown publisher. SmartScreen shows the generic "unrecognized app" warning; AV heuristics score unsigned+unrecognized executables higher. This is the **largest practical friction** for public distribution. | Obtain an OV/EV code-signing certificate and sign both the EXE (`PrayerMusicGuard.spec` `codesign_identity` / `signtool`) and the Inno installer (`.iss` `SignTool` directive). See §14. | None — signing is additive. Win7 SP1 needs SHA-1 or SHA-1+SHA-256 dual-signing; Win10/11 prefer SHA-256. |
| 1.2 | MEDIUM | `main.py:282-283` `keybd_event(VK_MEDIA_PLAY_PAUSE)` | Simulating global media keys is a classic "keylogger-like" API pattern. Benign here (single well-known key, no input capture), but combined with `EnumWindows` + `OpenProcess` it forms a heuristically suspicious signature set. | No behavioral change needed. **Signing (1.1) and a clear publisher identity** is the correct mitigation — it flips heuristics from "unknown" to "verified publisher". Optionally add a `getmedia`/`setautoplay` EV evidence statement to submission forms. | None. |
| 1.3 | MEDIUM | `main.py:604-607`, `backend_api.py:716-794` | Spawns `powershell.exe` child processes (`Get-Process`, `Get-CimInstance Win32_Process`, `tasklist`). Parent→`powershell.exe` spawning with encoded-looking command lines is a top AMSI/Defender heuristic (common in info-stealers). | All six invocations already use **fixed literal commands, `shell=False`, no user input** — no injection risk. To reduce heuristic noise, prefer the pure-`ctypes`/`winreg` enumeration already partially present (`main.py:618-654` reads Uninstall hives via `winreg`) and consider a `psapi`/`EnumProcesses` path via `ctypes` to replace the `Get-Process` PowerShell call. Keep `tasklist` as a last resort. | Low — `EnumProcesses` works on Win7 SP1→Win11. Careful testing on Win7 (`psapi` vs `kernel32` enumeration). |
| 1.4 | MEDIUM | `webview_main.py:90` | **Hardcoded absolute path** `C:\Program Files (x86)\Microsoft\EdgeWebView\Application\153.0.4234.32` pinned to one exact WebView2 build. A version pin that does not exist on a user's machine degrades to registry detection (already implemented as fallback at `webview_main.py:96-119`), but a stale pin can later silently point at an old/removed runtime. | Remove the literal pin and rely on the existing registry-based detection (it resolves the installed `pv` correctly). Keep the literal only as a comment-documented last resort. | None — registry detection already exists and is used in Phase 20.44 (`Edge/153.0.4234.48` resolved at runtime). |
| 1.5 | LOW | `PrayerMusicGuard.exe` manifest (`requestedExecutionLevel asInvoker`) | Correctly least-privilege (no `requireAdministrator`), so it does not trigger UAC-prompts-that-look-suspicious. **Correct as-is.** | None. | — |
| 1.6 | INFO | No UPX / no packer | `upx=False` in spec (lines 82, 97) and `release.ps1` invokes no packer. **Correct as-is** — UPX-compressed unsigned EXEs are a well-known false-positive magnet. | Keep UPX disabled. | — |

### Already correct
- Least-privilege `asInvoker` manifest.
- No packers/UPX (a real false-positive source).
- All child processes launched with `CREATE_NO_WINDOW` (`0x08000000`) — no flashing console windows.
- No `shell=True`, no `cmd.exe`, no `os.system`, no `os.popen` anywhere.

---

## 2. PyInstaller Packaging / Security Risks

| # | Severity | File / module | Exact reason | Recommended safe fix | Compatibility risk |
|---|---|---|---|---|---|
| 2.1 | **CRITICAL** | `PrayerMusicGuard.spec:16-22` | All five application modules are declared as **`datas`** and therefore copied into the OneDir bundle as **readable plain-text source**: `main.py` (181,764 B), `uiverse_combobox.py` (33,753 B), `webview_app\{backend_api, launcher, platform_check, webview_main}.py`. Confirmed byte-identical readable UTF-8 in `dist\Phase20-44-Visual-Review\PrayerMusicGuard\`. Full backend logic — prayer scheduling, media control, process/window enumeration, registry handling — is trivially extractable by any user or competitor. The same modules are *also* compiled into `PYZ-00.pyz` via `hiddenimports` (lines 33-39), so the plain-text copies are **pure redundancy**. | Stop shipping the `.py` files as `datas`. They are already compiled into PYZ through `hiddenimports`. The one true blocker is `backend_api.py:34-69` (`_main_py` + `_load_main`), which deliberately locates `main.py` **on disk** and `exec_module`s it — this is *why* the source ships. Refactor `_load_main` to `import pmg_main` (or `from main import ...`) so the frozen build uses the compiled PYZ copy and the `datas` entries can be deleted. Then optionally raise the bar further (§13). | Low-medium. Requires confirming no runtime `open()`/edit of `main.py` and that the `importlib` path was only an artifact of the source/frozen dual layout. Must re-test both source-run and frozen-run paths on Win7 SP1 and Win11. |
| 2.2 | **HIGH** | `PrayerMusicGuard.spec:53, 68, 71` | `block_cipher = None`, `cipher = None` on both `Analysis(...)` and `PYZ(...)`. The PYZ archive (which contains all application bytecode) is stored **unencrypted**. | Set a `block_cipher = PyiCipher...` (PyInstaller 5.x `pyz_crypto.PyiBlockCipher`) so PYZ is encrypted at rest. **Caveat:** this is **weak** protection — the key is embedded in the bootloader and recoverable; treat it as a speed bump, not a control. It is *only meaningful after 2.1 is fixed*, otherwise the plain-text `datas` copy defeats it entirely. PyInstaller 6.x removed this feature, so if you ever upgrade it must be replaced. | Low for 5.13.2 (supported). Not forward-compatible with PyInstaller ≥ 6. |
| 2.3 | MEDIUM | `dist\...\pystray\__pycache__\*.pyc` (5 files) | Bytecode caches from a dependency ship loose in the bundle. Not sensitive (public library) but contributes a "why is there bytecode" surface and inconsistent hygiene. | Add `--exclude-module pystray.__pycache__` handling or purge `*.pyc` from the COLLECT via a post-build step in `release.ps1`. | None. |
| 2.4 | MEDIUM | `dist\...\base_library.zip` (163 stdlib `.pyc`) | Standard PyInstaller stdlib container. Normal, not sensitive. **Correct as-is** — listed for completeness. | None. | — |
| 2.5 | MEDIUM | `dist\...\webview_app\frontend\js\app.js.bak` | A stale editor **backup of the frontend is shipped** in the release bundle. It is an old copy of `app.js` (15,299 B) and can confuse reviewers or diff tools ("which one runs?"). | Delete `app.js.bak` from the source tree (and all `*.bak`: `backend_api.py.bak`, `webview_main.py.bak` also exist in source) and add `*.bak` to `.gitignore` + a build-time exclusion. | None. |
| 2.6 | MEDIUM | `build\PrayerMusicGuard\*.toc`, `xref-PrayerMusicGuard.html`, `warn-*.txt` | ~4,500 absolute build-path references leak the full developer layout: `E:\prayer-music-guard\main.py`, `win7\venv\lib\site-packages\...`, PyInstaller hook paths, every asset path. These stay in `build\` (not shipped in `dist\`), but if `build\` is ever zipped, shipped, or committed, they reveal the toolchain and folder structure. | `--clean` already discards prior state; keep `build\` out of any distribution archive and out of source control (it is currently not under `releases\`). Optionally set PyInstaller `workpath` to a temp dir in `release.ps1`. | None. |
| 2.7 | LOW | `release.ps1` / `PrayerMusicGuard.iss:36` | The installer sources files from `dist\Phase18-OneDir-Test\PrayerMusicGuard\*` — a **stale folder name** that no longer matches the current build output (`Phase20-44-Visual-Review` / spec default). If run as-is it would fail or package the wrong build. | Parameterize `Source` in the `.iss` to the current `--distpath` (or emit the ISS dynamically in `release.ps1`). | None. |
| 2.8 | INFO | `strip=False`, `noarchive=False` | Defaults are fine and avoid debug-symbol stripping pitfalls. **Correct as-is** for this stack. | None. | — |

---

## 3. Startup / Autostart Implementation

**Verdict: correctly implemented, least-privilege, safe.**

| Aspect | Detail | Status |
|---|---|---|
| Mechanism | HKCU `Software\Microsoft\Windows\CurrentVersion\Run`, value `PrayerMusicGuard` (`main.py:92-93`) | ✅ Standard, per-user |
| Privilege | `KEY_SET_VALUE` on `HKEY_CURRENT_USER` only — **no admin required** (`main.py:120-139`) | ✅ Least privilege |
| Scope | No HKLM, no Task Scheduler, no Startup-folder writes | ✅ No elevation surface |
| Idempotency | Enable = `SetValueEx`; disable = `DeleteValue`; single named value | ✅ Clean toggle |
| Self-heal | Startup re-registers if settings.json says enabled but the value is missing (`main.py:1367-1377`) | ✅ Resilient |
| Value content | Frozen: `sys.executable`; source: quoted `"py" "main.py"` (`main.py:97-104`) | ✅ No injection |
| Bridge | `backend_api.py:610-621` gates through `_MAIN.set_autostart` then persists | ✅ Consistent |

No issue found. The registry value is written under the user's own hive, which is exactly how legitimate autostart apps behave and is not an AV red flag on its own.

---

## 4. subprocess / PowerShell / cmd Usage

**Verdict: safe — no injection, but heuristic noise (see 1.3).**

Six invocations exist. **All** use `shell=False`, fixed literal commands, `CREATE_NO_WINDOW`, and **zero user input** flows into any command:

| Location | Command | Purpose | Risk |
|---|---|---|---|
| `main.py:604-607` | `powershell Get-Process` | Process name+PID listing | Heuristic only (1.3) |
| `main.py:659-663` | `powershell` + `WScript.Shell` + `Get-ChildItem *.lnk` | Start Menu shortcut enumeration | Heuristic only |
| `backend_api.py:716-733` | `powershell Get-CimInstance Win32_Process` | Running-app enumeration | Heuristic only |
| `backend_api.py:753-770` | `powershell Get-WmiObject Win32_Process` | Same, older-Windows fallback | Heuristic only |
| `backend_api.py:787-794` | `tasklist /FO CSV /NH` | Last-resort name-only fallback | Minimal |
| `platform_check.py:136-141` | `[sys.executable, "--webview-child", "--probe"]` | WebView2 health probe child | None |

**Critical safety property:** the user-chosen player executable path (the only user-controlled value in this subsystem) is **never** interpolated into a shell command — it is compared in pure Python by exe stem (`main.py:219, 225, 677, 686`; `backend_api.py:703-707`). There is **no command-injection surface**.

### Already correct
- No `shell=True`, no `os.system`, no `os.popen`, no string-formatted `cmd.exe`.
- `installed_apps()` reads Uninstall hives via `winreg` directly rather than shelling out (`main.py:618-654`).

---

## 5. Temporary Files and Runtime File Operations

**Verdict: safe locations and atomic writes; one log-injection consideration.**

| Path | Writer | Contents | Assessment |
|---|---|---|---|
| `%APPDATA%\PrayerMusicGuard\prayer-music-guard.log` (+5×1 MB rotated) | `main.py:27-37` | Player exe **paths**, PIDs, window handles, pause/resume outcomes, city/country | User-only ACL (Roaming profile) ✅. Contains user-specific paths — normal for a local utility. |
| `%APPDATA%\PrayerMusicGuard\settings.json` | `main.py:593-599` | Config incl. `manual_city/country/latitude/longitude` | **Written atomically** (`.tmp` → `Path.replace()`) ✅ |
| `%APPDATA%\PrayerMusicGuard\backend_api.log` | `backend_api.py:48-57` | Bridge events, version, load errors | ✅ |
| `%APPDATA%\PrayerMusicGuard\bridge_diag.log` | `backend_api.py:848-867` | **Arbitrary frontend-supplied JSON appended verbatim** | See 5.1 |
| `%APPDATA%\PrayerMusicGuard\webview2_data\` | `webview_main.py:82-84` | WebView2 profile/storage | ✅ Standard |
| `<tempdir>\pmg_probe.log` | `platform_check.py:132-135` | Probe stdout/stderr, overwritten each run | ✅ Transient |

| # | Severity | File / module | Exact reason | Recommended safe fix | Compatibility risk |
|---|---|---|---|---|---|
| 5.1 | LOW | `backend_api.py:848-867` (`diag_report`) | The frontend can push an **arbitrary** payload that is serialized and appended to `bridge_diag.log` with no size cap or schema check (observed 278 KB). A malicious/compromised webview could bloat or forge diagnostic entries (log forging). The method is only reachable from the local trusted frontend, so impact is low. | Cap payload size (e.g. first 4 KB), `json.dumps` with a fixed key whitelist, and truncate the file on rotation like the main log. | None. |
| 5.2 | LOW | `main.py:45-49` (`LOCAL_DIR` fallback) | If `%APPDATA%\PrayerMusicGuard` cannot be created, settings fall back to `Path(__file__).resolve().parent` — in a **source** run that is the project dir; in a **frozen** OneDir run it would be the (potentially non-writable) bundle dir. Reaching this path is already rare and the code documents it as a last resort. | For frozen builds prefer `%LOCALAPPDATA%` over the bundle dir, since writing next to a signed EXE can also invalidate signatures in some configurations. | Low; source-run behavior unchanged. |

### Already correct
- **No `os.chmod`/`0o777`** anywhere; no world-writable files.
- No writes to `Program Files` or the executable directory in normal operation.
- Atomic settings persistence with `Path.replace()`.
- All log/state under the per-user `%APPDATA%` (default user-only ACL).

---

## 6. Network / Download Behavior

**Verdict: safe and minimal — HTTPS-only, verified certificates, no remote code.**

| Endpoint | Method | Data sent | TLS | Code |
|---|---|---|---|---|
| `https://ipapi.co/json/` | GET | None (User-Agent only) | ✅ default-verified | `main.py:728-729` |
| `https://api.aladhan.com/v1/timings/…` | GET | `method`, `timezone`, `city+country` or `lat+lon` | ✅ default-verified | `main.py:2963`, `backend_api.py:1038-1040` |
| `https://api.aladhan.com/v1/timingsByCity/…` | GET | same | ✅ default-verified | `main.py:2987`, `backend_api.py:1025` |

- **No `verify=False`**, no custom `ssl` context, no `certifi` override — the stdlib `ssl.create_default_context()` applies, so certificates are validated.
- **No download-and-execute.** No code is fetched from the network and executed.
- The only dynamic code loading is **local**: `backend_api.py:60-69` loads `main.py` from the local bundle (see 2.1 — this is the source-shipping root cause).
- The webview loads a **local** `index.html` served by pywebview's loopback HTTP server (`http://127.0.0.1:<port>/index.html`, bound to `127.0.0.1` only — confirmed). **No remote URLs** are loaded into the WebView2 surface.
- The resolved IP from geolocation is deliberately not stored; only city/country are kept (`main.py:723-726`, `735-739`).
- No raw `socket` usage.

| # | Severity | File / module | Exact reason | Recommended safe fix | Compatibility risk |
|---|---|---|---|---|---|
| 6.1 | LOW | Loopback HTTP server (pywebview) | The frontend is served over **plain `http://`** on a random `127.0.0.1` port. Loopback-only binding makes remote attack impractical, but any **local** process can fetch the page and invoke the `window.pywebview` bridge (16 methods incl. `save_settings`, `pause_now`, `browse_player`). This is inherent to pywebview's architecture, not a project bug. | No change to the architecture (explicitly out of scope). If ever desired, pywebview's `private_mode`/frameless options and a shared-token check would be the levers; document the loopback trust boundary instead. | Changing this alters the stable architecture — do not. |

---

## 7. Embedded Secrets, API Keys, Tokens or Credentials

**Verdict: CLEAN — no secrets in shipped code.**

- Searched `main.py`, `backend_api.py`, `webview_main.py`, `platform_check.py`, `uiverse_combobox.py` for `api_key`/`apikey`/`secret`/`password`/`token`/`bearer`/`credential` — **zero real hits** (only false positives: the `THEMES` color dict at `main.py:780-809`, `self.tokens` at `main.py:1384`).
- The only credential handling lives in **`diagnose.py` / `diagnose2.py`**, which are **developer-only scripts that are NOT bundled** (confirmed absent from `dist\Phase20-44-Visual-Review\PrayerMusicGuard\`). They read an NVIDIA API key from `C:/Users/slive/.local/share/opencode/auth.json` and send it as a `Bearer` header to `integrate.api.nvidia.com`. They hold the key in memory only, never persist it.
  - **INFO:** that path is a hard absolute user-specific path. These scripts must remain excluded from every release build (they currently are). Keep them out of `datas`/`hiddenimports` and consider moving them to a separate `tools/` directory excluded from packaging.

**No hardcoded coordinates, IPs, or embedded credentials anywhere in the application.**

---

## 8. Unsafe Permissions or Writable Executable Resources

**Verdict: safe.**

- **No `os.chmod`** calls, no `0o777`, no explicit permissive mode bits anywhere (verified by search).
- All writes target `%APPDATA%` (user-only ACL by default) or the system temp dir.
- No file is opened in a mode that grants cross-user writes.
- One consideration (5.2): the `LOCAL_DIR` fallback can write settings next to the script/EXE in constrained environments — low severity, and worth redirecting to `%LOCALAPPDATA%` for frozen builds so a writable file never sits beside a signed EXE.

---

## 9. DLL / Executable Loading Risks

**Verdict: safe — system DLLs only, no search-path manipulation.**

All native interop uses `ctypes.WinDLL`/`ctypes.windll` with **well-known system DLL names**: `kernel32`, `user32`, `winmm`, `shell32`, `shcore` (`main.py:161-162, 453, 507, 516`).

- **No `AddDllDirectory`, no `LoadLibrary`/`CDLL` with a path, no DLL loaded from a writable location** — the search path is the default system order.
- Native functions used are all benign, read-only or message-passing:
  `CreateMutexW` (single-instance), `OpenProcess(PROCESS_QUERY only)`, `QueryFullProcessImageNameW`, `CloseHandle`, `GetWindowThreadProcessId`, `EnumWindows`, `EnumChildWindows`, `GetClassNameW`, `IsWindowVisible`, `SendMessageTimeoutW`, `keybd_event`, `mciSendStringW`, `SetCurrentProcessExplicitAppUserModelID`, `SetProcessDpiAwareness`.
- `main.py:53-58` appends (never prepends) `vendor\` to `sys.path` **by design**, so the interpreter's own packages win — no DLL/Pyd hijack surface introduced.
- `user32.PostMessageW` and `user32.GetForegroundWindow` are declared but **never called** — dead prototypes that could be removed for hygiene (INFO).

**No DLL preloading/hijacking risk identified.**

---

## 10. Update / Release Security Risks

| # | Severity | File / module | Exact reason | Recommended safe fix | Compatibility risk |
|---|---|---|---|---|---|
| 10.1 | **HIGH** | `release.ps1`, `PrayerMusicGuard.iss` | **No Authenticode signature on the EXE or the installer.** `release.ps1` writes only `SHA256SUMS.txt` (an integrity *listing*, not a signature) and `RELEASE_MANIFEST.txt`. A user cannot verify the publisher, and SmartScreen will flag every fresh download. | Add `signtool sign` to `release.ps1` for both the EXE and the built installer; record the signing cert thumbprint in the manifest alongside the SHA-256 list. See §14. | None (additive). |
| 10.2 | MEDIUM | `PrayerMusicGuard.iss:36` | Installer `Source` path points at `dist\Phase18-OneDir-Test\...` — a stale, non-existent build folder. Running the release script today would package the wrong (or a missing) build. | Parameterize to the actual `--distpath` used by the current build. | None. |
| 10.3 | LOW | `release.ps1:161-190` | SHA-256 sums are produced and archived — good for tamper-evidence *if* the channel delivering `SHA256SUMS.txt` is itself trusted (a website/HTTPS release page). | Publish sums over HTTPS and ideally alongside a GPG/cosign signature of the sums file. | None. |

---

## 11. Python Source / Bytecode Exposure Inside the OneDir Build

**This is the central finding of the audit.**

Confirmed contents of `dist\Phase20-44-Visual-Review\PrayerMusicGuard\` (1,028 files):

| Exposure | Detail |
|---|---|
| **Plain-text `.py` — application** | 6 files: `main.py` (181,764 B), `uiverse_combobox.py` (33,753 B), `webview_app\{backend_api.py (45,473 B), launcher.py (10,815 B), platform_check.py (5,815 B), webview_main.py (13,211 B)}` — all verified **byte-identical, fully readable** |
| Plain-text `.py` — dependency | 11 files under `pystray\` (public library, not sensitive) |
| Loose `.pyc` | 5 under `pystray\__pycache__` (public library) |
| Bytecode container | `PYZ-00.pyz` (3,886,661 B, **unencrypted** — see 2.2) embedded in the EXE, containing all application modules |
| `base_library.zip` | 1,032,264 B, 163 stdlib `.pyc` (not sensitive) |
| Stray backup | `webview_app\frontend\js\app.js.bak` shipped (see 2.5) |
| Data assets | `assets\data\cities.json` (45,751 B), `countries.json` — readable data, intended |

**Why the source ships (root cause):** `backend_api.py:34-69` resolves `main.py` **on disk** (`_main_py()` → `sys._MEIPASS\main.py`) and `exec_module`s it at startup. That deliberate design choice is *why* `main.py` must be declared as `datas`. The module is simultaneously present in `PYZ-00.pyz` through `hiddenimports`, so the on-disk copy is redundant once `_load_main` is converted to a normal import.

**Impact:** 100% of the backend logic — scheduler, media control, process/window enumeration, registry autostart, the whole Tkinter app — is recoverable in seconds with a text editor. For a product preparing public distribution this is a total IP exposure.

---

## 12. Modules That Should Receive Stronger Protection

Ranked by sensitivity × exposure:

| Rank | Module | Why sensitive | Current exposure |
|---|---|---|---|
| 1 | **`main.py`** | Core engine: scheduler, APPCOMMAND media control, process/window enumeration (`EnumWindows`/`OpenProcess`), registry autostart, settings persistence, the full Tkinter UI. The largest single piece of IP (181 KB). | Plain-text on disk + unencrypted PYZ |
| 2 | **`webview_app\backend_api.py`** | The pywebview bridge: exposes 16 API methods to the webview, orchestrates pause/resume, loads `main.py`. | Plain-text on disk + unencrypted PYZ |
| 3 | **`uiverse_combobox.py`** | Custom UI widget implementation (33 KB). | Plain-text on disk + unencrypted PYZ |
| 4 | **`webview_app\webview_main.py`** | WebView2 bootstrap, runtime/storage paths, single-instance ownership. | Plain-text on disk + unencrypted PYZ |
| 5 | **`webview_app\launcher.py`, `platform_check.py`** | Frontend selection logic + probe. Least sensitive. | Plain-text on disk + unencrypted PYZ |
| — | `webview_app\frontend\*` (HTML/CSS/JS) | Frontend is inherently client-side; treat as public. Acceptable as-is. | Readable (expected for local web UI) |

---

## 13. Safe Code-Protection Options

**Constraints to honor:** Windows 7 SP1 x64 → Windows 11; Python 3.8.10 x64; PyInstaller 5.13.2; current pywebview/WebView2 architecture; **no packers, no aggressive obfuscation, no architecture change, no UI change.**

### Recommended — Tiered

**Tier 1 (must-do, zero architecture risk): eliminate plain-text shipping + encrypt PYZ**
1. Convert `_load_main()` in `backend_api.py` to a plain `import` (the module is already a `hiddenimport` in PYZ). Delete the six `datas` entries for `.py` files in `PrayerMusicGuard.spec`. → **No readable source remains on disk.**
2. Set `block_cipher` on `Analysis`/`PYZ` (PyInstaller 5.x `pyz_crypto.PyiBlockCipher`). → PYZ at rest is no longer a plain zip of bytecode.
3. Purge `*.bak`, `*.pyc` (loose), and `pystray\__pycache__` from the COLLECT; add `*.bak` to `.gitignore`.
- **Effect:** casual extraction goes from "open the folder" to "run a PyInstaller PYZ extractor + decompile 3.8 bytecode" — enough to defeat opportunistic copying.
- **Compatibility:** Win7→Win11 safe (pure PyInstaller 5.13.2 features). Verify both source-run and frozen-run paths after the import refactor. Note `block_cipher` is **not** available in PyInstaller ≥ 6, so keep 5.13.2 pinned or re-evaluate Tier 2 later.

**Tier 2 (stronger IP protection, still no packer): AOT compile the sensitive modules**
- Compile `main.py` / `backend_api.py` to native extension modules (`.pyd`) and import them as packages, so no Python bytecode of the core logic ships at all.
  - **Cython** (compile `.py` → `.pyd`): mature, 3.8-compatible, Win7-compatible when built with a supported MSVC toolchain. Requires the sensitive modules to be import-clean (few dynamic tricks). Best protection-to-compatibility ratio available without a packer.
  - **Nuitka** (compiles the whole app to C): strongest, but it restructures the build substantially and demands careful re-testing of the pywebview/window/scheduler path — higher regression risk against the "do not change the stable architecture" constraint.
- **Compatibility risk (Cython):** medium — needs a C build step in `release.ps1` and a Win7-compatible MSVC runtime; must retest `exec_module` removal, `sys._MEIPASS` asset resolution, and pystray/tkinter interplay on Win7 SP1 and Win11.
- **Explicitly rejected per constraints:** UPX/MPRESS packers, PyArmor-style runtime obfuscation, VMProtect — all fall under "packers or aggressive obfuscation" and are also top-tier AV false-positive triggers, which would undo the signing work in §1.1/§14.

**Tier 3 (recommended baseline, complementary): bytecode-only fallback**
If Tier 2 is too invasive, ship compiled `.pyc` (from a fixed `python -m compileall`) instead of `.py` while keeping PYZ encryption. Python 3.8 bytecode decompilers exist, so this is weaker than Cython, but it is a one-line build change with zero runtime risk.

---

## 14. Code-Signing Requirements for Future Releases

**Current state:** nothing is signed. `codesign_identity = None` (`PrayerMusicGuard.spec:87`), no `signtool` in `build_exe.bat` or `release.ps1`, no `SignTool` directive in `PrayerMusicGuard.iss`.

### Recommendation

| Step | Action |
|---|---|
| 1 | Purchase a **Code Signing Certificate** (OV minimum). For immediate SmartScreen reputation without a long ramp, **EV** is preferred; OV builds reputation over downloads/time. |
| 2 | Store the private key on a hardware token (HSM/USB token) — never on disk or in the repo. |
| 3 | In `release.ps1`, after PyInstaller: `signtool sign /fd sha256 /tr <timestamp-RFC3161> /td sha256 /sha1 <thumbprint> "PrayerMusicGuard.exe"` and the same for the installer output. |
| 4 | **Dual-sign (SHA-256 + SHA-1)** if Windows 7 SP1 support is required — Win7 SHA-2 support depends on installed updates; SHA-1 remains broadly accepted there. Win10/11 will use the SHA-256 signature. |
| 5 | Add `SignTool=...` / `SignedInstaller=yes` to `PrayerMusicGuard.iss` so the installer itself is signed. |
| 6 | Set `codesign_identity` in `PrayerMusicGuard.spec` so the bootloader-embedded manifest/publisher data is correct. |
| 7 | Record the certificate thumbprint + SHA-256 in `RELEASE_MANIFEST.txt` (alongside the existing `SHA256SUMS.txt`) so releases are auditable. |
| 8 | Consider submitting the signed binary to Microsoft for fast-track reputation (via partner portal) and to major AV vendors as a known-good application. |

**Benefits:** removes the "unrecognized app" SmartScreen gate, materially lowers heuristic AV scores (directly mitigating findings 1.1, 1.2, 1.3), verifies publisher identity for users, and prevents tamper-detection confusion.

**Compatibility risk:** none — signing is additive and does not alter runtime behavior on Win7 SP1 → Win11.

---

## 15. What Is Already Implemented Correctly

These require **no change** and should be preserved:

1. **No malicious behavior whatsoever** — no process injection, no cross-process memory access (`PROCESS_VM_READ`/`WriteProcessMemory`/`CreateRemoteThread`/`SuspendThread` all verified absent), no download-and-execute.
2. **Media control is message-based only** — targeted `WM_APPCOMMAND`/`APPCOMMAND_MEDIA_PAUSE` (`main.py:261-278`) plus a Win7-only `VK_MEDIA_PLAY_PAUSE` fallback (`main.py:281-283`); the "suspend" *settings string* is a name only, no process suspension occurs. Resume always uses the same channel that paused.
3. **Least-privilege autostart** — HKCU Run key, `KEY_SET_VALUE` only, no admin.
4. **No command-injection surface** — every subprocess is a fixed literal with `shell=False` and `CREATE_NO_WINDOW`; the only user-controlled value (player path) is matched in pure Python by exe stem.
5. **HTTPS-only network with certificate verification** — no `verify=False`, no custom SSL context.
6. **No secrets in application code**; developer diagnostic scripts are correctly excluded from the bundle.
7. **System-DLL-only native loading** — no DLL search-path manipulation, no loads from writable locations.
8. **No permissive filesystem permissions** — no `chmod`/`0o777`; writes confined to `%APPDATA%`/temp.
9. **Atomic settings persistence** (`.tmp` → `Path.replace()`).
10. **Least-privilege `asInvoker` manifest**; no UAC elevation requests.
11. **No packers/UPX** — avoids a major false-positive class.
12. **Loopback-only local webview** — the pywebview HTTP server binds `127.0.0.1`; no remote URLs are loaded into WebView2.
13. **Single-instance mutex** (`Global\PrayerMusicGuard_SingleInstance`) with graceful second-launch exit.
14. **Rotating, size-capped logging** (5 × 1 MB) in the main logger.
15. **Pinned, reproducible toolchain** (Python 3.8.10 x64 + PyInstaller 5.13.2) enforced by `release.ps1`.

---

## 16. Findings Register (consolidated)

| # | Sev | Component | One-line summary |
|---|---|---|---|
| 2.1 | **CRITICAL** | spec:16-22 + backend_api.py:34-69 | All application `.py` ships as readable plain text; root cause is on-disk `exec_module` of `main.py` |
| 1.1 | **HIGH** | release.ps1 / .iss / spec | No Authenticode signing of EXE or installer → SmartScreen + AV friction |
| 2.2 | **HIGH** | spec:53,68,71 | PYZ unencrypted (`cipher=None`) — only meaningful after 2.1 |
| 10.1 | **HIGH** | release pipeline | No signature on released artifacts; only SHA-256 listings |
| 1.3 | MEDIUM | main.py:604+, backend_api.py:716+ | PowerShell child processes create heuristic AV noise (behavior is safe) |
| 1.2 | MEDIUM | main.py:282-283 | Global media-key simulation looks keylogger-like to heuristics |
| 1.4 | MEDIUM | webview_main.py:90 | Hardcoded exact WebView2 runtime version pin |
| 2.3 | MEDIUM | bundle | 5 loose dependency `.pyc` shipped |
| 2.5 | MEDIUM | bundle/frontend | Stale `app.js.bak` shipped in release |
| 2.6 | MEDIUM | build/*.toc | ~4,500 absolute build-path references in `build\` (not shipped, keep it that way) |
| 10.2 | MEDIUM | .iss:36 | Installer sources from stale `dist\Phase18-OneDir-Test` |
| 5.1 | LOW | backend_api.py:848-867 | Unbounded frontend-supplied diag payload appended to log |
| 5.2 | LOW | main.py:45-49 | Settings fallback can write next to the EXE |
| 10.3 | LOW | release.ps1 | SHA-256 sums delivered without a signature over the sums file |
| 2.7 | LOW | .iss | Build-folder naming inconsistency across spec/bat/iss |
| 2.8 / 1.5 / 6.1 | INFO | various | Defaults correct; loopback trust boundary is inherent to pywebview |

**Count:** 3 HIGH, 6 MEDIUM, 4 LOW, 1 CRITICAL, plus correct-as-is items in §15.

---

## 17. Recommended Phase 20.46 Implementation Plan (NOT implemented)

**Objective:** eliminate source exposure and establish code signing, with zero architecture/runtime-behavior change and no packers.

### 20.46.A — Remove plain-text source from the bundle (fixes CRITICAL 2.1)
1. Refactor `webview_app/backend_api.py` `_load_main()` (`:60-69`) to import the compiled module instead of `exec_module`-ing `main.py` from disk: keep the on-disk path **only** for unfrozen source runs, and `import` from PYZ when `sys.frozen`.
2. Remove the six `.py` `datas` entries from `PrayerMusicGuard.spec` (`:16-22`), keeping the `hiddenimports` (`:33-39`) that already compile them into PYZ.
3. Verify `main.py`'s `__file__`/asset-resolution (`sys._MEIPASS`) still resolves after the switch; test both source-run and frozen-run on Win7 SP1 and Win11.
4. Add `*.bak` exclusion and purge `*.pyc`/`__pycache__` from COLLECT (fixes 2.3, 2.5).

### 20.46.B — Encrypt the PYZ archive (fixes HIGH 2.2)
5. Set `block_cipher = pyz_crypto.PyiBlockCipher(...)` in `PrayerMusicGuard.spec` for both `Analysis` and `PYZ`; confirm PyInstaller 5.13.2 behavior and note the ≥6 incompatibility.

### 20.46.C — Establish code signing (fixes HIGH 1.1 / 10.1)
6. Add a signed `signtool` step to `release.ps1` for the EXE and installer (SHA-256, RFC-3161 timestamp; dual SHA-1+SHA-256 if Win7 requires it).
7. Add `SignTool`/`SignedInstaller` to `PrayerMusicGuard.iss`; parameterize its `Source` path to the real `--distpath` (fixes 10.2).
8. Record cert thumbprint in `RELEASE_MANIFEST.txt`.

### 20.46.D — Hygiene (fixes MEDIUM/LOW)
9. Drop the hardcoded WebView2 version pin in `webview_main.py:90`, keeping the registry detection (`:96-119`).
10. Cap/whitelist `diag_report` payloads (`backend_api.py:848-867`).
11. Redirect the `LOCAL_DIR` fallback (`main.py:45-49`) to `%LOCALAPPDATA%` for frozen builds.
12. Keep `build\` out of distribution archives; optionally relocate the PyInstaller workpath.

### 20.46.E — Optional, higher protection (assess, don't commit yet)
13. Prototype compiling `main.py` + `backend_api.py` with **Cython** to `.pyd` and measure Win7 SP1 ↔ Win11 behavior across the pywebview/scheduler/tray path. Adopt only if regression risk is acceptable. **Do not** adopt UPX/PyArmor/VMProtect (packer + AV constraints).

### Verification gates for 20.46
- Frozen bundle contains **zero** `.py` application files and no loose `.pyc` (grep the COLLECT output).
- Full Phase 20.44-style build + real-EXE review passes again (all 130 checks) on the hardened bundle.
- `signtool verify` succeeds on both the EXE and the installer; SmartScreen no longer labels the app "unrecognized" on a clean test VM.
- Win7 SP1 x64 and Win11 both launch, render WebView2, bridge, pause/resume, autostart, and shut down cleanly.

---

**Audit complete. Read-only. No files modified, no builds created, no packages installed. STOP.**
