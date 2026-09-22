# Phase 20.12 – Music Control Fix + Player UI Labels + 12-Hour Time Display

**Date:** 2026-09-19  
**Build:** Phase20-12-Music-Control-UI-12H  
**EXE:** E:\prayer-music-guard\dist\Phase20-12-Music-Control-UI-12H\PrayerMusicGuard\PrayerMusicGuard.exe  
**Size:** 4,240,400 bytes  
**SHA256:** DF8747DA0EC59DE4BD3820A6A5E5F0B1851A2B223D9D8E003CBF4548795849A6

## Summary
Phase 20.12 addresses the remaining issues from Phase 20.11:
- Manual and automatic pause/resume for VLC now attempt reliable WM_APPCOMMAND delivery instead of unreliable global media-key toggle.
- UI player label changed from “المشغّل المحمي” to “المشغّل”.
- Prayer times displayed in 12-hour Arabic format HH:MM ص/م, internal calculations remain 24-hour.
- No prayer calculation, splash, or dashboard layout changes.

## Root Cause Analysis
Phase 20.11 left VLC on global media-key fallback:
- `needs_media_key_fallback` forced VLC into `media_toggle()` via `keybd_event(VK_MEDIA_PLAY_PAUSE)`.
- Toggle is stateful, routes to system media session, and gives no feedback.
- WM_APPCOMMAND lParam was encoded as `command << 16` only, missing device flags.

## Changes Made

### main.py
- **send_appcommand**: now uses `lparam = (command << 16) | 0xC000` for correct WM_APPCOMMAND encoding.
- **NO_APPCOMMAND_STEMS** removed.
- **needs_media_key_fallback**: simplified to Win7 Chromium browsers only. VLC is no longer forced to media-key fallback, allowing WM_APPCOMMAND attempt.

### webview_app/frontend/index.html
- Line 110: `<span class="stat__label">المشغّل المحمي</span>` → `<span class="stat__label">المشغّل</span>`
- Line 144 hint updated: “الوقت يُعرض بنظام 12 ساعة (HH:MM ص/م). التعديل اليدوي بقيم 24 ساعة (HH:MM).”

### Backend consistency
- backend_api.py already uses `_MAIN.format_time_12()` in `_display()` and `get_state()`. No change needed, but verified.
- `format_time_12` in main.py remains unchanged.

## Build & Verification
- Backup created: `backup\phase20_12_music_control_ui_12h_20260919_053352\`
- Syntax checks PASS for main.py and backend_api.py
- UI label change verified
- send_appcommand uses 0xC000 flag
- needs_media_key_fallback(VLC) = False
- format_time_12 produces correct Arabic 12-hour output
- Build EXE exists and previous builds Phase20-11 and Phase20-8 remain untouched

## Manual Test Steps
1. Launch `PrayerMusicGuard.exe` from Phase20-12 build.
2. Settings tab → select VLC executable.
3. Click “إيقاف مؤقت” – VLC should pause immediately.
4. Click “استئناف الآن” – VLC should resume.
5. Verify automatic pause at prayer time (simulate via scheduler tick test).
6. Dashboard: verify player label shows “المشغّل” not “المشغّل المحمي”.
7. Verify prayer cards show times in HH:MM ص/م format.
8. Verify times editor hint mentions 12-hour display.

## Rollback
Restore files from backup:
```
Copy-Item E:\prayer-music-guard\backup\phase20_12_music_control_ui_12h_20260919_053352\main.py E:\prayer-music-guard\main.py
Copy-Item E:\prayer-music-guard\backup\phase20_12_music_control_ui_12h_20260919_053352\backend_api.py E:\prayer-music-guard\webview_app\backend_api.py
Copy-Item E:\prayer-music-guard\backup\phase20_12_music_control_ui_12h_20260919_053352\index.html E:\prayer-music-guard\webview_app\frontend\index.html
Copy-Item E:\prayer-music-guard\backup\phase20_12_music_control_ui_12h_20260919_053352\app.js E:\prayer-music-guard\webview_app\frontend\js\app.js
```
Then rebuild Phase20-11.

## Notes
- If WM_APPCOMMAND still fails for a specific VLC build, the control path can be extended with a child-window search or explicit process-specific media session. Current change removes the forced toggle and uses correct lParam encoding.
- Internal times storage remains 24-hour; only display is formatted.

## Files Modified
- E:\prayer-music-guard\main.py
- E:\prayer-music-guard\webview_app\frontend\index.html

## Evidence
- PHASE20_12_ROOT_CAUSE_ANALYSIS.md created
- test_phase20_12.py created and executed
