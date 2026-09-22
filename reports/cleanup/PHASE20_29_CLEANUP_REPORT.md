# PHASE 20.29 — Project Cleanup & Organization Report

**Project:** `E:\prayer-music-guard`
**Date:** 2026-09-20
**Phase:** 20.29 — Project Cleanup & Organization
**Mode:** READ-ONLY inventory first → safe cleanup only. No build, no code changes, no UI/logic/config/build-system modifications.

---

## 1. Summary of Actions

| Action | Count | Detail |
|---|---|---|
| Report folders created | 4 | `reports/`, `reports/phases/`, `reports/qa/`, `reports/cleanup/` |
| Report files MOVED | 37 | 28 → `reports/phases/`, 9 → `reports/qa/` |
| Temp scripts DELETED | 30 | `tmp_*.py` / `tmp_*.json` / `tmp_*.txt` in project root |
| Test-output files DELETED | 4 | `run_output*.txt` in project root |
| Python cache files DELETED | 10 | `__pycache__/` (root: 4) + `webview_app/__pycache__/` (6) |
| Pre-cleanup backup created | 44 files | `cleanup_backup_phase20_29/deleted/` (0.61 MB) + SHA-256 manifest |
| External files touched | 0 | Outside-project files **listed only**, none deleted/moved |
| Source/UI/config/build changes | 0 | Zero modifications |

---

## 2. Moved Files (37)

All `.md` reports were relocated **without content changes**. `README.md` was intentionally kept at the project root (required project file, not a report).

### 2.1 → `reports/qa/` (9 files) — QA / UAT / runtime verification reports

| Source (project root) | Destination |
|---|---|
| `PHASE18_QA_REPORT.md` | `reports/qa/PHASE18_QA_REPORT.md` |
| `PHASE19_QA_REPORT.md` | `reports/qa/PHASE19_QA_REPORT.md` |
| `PHASE20_UAT_REPORT.md` | `reports/qa/PHASE20_UAT_REPORT.md` |
| `PHASE20_9_REMAINING_UAT_REPORT.md` | `reports/qa/PHASE20_9_REMAINING_UAT_REPORT.md` |
| `PHASE20_10_FUNCTIONAL_MANUAL_UAT_REPORT.md` | `reports/qa/PHASE20_10_FUNCTIONAL_MANUAL_UAT_REPORT.md` |
| `PHASE20_26_FULL_INTEGRATION_QA_REPORT.md` | `reports/qa/PHASE20_26_FULL_INTEGRATION_QA_REPORT.md` |
| `PHASE20_26R_RUNTIME_QA_REPORT.md` | `reports/qa/PHASE20_26R_RUNTIME_QA_REPORT.md` |
| `PHASE20_27_RELEASE_UAT_REPORT.md` | `reports/qa/PHASE20_27_RELEASE_UAT_REPORT.md` |
| `PHASE20_28_RUNTIME_QA_REPORT.md` | `reports/qa/PHASE20_28_RUNTIME_QA_REPORT.md` |

### 2.2 → `reports/phases/` (28 files) — phase fix/feature reports

`PHASE20_1_FIX_REPORT.md`, `PHASE20_2_SPLASH_REPORT.md`, `PHASE20_3_SPLASH_REPORT.md`,
`PHASE20_4_HTML_SPLASH_REPORT.md`, `PHASE20_5_HTML_CSS_SPLASH_FIX_REPORT.md`,
`PHASE20_6_HTML_SPLASH_WHITESCREEN_FIX_REPORT.md`, `PHASE20_7_SPLASH_SCOPE_FIX_REPORT.md`,
`PHASE20_8_SPLASH_TIMING_REPORT.md`, `REPORT_Phase20_11_Fixes.md`, `PHASE20_12_REPORT.md`,
`PHASE20_12_ROOT_CAUSE_ANALYSIS.md`, `PHASE20_13_UI_COUNTDOWN_12H_LOCATION_REPORT.md`,
`PHASE20_14_COUNTDOWN_LOCATION_REPORT.md`, `PHASE20_15_LOCATION_COUNTDOWN_REPORT.md`,
`PHASE20_16_WORLDWIDE_LOCATION_COUNTDOWN_REPORT.md`,
`PHASE20_17_FINAL_LOCATION_UI_COUNTDOWN_REPORT.md`,
`PHASE20_18_LOCATION_MODE_COUNTDOWN_DIRECTION_REPORT.md`,
`PHASE20_19_LOCATION_DROPDOWN_REBUILD_REPORT.md`, `PHASE20_20_LOCATION_COMBOBOX_FINAL_REPORT.md`,
`PHASE20_21_LOCATION_STATE_FIX_REPORT.md`, `PHASE20_22_LOCATION_COMBOBOX_REPORT.md`,
`PHASE20_23_UI_REGRESSION_FIX_REPORT.md`, `PHASE20_24_LOCATION_DATA_FIX_REPORT.md`,
`PHASE20_24R1_CITY_DATASET_REPORT.md`, `PHASE20_25_MUSIC_SETTINGS_UI_REPORT.md`,
`PHASE20_26R_FIX_REPORT.md`, `PHASE20_28_LOCATION_FIX_REPORT.md`, `PHASE20_28_RELEASE_REPORT.md`

**Note:** `releases/RELEASES.md` was left in place — it belongs to the protected `releases/` tree and was not moved.

---

## 3. Deleted Files (44)

All deleted items are **clearly generated / regenerable**. Exact copies with SHA-256 hashes are preserved in `cleanup_backup_phase20_29/deleted/` (see `backup_manifest.md`).

### 3.1 Temporary generated scripts & data (30) — `tmp_*` prefix, one-off dev scripts

`tmp_add_countries.py`, `tmp_add_countries2.py`, `tmp_add_validation.py`, `tmp_countries.py`,
`tmp_css.py`, `tmp_css_combobox.py`, `tmp_css_improve.py`, `tmp_css_topbar.py`,
`tmp_dom_check.py`, `tmp_fetch.json`, `tmp_fix_init.py`, `tmp_fix_mode.py`, `tmp_fix_mode2.py`,
`tmp_html_combobox.py`, `tmp_insert.py`, `tmp_open_country.py`, `tmp_replace_combobox_ui.py`,
`tmp_replace_init_ui.py`, `tmp_replace_location.py`, `tmp_replace_ui.py`, `tmp_res.json`,
`tmp_revert_topbar.py`, `tmp_save.json`, `tmp_save_utf8.txt`, `tmp_structure.py`,
`tmp_sync_fill.py`, `tmp_sync2.py`, `tmp_update_css.py`, `tmp_update_html.py`,
`tmp_update_init21.py`

**Safety check:** the only `tmp_` occurrence in the build system is the variable name `tmp_ret` in `PrayerMusicGuard.spec:42-43`. **No `tmp_*` file is referenced** by `main.py`, `webview_app/*`, any `.spec`, `build_exe.bat`, or `release.ps1`.

### 3.2 Stale test-run outputs (4)

`run_output.txt`, `run_output2.txt`, `run_output3.txt`, `run_output_test.txt`
(content: a stale `SyntaxError` traceback from 2026-09-15, long since fixed).

### 3.3 Python bytecode caches (10) — fully regenerable

- `__pycache__/` — `main.cpython-314.pyc`, `main.cpython-38.pyc`, `uiverse_combobox.cpython-314.pyc`, `uiverse_combobox.cpython-38.pyc`
- `webview_app/__pycache__/` — `backend_api.cpython-314.pyc`, `backend_api.cpython-38.pyc`, `launcher.cpython-314.pyc`, `launcher.cpython-38.pyc`, `platform_check.cpython-38.pyc`, `webview_main.cpython-38.pyc`

`vendor/__pycache__` and the `win7/` Python/venv caches were **left untouched** (inside protected trees).

---

## 4. Protected Files (verified unchanged)

Pre-cleanup SHA-256 hashes were captured for 26 critical files and **re-verified after cleanup: 26/26 match**.

### 4.1 Source code (untouched, syntax verified)
`main.py`, `uiverse_combobox.py` (required: imported by `main.py:24` and bundled in `PrayerMusicGuard.spec:17,39`),
`webview_app/app_entry.py`, `webview_app/backend_api.py`, `webview_app/launcher.py`,
`webview_app/platform_check.py`, `webview_app/webview_main.py`, `webview_app/splash.html`,
`webview_app/frontend/index.html`, `webview_app/frontend/css/{components,layout,skins,theme}.css`,
`webview_app/frontend/js/{app,theme}.js`

### 4.2 Build / config / packaging (untouched)
`PrayerMusicGuard.spec`, `PrayerMusicGuard-FIXES-TEST.spec`, `PrayerMusicGuard-SPLASH-WARNING.spec`,
`PrayerMusicGuard.iss`, `build_exe.bat`, `release.ps1`, `requirements.txt`, `requirements-win7.txt`,
`VERSION`, `README.md`, `.gitignore`, `opencode.json`, `تشغيل-صلاة-وسكون.bat` (launcher)

### 4.3 Protected directories (untouched — file counts verified identical pre/post)
`webview_app/` source tree, `assets/` (14), `.opencode/`, `vendor/` (1964), `win7/` (5965),
`build/` (20), `build-win7-test/` (20), `dist/` (26539), `releases/` (15), `backup/` (7367)

### 4.4 Backup files & test scripts (retained in place, not deleted)
- Source backups: `_backup_phase18.py`, `main_backup_before_real_redesign_2026-09-16.py`, `main_backup_before_ui_redesign.py`, `main_before_actual_ui_redesign.py`, `main_before_encoding_repair.py`, `main_before_final_ui_redesign.py`, `main_before_major_redesign.py`, `main_before_real_redesign.py`, `main_before_real_redesign_v2.py`, `main_before_top_navigation_redesign.py`, `main_before_true_ui_redesign.py`, `main_test.py`
- Config backups: `opencode.json.bak`, `webview_app/backend_api.py.bak`, `webview_app/webview_main.py.bak`, `webview_app/frontend/js/app.js.bak`
- Test / diagnostic / QA scripts: `test_all.py`, `test_details.py`, `test_import.py`, `test_meta.py`, `test_nvidia.py`, `test_phase20_11.py`, `test_phase20_12.py`, `test_phase20_13.py`, `test_phase20_28.py`, `test_phase20_28_frontend.js`, `test_reflow.py`, `two_model_test.py`, `diagnose.py`, `diagnose2.py`, `qa_phase20_28_runtime.py`, `uat_phase20_28_release.py`, `webview_app/test_webview.py`, `_installer_test.ps1`, `_mei_test.ps1`, `_single_instance_test*.ps1`, `_startup_test.ps1`

These are **not** clearly generated/regenerable and were deliberately left in place.

---

## 5. Suspicious External Files (E:\ root) — LISTED ONLY, NOT TOUCHED

No file outside `E:\prayer-music-guard\` was deleted, moved, or modified. Project-related files detected in `E:\` are listed below for awareness:

### 5.1 Project snapshot archive
| File | Size | Date |
|---|---|---|
| `E:\prayer-music-guard.zip` | 183,713,425 (~175 MB) | 2026-09-15 |

### 5.2 Project-generated launch/run logs (17) — from manual launch testing on 2026-09-15/16
`launch_test.log` (0 B), `launch_test2.log` (0 B), `launch_test3.log` (0 B), `launch2.log` (0 B),
`launch_final.log` (1,399 B), `launch_final2.log` (0 B), `launch_final_check.log` (0 B),
`launch_review.log` (0 B), `launch_v3.log` (0 B), `launch_v4.log` (0 B),
`prayer_run.log` (184 B), `prayer_run2.log` (184 B), `prayer_run3.log` (184 B),
`prayer_run_final.log` (0 B), `test_run.log` (184 B), `test_run2.log` (184 B)

### 5.3 Project-generated temp scripts (26) — encoding/CRLF/PIL debugging, 2026-09-15
`tmp_clean.py` (164,567 B — full cleaned copy of `main.py`), `tmp_nopil.py` (167,321 B — `main.py` variant),
`tmp_small.py`, `tmp_small2.py`, `tmp_small3.py`, `tmp_small200.py`, `tmp_diff.py`, `tmp_path.py`,
`tmp_check_accent.py`, `tmp_check_encoding.py`, `tmp_check_pil.py`, `tmp_check_version.py`,
`tmp_ascii_crlf.py`, `tmp_lf_test.py`, `tmp_make_lf.py`, `tmp_test_crlf.py`, `tmp_test2.py`,
`test_scope.py`, plus outputs `tmp_diff.txt`, `tmp_err.txt`, `tmp_clean_out.txt`,
`tmp_nopil_out.txt`, `tmp_small_out.txt`, `tmp_small2_out.txt`, `tmp_small3_out.txt`, `tmp_small200_out.txt`

**Recommendation:** these are safe to remove after confirmation, but per instructions they were only inventoried. Unrelated `E:\` items (ISOs, `CV`, `Disk Drill`, `$RECYCLE.BIN`, `System Volume Information`, Arabic-named folders, etc.) were left alone.

---

## 6. Pre-Cleanup Backup & Manifest

```
cleanup_backup_phase20_29/
├── backup_manifest.md          # full file list + sizes + SHA-256 + restore instructions
└── deleted/                    # exact copies of all 44 deleted files
    ├── __pycache__/            # 4 .pyc
    ├── run_output*.txt         # 4
    ├── tmp_*                   # 30
    └── webview_app/__pycache__/ # 6 .pyc
```

Moved reports are recoverable by relocation (old→new paths documented in the manifest). The `backup/` protected tree was **not** written to.

---

## 7. Final Project Structure

```
E:\prayer-music-guard\
├── .gitignore
├── .opencode/                        [PROTECTED]
├── assets/                           [PROTECTED]  audio/ data/ icons/ images/
├── backup/                           [PROTECTED]  33 phase-backup snapshots
├── build/                            [PROTECTED]  PyInstaller onedir work
├── build-win7-test/                  [PROTECTED]  Win7 test build
├── build_exe.bat                     [PROTECTED]
├── cleanup_backup_phase20_29/        [NEW] pre-cleanup backup + manifest
├── diagnose.py, diagnose2.py         [retained]
├── dist/                             [PROTECTED]  26 onedir builds + installers
├── main.py                           [PROTECTED — source]
├── main_backup_*.py / main_before_*.py / main_test.py / _backup_phase18.py  [retained backups]
├── opencode.json (+ .bak)
├── PrayerMusicGuard.spec / -FIXES-TEST.spec / -SPLASH-WARNING.spec / .iss   [PROTECTED]
├── qa_phase20_28_runtime.py, uat_phase20_28_release.py                     [retained]
├── README.md                         [PROTECTED — kept at root]
├── release.ps1                       [PROTECTED]
├── releases/                         [PROTECTED]  v1.2.5 / v1.2.6 / v1.2.7 + RELEASES.md
├── reports/                          [NEW]
│   ├── cleanup/                      # this report + future cleanup reports
│   ├── phases/                       # 28 phase reports
│   └── qa/                           # 9 QA/UAT reports
├── requirements.txt, requirements-win7.txt                                  [PROTECTED]
├── test_*.py, test_phase20_28_frontend.js, two_model_test.py                [retained]
├── uiverse_combobox.py               [PROTECTED — imported by main.py]
├── VERSION                           [PROTECTED]
├── vendor/                           [PROTECTED]
├── webview_app/                      [PROTECTED — source + frontend/]
├── win7/                             [PROTECTED]  python 3.8 + venv
└── تشغيل-صلاة-وسكون.bat              [PROTECTED — launcher]
```

---

## 8. Verification Results

| Check | Result |
|---|---|
| Protected file SHA-256 hashes (26 files) | **26/26 identical** |
| `dist/`, `releases/`, `backup/`, `build/`, `build-win7-test/`, `vendor/`, `win7/`, `assets/`, `webview_app/frontend/` file counts | **all identical** to pre-cleanup baseline |
| `webview_app/` count 23 → 17 | delta = exactly the 6 removed `.pyc` caches; all source files hash-verified unchanged |
| Python syntax (`py_compile`): `main.py`, `uiverse_combobox.py`, all 5 `webview_app/*.py` | **7/7 OK, 0 errors** |
| JS syntax (`node --check`): `app.js`, `theme.js` | **2/2 OK** |
| Required files present (`main.py`, `VERSION`, `README.md`, specs, requirements, `webview_app/`, `assets/`) | **all present** |
| Reports relocated | **37/37** (28 phases + 9 qa); only `README.md` remains at root |
| Temp files removed | 44 deleted (30 tmp_* + 4 run_output* + 10 .pyc); 0 remaining |
| No source / UI / logic / config / build-system modification | **confirmed** |

---

## 9. Result

### **PASS**

- 37 reports organized into `reports/phases/` and `reports/qa/`.
- 44 clearly-generated files removed (backed up first with SHA-256 manifest).
- All protected files, directories, and release/build artifacts byte-identical to pre-cleanup state.
- Python and JS syntax verified unchanged.
- Zero changes to source code, UI, logic, configuration, or build system.

**No build performed. No code changes. Stopping after report, as instructed.**
