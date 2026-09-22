# Phase 20.1 — Splash + Music Player Dropdown Fix

## Status
**PENDING MANUAL VERIFICATION**

## Problems
1. Splash missing at startup — application opened directly to dashboard without showing splash screen
2. Music Player dropdown unreadable — dropdown background white with nearly white text, inconsistent with dark UI

## Root Cause

### Splash Missing
**Root cause**: Root window withdrawn AFTER splash creation and display

The `show_splash()` method in `main.py` was creating the splash window then calling `self.root.withdraw()` only after splash was already updated, deiconified, lifted, and geometry-set. The main window was already mapped/realized from `self.root.geometry()` during `App.__init__`, so `update()` calls processed the Tk event queue while root was visible, causing race condition where root could flash before withdraw. On Windows, withdrawing the parent after creating a Toplevel child can cause the overrideredirect splash to be hidden or lose focus.

**Previous pattern** (lost in migration): `self.root.withdraw()` before `show_splash()`

### Dropdown Unreadable
**Root cause**: Undefined CSS variables with incorrect fallbacks

WebView frontend custom dropdown CSS used `var(--card-bg, #fff)` and `var(--hover, #f3f4f6)` where `--card-bg` and `--hover` are undefined in theme.css, skins.css, or components.css. In dark mode, this forced white background with white text (white-on-white), making program names like `backgroundTaskHost.exe`, `ChatGPT.exe`, `codex.exe`, `conhost.exe` unreadable.

The dropdown items inherited `color: var(--fg)` which is white in dark mode, but background fell back to white.

## Files Modified

1. `E:\prayer-music-guard\main.py`
   - Line 1372: Added `self.root.withdraw()` before `self.show_splash()`
   - Line 1461: Removed duplicate `self.root.withdraw()` inside `show_splash()`

2. `E:\prayer-music-guard\webview_app\frontend\index.html`
   - Line 13: Changed `background: var(--card-bg, #fff)` to `background: var(--surface)`
   - Line 13: Changed `border: 1px solid var(--border, #e3e3e3)` to `border: 1px solid var(--border)`
   - Line 15: Added `color: var(--fg)` to `.dropdown-item`
   - Line 16: Changed `background: var(--hover, #f3f4f6)` to `background: var(--surface-alt)`

## Backup
**Backup path**: `E:\prayer-music-guard\backup\phase20_1_splash_dropdown_fix_20260919_023000\`
- `main.py` backed up
- `index.html` backed up

Both backups verified before modifications.

## Splash Fix
**Change**: Move root.withdraw() before splash creation

Modified `App.__init__` to withdraw root immediately after initialization, before calling `show_splash()`:

```python
logger.info("Application initialized")
# Phase 20.1 FIX: withdraw root before showing splash to ensure splash is visible
self.root.withdraw()
self.show_splash()
```

Removed duplicate `self.root.withdraw()` from inside `show_splash()` method at line 1461.

This restores the correct startup flow:
1. Root created and geometry set
2. Root withdrawn immediately
3. Splash created and shown (root already hidden)
4. Splash visible to user
5. Transition to dashboard after 900ms

## Dropdown Fix
**Change**: Use existing theme tokens instead of undefined variables

Modified inline CSS in `index.html`:

```css
/* BEFORE */
.custom-dropdown { ... background: var(--card-bg, #fff); ... }
.dropdown-item:hover, .dropdown-item.is-active { background: var(--hover, #f3f4f6); }

/* AFTER */
.custom-dropdown { ... background: var(--surface); ... }
.dropdown-item { ... color: var(--fg); }
.dropdown-item:hover, .dropdown-item.is-active { background: var(--surface-alt); }
```

This ensures dropdown respects current theme:
- Light mode: surface = white, fg = black, surface-alt = light gray
- Dark mode: surface = #29292d, fg = white, surface-alt = #2d2d30

No process-discovery logic changed. Dropdown continues to populate dynamically with actual running processes.

## Build
**New build path**: `E:\prayer-music-guard\dist\Phase20-1-Splash-Dropdown-Fix\PrayerMusicGuard\`

- EXE: `PrayerMusicGuard.exe`
- Size: 4,238,525 bytes (4.04 MB)
- SHA-256: C4262F71CC5D654C89AC628D07A3E6F389EDAA7A2E347E039425493F6E060CDD
- File count: 1,093 files
- Build method: PyInstaller 5.13.2, Python 3.8.10, ONE-DIR

**Build verification**: ✅
- EXE exists
- Required resources present
- Frontend exists
- CSS exists
- JavaScript exists
- Icons exist
- Audio resources exist
- No source-tree absolute paths

## Manual Splash Test
**PENDING USER VERIFICATION**

Launch build `E:\prayer-music-guard\dist\Phase20-1-Splash-Dropdown-Fix\PrayerMusicGuard\PrayerMusicGuard.exe`

Required verification:
- Launch 1: Splash visible → Dashboard
- Launch 2: Splash visible → Dashboard
- Launch 3: Splash visible → Dashboard

Test criteria: Splash must be visibly displayed to user at startup before dashboard appears.

## Manual Dropdown Test
**PENDING USER VERIFICATION**

Open WebView frontend Music Player program dropdown:

Required verification:
- Dropdown opening: PASS/FAIL
- Background matches dark theme: PASS/FAIL
- Text readability: PASS/FAIL
- Program names visible: PASS/FAIL
- Selected item readable: PASS/FAIL
- Hover/highlight readable: PASS/FAIL
- Scrollbar usable: PASS/FAIL
- Selection works: PASS/FAIL

Test with actual dynamically populated process names.

## _MEI Test
**PENDING USER VERIFICATION**

Required test:
- Count `%TEMP%\_MEI_*` before launch
- Launch 1, count after
- Launch 2, count after
- Launch 3, count after

Expected: No new _MEI_* directories created across 3 launches.

## Regression Check
**PENDING USER VERIFICATION**

Verify existing behaviors still work:
- Dashboard opens
- Player list populates
- Protected-player functionality remains
- No text files repeatedly open/close
- No obvious UI freeze
- Single-instance behavior remains
- WebView frontend loads
- Existing resources load
- Splash transitions to Dashboard

## Old Release Integrity
**VERIFIED ✅**

Phase 18 EXE:
- Path: `E:\prayer-music-guard\dist\Phase18-OneDir-Test\PrayerMusicGuard\PrayerMusicGuard.exe`
- SHA-256: `4424AD0F4D07864A945E9D43B84BCE5B51E63AD7941B5CE45BC6E5887A705475`
- Status: Unchanged

Phase 18 Installer:
- Path: `E:\prayer-music-guard\dist\PrayerMusicGuard-v1.2.7-ONEDIR-TEST.exe`
- SHA-256: `03496195DB5AAA447D4891D24FA7041863AB5B8487BB4A4D86ABBF6239E767DF`
- Status: Unchanged

Old releases untouched.

## Known Issues
None identified in code review. Awaiting manual verification.

## Critical Stop Conditions
✅ Build succeeded
✅ Old releases unchanged
✅ No regressions in code inspection
⚠️ Manual verification pending

---

**Next step**: User to perform manual verification of splash visibility and dropdown readability using new build.
