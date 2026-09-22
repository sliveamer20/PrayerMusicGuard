# Phase 20.9 — Remaining UI & Functional UAT Audit

## Build Under Test
**Phase 20.8 build** – Splash timing refined
- Build path: `E:\prayer-music-guard\dist\Phase20-8-Splash-Timing\PrayerMusicGuard\PrayerMusicGuard.exe`
- SHA-256: `FD0C7C4667ABDDCAF518B6FDDF51E38030B1D396C6B4E37B10075226AC3ED9A7`
- Status: Last manually verified build for Splash

## Already Verified
- HTML/CSS Splash: PASS
- Arabic title: PASS
- Loading bar: PASS
- Animation: PASS
- No white screen: PASS
- No Tkinter Splash in normal path: PASS
- Splash timing ~3s: PASS
- Dashboard: PASS
- Music Player Dropdown Background/Text/Selection/Hover: PASS

## UAT Table

### 1. Music Player Selection

**TEST:** Open program → open music-player/program selection list → select currently running music/audio player → confirm selected process/program displayed correctly.

**RESULT:** NOT TESTED

**EVIDENCE:** Manual interaction required with live running processes. Code review shows:
- `refresh_processes()` daemon thread runs every 15s
- `process_rows()` uses PowerShell `Get-Process` to enumerate running processes
- Installed apps scanned via WinReg + Start Menu PowerShell
- Combobox values populated via `apply_values()`

**NOTES:** Cannot verify process enumeration accuracy without live system. Static analysis shows PowerShell spawning on each refresh with potential overlapping spawns between worker thread and manual refresh.

### 2. Pause Function

**TEST:** Confirm selected music player can actually be paused/stopped by Prayer Music Guard. Confirm no UI freeze occurs.

**RESULT:** NOT TESTED

**EVIDENCE:** Code review shows:
- `App.pause_target()` uses `SendMessageTimeoutW` with `WM_APPCOMMAND` → `APPCOMMAND_MEDIA_PAUSE`
- Fallback to global media key for Windows 7 browsers
- `SMTO_ABORTIFHUNG` flag with 200ms timeout

**NOTES:** Pause requires actual media player window HWND. Cannot verify without live player. Potential issue: `player_hwnds()` uses `EnumWindows` with PID matching – may miss UWP apps.

### 3. Prayer Time Behavior

**TEST:** Verify next prayer identified correctly, correct prayer highlighted in green, NEXT prayer highlighted, check transition.

**RESULT:** NOT TESTED

**EVIDENCE:** Code review shows:
- `tick()` runs every 5s, `TRIGGER_CATCHUP_MINUTES = 5`
- Prayer due check: `0 <= now_minutes - _hhmm_to_minutes(t) < TRIGGER_CATCHUP_MINUTES`
- `refresh_dashboard()` highlights next prayer with `PrayerNext.TLabel/TEntry` style
- `self.done` set tracks completed prayers per day

**NOTES:** Logic appears correct per static analysis. Manual verification requires waiting for actual prayer times or mocking clock.

### 4. Automatic Resume

**TEST:** Verify music resumes after configured delay following prayer time. Confirm resume happens only once. Confirm no repeated pause/resume loop.

**RESULT:** NOT TESTED

**EVIDENCE:** Code review shows:
- `self.resume_at = now + timedelta(minutes=data["minutes"])`
- `tick()` checks `if self.resume_at and now >= self.resume_at:` → `resume_now()`
- `self._active_prayer` set on pause, cleared after resume

**NOTES:** Potential race: `tick()` runs every 5s, resume check may fire across multiple ticks if `resume_at` not cleared immediately. Static analysis shows `resume_now()` does not clear `self.resume_at` explicitly – may need verification.

### 5. Music Player UI During Operations

**TEST:** While pause/resume occurs, confirm music player UI does not freeze and Prayer Music Guard remains responsive.

**RESULT:** NOT TESTED

**EVIDENCE:** Code uses `SendMessageTimeoutW` with `SMTO_ABORTIFHUNG` and 200ms timeout to avoid hanging. `pause_target` and `resume_now` run in main Tk thread.

**NOTES:** Blocking SendMessageTimeout in UI thread could cause brief UI freeze on hung target window. Cannot verify without live test.

### 6. Text File / Process Behavior

**TEST:** Verify application does NOT repeatedly open and close text files. Watch for repeated external windows/processes.

**RESULT:** NOT TESTED – STATIC ANALYSIS FINDINGS

**EVIDENCE:** Static analysis reveals:
- `process_rows()` spawns PowerShell every call
- Background worker `_process_rows_worker()` runs every 15s → continuous PowerShell spawns
- Manual `refresh_processes()` spawns additional PowerShell thread
- No rate-limit or lock between worker and manual refresh → overlapping spawns possible
- `startmenu_apps()` uses PowerShell COM object for Start Menu links

**NOTES:** This is a potential issue. Repeated PowerShell spawning may cause CPU churn and process proliferation, especially on Windows 7. Requires monitoring with Process Explorer.

### 7. System Tray

**TEST:** Confirm Prayer Music Guard appears correctly in Windows system tray. Right-click icon, verify context menu, verify "Open Program" works, verify tray icon click behavior.

**RESULT:** NOT TESTED

**EVIDENCE:** Code review shows:
- `pystray.Icon` created with menu items: فتح البرنامج, بدء/إيقاف المراقبة, استئناف الموسيقى الآن, خروج
- `hide_to_tray()` withdraws root window
- `show_window()` deiconifies and focuses

**NOTES:** Requires manual Windows tray interaction. Cannot verify icon rendering or menu behavior statically.

### 8. General Stability

**TEST:** Leave program running, interact with Dashboard, change settings, confirm no crashes, freezes, repeated windows, abnormal CPU.

**RESULT:** NOT TESTED

**EVIDENCE:** Code review shows:
- `tick()` runs every 5s indefinitely
- `refresh_processes()` daemon thread runs every 15s
- Settings saved atomically with temp file replace
- Single-instance mutex via `Global\PrayerMusicGuard_SingleInstance`

**NOTES:** Long-running stability requires extended manual test. Potential concerns: PowerShell process leak from overlapping spawns, memory growth from process cache without lock.

## Summary

**Tests Performed:** 0 manual tests performed in this phase
**PASS:** 0
**FAIL:** 0
**NOT TESTED:** 8 of 8 functional UAT items

## Static Analysis Findings

### Potential Issues Identified

1. **PowerShell Process Spawning Churn**
   - `process_rows()` + `installed_apps()` + `startmenu_apps()` all spawn PowerShell
   - Background worker runs every 15s
   - Manual refresh spawns parallel thread
   - No locking between worker and manual refresh
   - Severity: MEDIUM
   - Risk: CPU churn, process proliferation on slow systems

2. **Process Cache Race Condition**
   - `self._process_rows` written by worker thread, read by UI thread via `after(0)`
   - No thread lock around cache
   - Severity: LOW

3. **Resume Timing**
   - `self.resume_at` not cleared immediately after `resume_now()`
   - Could cause repeated resume attempts across ticks
   - Requires verification

## Recommended Next Phase

**UAT INCOMPLETE**

Manual testing is required for all functional items. No failures can be confirmed or ruled out without live interaction.

**Recommended next action:** Schedule manual UAT session with user to perform items 1-8 above. Provide checklist and capture screenshots/logs for each step.

If PowerShell spawning issue confirmed, recommend **Phase 21 — Process Enumeration Optimization** to debounce refreshes and add thread locking.

## Final Status

**UAT INCOMPLETE**

No code changes made. No failures discovered in static analysis that can be confirmed without manual testing. Report documents test gaps and static analysis observations for next phase planning.

---
*Phase 20.9 conducted read-only. No source code modified. No builds created.*
