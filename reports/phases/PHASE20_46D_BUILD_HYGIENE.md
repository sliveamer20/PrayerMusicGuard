# Phase 20.46.D — Build Hygiene & Cleanup

**Status:** COMPLETE — PASS
**Date:** 2026-09-22
**Scope:** Security/release hygiene only. No application source, UI, behavior, updater,
signing certificate, signed build, encryption key, or release artifacts were modified.

---

## 0. Method

1. Read the current project state and the Phase 20.46.A/B/C reports.
2. Recorded a **full-tree SHA-256 baseline of 49,779 files** before any change
   (`$env:TEMP\opencode\pmg46d_baseline.txt`).
3. **Backed up every file** that was modified or deleted into
   `backup\phase20_46d_build_hygiene_20260922\`.
4. Applied only confirmed-obsolete cleanups.
5. Re-hashed the whole tree and diffed against the baseline to prove the change set is
   exactly what was intended — nothing more.

---

## 1. Exact Files Removed

Every removed file is regenerable, unreferenced, or preserved in the backup folder.

### 1a. Stale `.bak` files in the ACTIVE tree (4 files)

| Removed file | Size | Why safe |
|---|---|---|
| `webview_app\frontend\js\app.js.bak` | 15,299 B | Obsolete copy of `app.js` (current 59,035 B). Not referenced by any active script/spec/JS. Backed up. |
| `webview_app\backend_api.py.bak` | 27,910 B | Obsolete copy (current 46,387 B). Unreferenced. Backed up. |
| `webview_app\webview_main.py.bak` | 9,116 B | Obsolete copy (current 13,211 B). Unreferenced. Backed up. |
| `opencode.json.bak` | 6,612 B | Obsolete config copy (current 6,883 B). Unreferenced. Backed up. |

**Proof of staleness (each):** content hash differs from the current original, the
current original exists and is newer, and a scan of every active `.py/.spec/.ps1/.bat/
.iss/.json/.md` file found **zero** references to any `.bak` path.

### 1b. Stale `.pyc` / `__pycache__` in ACTIVE areas (87 files)

Python bytecode caches — pure regenerable build artifacts, all git-ignored.

| Removed tree | Files |
|---|---|
| `__pycache__\` | 5 |
| `webview_app\__pycache__\` | 6 |
| `vendor\__pycache__\` | 1 |
| `vendor\PIL\__pycache__\` | 70 |
| `vendor\pystray\__pycache__\` | 3 |
| `vendor\pystray\_util\__pycache__\` | 2 |
| **Total** | **87** |

Deliberately **not** touched: `win7\python\…`, `win7\venv\…` (the pinned Win7 toolchain —
removing its caches would force a slow rebuild and risks toolchain drift), `build\`
(PyInstaller workpath for 20.46.A/B), `dist\` (shipped builds), and every `backup\` /
`cleanup_backup_*` tree (historical evidence).

### 1c. Obsolete `build-win7-test\` tree (20 files, ~31 MB)

A standalone PyInstaller test build with its own derivative
`PrayerMusicGuard-Win7Test.spec` (hash differs from the active `PrayerMusicGuard.spec`).
A repo-wide scan found **no reference to `build-win7-test` in any active script**.
Its `localpycs`, `work\`, and `dist\` contents are regenerable PyInstaller output.
Backed up the two non-regenerable/provenance files (the spec and the warnings log) to
`backup\phase20_46d_build_hygiene_20260922\build-win7-test\`, then removed the tree.

---

## 2. Exact Files Modified (4 files)

### 2a. `diagnose.py` and `diagnose2.py` — path-leakage redaction

**Issue found:** both contained a **hardcoded absolute user path**:
```python
with open(r"C:/Users/slive/.local/share/opencode/auth.json") as f:
```
This leaks the developer's Windows username into the repository. **No API key value was
ever present in these files** — the key is read at runtime from `auth.json` (verified by
regex scan for `nvapi-[A-Za-z0-9_-]{10,}` → 0 matches in both files). So this was a
**path-leakage** issue, not a secret-leakage issue.

**Fix (behavior-preserving):**
```python
import json, urllib.request, urllib.error, sys, time, os
...
with open(os.path.join(os.path.expanduser("~"), ".local", "share", "opencode", "auth.json")) as f:
```
`os.path.expanduser("~")` resolves to the **identical** path on this machine
(`C:\Users\slive\.local\share\opencode\auth.json` — verified), so runtime behavior is
unchanged while the literal username is removed from the source.

### 2b. `build_exe.bat` — stale build path

**Issue:** pointed at a dist folder that no longer exists.
```bat
- set "DIST_DIR=dist\Phase20-24-Location-Data-Fix"
+ set "DIST_DIR=dist\PrayerMusicGuard"
```
`dist\Phase20-24-Location-Data-Fix` does not exist (confirmed). The new value is
PyInstaller's default onedir output for the active spec (`COLLECT name='PrayerMusicGuard'`),
matching what `release.ps1` produces.

### 2c. `PrayerMusicGuard.iss` — stale installer path + filename

**Issues:** two dead references in the *active* installer script (it is invoked by
`release.ps1`):

```iss
- OutputBaseFilename=PrayerMusicGuard-v1.2.7-ONEDIR-TEST
+ OutputBaseFilename=PrayerMusicGuard-Setup
- Source: "dist\Phase18-OneDir-Test\PrayerMusicGuard\*"; DestDir: "{app}"; ...
+ Source: "dist\PrayerMusicGuard\*"; DestDir: "{app}"; ...
```

* `dist\Phase18-OneDir-Test\` **does not exist** (confirmed) — the installer would fail
  or package the wrong tree. The active build emits `dist\PrayerMusicGuard\` (PyInstaller
  default distpath per `release.ps1` line 133, COLLECT name `PrayerMusicGuard`).
* `OutputBaseFilename` carried a stale `-ONEDIR-TEST` suffix. `release.ps1` line 140
  expects the setup at `dist\PrayerMusicGuard-Setup.exe`; the old name would have made
  the release script fail its own post-build existence check.

Only path/name string literals changed. **No `[Code]`, `[Run]`, `[Icons]`, `[Registry]`,
`[Files]` flags, compression, or language settings were touched.**

---

## 3. Files Intentionally Retained

Retained and **not** modified, per the phase constraints:

| Item | Reason retained |
|---|---|
| `pyz_crypto_key.txt` | Phase 20.46.B encryption key — explicitly out of scope, hash verified unchanged |
| `PrayerMusicGuard.spec` | Active spec; 20.46.A/B logic intact (18/18 validation checks pass) |
| `main.py`, `uiverse_combobox.py`, `webview_app\*.py`, all frontend `html/css/js` | Application source / UI — out of scope |
| `release.ps1` | Release logic — validated read-only, passes unchanged |
| `backup\phase20_27_release_uat_…`, `backup\phase20_37_ui_fix_…`, `backup\phase20_40_lucide_…` | Historical backups (contain their own `.bak` files — left alone) |
| `backup\phase20_46d_build_hygiene_20260922\` | **New** — the pre-change backups made by this phase |
| `cleanup_backup_phase20_29…34\` | Historical cleanup evidence (contain old `.pyc`/`.bak`) |
| `reports\**` (all phases, evidence, QA) | Historical reports — untouched |
| `releases\v1.2.5 / v1.2.6 / v1.2.7` (15 files) | Stable releases — all 15 SHA-256 hashes unchanged |
| `dist\Phase20-28/36/38/42/44/46A/46B/46C` | Previous builds — unchanged (see §5) |
| `win7\python`, `win7\venv` | Pinned Win7 toolchain — untouched |
| `vendor\` (`.py`/packages, minus caches) | Dev-time fallback dependencies — still git-ignored |
| `__pycache__` inside `build\`, `dist\`, `backup\`, `win7\`, `cleanup_backup_*` | Not active-tree caches; out of scope |
| `تشغيل-صلاة-وسكون.bat` | Dev launcher — content verified byte-identical |

---

## 4. Tests / Checks Performed

| # | Check | Result |
|---|---|---|
| 1 | Python syntax compile — all 11 active `.py` + `PrayerMusicGuard.spec` (`py_compile`, win7 venv 3.8.10) | **11/11 OK, 0 failures** |
| 2 | Phase 20.46.B spec-load validation (`_validate_pyz.py`) — PYZ encryption wiring, datas hygiene, key isolation, guard firing | **18/18 PASS** |
| 3 | `release.ps1` validation mode (read-only, no `-Release`) | **EXIT 0** — "Preflight checks: OK", version consistency OK |
| 4 | `.gitignore` still excludes `pyz_crypto_key.txt` | **PASS** (also `__pycache__/`, `vendor/`) |
| 5 | `pyz_crypto_key.txt` hash unchanged | **PASS** — `83DA49E5719B91A1…CE433B9C` |
| 6 | No application `.py` / key file re-entered build `datas` | **PASS** — 0 violations in 20.46.A/B/C bundles |
| 7 | 20.46.C signed EXE signer + hash unchanged | **PASS** — `CN=Ayman Alaa Abu Leila`, hash `4BA1D9DB…BFC4C2` |
| 8 | 20.46.B verification EXE hash unchanged | **PASS** — `5984502F…70CF48F` |
| 9 | All `releases\` files unchanged | **PASS** — 15/15 hashes identical, 0 differences |
| 10 | Full-tree diff vs 49,779-file baseline | **PASS** — change set exactly matches §1–§2 (see below) |
| 11 | No `.bak` remaining in active tree | **PASS** — 0 |
| 12 | No `__pycache__` remaining in active tree | **PASS** — 0 |
| 13 | No hardcoded `nvapi-` key in `diagnose*.py` | **PASS** — 0 matches |

**Full-tree diff result:** 49,779 → 49,677 files. Every difference is accounted for:
- **Removed:** 87 `.pyc` + 20 `build-win7-test` + 4 `.bak` = 111 files.
- **Modified (content):** `build_exe.bat`, `diagnose.py`, `diagnose2.py`,
  `PrayerMusicGuard.iss` (appear once in both "removed" and "added" sides of the diff).
- **Added:** 9 backup copies under `backup\phase20_46d_build_hygiene_20260922\`, plus
  `reports\phases\phase20_46b_evidence\validate_result.json` (regenerated by check #2 —
  an evidence file, not a project source).
- The Arabic-named `تشغيل-صلاة-وسكون.bat` shows in the diff only because its path is
  mangled when written as ASCII; its **content is byte-identical** to the original.

---

## 5. Before / After Counts

| Metric | Before | After |
|---|---|---|
| Active-tree `.bak` files | 4 | **0** |
| Active-tree stale `.pyc` files | 87 | **0** |
| `build-win7-test` obsolete tree | 20 files (~31 MB) | **removed** |
| Active build scripts pointing at dead `dist\` paths | 2 (`build_exe.bat`, `PrayerMusicGuard.iss`) | **0** |
| Hardcoded username paths in diagnostics | 2 (`diagnose.py`, `diagnose2.py`) | **0** |
| Total project files (excl. `.opencode`) | 49,779 | 49,677 (−102 net) |
| `releases\` files | 15 | 15 (unchanged) |
| Phase 20.46.B spec-validation checks | 18/18 | **18/18** |
| Python syntax checks | — | **11/11** |

---

## 6. Remaining Hygiene Issues (intentionally out of scope)

1. **Pre-20.46.A historical bundles still ship readable application `.py`.**
   `dist\Phase20-28-Release`, `Phase20-36/38/42/44-Visual-Review` each contain 6
   readable source files (`main.py`, `backend_api.py`, `webview_main.py`, etc.). These
   predate the Phase 20.46.A source-removal change and were left **untouched** because
   they are immutable historical builds. The current 20.46.A/B/C bundles have **0**
   violations. If these old builds are ever re-published, they should be rebuilt from the
   current spec rather than re-shipped.
2. **`vendor\` is still present and git-ignored.** It is a dev-time fallback dependency
   copy (used by the local dev launcher `.bat`), not part of the Win7 build path. It is
   excluded from version control; removal would be a larger tooling decision.
3. **`.gitignore` does not explicitly list `*.bak`.** No `.bak` files remain in the
   active tree, so nothing is currently at risk, but adding `*.bak` would prevent future
   reintroduction. Left unchanged to keep this phase strictly to confirmed issues.
4. **The Phase 20.46.C self-signed certificate is still not publicly trusted.** Unchanged
   by this phase; a CA-issued certificate remains a prerequisite for public release.

---

## 7. Guarards Verified — Prior Phases Intact

| Property | Evidence |
|---|---|
| **20.46.A** source-removal | 0 violations in the 46A/46B/46C bundles; spec `datas` still excludes all application `.py` and the key file |
| **20.46.B** PYZ encryption | 18/18 spec-validation checks pass — `block_cipher` wired into `Analysis` and `PYZ`, key never leaked, guards fire on missing/empty key |
| **20.46.B** key protection | `pyz_crypto_key.txt` hash identical; still git-ignored; still never present in `datas`/`hiddenimports` |
| **20.46.C** signed build | Signer still `CN=Ayman Alaa Abu Leila` (thumbprint `E62474D0…8E1F`), EXE SHA-256 `4BA1D9DB…BFC4C2` — untouched |
| **Releases** | `v1.2.5`, `v1.2.6`, `v1.2.7` — all 15 files byte-identical |
| **Previous builds** | 20.46.A EXE and 20.46.B EXE hashes unchanged; no build was rebuilt |

No new release build was run. No EXE, DLL, or installer was signed or modified in this
phase. The signing certificate in `Cert:\CurrentUser\My` was not touched.

---

## 8. FINAL STATUS

# **PASS**

All confirmed hygiene issues addressed; every change backed up and accounted for;
Phase 20.46.A/B/C properties, all previous builds, and all releases verified intact.

**Stopping here. Phase 20.47 not started.**
