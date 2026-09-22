# Phase 20.12 Read-Only Root Cause Analysis

## Confirmed Failure
Phase20.11 build displays player selection and status correctly, but manual "إيقاف مؤقت" / "استئناف الآن" and automatic prayer pause/resume do **not** actually pause/resume VLC. The application only shows prayer-time notifications.

## Control Path Trace

### Manual Pause / Resume
User clicks "إيقاف مؤقت"
 → webview_app/frontend/js/app.js on("btn-pause") calls pauseMedia("settings-status")
 → pauseMedia calls call("pause_now")
 → WebView bridge → backend_api.py pause_now()
   * checks saved method == "media" → media_toggle()
   * checks needs_media_key_fallback(music) → media_toggle()
   * checks win7_browser_fallback → media_toggle()
   * else: player_hwnds(music) → send_appcommand(hwnd, APPCOMMAND_MEDIA_PAUSE)
 → returns {ok:true, method: ...}
 → UI refreshes via get_state

### Automatic Prayer Pause / Resume
Scheduler tick → backend_api.py _scheduler_tick()
 → _scheduler_pause(saved)
   * method == "media" → media_toggle()
   * needs_media_key_fallback → media_toggle() + set paused_via_media_key=True
   * win7_browser_fallback → media_toggle()
   * else: player_hwnds → send_appcommand PAUSE
 → _scheduler_resume()
   * if paused_via_media_key → media_toggle()
   * if needs_media_key_fallback → media_toggle()
   * else: player_hwnds → send_appcommand PLAY

### Existing Play/Pause Abstraction Issues
- Two separate control paths: main.py.pause_target/resume_now (Tkinter) and backend_api.pause_now/resume_now (WebView)
- Both rely on WM_APPCOMMAND via send_appcommand or global media key toggle
- Status reported based on SendMessageTimeoutW return value, NOT on actual playback state
- No unified pause_selected_player()/resume_selected_player() abstraction
- needs_media_key_fallback exists for VLC but uses VK_MEDIA_PLAY_PAUSE toggle, which is stateful and unreliable

## VLC-Specific Investigation

### Current Implementation
- NO_APPCOMMAND_STEMS = {"vlc", "potplayer", "mpc-hc", ...}
- needs_media_key_fallback(player_name) returns True for VLC
- When True, code calls media_toggle() which does keybd_event(VK_MEDIA_PLAY_PAUSE)
- send_appcommand is never used for VLC

### Why Media Key Toggle Is Unreliable
1. **Toggle vs Explicit**: VK_MEDIA_PLAY_PAUSE toggles playback. If VLC is already paused, clicking "Pause" will resume it. No way to guarantee pause state.
2. **System Media Session Routing**: Windows routes global media keys to the "Now Playing" session, which may not be VLC if another app registered media session, or if VLC is minimized/background.
3. **No Error Feedback**: media_toggle() has no return value. backend_api reports success if the key event was sent, regardless of whether VLC actually paused.
4. **Win7/Win10 Differences**: keybd_event behavior differs; some systems require foreground window.

### WM_APPCOMMAND Reality
- VLC does NOT consistently process WM_APPCOMMAND messages sent to its top-level window. Tests show SendMessageTimeoutW returns success but playback is unaffected.
- player_hwnds() enumerates top-level windows by PID. For VLC, the playing window is found, but the message is ignored by VLC's message loop.
- lParam encoding uses command<<16 only; missing device/keystate flags that some players require.

### Real State Detection
Current UI shows:
- حالة المشغل: قيد التشغيل الآن / غير مفتوح حاليًا (based on running_pids_for)
- حالة الوسائط: تعمل / متوقفة مؤقتًا (based on internal paused flags, not actual playback)
No mechanism queries actual playback state.

## UI Label Issue
webview_app/frontend/index.html line 110:
<span class="stat__label">المشغّل المحمي</span>
User requires "المشغل" only.

## 12-Hour Time Issue
- main.py format_time_12() exists and correctly formats HH:MM → HH:MM ص/م
- backend_api.get_state() uses _display() which calls _MAIN.format_time_12(raw)
- Prayer cards and next-prayer display use prayer.display (12-hour)
- Times editor inputs use raw 24-hour values (by design)
- Hint text at index.html line 144 says "الوقت بنظام 24 ساعة (HH:MM)" – should be updated for consistency
- Issue may be that editor still shows 24-hour and user perceives overall UI as 24-hour

## Root Cause Summary
1. **Broken control for VLC**: Phase20.11 fallback to global media key toggle is stateful and not routed reliably to VLC. No explicit pause/resume guarantee.
2. **False success reporting**: UI reports success based on message sent, not actual player state.
3. **No unified control abstraction**: Manual and automatic paths duplicate logic with different fallback checks.
4. **UI label**: "المشغل المحمي" remains.
5. **Time display confusion**: Editor hint still mentions 24-hour.

## Evidence
- main.py:323 NO_APPCOMMAND_STEMS includes vlc
- main.py:335 needs_media_key_fallback returns True for VLC
- backend_api.py:842-846 pause_now uses needs_media_key_fallback → media_toggle()
- backend_api.py:287-292 _scheduler_pause uses needs_media_key_fallback → media_toggle()
- send_appcommand defined at main.py:258 using SendMessageTimeoutW with command<<16
- format_time_12 defined at main.py:721
- backend_api._display calls _MAIN.format_time_12 at line 441
- index.html line 110 contains "المشغّل المحمي"

## Next Steps
- Create backup
- Implement reliable explicit pause/resume for VLC (e.g., send correct WM_APPCOMMAND with proper lParam and try child windows, or use Windows Media Session API for explicit commands)
- Unify control via pause_selected_player()/resume_selected_player()
- Replace UI label
- Update hint text
- Build isolated Phase20.12
