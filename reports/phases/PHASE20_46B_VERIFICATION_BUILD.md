# Phase 20.46.B — Verification Build ONLY

**Status: PASS** — the encrypted-PYZ build was built, proven encrypted, and passed every
runtime, regression, and hygiene check.

**Date:** 2026-09-22
**Mode:** READ / BUILD / QA only. No source, spec, or config file was modified. The only
write outside the new build/evidence folders was reverting the theme side-effect the
regression harness itself caused (`settings.json` `theme` restored to `dark` — the same
cleanup as Phase 20.46.A; times/music untouched).
**Toolchain:** pinned `win7\venv` — Python 3.8.10 x64, PyInstaller 5.13.2, tinyaes 1.1.2.

---

## 1. Build result

| Item | Value |
|---|---|
| Command | `win7\venv\Scripts\pyinstaller.exe PrayerMusicGuard.spec --distpath dist\Phase20-46B-Verification --workpath build\Phase20-46B-Verification --noconfirm` |
| Exit code | **0** (21.5 s) |
| Cipher arming (log) | `INFO: Will encrypt Python bytecode with provided cipher key` |
| Auto hidden import (log) | `INFO: Analyzing hidden import 'tinyaes'` — the `Analysis(cipher=…)` side-effect |
| PYZ | `INFO: Building PYZ (ZlibArchive) …\PYZ-00.pyz completed successfully` |
| Expected deprecation | `DEPRECATION: Bytecode encryption will be removed in PyInstaller v6…` (non-fatal; 5.13.2 mechanism) |

## 2. EXE / bundle metrics

| Metric | Value |
|---|---|
| EXE path | `dist\Phase20-46B-Verification\PrayerMusicGuard\PrayerMusicGuard.exe` |
| EXE SHA-256 | `5984502F83847C0C4D343AE28FC29650EB5FD4DCAB996C601ED8A496870CF48F` |
| EXE size | 4,264,707 B |
| Bundle | 1,023 files / 32,526,832 B (30.99 MB) |
| vs Phase 20.46.A | +1 file, +66,430 B — **exact closure:** only `tinyaes.cp38-win_amd64.pyd` (new, 55,296 B) and the EXE (+11,134 B, the encrypted PYZ's per-entry 16-byte IV across 684 modules + the embedded key module); the other **1,021 files are size-identical**, and `python38.dll` / `_ctypes.pyd` hash-identical |

## 3. Encryption verification — 26/26 PASS

Harness: `reports\phases\phase20_46b_evidence\_verify_pyz.py` (results:
`pyz_encryption_result.json`). Uses PyInstaller's **own** readers against the **shipped
EXE**: `CArchiveReader(EXE)` → embedded PKG TOC → `ZlibArchiveReader(EXE, offset)` over
the embedded PYZ, with the key supplied (or withheld) through the same
`pyimod00_crypto_key` module the bootloader uses.

- **Structural:** the EXE's embedded CArchive TOC carries `PYZ-00.pyz` (typecode `'z'`);
  the embedded PYZ header begins `b'PYZ\0'` with the **encryption flag byte at offset 12
  == 1** (writers.py:71-78), TOC offset 3,869,234; the standalone workpath `PYZ-00.pyz`
  carries the identical flag. PYZ TOC holds 684 modules.
- **WITHOUT the key:** `ZlibArchiveReader` arms no cipher; extracting `backend_api` and
  `main` fails — `Error -3 while decompressing data: incorrect header check` (the entries
  are ciphertext, not zlib).
- **WITH A WRONG key:** the reader arms a cipher, but extraction still fails with the
  same zlib header error — the real key is required.
- **WITH THE REAL key** (from `pyz_crypto_key.txt`): **all 7 application modules
  extract** and are provably ours by `co_names`: `backend_api`→`BackendAPI,get_state,
  save_settings`; `main`→`acquire_single_instance`; `launcher`→`main`;
  `webview_main`→`run`; `platform_check`→`can_use_html_frontend`;
  `uiverse_combobox`→`CountryCitySelector`; `app_entry`→`main`.
- **Runtime decryption backend:** `tinyaes.cp38-win_amd64.pyd` is bundled (55,296 B).
- **Key placement (correct by design):** `pyimod00_crypto_key` is a module entry
  (typecode `'m'`, offset 0) in the EXE's **CArchive** — *outside* the encrypted PYZ,
  because the bootloader cannot read the key from the archive it must decrypt. **No
  readable crypto-key file exists anywhere in the bundle folder** (the only copies are
  the build-time workpath artifacts).

## 4. Application-source inspection

| Check | Result |
|---|---|
| Application `.py` in bundle (`main`, `uiverse_combobox`, `backend_api`, `launcher`, `platform_check`, `webview_main`, `app_entry`) | **0** — Phase 20.46.A's no-plain-source property preserved; all seven ship only as encrypted PYZ bytecode |
| `pyz_crypto_key.txt` / any `*crypto_key*` file in bundle | **0** |
| Pre-existing `pystray\` dependency `.py` | 13 (unchanged since 20.44 — Phase 20.46.D scope) |
| Assets/frontend | `assets\icons\prayer_music_guard.ico`, `webview_app\frontend\{index.html,js\app.js,css\skins.css}`, `webview_app\splash.html`, `webview\js\api.js` — **all present** |

## 5. Runtime results — 66/66 PASS

Live EXE launched with the documented test-environment switch
(`WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS=--remote-debugging-port=9502`, env var only — no
project file modified; the same mechanism as Phases 20.38/20.42/20.44/20.46.A). Harness:
`reports\phases\phase20_46b_evidence\_verify.js` (results: `verify_result.json`).

- **Startup/WebView2:** page target `http://127.0.0.1:54391/index.html`, title
  `صلاة وسكون`, `readyState=complete`, 478 chars of rendered content.
- **Bridge:** `window.pywebview.api` present with **16 methods**; `get_state()` round-trip
  **ok=true in 5 ms**; version 1.2.7; 5 prayers (Fajr 05:20 ص … Isha 08:16 م), exactly
  one `is_next` (Asr).
- **Prayer UI:** 5 cards keyed Fajr..Isha with Arabic names and live countdown ring
  (`العصر`, 04:21 م, `02:31:49`).
- **All 3 save buttons** (`#btn-save-times`, `#btn-save-music`, `#btn-save`): real CDP
  clicks drive the exact Phase 20.43 animation — `.is-saving` applied without hover,
  `has-saved` once, `cubic-bezier(0.5,0,0.25,1)`, 1 s, zoom 1.75/0.75/1, button becomes
  the 40×40 container, label restored (`تم حفظ الإعدادات.`), guard cleared; dark-theme
  repeat identical (1,000 ms).
- **Failed save:** real backend rejection (minutes 999 → `المدة من 1 إلى 180 دقيقة.`)
  produces **no** animation, intact label, `is-error` status.
- **Themes/RTL:** light + dark applied and styling changes; `dir=rtl`, `lang=ar`.
- **Errors:** **0** CDP page exceptions, **0** `console.error`.
- **Clean shutdown:** graceful close → 2 processes → 0 leftover; webview.log records
  `webview.start() returned normally`; launcher log `HTML frontend closed cleanly`;
  **0** error hits across 2,181 webview.log lines; full pipeline logged (splash →
  WebView2 → bridge → single-instance acquired → scheduler → ready flag).

## 6. Tkinter fallback (PMG_FORCE_TK=1) — PASS

`PMG_FORCE_TK=1` forced the frozen `runpy.run_module("main")` path — i.e. `main`
**imported out of the encrypted PYZ** with no `main.py` on disk:

- launcher log: `using Tkinter fallback: PMG_FORCE_TK set`
- app log: `Application starting: PrayerMusicGuard v1.2.7 (frozen run, python 3.8.10)`
- Tk window title `صلاة وسكون - v1.2.7`; tray icon loaded + started; monitoring armed;
  `Monitoring tick #1: alive …; next prayer Asr at 16:21`; process-cache worker started
- terminated with 0 leftover processes (the app hides-to-tray on window close by design,
  so termination was via the process/tray path)

This is the key **20.46.A × 20.46.B interaction proof**: the encrypted archive imports
and runs the application end-to-end on both frontend paths (WebView2 and Tk).

## 7. Regression results — PASS

Harness: `reports\phases\phase20_46b_evidence\_regress.js` (the project's existing
20.42/20.44 suite, re-pointed to port 9502; results: `review_result.json`). `errors: []`.
Measurements match Phase 20.44/20.46.A exactly, in both themes: buttons
`btn-pause`/`btn-resume` 119.9×43 (min-height 40 px, accent class on pause); monitor chip
on/off/restored (`chip--on`/`chip--off`); WhatsApp link 84×24 (`wa.me` target, 0.5 s
transition, real-cursor hover); radios 34×34 with 9 px dot; checkboxes 16.89×16.89,
3.25 px radius; alert variants (`is-success` 551×36.38, 4 px bar); theme toggle
dark↔light sticks; `dir=rtl`, `lang=ar`.

## 8. Errors / harness issues

No application defects. Harness-side issues found and fixed (all in evidence scripts, no
project file involved):

1. Two evidence scripts computed `PROJECT_ROOT` with two `..` instead of three
   (evidence → phases → reports → root) — corrected.
2. `CArchiveReader`'s TOC already stores `typecode` as `str`; a redundant `chr()` raised
   `TypeError` — removed.
3. The key-module lookup initially assumed `pyimod00_crypto_key` was inside the PYZ; it
   is in the outer **CArchive** (correct architecture — it cannot live inside the archive
   it decrypts). Check corrected; the false failure became a PASS.
4. An ad-hoc PowerShell scan for the CArchive `MEI` cookie mis-handled octal escapes;
   abandoned in favour of PyInstaller's own `CArchiveReader`.
5. Test side-effect: the regression harness left `settings.json` `theme` on `light`;
   restored to the user's `dark` (music/times/minutes/location unchanged).

## 9. Previous builds / releases untouched

A pre-build snapshot of `dist\` + `releases\` (6,181 entries, 13 EXE hashes) was compared
post-run: **0 entries missing**, **+1,023 added — exactly the new verification bundle's
file count**. Prior build hashes are unchanged: 20.44
`C8DBF268CF48C0AF23022FF54AFE9CB952FB35F5B94F3087532B19840B23DC6F`, 20.46.A
`8035180C1A37F56B001F8EB697348F740CEC09741EC81EB485DACF4D6E706E37`. No release was
produced. TEMP `_MEI*` dirs all predate this session (none created by this OneDir build).

## 10. Scope confirmations

- **20.46.C (signing):** not implemented — `codesign_identity=None` unchanged, no
  Authenticode step.
- **20.46.D (hygiene purge):** not implemented — the 13 pre-existing `pystray\` `.py`
  dependency files remain, untouched.
- **20.46.E (Cython/Nuitka):** not implemented — no native compilation of application
  sources.
- **No packers** (UPX/PyArmor/VMProtect); `upx=False`, `strip=False` throughout.
- No source/spec/config modified in this phase (READ/BUILD/QA only).

## 11. Final verdict

**PASS.** The Phase 20.46.B encrypted-PYZ build succeeds with the pinned Win7 toolchain;
the shipped EXE's embedded PYZ is provably encrypted (flag byte set; unreadable without
the key *and* with a wrong key; readable with the real key into the seven recognizable
application modules); no application source or key file ships; the live EXE passes 66/66
runtime checks and the full 20.42/20.44 regression with zero errors and a clean
shutdown; the Tkinter fallback imports `main` from the encrypted archive successfully;
and every prior build/release is byte-for-byte untouched.

Evidence: `reports\phases\phase20_46b_evidence\` — `_verify_pyz.py`,
`pyz_encryption_result.json` (26/26), `_verify.js`, `verify_result.json` (66/66),
`_regress.js`, `review_result.json` (`errors: []`), baseline snapshot, and PNG captures.
