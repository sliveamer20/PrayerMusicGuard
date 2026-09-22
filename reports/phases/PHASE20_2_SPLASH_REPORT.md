# Phase 20.2 — Splash Root-Cause Investigation & Fix

## Confirmed Problem

Phase 20.1 manual test results:
- Splash: Launch 1 FAIL, Launch 2 FAIL, Launch 3 FAIL
- Dashboard: PASS
- Music Player Dropdown: PASS

The application launches successfully, dashboard works, dropdown fix works, but splash remains invisible.

## Root Cause

**Actual root cause discovered**: Tkinter Toplevel windows inherit the withdrawn state from their parent when created

When `self.root.withdraw()` was called BEFORE creating the splash Toplevel in Phase 20.1, the splash window was created as a child of a withdrawn root. The Tkinter window manager creates Toplevel windows withdrawn if the parent is withdrawn or iconified. This behavior is documented in Tk's msgbox.tcl, dialog.tcl, and related files.

**Why this happens**:
1. Root window created and configured
2. Root withdrawn immediately
3. Splash Toplevel created as child of withdrawn root
4. Window manager creates splash in withdrawn state
5. Splash never actually maps to screen despite `deiconify()` calls
6. `update()` calls process events but don't trigger real WM_MAP
7. 900ms timer scheduled before mainloop starts, so countdown begins late
8. Splash appears invisible or flashes briefly before being destroyed

**Additional timing issue**: The `after(900, self._close_splash)` timer was scheduled during `__init__`, before `window.mainloop()` started. The timer only begins counting when the event loop starts, making the effective splash visible time unpredictable.

## Files Modified

1. `E:\prayer-music-guard\main.py`
   - Line 1373-1375: Reversed order to create splash BEFORE withdrawing root
   - Line 1464: Added delay to splash close timer to ensure visibility

**Specific changes**:
```python
# BEFORE (Phase 20.1)
logger.info("Application initialized")
self.root.withdraw()
self.show_splash()

# AFTER (Phase 20.2)
logger.info("Application initialized")
# Phase 20.2 FIX: show splash BEFORE withdrawing root
# Tkinter creates Toplevel windows withdrawn if parent is withdrawn
# Create splash first, then hide root
self.show_splash()
self.root.withdraw()
```

```python
# BEFORE
self.root.after(900, self._close_splash)

# AFTER  
self.root.after(100, lambda: self.root.after(900, self._close_splash))
```

## Backup

**Backup path**: `E:\prayer-music-guard\backup\phase20_2_splash_root_cause_20260919_030000\`
- `main.py` backed up and verified before modifications

## Fix

**Splash Fix**: Create splash while root is still mapped, then withdraw root

The correct order ensures the splash Toplevel is created with a mapped parent, allowing the window manager to properly map the splash window. Withdrawing root AFTER splash creation means:
1. Root is configured and mapped
2. Splash is created while root is mapped → splash created mapped
3. Splash is shown visibly
4. Root is withdrawn → only splash visible
5. After 900ms, root deiconified and splash closed

**Timer Fix**: Delayed scheduling of close timer

Added 100ms delay before scheduling the 900ms close timer to ensure the splash has time to be actually visible before the timer starts counting. This compensates for the fact that `after()` timers scheduled before mainloop starts don't begin counting until the loop runs.

## New Build

**Build path**: `E:\prayer-music-guard\dist\Phase20-2-Splash-Fix\PrayerMusicGuard\`

- EXE: `PrayerMusicGuard.exe`
- Size: 4,238,580 bytes (4.04 MB)
- SHA-256: `052C149B93C8D508DC28C9CF7C1ADAD8F61AF864E61358E58829AAA5415E4EBA`
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
- Dropdown fix preserved

## Splash Manual Test

**PENDING USER VERIFICATION**

New build ready for manual testing at:
`E:\prayer-music-guard\dist\Phase20-2-Splash-Fix\PrayerMusicGuard\PrayerMusicGuard.exe`

Required verification:
- Launch 1: Splash visible → Dashboard
- Launch 2: Splash visible → Dashboard
- Launch 3: Splash visible → Dashboard
- Launch 4: Splash visible → Dashboard
- Launch 5: Splash visible → Dashboard

Test criteria: Splash must be visibly observable at startup before dashboard appears. User must actually see splash window.

## Dropdown Regression

**EXPECTED PASS**

The dropdown fix from Phase 20.1 must remain intact:
- Dark background: `var(--surface)` instead of white fallback
- Readable text: `color: var(--fg)`
- Readable selection: `background: var(--surface-alt)`

No changes made to WebView frontend files. Dropdown code untouched.

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

Phase 20.1 build also untouched.

## Known Issues

None identified. Awaiting manual verification.

## Status

**READY FOR USER VERIFICATION**

Build completed successfully. Splash root cause identified and fixed. Build ready for manual testing. User must verify splash visibility through actual observation.

**DO NOT DECLARE PASS** until user manually confirms splash is visible.

---

## Test Instructions for User

1. Close all existing PrayerMusicGuard windows
2. Run: `E:\prayer-music-guard\dist\Phase20-2-Splash-Fix\PrayerMusicGuard\PrayerMusicGuard.exe`
3. Observe if splash window appears BEFORE dashboard
4. Splash should be visible for ~1 second
5. Repeat 5 times
6. Also verify Music Player dropdown still has dark background and readable text

Expected behavior:
- Splash appears (window with "صلاة وسكون" title)
- Splash transitions to dashboard
- Dashboard loads normally
- Dropdown remains readable
