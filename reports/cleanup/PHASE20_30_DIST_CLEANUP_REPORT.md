# PHASE 20.30 — Dist Cleanup Report

**Project:** `E:\prayer-music-guard`
**Date:** 2026-09-20
**Phase:** 20.30 — Dist Cleanup (follows Phase 20.29B, which PASSED)
**Mode:** Verify existing pre-deletion backup → delete proven-obsolete `dist` builds/files only → verify + manifest. No code changes, no build.

---

## 0. Resumption Note — Work Recovered, Not Repeated

The previous session was interrupted ("Service Temporarily Unavailable") mid-phase. State on resumption was inspected before any action:

| Step | State at resumption | Action taken |
|---|---|---|
| Pre-deletion backup | **COMPLETE** — `cleanup_backup_phase20_30\deleted\` held all 25 obsolete folders + 8 obsolete root files (25,507 files) | **Reused as-is.** No second backup created, no duplication |
| Deletion from `dist` | **NOT STARTED** — `dist` still contained all 26 folders + 8 root files | **Executed once**, from a guard-checked target list |
| Manifests / report | Not created | Created (this file + 2 manifests) |

No step was repeated and no file was processed twice. The backup was treated as read-only ground truth: the deletion work-list was **derived from the backup**, so by construction nothing could be deleted that was not already backed up.

---

## 1. Summary of Actions

| Action | Count | Detail |
|---|---|---|
| Obsolete `dist` folders DELETED | 25 | Phase 18/20.1–20.27 superseded builds + root `PrayerMusicGuard\` onedir build |
| Obsolete `dist` root files DELETED | 8 | 7 stray `.exe` builds + `build_log.txt` |
| **Total files deleted** | **25,507** | **881.98 MB** (882 MB) freed from `dist` |
| Pre-deletion backup (pre-existing) | 25,507 files / 882 MB | `cleanup_backup_phase20_30\deleted\{folders,root_files}\` — **verified before deleting** |
| Release build KEPT | 1 folder, 1,032 files, 31.38 MB | `dist\Phase20-28-Release` — the latest valid release |
| SHA-256 manifest created | 1,032 entries | `Phase20-28-Release_SHA256_manifest.md` |
| Deleted-items manifest created | 25,507 rows | `deleted_items_manifest.txt` |
| Source / release / backup / build files affected | **0** | 11 protected dir trees byte-identical; 9 protected file hashes identical |

---

## 2. Pre-Deletion Backup Verification (gate before any deletion)

Deletion was gated on the backup proving complete and content-faithful. Four independent checks, all run against the live `dist` before anything was removed:

| Check | Result |
|---|---|
| Name-set parity — every deletable `dist` file present in backup | **25,507 / 25,507** (0 missing) |
| Name-set parity — no orphan backup entries with no source counterpart | **0 orphans** |
| Size parity — every paired file byte-for-byte identical size | **25,507 / 25,507** (0 mismatches) |
| Content parity — SHA-256 spot-check of largest/most significant files | **5 / 5 MATCH** |
| Protected release absent from backup (must not be deletable) | **0 entries** — `Phase20-28-Release` correctly never backed up |

SHA-256 spot-checks (src vs backup, all **MATCH**):

| File | Size | SHA-256 |
|---|---|---|
| `PrayerMusicGuard.exe` | 16,446,064 | `AA0604C539A704746A4148EB84A957585A6A1ACF9EFBA4F803D0D28BE481BFDC` |
| `PrayerMusicGuard-Setup.exe` | 18,239,729 | `70574567A33435DF260D5AD2D7A1569569E36C4AFBB0EE8C5B0E7772896636BC` |
| `build_log.txt` | 288 | `28F1A96A0C01415FBEB55372F5EB93F03535562CA0E7DD6D1E9B686079733529` |
| `Phase20-27-Release-UAT\PrayerMusicGuard\PrayerMusicGuard.exe` | — | `3B49918FB8261B2C62D7EBDDC8AD652B660CBF03F7BD9E1C0655E1ED20B550CF` |
| `Phase18-OneDir-Test\PrayerMusicGuard\main.py` | — | matched backup copy |

Backup layout (unchanged from the interrupted session):

```
cleanup_backup_phase20_30/
├── deleted/
│   ├── folders/      # 25 obsolete dist folders, full recursive copies (25,499 files)
│   └── root_files/   # 8 obsolete dist root files (7 .exe + build_log.txt)
├── Phase20-28-Release_SHA256_manifest.md   # [NEW] 1,032-entry manifest of the KEPT release
├── deleted_items_manifest.txt              # [NEW] 25,507-row manifest of everything deleted
├── _baseline_dirs.csv                      # [NEW] pre-cleanup protected-dir baseline
├── _baseline_files.csv                     # [NEW] pre-cleanup protected-file hashes
├── _deletion_targets.csv                   # [NEW] guard-approved work-list (33 items)
└── _deletion_results.csv                   # [NEW] per-item outcome (33/33 deleted)
```

Everything deleted in this phase is recoverable verbatim from `cleanup_backup_phase20_30\deleted\`.

---

## 3. Deletion Safety Guard

Rather than deleting "everything in `dist` except the release", the work-list was **derived from the verified backup** and guard-checked:

- Each of the 25 backup `folders\` entries mapped to an existing `dist` folder → 25 targets
- Each of the 8 backup `root_files\` entries mapped to an existing `dist` file → 8 targets
- **Guard rule:** any backup entry named `Phase20-28-Release` would have aborted the run. **0 guard failures.**
- Keeper confirmed present before deletion, and the deletion set explicitly excluded it.

**Result: 33 / 33 targets deleted successfully, 0 failures, 0 retries.**

---

## 4. Deleted Items (33)

### 4.1 Obsolete build folders (25)

Superseded intermediate PyInstaller builds from Phase 18 and Phases 20.1–20.27. Each is a near-identical ~31 MB onedir tree of the *same* application, made obsolete by `Phase20-28-Release`.

| Folder | Files | MB |
|---|---|---|
| `Phase18-OneDir-Test` | 1,023 | 31.05 |
| `Phase20-1-Splash-Dropdown-Fix` | 1,023 | 31.05 |
| `Phase20-2-Splash-Fix` | 1,023 | 31.05 |
| `Phase20-3-Splash-Deep-Fix` | 1,023 | 31.05 |
| `Phase20-4-HTML-CSS-Splash` | 1,023 | 31.05 |
| `Phase20-5-HTML-CSS-Splash-Fix` | 1,024 | 31.05 |
| `Phase20-6-Splash-WhiteScreen-Fix` | 1,024 | 31.05 |
| `Phase20-7-Splash-Scope-Fix` | 1,024 | 31.05 |
| `Phase20-8-Splash-Timing` | 1,024 | 31.05 |
| `Phase20-11-Music-Control-Fix` | 1,024 | 31.05 |
| `Phase20-12-Music-Control-UI-12H` | 1,024 | 31.05 |
| `Phase20-13-UI-Countdown-12H-Location` | 1,024 | 31.06 |
| `Phase20-14-Countdown-Location` | 1,024 | 31.06 |
| `Phase20-15-Location-Countdown` | 1,024 | 31.07 |
| `Phase20-16-Worldwide-Location-Countdown` | 1,024 | 31.07 |
| `Phase20-17-Final-Location-UI-Countdown` | 1,024 | 31.07 |
| `Phase20-18-Location-Mode-Countdown-Direction` | 1,024 | 31.07 |
| `Phase20-19-Location-Dropdown-Rebuild` | 1,024 | 31.08 |
| `Phase20-20-Location-Combobox-Final` | 1,024 | 31.08 |
| `Phase20-21-Location-State-Fix` | 1,024 | 31.08 |
| `Phase20-22-Location-Combobox-Uiverse` | 970 | 28.71 |
| `Phase20-23-UI-Regression-Fix` | 1,028 | 31.19 |
| `Phase20-24-Location-Data-Fix` | 1,028 | 31.19 |
| `Phase20-27-Release-UAT` | 1,028 | 31.21 |
| `PrayerMusicGuard` (root onedir build) | 970 | 28.71 |

### 4.2 Obsolete root-level executables / log (8)

Stray one-file builds and a stale build log left directly in `dist\`. None is the shipped release: the canonical release is the onedir tree in `Phase20-28-Release`, and the surviving installer lives in `releases\`.

| File | Size | SHA-256 |
|---|---|---|
| `PrayerMusicGuard.exe` | 16,446,064 | `AA0604C539A704746A4148EB84A957585A6A1ACF9EFBA4F803D0D28BE481BFDC` |
| `PrayerMusicGuard-Setup.exe` | 18,239,729 | `70574567A33435DF260D5AD2D7A1569569E36C4AFBB0EE8C5B0E7772896636BC` |
| `PrayerMusicGuard_v1.2.7_old.exe` | 16,416,372 | in manifest |
| `PrayerMusicGuard-v1.2.7-FIXES-TEST.exe` | 16,446,061 | in manifest |
| `PrayerMusicGuard-v1.2.7-new.exe` | 16,446,004 | in manifest |
| `PrayerMusicGuard-v1.2.7-ONEDIR-TEST.exe` | 14,621,163 | in manifest |
| `PrayerMusicGuard-v1.2.7-SPLASH-WARNING-FIX.exe` | 16,461,108 | in manifest |
| `build_log.txt` | 288 | `28F1A96A0C01415FBEB55372F5EB93F03535562CA0E7DD6D1E9B686079733529` |

---

## 5. KEPT — `dist\Phase20-28-Release` (integrity verified)

The single retained build: the Phase 20.28 release, a complete PyInstaller **onedir** tree.

```
dist\Phase20-28-Release\PrayerMusicGuard\   1,032 files, 31.383 MB
├── PrayerMusicGuard.exe      4,253,142 B   (entry-point bootloader)
├── main.py                     181,764 B   (bundled app source)
├── uiverse_combobox.py          33,753 B
├── python38.dll               4,211,376 B
├── *.pyd / base_library.zip / *.dll        (CPython runtime)
├── tcl\ tcl8\ tk\                          (Tk runtime, 917 files)
├── webview\ webview_app\ assets\           (UI + 14 assets, 3.19 MB)
├── pystray\ pythonnet\ clr_loader\ PIL\    (tray icon, .NET bridge, imaging)
└── importlib_metadata-8.5.0.dist-info\
```

| Check | Result |
|---|---|
| File count vs pre-cleanup baseline | **1,032 / 1,032** — identical |
| Total size vs pre-cleanup baseline | **31.383 / 31.383 MB** — identical |
| Manifest rows cross-checked back against `dist` (path exists + size matches) | **1,032 / 1,032, 0 mismatches** |
| Entry-point exe present | **YES** — `PrayerMusicGuard\PrayerMusicGuard.exe` (4,253,142 B) |
| Bundled `main.py` hash vs active source `main.py` | **IDENTICAL** — `6E998725B1E41D52B98B353D42E2B8CF0BCB675C95999E2EA1D1DD3CF7397AAB` |

Key release hashes (full list in the manifest):

| File | SHA-256 |
|---|---|
| `PrayerMusicGuard\PrayerMusicGuard.exe` | `6D2E434F673948C684C66D91FE6249D998074825D2B31E3C7A1DADB7D64ACB18` |
| `PrayerMusicGuard\main.py` | `6E998725B1E41D52B98B353D42E2B8CF0BCB675C95999E2EA1D1DD3CF7397AAB` |
| `PrayerMusicGuard\python38.dll` | `2F3E368F5BCC1DDA5E951682008A509751E6395F7328FD0F02C4E1A11F67C128` |

---

## 6. Verification — Nothing Outside the Target Set Was Touched

Baselines were captured **before** deletion and re-compared **after**.

### 6.1 Protected directory trees (11)

| Directory | Files | MB | Before == After |
|---|---|---|---|
| `dist\Phase20-28-Release` | 1,032 | 31.383 | **IDENTICAL** |
| `releases` | 15 | 87.96 | **IDENTICAL** |
| `backup` | 7,367 | 137.33 | **IDENTICAL** |
| `build` | 20 | 14.15 | **IDENTICAL** |
| `build-win7-test` | 20 | 29.00 | **IDENTICAL** |
| `vendor` | 1,964 | 23.48 | **IDENTICAL** |
| `win7` | 5,965 | 85.58 | **IDENTICAL** |
| `assets` | 14 | 3.19 | **IDENTICAL** |
| `webview_app` | 17 | 0.23 | **IDENTICAL** |
| `reports` | 39 | 0.25 | **IDENTICAL** (now 40 incl. this report) |
| `.opencode` | 3,771 | 56.21 | **IDENTICAL** |

### 6.2 Protected source / config files (9)

All SHA-256 hashes identical pre- vs post-cleanup: `main.py`, `uiverse_combobox.py`, `VERSION`, `README.md`, `PrayerMusicGuard.spec`, `build_exe.bat`, `release.ps1`, `requirements.txt`, `.gitignore`.

### 6.3 Final `dist` state

```
E:\prayer-music-guard\dist\
└── Phase20-28-Release/        # the ONLY remaining dist build
    └── PrayerMusicGuard/      1,032 files, 31.383 MB
```

- Residual obsolete items in `dist`: **0**
- `E:\` free space: **104.65 GB → 105.54 GB** (≈0.9 GB recovered — consistent with on-disk dedup of near-identical builds)

---

## 7. Result

### **PASS**

- Backup from the interrupted session was **verified complete** (25,507 / 25,507 name + size parity, 5 / 5 hash spot-checks) **before** any deletion, then **reused — not duplicated**.
- 33 obsolete `dist` items (25 superseded build folders + 8 stray root files) deleted: **25,507 files, 881.98 MB** removed.
- `dist` now contains exactly one build: **`Phase20-28-Release`**, verified intact (1,032 files, 31.383 MB, unchanged from baseline).
- SHA-256 manifest created for the kept release (1,032 entries, round-trip verified 0 mismatches); deleted-items manifest created (25,507 rows) — every deletion is recoverable verbatim.
- 11 / 11 protected directory trees byte-identical and 9 / 9 protected file hashes identical: **no source, release, backup, or build files affected**.
- All 33 deletions completed in a single pass; 0 failures, 0 retries, no duplicate processing.

**No code changes. No build performed. Stopping after report, as instructed.**
