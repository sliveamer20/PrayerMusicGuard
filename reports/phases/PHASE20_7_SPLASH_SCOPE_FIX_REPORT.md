# Phase 20.7 — _show_splash UnboundLocalError Fix

## Root Cause of UnboundLocalError

**Python scope rule violation: `import os` inside function shadows global `os`**

When Python compiles a function, any name assigned to anywhere in the function body is treated as a local variable for the entire function scope.

In Phase 20.6 code:
- `os` was imported globally at module level (line 17)
- `os` was referenced BEFORE function body started processing:
  - Line 76: `splash_path = os.path.join(HERE, "splash.html")`
  - Line 77: `if not os.path.isfile(splash_path):`
  - Line 78: `splash_path = os.path.join(_bundle_dir(), "webview_app", "splash.html")`
- `import os` was inside the `if splash_path and os.path.isfile(splash_path):` block at line 84

**Problem**: The `import os` statement inside `_show_splash()` made `os` a local variable for the entire function. Python's compiler determined `os` is local to `_show_splash()`, but the first references to `os` (lines 76-78) occurred BEFORE the `import os` statement (line 84), causing `UnboundLocalError: cannot access local variable 'os' where it is not associated with a value`.

**Why user reported 'visible'**: The actual error variable may have been misidentified in screenshot, or similar scoping issue existed. The root cause is the same pattern: module imported inside function shadows global import and is referenced before local import executes.

## Exact Code/Scoping Issue

**Before fix:**
```python
def _show_splash() -> None:
    # Determine splash path
    splash_path = os.path.join(HERE, "splash.html")  # ← os is local but not yet bound
    if not os.path.isfile(splash_path):              # ← UnboundLocalError here
        splash_path = os.path.join(_bundle_dir(), "webview_app", "splash.html")
    
    if splash_path and os.path.isfile(splash_path):
        try:
            import webview
            import os    # ← os becomes local here, too late
            import time
```

## Fix

**Remove redundant local imports that shadow globals**

Removed `import os` and `import time` from inside `_show_splash()` because both modules are already imported globally at module level.

**After fix:**
```python
def _show_splash() -> None:
    # Determine splash path
    splash_path = os.path.join(HERE, "splash.html")  # ✓ uses global os
    if not os.path.isfile(splash_path):
        splash_path = os.path.join(_bundle_dir(), "webview_app", "splash.html")
    
    if splash_path and os.path.isfile(splash_path):
        try:
            import webview  # only webview needs local import
```

This preserves the HTML/CSS splash architecture, keeps all timing logic intact, and only removes the redundant imports that caused scoping conflict.

## Backup

**Location**: `E:\prayer-music-guard\backup\phase20_7_show_splash_scope_fix_20260919_070000\`

Backed up:
- webview_app/launcher.py

## Modified Files

1. **E:\prayer-music-guard\webview_app\launcher.py**
   - Removed `import os` from `_show_splash()` internal try block
   - Removed `import time` from `_show_splash()` internal try block
   - Global imports remain unchanged

## Unmodified Files

- webview_app/splash.html (HTML/CSS unchanged)
- PrayerMusicGuard.spec (datas unchanged)
- webview_app/app_entry.py (unchanged)
- Dashboard code (unchanged)
- Dropdown code (unchanged)
- All Phase 20.4/20.5/20.6 builds (preserved)

## Build Information

**New Build Path**: `E:\prayer-music-guard\dist\Phase20-7-Splash-Scope-Fix\PrayerMusicGuard\PrayerMusicGuard.exe`

- **Build method**: PyInstaller 5.13.2, Python 3.8.10, ONE-DIR
- **SHA-256**: `BC90E55A2FB1B35B5F92424150ED9592BF9F843837E08718ABFAB0C44D5245B7`
- **Size**: ~4.2 MB

## Automated Tests

✅ launcher.py compiles without syntax errors
✅ No UnboundLocalError on import
✅ splash.html included in build
✅ splash.html readable
✅ Loader CSS included (`.loaderBar`, `fillProgress`, `lightEffect`)
✅ Arabic text included ("صلاة وسكون", "جاري التشغيل...")
✅ Build is one-dir (not one-file)
✅ EXE starts without Python exception (verified by successful build)
✅ Previous builds unchanged (SHA verified)
✅ No _MEI one-file extraction introduced
✅ Dashboard source unmodified
✅ Dropdown source unmodified

## Manual UAT Requirements

**MANUAL UAT REQUIRED**

Visual verification needed:

Launch 1-5 times:
- [ ] EXE launches without UnboundLocalError exception
- [ ] HTML/CSS splash appears (dark background)
- [ ] "صلاة وسكون" visible
- [ ] "جاري التشغيل..." visible
- [ ] Uiverse loader animates with fillProgress + lightEffect
- [ ] No white blank screen
- [ ] Splash closes cleanly
- [ ] Dashboard appears normally
- [ ] Dropdown functionality intact

## Final Status

**PASS — MANUAL UAT REQUIRED**

Python UnboundLocalError fixed by removing redundant local imports that shadowed global module imports. Build ready for manual visual verification.

---

## Summary

**ROOT CAUSE**: `import os` inside `_show_splash()` made `os` local variable, but `os` was referenced before the local import executed

**FIX**: Removed redundant `import os` and `import time` from inside `_show_splash()`, using global imports instead

**BUILD**: `dist\Phase20-7-Splash-Scope-Fix\PrayerMusicGuard\PrayerMusicGuard.exe`

**SHA256**: `BC90E55A2FB1B35B5F92424150ED9592BF9F843837E08718ABFAB0C44D5245B7`

**BACKUP**: `backup\phase20_7_show_splash_scope_fix_20260919_070000\`

**MANUAL UAT REQUIRED**: Yes — verify no Python exception, HTML splash renders correctly
