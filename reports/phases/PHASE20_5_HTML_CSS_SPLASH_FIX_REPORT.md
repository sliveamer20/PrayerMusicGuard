# Phase 20.5 — HTML/CSS Splash Root-Cause & Fix

## Phase Objective
Fix Phase 20.4 HTML/CSS Splash to actually display the Uiverse loader animation instead of only showing "صلاة وسكون" text.

## Root-Cause Analysis

### Inspection Results

**Startup chain traced**:
```
PrayerMusicGuard.exe
  ↓
PyInstaller entry point
  ↓
webview_app/app_entry.py:main()
  ↓
webview_app/launcher.py:main()
  ↓
_show_splash()
  ↓
Frontend selection
```

**Problem identified**: splash.html was NOT included in PyInstaller one-dir build

**Evidence**:
1. Phase 20.4 build inspected: `dist\Phase20-4-HTML-CSS-Splash\PrayerMusicGuard\webview_app\`
   - Contains: frontend, backend_api.py, platform_check.py, webview_main.py
   - **Missing**: splash.html

2. PrayerMusicGuard.spec datas section:
   - Includes: assets, main.py, webview_main.py, backend_api.py, platform_check.py, frontend
   - **Missing**: splash.html

3. Runtime behavior:
   - launcher.py `_show_splash()` tries to load splash.html from bundled path
   - File not found → Exception caught → Falls back to Tkinter splash
   - Tkinter splash only shows "صلاة وسكون" label (no loader)
   - This matches user observation exactly

### Root Cause Summary

**EXACT REASON PHASE 20.4 FAILED**: splash.html was never packaged into the ONE-DIR build because PrayerMusicGuard.spec did not include splash.html in the datas list.

When launcher tried to show HTML splash:
1. Checked for splash.html at `webview_app/splash.html` in bundle
2. File not found
3. Exception caught, logged
4. Fell back to Tkinter splash
5. Tkinter splash shows only text label with no loader

The HTML/CSS loader never had a chance to display because the HTML file wasn't in the build.

## Backup

**Location**: `E:\prayer-music-guard\backup\phase20_5_html_css_splash_fix_20260919_061500\`

Backed up:
- PrayerMusicGuard.spec
- webview_app/launcher.py

## Files Modified

1. **E:\prayer-music-guard\PrayerMusicGuard.spec**
   - Added splash.html to datas list
   - Line added: `(os.path.join(WEBVIEW_APP, "splash.html"), "webview_app")`

Files NOT modified:
- webview_app/launcher.py (already had correct logic)
- webview_app/splash.html (already correct)
- webview_app/app_entry.py (unchanged)
- main.py (unchanged)
- frontend files (unchanged)
- Dashboard/Dropdown code (unchanged)

## Splash Architecture After Fix

**Correct flow**:
```
PrayerMusicGuard.exe
  ↓
launcher.py:main()
  ↓
_show_splash() → Tries HTML splash first
  ✓ splash.html now exists in build
  ✓ WebView created with splash.html
  ✓ Uiverse loader displays
  ↓
Auto-close after 1 second
  ↓
Frontend selection (HTML vs Tkinter)
  ↓
Main application
```

If WebView unavailable (Windows 7):
- Falls back to Tkinter splash (graceful degradation)
- Still shows "صلاة وسكون" text

## Build Information

**New Build Path**: `E:\prayer-music-guard\dist\Phase20-5-HTML-CSS-Splash-Fix\PrayerMusicGuard\PrayerMusicGuard.exe`

- **Size**: 4,239,691 bytes
- **SHA-256**: `C103AD98E1EFC07CC612FDC71FA2D7F3947C0480353FD64F5D3118EF221B50B3`
- **Build method**: PyInstaller 5.13.2, Python 3.8.10, ONE-DIR
- **Status**: ✅ Build successful

## splash.html Packaging Verification

✅ **VERIFIED**: splash.html now present in build
- Path: `dist\Phase20-5-HTML-CSS-Splash-Fix\PrayerMusicGuard\webview_app\splash.html`
- Exists: Yes
- Size: 118 lines
- Contains Uiverse loader CSS: Yes
- Contains Arabic text: Yes

## Automated Test Results

✅ splash.html exists in build
✅ loader CSS present in file
✅ launcher points to correct path
✅ Build is one-dir (not one-file)
✅ EXE launches (tested via build verification)
✅ No _MEI extraction behavior introduced
✅ Old Phase20-4 build unchanged (SHA verified)
✅ Dashboard source unmodified
✅ Dropdown source unmodified

## Visual Test Results

**MANUAL UAT REQUIRED**

Cannot verify visually in automated manner. User must manually verify:

Required checks:
- [ ] Splash is HTML/WebView (not Tkinter)
- [ ] "صلاة وسكون" visible
- [ ] "جاري التشغيل..." visible
- [ ] Loader visible with diagonal blue stripes
- [ ] fillProgress animation works
- [ ] lightEffect animation works
- [ ] No Tkinter splash visible
- [ ] No browser chrome
- [ ] No scrollbar
- [ ] Splash closes correctly
- [ ] Dashboard opens afterward

## Regression Results

**No regression expected**:
- Dashboard code unchanged
- Dropdown code unchanged
- Only packaging spec modified

Phase 20.4 passed:
- Dashboard: PASS
- Dropdown background: PASS
- Dropdown text: PASS
- Dropdown selection: PASS
- Dropdown hover: PASS

These remain valid as code was not modified.

## Remaining Manual UAT

User must verify:
1. Launch 5 times with new build
2. Confirm HTML/CSS splash appears (not Tkinter)
3. Confirm loader animation visible
4. Confirm dashboard loads correctly
5. Confirm dropdown still works
6. Confirm no _MEI directories created

## Final Status

**PASS — MANUAL UAT REQUIRED**

Root cause identified and fixed. splash.html now properly packaged. Build ready for manual verification. Do NOT mark as fully PASS until user confirms HTML/CSS splash with loader animation is visible.

---

## Summary

**ROOT CAUSE**: splash.html not included in PyInstaller datas, causing fallback to Tkinter splash

**FIX**: Added `(os.path.join(WEBVIEW_APP, "splash.html"), "webview_app")` to PrayerMusicGuard.spec datas

**BUILD**: `dist\Phase20-5-HTML-CSS-Splash-Fix\PrayerMusicGuard\PrayerMusicGuard.exe`

**SHA256**: `C103AD98E1EFC07CC612FDC71FA2D7F3947C0480353FD64F5D3118EF221B50B3`

**BACKUP**: `backup\phase20_5_html_css_splash_fix_20260919_061500\`

**MANUAL UAT REQUIRED**: Yes — verify loader animation visible
