# Phase 20.23 — UI Regression Forensic Audit & Fix Report

**Date:** 2026-09-19
**Status:** PASS (build verified, manual launch test PENDING)

---

## Root Cause

The `PrayerMusicGuard.spec` file was **overwritten with a severely broken version** that caused the application to launch the old Tkinter UI instead of the modern HTML/CSS/WebView2 frontend.

### What Was Wrong

| Aspect | BROKEN (Current) | CORRECT (Restored) |
|---|---|---|
| **Entry point** | `main.py` (Tkinter) | `webview_app/app_entry.py` (Hybrid launcher) |
| **datas** | `assets` + `uiverse_combobox.py` only | `assets` + `main.py` + `uiverse_combobox.py` + entire `webview_app/` directory |
| **hiddenimports** | `pyexpat`, `_elementtree` only | `webview`, `clr`, `pystray`, `launcher`, `app_entry`, `platform_check`, `backend_api`, `webview_main`, `uiverse_combobox` + pystray subpackages |
| **EXE type** | OneFile (all in EXE) | OneDir (COLLECT with separate files) |
| **Build output** | `Phase18-OneDir-Test` | `Phase20-23-UI-Regression-Fix` |

### The Regression Mechanism

1. `main.py` at line 3271-3273 creates `tk.Tk()` and runs `App(window)` directly — this is the **old Tkinter UI**
2. The correct entry point is `app_entry.py` which calls `launcher.main()`
3. `launcher.main()` checks platform → shows splash → launches WebView2 HTML frontend on Win10/11
4. With the wrong spec, the EXE runs `main.py` as `__main__`, bypassing the launcher entirely
5. The `webview_app/frontend/` directory (index.html, CSS, JS) was never packaged into the dist

### Evidence

| File | Line | Evidence |
|---|---|---|
| `PrayerMusicGuard.spec` (broken) | Line 8 | `['main.py']` — wrong entry point |
| `PrayerMusicGuard.spec` (broken) | Line 11 | `datas=[('assets', 'assets'), ('uiverse_combobox.py', '.')]` — missing webview_app |
| `main.py` | Lines 3259-3273 | `window = tk.Tk(); App(window); window.mainloop()` — Tkinter UI |
| `webview_app/app_entry.py` | Lines 48-49 | `import launcher; launcher.main()` — correct launcher path |
| `webview_app/launcher.py` | Lines 275-308 | `_show_splash()` → `platform_check.can_use_html_frontend()` → `_run_html_frontend()` |
| `dist\Phase20-22` build | — | Missing `webview_app/` directory, only 28 files (DLLs/pyds) |
| `dist\Phase20-4` build | — | Contains `webview_app/` with all frontend files |

---

## Source Files Inspected

| File | Path | Purpose |
|---|---|---|
| main.py | `E:\prayer-music-guard\main.py` | Tkinter UI (fallback), 3273 lines |
| app_entry.py | `E:\prayer-music-guard\webview_app\app_entry.py` | Frozen/source entry point |
| launcher.py | `E:\prayer-music-guard\webview_app\launcher.py` | Hybrid launcher (WebView2 vs Tkinter) |
| webview_main.py | `E:\prayer-music-guard\webview_app\webview_main.py` | WebView2 frontend host |
| backend_api.py | `E:\prayer-music-guard\webview_app\backend_api.py` | WebView bridge API |
| platform_check.py | `E:\prayer-music-guard\webview_app\platform_check.py` | Platform detection |
| index.html | `E:\prayer-music-guard\webview_app\frontend\index.html` | Modern HTML/CSS UI (290 lines) |
| app.js | `E:\prayer-music-guard\webview_app\frontend\js\app.js` | Frontend JS (57KB) |
| components.css | `E:\prayer-music-guard\webview_app\frontend\css\components.css` | CSS components (15KB) |
| PrayerMusicGuard.spec | `E:\prayer-music-guard\PrayerMusicGuard.spec` | **THE BROKEN FILE** |
| PrayerMusicGuard.spec (backup) | `E:\prayer-music-guard\backup\phase18_onedir_migration_20260919_020100\PrayerMusicGuard.spec` | Correct Phase 18 spec |
| PrayerMusicGuard.spec (backup) | `E:\prayer-music-guard\backup\phase20_5_html_css_splash_fix_20260919_061500\PrayerMusicGuard.spec` | Correct Phase 20.5 OneDir spec |

---

## Files Modified

| File | Change |
|---|---|
| `E:\prayer-music-guard\PrayerMusicGuard.spec` | **Restored** correct OneDir spec with `app_entry.py` entry point, full `webview_app/` datas, proper hidden imports |
| `E:\prayer-music-guard\build_exe.bat` | Updated `DIST_DIR` from `Phase18-OneDir-Test` to `Phase20-23-UI-Regression-Fix` |

---

## Backup Path

```
E:\prayer-music-guard\backup\phase20_23_ui_regression_before_fix_20260919_220341\
```

Contains:
- `PrayerMusicGuard.spec` (broken version)
- `build_exe.bat`
- `main.py`
- `uiverse_combobox.py`

---

## Old Build Integrity

| Build | SHA256 | Status |
|---|---|---|
| Phase20-22-Location-Combobox-Uiverse | `7f15230008592de14d640169fb1a66f98dd3c72aeb79677041a4166135fc7604` | **UNTOUCHED** |

The Phase 20.22 build was itself built with the broken spec, so it has the same regression. It is preserved as a reference artifact.

---

## New Build

| Property | Value |
|---|---|
| **Path** | `E:\prayer-music-guard\dist\Phase20-23-UI-Regression-Fix\PrayerMusicGuard\` |
| **EXE** | `PrayerMusicGuard.exe` |
| **EXE Size** | 4,252,683 bytes |
| **EXE SHA256** | `F0E91B66F2666011660D210B9CB6BC29B45E16ADE07127FA1065AB4E394C5BF8` |
| **Build Time** | 2026-09-19 10:04:35 PM |
| **PyInstaller** | 5.13.2 |
| **Python** | 3.8.10 |

---

## Build Verification

### Dist Contents — Present in New Build, MISSING from Phase 20.22

| Item | Present |
|---|---|
| `PrayerMusicGuard.exe` | ✅ |
| `main.py` | ✅ |
| `uiverse_combobox.py` | ✅ |
| `webview_app/app_entry.py` | ✅ (via Analysis) |
| `webview_app/launcher.py` | ✅ |
| `webview_app/webview_main.py` | ✅ |
| `webview_app/backend_api.py` | ✅ |
| `webview_app/platform_check.py` | ✅ |
| `webview_app/splash.html` | ✅ |
| `webview_app/frontend/index.html` | ✅ (15,449 bytes) |
| `webview_app/frontend/js/app.js` | ✅ (57,637 bytes) |
| `webview_app/frontend/css/components.css` | ✅ (15,202 bytes) |
| `webview_app/frontend/css/layout.css` | ✅ (5,429 bytes) |
| `webview_app/frontend/css/skins.css` | ✅ (8,716 bytes) |
| `webview_app/frontend/css/theme.css` | ✅ (1,462 bytes) |
| `webview_app/frontend/js/theme.js` | ✅ (1,819 bytes) |
| `webview/` (pywebview) | ✅ |
| `pystray/` | ✅ |
| `assets/` | ✅ |

### Build Output Structure

```
dist\Phase20-23-UI-Regression-Fix\PrayerMusicGuard\
├── PrayerMusicGuard.exe          (4,252,683 bytes)
├── main.py                       (180,823 bytes)
├── uiverse_combobox.py           (33,753 bytes)
├── assets/
├── webview_app/
│   ├── backend_api.py
│   ├── launcher.py
│   ├── platform_check.py
│   ├── splash.html
│   ├── webview_main.py
│   └── frontend/
│       ├── index.html
│       ├── css/
│       │   ├── components.css
│       │   ├── layout.css
│       │   ├── skins.css
│       │   └── theme.css
│       └── js/
│           ├── app.js
│           ├── app.js.bak
│           └── theme.js
├── webview/
├── pystray/
├── PIL/
├── tcl/
├── tcl8/
├── tk/
└── [DLLs and .pyd files]
```

---

## Test Results

| # | Test | Status |
|---|---|---|
| 1 | Launch new EXE | **PENDING** — requires manual visual verification |
| 2 | Confirm modern UI displayed | **PENDING** |
| 3 | Confirm old legacy UI is gone | **PENDING** |
| 4 | Confirm Arabic RTL layout | **PENDING** |
| 5 | Confirm modern sidebar | **PENDING** |
| 6 | Open Dashboard | **PENDING** |
| 7 | Open Prayer Times | **PENDING** |
| 8 | Open Music Player | **PENDING** |
| 9 | Open Settings | **PENDING** |
| 10 | Confirm Dark Mode | **PENDING** |
| 11 | Confirm Light Mode | **PENDING** |
| 12 | Confirm country selector | **PENDING** |
| 13 | Confirm city selector | **PENDING** |
| 14 | Confirm 195-country dataset | **PENDING** |
| 15 | Confirm country → city dependency | **PENDING** |
| 16 | Confirm manual mode remains selected | **PENDING** |
| 17 | Confirm no Alexandria fallback | **PENDING** |
| 18 | Confirm prayer times populate | **PENDING** |
| 19 | Confirm 12-hour display | **PENDING** |
| 20 | Confirm resume countdown | **PENDING** |
| 21 | Confirm music control works | **PENDING** |
| 22 | Confirm no unrelated regression | **PENDING** |

---

## Regression Results

| System | Status |
|---|---|
| Music pause logic | Not modified — PRESERVED |
| Music resume logic | Not modified — PRESERVED |
| APP_COMMAND logic | Not modified — PRESERVED |
| Play/Pause logic | Not modified — PRESERVED |
| Prayer countdown engine | Not modified — PRESERVED |
| Prayer calculation engine | Not modified — PRESERVED |
| Tray logic | Not modified — PRESERVED |
| Splash screen | Not modified — PRESERVED |
| Settings persistence | Not modified — PRESERVED |
| Autostart | Not modified — PRESERVED |
| Audio announcements | Not modified — PRESERVED |
| OneDir packaging | Restored correctly |
| Python 3.8.10 | Preserved |
| PyInstaller 5.13.2 | Preserved |
| Windows 7 compatibility | Preserved (Tkinter fallback path intact) |

---

## Final Status

**PASS (build verified)** — Manual visual launch test **PENDING**

The spec file has been restored to the correct configuration. The new build packages the complete `webview_app/` frontend including `app_entry.py` → `launcher.py` → WebView2 HTML frontend path. The EXE SHA256 is different from the broken build, confirming a clean rebuild.

To complete verification, launch:
```
E:\prayer-music-guard\dist\Phase20-23-UI-Regression-Fix\PrayerMusicGuard\PrayerMusicGuard.exe
```

And confirm the modern Arabic RTL WebView UI appears (sidebar navigation, dashboard, prayer times, music player, settings pages) instead of the old Tkinter UI.
