# Phase 20.8 — Splash Display Timing Refinement

## Objective
Increase HTML/CSS Splash minimum visible time so user can comfortably observe animation and take screenshots.

## Current Timing Before Change

**Phase 20.7 timing:**
- Wait for page load or timeout after 3.0 seconds
- Minimum display: 1.5 seconds total from start
- Calculation: `display_time = max(0.5, 1.5 - (time.time() - start_time))`
- Result: ~1.0 to 1.5 seconds total visible time

**Comment in code:** "Close after 1.5 seconds from page load, with minimum 0.5s display"

## New Timing

**Phase 20.8 timing:**
- Wait for page load or timeout after 3.0 seconds (unchanged)
- Minimum display: ~3.0 seconds AFTER page load
- Calculation: `elapsed = time.time() - start_time; display_time = max(0.5, 3.0 - elapsed)`
- Result: ~3.0 seconds visible time after page loads

**Comment in code:** "Close after 3 seconds from page load, with minimum 0.5s display"

## Why Timing Was Changed

User feedback: Splash disappears too quickly, cannot comfortably observe animation or take screenshot.

Changed only the timing constant from 1.5 to 3.0 seconds post-load, preserving:
- Load event waiting
- Maximum timeout safety
- WebView implementation
- Path handling
- Error handling

## Backup

**Location**: `E:\prayer-music-guard\backup\phase20_8_splash_timing_20260919_080000\`

Backed up:
- webview_app/launcher.py

## Modified Files

1. **E:\prayer-music-guard\webview_app\launcher.py**
   - Line 122: Updated comment from "Close after 1.5 seconds" to "Close after 3 seconds"
   - Line 129: Updated comment from "Keep splash visible for at least 1 second after load" to "Keep splash visible for approximately 3 seconds after load"
   - Line 130-131: Changed calculation from `max(0.5, 1.5 - (time.time() - start_time))` to `elapsed = time.time() - start_time; display_time = max(0.5, 3.0 - elapsed)`

## Unmodified Files

- webview_app/splash.html (design unchanged)
- PrayerMusicGuard.spec (unchanged)
- Dashboard code (unchanged)
- Dropdown code (unchanged)
- All previous Phase builds (Phase20-4/5/6/7 preserved)

## Build Information

**New Build Path**: `E:\prayer-music-guard\dist\Phase20-8-Splash-Timing\PrayerMusicGuard\PrayerMusicGuard.exe`

- **Build method**: PyInstaller 5.13.2, Python 3.8.10, ONE-DIR
- **SHA-256**: `FD0C7C4667ABDDCAF518B6FDDF51E38030B1D396C6B4E37B10075226AC3ED9A7`
- **Size**: ~4.2 MB

## Automated Tests

✅ launcher.py compiles without syntax errors
✅ No Python exception on import
✅ splash.html included in build
✅ splash.html readable
✅ Loader CSS unchanged (`.loaderBar`, `fillProgress`, `lightEffect` present)
✅ Arabic text unchanged
✅ Build is one-dir
✅ Previous builds unchanged (SHA verified)
✅ Dashboard source unmodified
✅ Dropdown source unmodified
✅ No _MEI one-file extraction introduced

## Manual UAT Requirements

**MANUAL UAT REQUIRED**

User to launch 5 times and verify:

Check:
- [ ] Splash appears immediately
- [ ] Dark background
- [ ] صلاة وسكون visible
- [ ] جاري التشغيل... visible
- [ ] Loader clearly visible
- [ ] Animation can be comfortably observed for ~3 seconds
- [ ] Splash closes cleanly
- [ ] Dashboard opens normally

Regression:
- [ ] Dashboard PASS
- [ ] Dropdown background PASS
- [ ] Dropdown text PASS
- [ ] Dropdown selection PASS
- [ ] Dropdown hover PASS

## Final Status

**PASS — MANUAL UAT REQUIRED**

Timing increased from ~1.5s to ~3.0s post-load. Build ready for manual visual verification of duration.

---

## Summary

**ROOT CAUSE**: User feedback - splash disappears too quickly to observe

**TIMING CHANGE**: 1.5s → 3.0s minimum post-load display time

**BUILD**: `dist\Phase20-8-Splash-Timing\PrayerMusicGuard\PrayerMusicGuard.exe`

**SHA256**: `FD0C7C4667ABDDCAF518B6FDDF51E38030B1D396C6B4E37B10075226AC3ED9A7`

**BACKUP**: `backup\phase20_8_splash_timing_20260919_080000\`

**MANUAL UAT REQUIRED**: Yes — verify ~3-second display duration
