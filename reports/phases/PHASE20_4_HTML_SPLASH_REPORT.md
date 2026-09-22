# Phase 20.4 — HTML/CSS Splash

## Objective
Convert Splash Screen UI from basic Tkinter visual design to modern HTML/CSS Splash Screen while preserving reliable Phase 20.3 startup architecture.

## Existing Splash Architecture
Phase 20.3 implemented:
- Splash shown in launcher.py before frontend selection
- Tkinter splash window with "صلاة وسكون" text
- Works regardless of HTML/Tkinter frontend choice
- 1-second display before proceeding

Entry point: `webview_app/app_entry.py` → `webview_app/launcher.py` → `main()` → `_show_splash()` → frontend selection

## New HTML/CSS Architecture
Phase 20.4 implements:
- HTML/CSS splash using WebView2 for modern Windows
- Uses user's supplied Uiverse loader pattern as design basis
- Preserves Phase 20.3 startup sequence
- Tkinter splash fallback for Windows 7 or WebView unavailable

**Startup flow**:
```
PrayerMusicGuard.exe
  ↓
launcher.py:main()
  ↓
_show_splash() → HTML/CSS via WebView (or Tkinter fallback)
  ↓
Frontend selection (HTML vs Tkinter)
  ↓
Application initialization
  ↓
Main UI
```

## Loader Pattern
Used the user's supplied Uiverse loader pattern as-is with minimal adaptations:
- Striped diagonal effect preserved
- Blue gradient colors: #0031F2, #006DFE preserved
- Progress animation: fillProgress 6s ease-in-out infinite
- Light effect animation: lightEffect 1s infinite linear
- Rounded bar design preserved
- Dark background consistent with PrayerMusicGuard visual language

**Modifications made**:
- Adapted colors to dark theme (#202024 background)
- Centered layout for Splash
- Added Arabic text: "صلاة وسكون" and "جاري التشغيل..."
- Simplified container for Splash use case

## Files Modified

1. **E:\prayer-music-guard\webview_app\splash.html** (NEW)
   - HTML/CSS splash page
   - Uses Uiverse loader pattern
   - Arabic text support
   - Dark theme consistent with app

2. **E:\prayer-music-guard\webview_app\launcher.py** (MODIFIED)
   - Updated `_show_splash()` function
   - Tries HTML/CSS splash via WebView first
   - Falls back to Tkinter splash if WebView unavailable
   - Preserves Phase 20.3 startup architecture

**Backup**: `E:\prayer-music-guard\backup\phase20_4_html_css_splash_20260919_050000\`

## New Build

**Path**: `E:\prayer-music-guard\dist\Phase20-4-HTML-CSS-Splash\PrayerMusicGuard\PrayerMusicGuard.exe`

- **Size**: 4,239,691 bytes (4.05 MB)
- **SHA-256**: `7D3C1B41E00A174AC47C280EA6B1165DA9243CAC7F627EAAC0A147FC15BD5861`
- **Build method**: PyInstaller 5.13.2, Python 3.8.10, ONE-DIR
- **Build verification**: ✅ EXE exists, resources present

## Manual Splash Test

**PENDING USER VERIFICATION**

New build ready at:
`E:\prayer-music-guard\dist\Phase20-4-HTML-CSS-Splash\PrayerMusicGuard\PrayerMusicGuard.exe`

Required verification:
- Launch 1: HTML/CSS Splash appears → Main UI loads
- Launch 2: HTML/CSS Splash appears → Main UI loads
- Launch 3: HTML/CSS Splash appears → Main UI loads
- Launch 4: HTML/CSS Splash appears → Main UI loads
- Launch 5: HTML/CSS Splash appears → Main UI loads

**Test criteria**: Splash must be HTML/CSS styled, loader animates, no Tkinter splash visible, dashboard loads normally.

## Visual Verification Checklist

Pending user verification:
- [ ] Splash is HTML/CSS styled (not basic Tkinter)
- [ ] Splash is not the old Tkinter design
- [ ] "صلاة وسكون" is visible
- [ ] Loader is visible
- [ ] Loader has striped diagonal pattern
- [ ] Loader animates
- [ ] Blue colors visible (#0031F2, #006DFE)
- [ ] Animation smooth
- [ ] No white browser page
- [ ] No scrollbars
- [ ] No browser chrome
- [ ] Splash centered
- [ ] Splash looks clean
- [ ] Dashboard appears normally after Splash

## Dropdown Regression

**EXPECTED PASS**

No changes made to WebView frontend CSS or dropdown implementation. Phase 20.1 dropdown fix remains intact.

Verify after Splash test:
- Background: PASS/FAIL
- Text: PASS/FAIL
- Selection: PASS/FAIL
- Hover: PASS/FAIL

Expected: All PASS

## Startup Regression

Verify:
- Dashboard opens normally
- WebView loads correctly
- No startup errors
- No duplicate windows
- Single-instance behavior maintained
- Application responsive

## _MEI Test

**PENDING USER VERIFICATION**

Required:
- Count `%TEMP%\_MEI_*` before launch
- After launch 1, count again
- After launch 2, count again
- After launch 3, count again

Expected: No new _MEI_* directories created

## Old Artifact Integrity

**VERIFIED ✅**

Phase 18 EXE:
- SHA-256: `4424AD0F4D07864A945E9D43B84BCE5B51E63AD7941B5CE45BC6E5887A705475`
- Status: UNCHANGED ✅

Phase 20.3 build:
- SHA-256: `6F213C793AB8C8329CBC80B8916B4B2B5A1A8653595433F350DBF90D5BCB93EB`
- Status: UNCHANGED ✅

## Known Issues

None identified. Awaiting manual verification.

## Status

**READY FOR USER VERIFICATION**

Phase 20.4 HTML/CSS Splash implementation complete. Build ready for manual testing. Do not declare PASS until user manually verifies HTML/CSS Splash appears correctly on 5 launches.

**DO NOT PROCEED** with Phase 20 UAT until Splash verification complete.
