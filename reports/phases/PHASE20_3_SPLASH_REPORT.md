# Phase 20.3 — Deep Splash Root-Cause Investigation

## Confirmed Failure

Phase 20.2 manual test results:
- Splash: Launch 1-5 all FAIL
- Dashboard: PASS
- Music Player Dropdown: All PASS

Splash still invisible despite Phase 20.2 fix.

## Startup Trace

**Actual entry point discovered**:
```
PrayerMusicGuard.exe
  ↓
PyInstaller entry (PrayerMusicGuard.spec:53)
  ↓
webview_app/app_entry.py:main()
  ↓
webview_app/launcher.py:main()
  ↓
platform_check.can_use_html_frontend()
  ↓
IF True (Windows 10/11 + WebView2): HTML frontend
IF False: Tkinter main.py
```

**Critical finding**: The splash in main.py is NEVER executed on Windows 10/11 with WebView2 because the launcher uses HTML frontend instead of Tkinter fallback!

## Root Cause

**ACTUAL ROOT CAUSE**: Splash code exists only in main.py (Tkinter), but the packaged application entry point is webview_app/app_entry.py which uses webview_app/launcher.py to decide between HTML frontend and Tkinter fallback.

On Windows 10/11 with WebView2 installed:
- launcher.py detects HTML frontend is available
- launcher.py starts HTML frontend via pywebview
- main.py is NEVER executed
- Splash code in main.py never runs

The Phase 20.1 and 20.2 fixes modified main.py, but main.py was never being executed in the user's environment!

## Why Phase 20.2 Fix Failed

Phase 20.2 fixed the Tkinter splash window ordering issue (create splash before withdrawing root), but this fix was irrelevant because:
1. The application uses HTML frontend, not Tkinter
2. main.py is never executed
3. The Tkinter splash code is dead code in this configuration

This is a configuration issue, not a code bug in the splash itself.

## Fix Applied

**File modified**: `E:\prayer-music-guard\webview_app\launcher.py`

Added splash display BEFORE frontend selection decision:

```python
def main() -> None:
    # Phase 20.3 FIX: Show splash before frontend selection
    # Splash must be visible regardless of HTML/Tkinter choice
    _show_splash()
    
    if os.environ.get("PMG_FORCE_TK", "").strip().lower() in ("1", "true", "yes"):
        _run_tkinter_fallback("PMG_FORCE_TK set")
        return
    ...
```

**New function added**: `_show_splash()`

Creates a minimal Tkinter splash window that:
- Shows BEFORE launcher decides on HTML vs Tkinter
- Displays for 1 second
- Works regardless of which frontend is chosen
- Uses independent Tk root, not dependent on main.py
- Minimal code to avoid blocking startup

This ensures splash is visible whether HTML frontend or Tkinter fallback is used.

## Files Modified

1. `E:\prayer-music-guard\webview_app\launcher.py`
   - Added `_show_splash()` function
   - Modified `main()` to call `_show_splash()` before frontend selection

## Backup

**Backup path**: `E:\prayer-music-guard\backup\phase20_3_splash_deep_fix_20260919_040000\`
- `main.py` backed up

**Note**: launcher.py was modified, not backed up in this location. Backup should be considered for launcher.py as well.

## New Build

**Build path**: `E:\prayer-music-guard\dist\Phase20-3-Splash-Deep-Fix\PrayerMusicGuard\`

- EXE: `PrayerMusicGuard.exe`
- Size: 4,239,228 bytes (4.04 MB)
- SHA-256: `6F213C793AB8C8329CBC80B8916B4B2B5A1A8653595433F350DBF90D5BCB93EB`
- File count: 1,093 files
- Build method: PyInstaller 5.13.2, Python 3.8.10, ONE-DIR

**Build verification**: ✅
- EXE exists
- Required resources present
- HTML frontend resources preserved
- Tkinter fallback preserved
- Dropdown fix preserved

## Manual Splash Test

**PENDING USER VERIFICATION**

New build ready at:
`E:\prayer-music-guard\dist\Phase20-3-Splash-Deep-Fix\PrayerMusicGuard\PrayerMusicGuard.exe`

Required verification:
- Launch 1: Splash visible → HTML/Tkinter dashboard
- Launch 2: Splash visible → HTML/Tkinter dashboard
- Launch 3: Splash visible → HTML/Tkinter dashboard
- Launch 4: Splash visible → HTML/Tkinter dashboard
- Launch 5: Splash visible → HTML/Tkinter dashboard

Test criteria: Splash must be visibly observable at startup before dashboard appears, regardless of whether HTML or Tkinter frontend is used.

## Dropdown Regression

**EXPECTED PASS**

No changes made to WebView frontend or dropdown code. Dropdown fix from Phase 20.1 remains intact:
- Dark background: `var(--surface)`
- Readable text: `color: var(--fg)`
- Readable selection: `background: var(--surface-alt)`

## _MEI Test

**PENDING USER VERIFICATION**

Required test:
- Count `%TEMP%\_MEI_*` before launch
- After launch 1, count again
- After launch 2, count again
- After launch 3, count again

Expected: No new _MEI_* directories created.

## Old Artifact Integrity

**VERIFIED ✅**

Phase 18 EXE:
- Path: `E:\prayer-music-guard\dist\Phase18-OneDir-Test\PrayerMusicGuard\PrayerMusicGuard.exe`
- SHA-256: `4424AD0F4D07864A945E9D43B84BCE5B51E63AD7941B5CE45BC6E5887A705475`
- Expected: `4424AD0F4D07864A945E9D43B84BCE5B51E63AD7941B5CE45BC6E5887A705475`
- Status: UNCHANGED ✅

Phase 18 Installer:
- Path: `E:\prayer-music-guard\dist\PrayerMusicGuard-v1.2.7-ONEDIR-TEST.exe`
- SHA-256: `03496195DB5AAA447D4891D24FA7041863AB5B8487BB4A4D86ABBF6239E767DF`
- Expected: `03496195DB5AAA447D4891D24FA7041863AB5B8487BB4A4D86ABBF6239E767DF`
- Status: UNCHANGED ✅

Phase 20.1 and Phase 20.2 builds also untouched.

## Remaining Issues

None identified. Awaiting manual verification.

## Status

**READY FOR USER VERIFICATION**

Root cause identified: Splash in main.py never executed due to HTML frontend selection. Fix implemented by showing splash in launcher before frontend decision. Build ready for manual testing.

**DO NOT DECLARE PASS** until user manually confirms splash is visible.

---

## Key Insight

The actual problem was architectural, not code-related. The application has a hybrid architecture:
- HTML frontend for Windows 10/11 with WebView2
- Tkinter fallback for Windows 7 or missing WebView2

The splash was only in the Tkinter code path, so it was invisible in the HTML path which is the default for modern Windows.

The fix shows splash at the launcher level, before the frontend decision, ensuring visibility regardless of which UI path is taken.
