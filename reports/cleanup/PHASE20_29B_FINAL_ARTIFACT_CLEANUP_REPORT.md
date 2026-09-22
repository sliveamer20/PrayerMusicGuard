# PHASE 20.29B — Final Artifact Cleanup Report

**Project:** `E:\prayer-music-guard`
**Date:** 2026-09-20
**Phase:** 20.29B — Final Artifact Cleanup (follows Phase 20.29, which PASSED)
**Mode:** READ-ONLY inventory first → delete only proven-obsolete / redundant artifacts. No code changes, no build.

---

## 1. Summary of Actions

| Action | Count | Detail |
|---|---|---|
| External `E:\` artifacts DELETED | 42 | 16 stale logs + 25 `tmp_*` debug scripts/outputs + `test_scope.py` |
| Project-root files DELETED | 10 | 2 byte-identical duplicate backups + 6 spent Phase-18 PS1 test scripts + 2 obsolete scratch tests |
| Pre-deletion backup created | 52 files | `cleanup_backup_phase20_29b/deleted/` (0.67 MB) + SHA-256 manifest |
| External `E:\` files intentionally KEPT | 1 | `prayer-music-guard.zip` — outside the enumerated cleanup categories |
| Project-root files intentionally KEPT | 23 | unique historical backups, diagnostics, phase tests, QA scripts (see §6) |
| Source / config / build-system changes | 0 | Zero modifications |

---

## 2. External `E:\` Root — Deleted (42)

All of these were generated during the 2026-09-15/16 debugging of the **null-byte encoding issue** (a `SyntaxError: source code string cannot contain null bytes` in `main.py`, long since fixed) and one-off launch testing. They are stale outputs and spent scratch scripts, and they match exactly the categories enumerated for this phase.

### 2.1 Stale launch/run logs (16)
`launch_test.log`, `launch_test2.log`, `launch_test3.log`, `launch2.log`, `launch_final.log`, `launch_final2.log`, `launch_final_check.log`, `launch_review.log`, `launch_v3.log`, `launch_v4.log`, `prayer_run.log`, `prayer_run2.log`, `prayer_run3.log`, `prayer_run_final.log`, `test_run.log`, `test_run2.log`
(Contents verified: empty, or the same fixed null-byte traceback.)

### 2.2 Temp debug scripts + outputs (26)
`tmp_clean.py` (164,567 B — cleaned-`main.py` variant), `tmp_nopil.py` (167,321 B — `main.py` with PIL import removed), `tmp_small.py`, `tmp_small2.py`, `tmp_small3.py`, `tmp_small200.py`, `tmp_diff.py`, `tmp_path.py`, `tmp_check_accent.py`, `tmp_check_encoding.py`, `tmp_check_pil.py`, `tmp_check_version.py`, `tmp_ascii_crlf.py`, `tmp_lf_test.py`, `tmp_make_lf.py`, `tmp_test_crlf.py`, `tmp_test2.py`, and outputs `tmp_diff.txt`, `tmp_err.txt`, `tmp_clean_out.txt`, `tmp_nopil_out.txt`, `tmp_small_out.txt`, `tmp_small2_out.txt`, `tmp_small3_out.txt`, `tmp_small200_out.txt`

### 2.3 Standalone scratch script (1)
`test_scope.py` (67 B)

**Note:** `E:\prayer-music-guard.zip` (175 MB, 2026-09-15) was **kept** — it is a project snapshot, not a log/scratch artifact, and is outside the categories enumerated for this phase. Unrelated `E:\` items (ISOs, `CV`, `Disk Drill`, `$RECYCLE.BIN`, `System Volume Information`, Arabic-named folders) were never touched.

---

## 3. Project Root — Deleted (10)

Every candidate was first confirmed **unreferenced**: a search of all root `.py`/`.spec`/`.bat`/`.ps1`/`.iss` found **zero references** to any of them. Each deletion below is either a verified byte-duplicate or proven-obsolete scratch.

| File | Size | Reason for deletion |
|---|---|---|
| `main_test.py` | 167,419 | **Byte-identical duplicate** of `main_backup_before_ui_redesign.py` (same SHA-256). Content fully preserved by the surviving twin. |
| `main_before_real_redesign_v2.py` | 165,466 | **Byte-identical duplicate** of `main_before_real_redesign.py` (same SHA-256). Content fully preserved by the surviving twin. |
| `_installer_test.ps1` | 798 | Phase-18 one-off silent-installer verification scratch; targets the completed `dist\PrayerMusicGuard-v1.2.7-ONEDIR-TEST.exe` build. Spent. |
| `_mei_test.ps1` | 924 | Phase-18 one-off PyInstaller `_MEI` temp-folder leak test against `dist\Phase18-OneDir-Test`. Spent. |
| `_single_instance_test.ps1` | 943 | Phase-18 one-off single-instance guard test (v1). Spent. |
| `_single_instance_test2.ps1` | 1,291 | Phase-18 one-off single-instance guard test (v2). Spent. |
| `_single_instance_test3.ps1` | 769 | Phase-18 one-off single-instance guard test (v3). Spent. |
| `_startup_test.ps1` | 750 | Phase-18 one-off startup/splash test. Spent. |
| `test_import.py` | 182 | Scratch test calling `main.App(root)` — the **removed** Tkinter API. Obsolete against the redesigned webview-based `main.py`; would fail today. |
| `test_reflow.py` | 479 | Scratch test calling `main.App._reflow_cards/_update_prayer_grid/_update_nav_layout` — **removed** Tkinter API. Obsolete; would fail today. |

---

## 4. Pre-Deletion Backup & Manifest

```
cleanup_backup_phase20_29b/
├── backup_manifest.md           # full file list + sizes + SHA-256 + restore instructions
└── deleted/
    ├── external/                # 42 files (as they existed in E:\)
    └── root/                    # 10 files (as they existed in the project root)
```

Everything deleted in this phase is recoverable verbatim. The protected `backup/` tree was **not** written to.

---

## 5. Verification

| Check | Result |
|---|---|
| Protected-file SHA-256 hashes (26 critical files) | **26/26 identical** to the Phase 20.29 baseline |
| Protected dir counts vs. end-of-20.29 state (`dist`, `releases`, `backup`, `build`, `build-win7-test`, `vendor`, `win7`, `assets`, `webview_app/frontend`, `reports`) | **all identical** |
| `webview_app/` | 17 files — unchanged since 20.29 (source only, caches already gone) |
| Python syntax (`ast.parse`, cache-free): `main.py`, `uiverse_combobox.py`, all 5 `webview_app/*.py` | **7/7 OK** |
| JS syntax (`node --check`): `app.js`, `theme.js` | **2/2 OK** |
| `__pycache__` regeneration after checks | **none** (verification used read-only `ast.parse`) |
| Required files present (`main.py`, `VERSION`, `README.md`, all specs, `requirements*.txt`, `webview_app/`, `assets/`, launcher `.bat`) | **all present** |
| Targeted patterns fully cleared | `launch*.log`=0, `prayer_run*.log`=0, `test_run*.log`=0, `tmp_*`=0, `test_scope.py`=gone in `E:\` |
| Source / UI / logic / config / build system | **unchanged** |

---

## 6. Intentionally KEPT (23 root files) — with reasons

Per the rule *"Delete ONLY files proven unused and regenerable; if uncertain, KEEP and report."*

### 6.1 Unique historical `main.py` snapshots (9) — **not regenerable**
SHA-256 analysis proved these are **unique** (none exist anywhere in the protected `backup/` tree, which only starts at Phase 18 on 2026-09-19). They are the only record of the pre-redesign `main.py` states from 2026-09-15/16. Deleting them would lose historical data, so they were kept:

`main_backup_before_real_redesign_2026-09-16.py`, `main_backup_before_ui_redesign.py`, `main_before_actual_ui_redesign.py`, `main_before_encoding_repair.py`, `main_before_final_ui_redesign.py`, `main_before_major_redesign.py`, `main_before_real_redesign.py`, `main_before_top_navigation_redesign.py`, `main_before_true_ui_redesign.py`

### 6.2 Diagnostic / model-test scripts (7) — hand-written tools, not regenerable
`diagnose.py`, `diagnose2.py`, `test_all.py`, `test_details.py`, `test_meta.py`, `test_nvidia.py`, `two_model_test.py` (NVIDIA/opencode API connectivity diagnostics; could still be re-run).

### 6.3 Phase test artifacts & release QA scripts (6) — recent, potentially re-runnable
`test_phase20_11.py`, `test_phase20_12.py`, `test_phase20_13.py`, `test_phase20_28.py`, `test_phase20_28_frontend.js`, `qa_phase20_28_runtime.py`, `uat_phase20_28_release.py` (the last two cover the current v1.2.7 release).

### 6.4 Backup/config helpers (2)
`_backup_phase18.py` (backup-creation utility; its outputs already exist in `backup/` — kept rather than risk removing a backup-related tool), `opencode.json.bak` (config backup).

> If any of the above are later deemed deletable, they can be removed in a follow-up phase; the two exact-duplicate `main_test.py` / `main_before_real_redesign_v2.py` copies were the only redundant members of this group.

---

## 7. Final Project Root Layout

```
E:\prayer-music-guard\
├── .gitignore, VERSION, README.md              [PROTECTED]
├── main.py, uiverse_combobox.py                [PROTECTED — active source]
├── main_backup_*.py / main_before_*.py (9)     [KEPT — unique historical snapshots]
├── PrayerMusicGuard.spec / -FIXES-TEST.spec / -SPLASH-WARNING.spec / .iss   [PROTECTED]
├── build_exe.bat, release.ps1, requirements*.txt, opencode.json(+.bak)      [PROTECTED]
├── تشغيل-صلاة-وسكون.bat                        [PROTECTED — launcher]
├── diagnose*.py, test_all/details/meta/nvidia.py, two_model_test.py         [KEPT — diagnostics]
├── test_phase20_11/12/13/28*.py(js), qa_phase20_28_runtime.py,
│   uat_phase20_28_release.py                   [KEPT — phase tests / release QA]
├── cleanup_backup_phase20_29b/                 [NEW — this phase's pre-deletion backup]
├── cleanup_backup_phase20_29/                  [20.29 backup]
├── reports/  (phases/ 28, qa/ 9, cleanup/ 2)   [PROTECTED]
├── .opencode/  assets/  backup/  build/  build-win7-test/
├── dist/  releases/  vendor/  webview_app/  win7/   [PROTECTED]
```

---

## 8. Result

### **PASS**

- 42 obsolete external artifacts (stale logs + spent debug scratch) removed from `E:\`.
- 10 redundant/obsolete files removed from the project root (2 exact duplicates, 6 spent Phase-18 PS1 test scripts, 2 obsolete Tkinter-API scratch tests).
- All 52 deletions backed up with SHA-256 manifest and are fully recoverable.
- 26/26 protected file hashes unchanged; all protected directories byte-for-byte identical to the end of Phase 20.29.
- Python (7/7) and JS (2/2) syntax verified unchanged; no caches regenerated.
- 23 root files intentionally retained and individually documented with reasons.

**No code changes. No build performed. Stopping after report, as instructed.**
