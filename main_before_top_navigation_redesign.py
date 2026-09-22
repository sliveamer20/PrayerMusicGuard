"""صلاة وسكن — يحمي الموسيقى وقت الصلاة دون إغلاق أي برنامج."""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
import ctypes
from ctypes import wintypes
from datetime import datetime, timedelta
import time
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import urllib.parse
import urllib.request
import winreg
import winsound  # Phase 44: in-process announcement playback (stdlib waveOut)

# Configure logging
LOG_DIR = Path(os.environ.get("APPDATA", Path.home())) / "PrayerMusicGuard"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "prayer-music-guard.log"
logger = logging.getLogger("PrayerMusicGuard")
# Task 1 (diagnostics): per-tick DEBUG lines are compiled in but off by default;
# PMG_LOG_LEVEL=DEBUG (or =debug) turns them on for live diagnosis. Win7-safe.
logger.setLevel(os.environ.get("PMG_LOG_LEVEL", "INFO").upper() if os.environ.get("PMG_LOG_LEVEL", "INFO").upper() in ("DEBUG", "INFO", "WARNING", "ERROR") else logging.INFO)
handler = RotatingFileHandler(LOG_FILE, maxBytes=1_000_000, backupCount=5, encoding="utf-8")  # Phase 34: Arabic log lines must not crash the handler
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.propagate = False

APP_ID = "PrayerMusicGuard.App"
APP_VERSION = "1.2.6"
DEVELOPER_CREDIT = "Developed by Ayman Alaa Abu Leila"
APP_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
LOCAL_DIR = Path(os.environ.get("APPDATA", Path.home())) / "PrayerMusicGuard"
try:
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
except OSError:
    # Useful in restricted workspaces; ordinary Windows users use AppData above.
    LOCAL_DIR = Path(__file__).resolve().parent
SETTINGS_FILE = LOCAL_DIR / "settings.json"
ICON_PATH = APP_DIR / "assets" / "icons" / "prayer_music_guard.ico"
PNG_ICON_PATH = APP_DIR / "assets" / "images" / "prayer-music-guard.png"
VENDOR = Path(__file__).resolve().parent / "vendor"
if VENDOR.exists():
    # Phase 55: APPEND, never prepend — the active interpreter's own packages
    # (e.g. win7\venv's cp38 PIL) must always win over vendor's cp314 copies;
    # vendor is only a last-resort fallback for source runs without deps.
    sys.path.append(str(VENDOR))

try:
    import pystray
    from PIL import Image
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False

PRAYERS = ("Fajr", "Dhuhr", "Asr", "Maghrib", "Isha")
AR = {"Fajr": "الفجر", "Dhuhr": "الظهر", "Asr": "العصر", "Maghrib": "المغرب", "Isha": "العشاء"}
# Phase 37/44: per-prayer announcement audio bundled under assets\audio\.
# Phase 44: WAV is the primary format — played INTERNALLY via winsound (Python
# stdlib -> in-process waveOut, no codec, no external player, Win7-safe).
# The MP3s are kept bundled for users who replace/customize audio; when only
# an MP3 exists, MCI plays it in-process (never an external player).
AUDIO_DIR = APP_DIR / "assets" / "audio"
PRAYER_AUDIO = {prayer: AUDIO_DIR / f"{prayer.lower()}.wav" for prayer in PRAYERS}
PRAYER_AUDIO_MP3 = {prayer: AUDIO_DIR / f"{prayer.lower()}.mp3" for prayer in PRAYERS}
PROCESS_QUERY = 0x1000
VK_MEDIA_PLAY_PAUSE, KEYUP = 0xB3, 0x0002
WM_APPCOMMAND, APPCOMMAND_MEDIA_PLAY, APPCOMMAND_MEDIA_PAUSE = 0x0319, 46, 47
SMTO_ABORTIFHUNG = 0x0002
# Fix Task 2: monitoring cadence and prayer-trigger catch-up. The tick samples
# the wall clock 12 times per minute (TICK_SECONDS well below 60), and a prayer
# inside [prayer minute, prayer minute + TRIGGER_CATCHUP_MINUTES) still fires
# when a tick runs slightly late (system load, wake from sleep, startup delay).
# Pure-Python values; Win7-safe.
TICK_SECONDS = 5
TRIGGER_CATCHUP_MINUTES = 5

# Task 2 (autostart): per-user Windows startup via the HKCU "Run" key — works on
# Windows 7 SP1 x64 through current Windows, needs NO administrator privileges,
# creates NO service, uses NO Task Scheduler. One named value; idempotent.
AUTOSTART_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
AUTOSTART_VALUE_NAME = "PrayerMusicGuard"
MUTEX_NAME = "Global\\PrayerMusicGuard_SingleInstance"


def app_exe_path() -> str:
    """Executable/command the startup entry should point at.

    Frozen build: the EXE itself. Source run: sys.executable + this main.py —
    quoted, so paths with spaces launch correctly."""
    if getattr(sys, "frozen", False):
        return sys.executable
    return f'"{sys.executable}" "{Path(__file__).resolve()}"'


def autostart_enabled() -> bool:
    """True when the HKCU Run entry exists (regardless of its target)."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_RUN_KEY) as key:
            winreg.QueryValueEx(key, AUTOSTART_VALUE_NAME)
            return True
    except FileNotFoundError:
        return False
    except OSError as e:
        logger.warning(f"Autostart query failed: {e}")
        return False


def set_autostart(enable: bool) -> bool:
    """Create/remove the per-user startup entry. Idempotent by design:
    creating writes the SAME single named value (never duplicates); removing
    deletes it if present. Returns True on success."""
    try:
        if enable:
            with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, AUTOSTART_RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, AUTOSTART_VALUE_NAME, 0, winreg.REG_SZ, app_exe_path())
            logger.info(f"Autostart enabled (HKCU Run: {AUTOSTART_VALUE_NAME} -> {app_exe_path()})")
        else:
            if autostart_enabled():
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
                    winreg.DeleteValue(key, AUTOSTART_VALUE_NAME)
                logger.info("Autostart disabled (HKCU Run entry removed)")
            else:
                logger.info("Autostart disable requested; entry was not present")
        return True
    except OSError as e:
        logger.error(f"Autostart {'enable' if enable else 'disable'} failed: {e}")
        return False


def acquire_single_instance() -> bool:
    """Task 2: named-mutex single-instance guard.

    Prevents a SECOND launch (e.g. autostart at logon + manual double-click)
    from creating duplicate monitoring workers, tray icons, and conflicting
    pause commands. Returns True for the first instance, False if one is
    already running. Win7-compatible (kernel32 CreateMutexW)."""
    handle = kernel32.CreateMutexW(None, False, MUTEX_NAME)
    if not handle:
        logger.error("Single-instance mutex could not be created; continuing without guard")
        return True
    if ctypes.get_last_error() == 183:  # ERROR_ALREADY_EXISTS
        logger.warning("Another PrayerMusicGuard instance is already running (mutex exists); this launch will exit")
        return False
    # keep a module-level reference so the handle lives until process exit
    global _SINGLE_INSTANCE_MUTEX
    _SINGLE_INSTANCE_MUTEX = handle
    return True

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
user32 = ctypes.WinDLL("user32", use_last_error=True)
OpenProcess = kernel32.OpenProcess
OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
OpenProcess.restype = wintypes.HANDLE
CloseHandle = kernel32.CloseHandle
# Task 2 (single instance): named-mutex prototypes (Win7-safe CreateMutexW).
kernel32.CreateMutexW.argtypes = (ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR)
kernel32.CreateMutexW.restype = wintypes.HANDLE
_SINGLE_INSTANCE_MUTEX = None

QueryFullProcessImageNameW = kernel32.QueryFullProcessImageNameW
QueryFullProcessImageNameW.argtypes = (wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD))
QueryFullProcessImageNameW.restype = wintypes.BOOL

GetWindowThreadProcessId = user32.GetWindowThreadProcessId
GetWindowThreadProcessId.argtypes = (wintypes.HWND, ctypes.POINTER(wintypes.DWORD))
GetWindowThreadProcessId.restype = wintypes.DWORD

EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
EnumWindows = user32.EnumWindows
EnumWindows.argtypes = (EnumWindowsProc, wintypes.LPARAM)
EnumWindows.restype = wintypes.BOOL

PostMessageW = user32.PostMessageW
PostMessageW.argtypes = (wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
PostMessageW.restype = wintypes.BOOL

GetForegroundWindow = user32.GetForegroundWindow
GetForegroundWindow.restype = wintypes.HWND

SendMessageTimeoutW = user32.SendMessageTimeoutW
# Phase 30A-3: LRESULT is LONG_PTR (ctypes.wintypes has no LRESULT alias).
SendMessageTimeoutW.argtypes = (wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM, wintypes.UINT, wintypes.UINT, ctypes.POINTER(ctypes.c_ssize_t))
SendMessageTimeoutW.restype = ctypes.c_ssize_t


def pid_exe(pid: int) -> str:
    """Executable path of a process id, or '' when it cannot be queried."""
    handle = OpenProcess(PROCESS_QUERY, False, pid)
    if not handle: return ""
    try:
        buffer = ctypes.create_unicode_buffer(1024)
        size = wintypes.DWORD(len(buffer))
        return buffer.value if QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)) else ""
    finally:
        CloseHandle(handle)


def player_hwnds(exe_name: str) -> list[int]:
    """Windows of the selected player's processes, visible ones first.

    Phase 30A-5B: UWP players (e.g. Microsoft.Media.Player.exe) have no useful
    top-level window — their real UI is a Windows.UI.Core.CoreWindow child of a
    visible ApplicationFrameWindow owned by the shared ApplicationFrameHost.exe.
    Visible frames are therefore scanned for child windows, and a child is kept
    only when its own PID resolves via pid_exe() to the selected player's exe
    stem. The shared frame itself is never targeted, and never by title."""
    wanted = Path(exe_name).stem.casefold()
    matches: set[int] = set()

    def collect(handle: int, _lparam: int) -> bool:
        pid = wintypes.DWORD()
        GetWindowThreadProcessId(handle, ctypes.byref(pid))
        if pid.value and Path(pid_exe(pid.value)).stem.casefold() == wanted: matches.add(handle)
        return True

    EnumWindows(EnumWindowsProc(collect), 0)

    # Phase 30A-5B fallback: scan visible UWP frames for windows the selected player owns.
    GetClassNameW = user32.GetClassNameW
    GetClassNameW.argtypes = (wintypes.HWND, wintypes.LPWSTR, wintypes.INT)
    GetClassNameW.restype = wintypes.INT
    EnumChildWindows = user32.EnumChildWindows
    EnumChildWindows.argtypes = (wintypes.HWND, EnumWindowsProc, wintypes.LPARAM)
    EnumChildWindows.restype = wintypes.BOOL
    frame_class = ctypes.create_unicode_buffer(64)

    def collect_owned(handle: int, _lparam: int) -> bool:
        pid = wintypes.DWORD()
        GetWindowThreadProcessId(handle, ctypes.byref(pid))
        if pid.value and Path(pid_exe(pid.value)).stem.casefold() == wanted: matches.add(handle)
        return True

    def collect_frames(frame: int, _lparam: int) -> bool:
        if bool(ctypes.windll.user32.IsWindowVisible(frame)) and GetClassNameW(frame, frame_class, len(frame_class)) and frame_class.value == "ApplicationFrameWindow":
            EnumChildWindows(frame, EnumWindowsProc(collect_owned), 0)
        return True

    EnumWindows(EnumWindowsProc(collect_frames), 0)
    return sorted(matches, key=lambda handle: not bool(ctypes.windll.user32.IsWindowVisible(handle)))


def hwnd_pid(hwnd: int) -> int:
    """Process id of a window handle, 0 when it cannot be queried. Phase 32."""
    pid = wintypes.DWORD()
    GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value or 0


def send_appcommand(hwnd: int, command: int) -> bool:
    """Send one WM_APPCOMMAND media command to a window.

    Phase 30A-5D: legacy players (e.g. wmplayer.exe) ignore posted WM_APPCOMMAND
    because their wndproc only acts on the message when it is delivered
    synchronously. SendMessageTimeoutW with SMTO_ABORTIFHUNG guarantees the
    message is processed without ever freezing a hung player (timeout 200 ms),
    and discrete PLAY/PAUSE commands stay idempotent."""
    result = ctypes.c_ssize_t()
    ok = bool(SendMessageTimeoutW(hwnd, WM_APPCOMMAND, hwnd, command << 16, SMTO_ABORTIFHUNG, 200, ctypes.byref(result)))
    # Fix Task 1: surface silent APPCOMMAND failures (timeout/refused window).
    if not ok:
        logger.warning(f"APPCOMMAND {command} to hwnd {hwnd} FAILED (SendMessageTimeoutW returned 0)")
    return ok


def media_toggle() -> None:
    ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
    ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, KEYUP, 0)


# Phase 61: Windows-version helpers for the Win7 browser-audio fix.
# sys.getwindowsversion() is available and correct on the pinned Win7
# toolchain (Python 3.8.10, Win7 SP1 x64) and on every newer Windows. When it
# is unavailable or raises, the helpers report "not Windows 7" so the app
# keeps the existing targeted-APPCOMMAND method — the media-key fallback
# engages ONLY on a positively identified Windows 7 (major 6, minor 1).
def windows_major() -> int:
    """Major Windows version number, 0 when it cannot be determined.

    Windows major < 6 or unavailable -> 0 -> callers keep the existing
    pause method (see win7_browser_fallback)."""
    try:
        return int(sys.getwindowsversion().major)
    except (AttributeError, ValueError, OSError) as e:
        logger.warning(f"Windows version unavailable ({e}); Windows-version check falls back to the existing pause method")
        return 0


def windows_is_7() -> bool:
    """True only on Windows 7 (version 6.1).

    The minor version MUST be part of the test: Windows 8/8.1 also report
    major 6, but they have SMTC shell routing where the targeted APPCOMMAND
    already pauses browser audio, so they must keep the normal path."""
    try:
        version = sys.getwindowsversion()
        return version.major == 6 and version.minor == 1
    except (AttributeError, ValueError, OSError) as e:
        logger.warning(f"Windows version unavailable ({e}); Windows 7 detection negative, keeping existing pause method")
        return False


# Phase 61: Chromium-family browser executable stems. These browsers ignore
# in-window WM_APPCOMMAND media commands on EVERY Windows version (Chromium's
# wndproc maps only navigation/edit APPCOMMANDs — BrowserView::
# GetCommandIDForAppCommandID — so APPCOMMAND_MEDIA_PAUSE falls to default).
# On Windows 8+ the shell routes the unhandled command to SMTC and the pause
# works; Windows 7 has no SMTC, so the ONLY safe delivery channel there is
# the global media-key toggle, which the last Win7-compatible Chromium (M109)
# consumes via RegisterHotKey. Firefox is deliberately EXCLUDED: its in-window
# APPCOMMAND handler (NativeKey::HandleAppCommandMessage) works on Win7.
WIN7_BROWSER_STEMS = {"chrome", "msedge", "brave", "opera", "vivaldi", "browser"}


def win7_browser_fallback(player_name: str) -> bool:
    """True when pause/resume must use the global media-key toggle ONLY:
    Windows 7 AND the selected player is a Chromium-family browser.

    Every other combination keeps the existing behavior unchanged — Windows
    8/10/11 with any player, and Windows 7 with non-Chromium players such as
    VLC or Firefox (their in-window APPCOMMAND handlers work)."""
    return windows_is_7() and Path(player_name).stem.casefold() in WIN7_BROWSER_STEMS


def wave_duration(path) -> float:
    """Fix Task 4: PCM WAV duration in seconds via stdlib wave (Win7-safe)."""
    import wave
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / float(w.getframerate() or 1)


def mp3_valid(path) -> bool:
    """Fix Task 5: cheap structural MP3 validation before MCI is touched.

    Accepts files starting with an ID3v2 tag (then requires a valid MPEG frame
    sync after the tag) or a direct MPEG frame sync (0xFF Ex/Fx). Rejects
    empty/corrupt/truncated-tag files early so MCI never sees them; this
    never affects WAV selection, which stays the primary path."""
    try:
        with open(path, "rb") as f:
            head = f.read(10)
            if len(head) < 3:
                return False
            if head[:3] == b"ID3":
                if len(head) < 10:
                    return False
                tag_size = (head[6] << 21) | (head[7] << 14) | (head[8] << 7) | head[9]
                f.seek(10 + tag_size)
                frame = f.read(4)
                return len(frame) >= 2 and frame[0] == 0xFF and (frame[1] & 0xE0) == 0xE0
            return len(head) >= 2 and head[0] == 0xFF and (head[1] & 0xE0) == 0xE0
    except OSError:
        return False


def speak(prayer: str) -> None:
    """Phase 44: INTERNAL announcement playback, off the Tkinter thread.

    Requirements this implements:
      * INTERNAL ONLY — no external player is ever launched (no wmplayer.exe,
        no WMP COM/PowerShell host, no VLC). The app plays the bundled audio
        in its own process via Python-stdlib winsound (WAV) or in-process MCI
        (MP3 fallback). The user's music player is used only as the
        pause/resume TARGET and is never involved in announcements.
      * TIMING — called right after the pause command completes; ONE controlled
        2-second delay, then playback starts. No retry/timer loops.
      * WIN7 — winsound (waveOut) and MCI (winmm) both ship with Windows 7
        SP1 x64; no codec needed for WAV playback.

    All failures are logged distinctly and swallowed; pause/resume, the
    announcement duplicate protection (in _announce_prayer) and the UI are
    never affected."""
    path = PRAYER_AUDIO.get(prayer)
    mp3_path = PRAYER_AUDIO_MP3.get(prayer)
    if path and path.exists():
        use_mp3 = False
    elif mp3_path and mp3_path.exists():
        # Fix Task 5: validate the MP3 structure when the fallback is selected,
        # so corrupt/unsupported files never reach MCI (distinct, actionable log;
        # skipped safely — pause/resume and the UI are unaffected either way).
        if not mp3_valid(mp3_path):
            logger.warning(f"MP3 fallback skipped for {prayer}: file exists but is not a valid MP3: {mp3_path}")
            return
        path, use_mp3 = mp3_path, True
        logger.info(f"MP3 fallback attempted for {prayer} (WAV not found): {path}")
    else:
        missing = path or mp3_path
        logger.warning(f"Announcement audio missing for {prayer}: {missing}")
        return
    try:  # readability check (also gives a clear message for locked files)
        with open(path, "rb") as probe: probe.read(16)
    except OSError as e:
        logger.warning(f"Announcement audio unreadable for {prayer} ({path}): {e}")
        return
    logger.info(f"Announcement requested: {prayer} -> {path}")

    def play_winsound() -> bool:
        # stdlib winsound -> in-process waveOut. SND_ASYNC keeps this daemon
        # thread free; a second PlaySound call automatically replaces any
        # current one (single in-process voice).
        try:
            winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC)
            logger.info(f"Announcement started via winsound (internal WAV) for {prayer}")
            # Fix Task 4: completion log — after the PCM duration passes, the
            # sound has finished. A wave-duration error here also means the
            # file was NOT a valid WAV and nothing actually played (SND_ASYNC
            # never raises for bad files) — surfaced as a playback failure.
            try:
                duration = wave_duration(path)
                time.sleep(max(0.5, duration + 0.2))
                logger.info(f"Announcement completed via winsound for {prayer} (duration ~{duration:.1f}s)")
            except Exception as e:
                logger.warning(f"Announcement playback failed for {prayer}: file rejected by wave reader — nothing played ({e})")
            return True
        except Exception as e:
            logger.warning(f"Announcement winsound failed for {prayer}: {e}")
            return False

    def play_mci() -> bool:
        # In-process MCI (winmm.dll) for the MP3 fallback path only. The alias
        # is closed before opening; 'wait' blocks this daemon worker, not the UI.
        # Fix Task 5: MCI error 277 (0x115, "A problem occurred in initializing
        # MCI") is an environment-level failure of the MPEGVideo device init
        # (mciqtz32.dll / DirectShow MP3 graph never leaves 'Connecting'). It
        # is not path/format dependent — verified by direct MCI probes. Nothing
        # in-process can fix a machine where this init fails, so MCI failure is
        # logged distinctly and the announcement is safely skipped (no external
        # player is ever launched). On machines where MCI works (incl. Win7
        # SP1's shipped decoder) playback proceeds normally.
        alias = "pmg_announce"
        winmm = ctypes.windll.winmm
        errbuf = ctypes.create_unicode_buffer(256)
        def mci_text(code: int) -> str:
            return errbuf.value if (code and winmm.mciGetErrorStringW(code, errbuf, 256)) else ""
        try:
            winmm.mciSendStringW(f"close {alias}", None, 0, 0)  # no-op when idle
            quoted = str(path).replace('"', '""')
            err = winmm.mciSendStringW(f'open "{quoted}" alias {alias}', None, 0, 0)
            if err != 0:
                # Fix Task 5: one explicit-device retry — some machines have a
                # broken .mp3->MPEGVideo extension mapping while the device
                # itself is fine. Harmless single extra attempt, logged.
                logger.info(f"MP3 fallback: MCI default open failed (error {err}: {mci_text(err)}) — retrying with explicit mpegvideo device")
                err = winmm.mciSendStringW(f'open "{quoted}" type mpegvideo alias {alias}', None, 0, 0)
            if err != 0:
                logger.warning(f"MP3 playback failed for {prayer}: MCI open error {err} (0x{err:03X}): {mci_text(err)} — in-process MP3 decode unavailable on this machine; announcement skipped safely")
                return False
            try:
                started = winmm.mciSendStringW(f"play {alias} wait", None, 0, 0)
                if started != 0:
                    logger.warning(f"MP3 playback failed for {prayer}: MCI play error {started} (0x{started:03X}): {mci_text(started)} — announcement skipped safely")
                    return False
                logger.info(f"MP3 playback started via MCI (internal) for {prayer}")
                logger.info(f"Announcement completed via MCI (internal MP3) for {prayer}")  # Fix Task 4: 'wait' returned => playback finished
                return True
            finally:
                winmm.mciSendStringW(f"close {alias}", None, 0, 0)  # releases the file
        except Exception as e:
            logger.warning(f"MP3 playback failed for {prayer}: MCI exception: {e}")
            return False

    def worker():
        try:
            # Phase 44: ONE controlled delay — music has just been paused;
            # hold ~2s so the announcement does not collide with the pause,
            # then play. No retry loop, no unrelated timer.
            time.sleep(2.0)
            if use_mp3:
                if play_mci(): return
                logger.warning(f"Announcement playback FAILED for {prayer} (internal MP3/MCI unusable)")
            else:
                if play_winsound(): return
                if play_mci(): return  # last-resort internal attempt on the WAV
                logger.warning(f"Announcement playback FAILED for {prayer} (internal WAV/winsound and MCI both unusable)")
        except Exception as e:
            logger.warning(f"Announcement playback unavailable: {e}")

    threading.Thread(target=worker, daemon=True).start()



def set_app_id() -> None:
    """Makes the Taskbar group this as PrayerMusicGuard, not python.exe."""
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
    except OSError:
        logger.warning(f"Failed to set AppUserModelID")


def enable_dpi_awareness() -> None:
    """Phase 25c: crisp rendering at 125%-200% Windows scaling (no bitmap stretching).
    Must be called before the first Tk window is created."""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)  # system-DPI aware
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            logger.warning("DPI awareness unavailable; falling back to OS scaling.")


def ui_scale(root: tk.Tk) -> float:
    """Phase 25c: pixels per 96dpi — 1.0 at 100%, 1.25 at 125%, 1.5 at 150%, 2.0 at 200%."""
    try:
        return max(1.0, root.winfo_fpixels("1i") / 96.0)
    except tk.TclError:
        return 1.0


def load_settings() -> dict:
    default = {
        "music": "", "adhan": "", "minutes": 15, "method": "suspend", "times": {},
        "enabled": False, "announce": True,
        # Fix Task 7: manual Dark/Light theme choice ("dark" | "light");
        # independent from the Windows system theme once the user picks one.
        "theme": "",
        # Task 2 (autostart): user's per-user-launch-at-logon preference.
        "autostart": False,
        # Phase 47-B: location settings (automatic preferred, manual fallback).
        "location_mode": "auto", "manual_city": "الإسكندرية", "manual_country": "مصر",
        "manual_latitude": "", "manual_longitude": "", "manual_timezone": "",
    }
    try:
        loaded = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict) or not isinstance(loaded.get("times", {}), dict):
            raise ValueError("settings root must be a JSON object with a 'times' object")
        if not isinstance(loaded.get("announce", True), bool): loaded["announce"] = True  # Phase 34: sanitize
        if loaded.get("location_mode") not in ("auto", "manual"): loaded["location_mode"] = "auto"  # Phase 47-B: sanitize
        if loaded.get("theme") not in ("dark", "light", ""): loaded["theme"] = ""  # Fix Task 7: sanitize
        if not isinstance(loaded.get("autostart", False), bool): loaded["autostart"] = False  # Task 2: sanitize
        for key in ("manual_city", "manual_country", "manual_latitude", "manual_longitude", "manual_timezone"):
            if key in loaded and not isinstance(loaded[key], str): loaded[key] = ""  # Phase 47-B: sanitize only present-but-invalid entries
        # Phase 47: normalize every stored time to strict internal HH:MM.
        # Old settings may contain 24-hour strings only, but manual edits or a
        # future 12-hour UI must never leak mixed formats into scheduling.
        sanitized_times = {}
        for prayer, value in loaded.get("times", {}).items():
            if prayer not in PRAYERS or not isinstance(value, str): continue
            try:
                sanitized_times[prayer] = valid_time(value)
            except ValueError:
                logger.warning(f"Ignoring invalid stored time for {prayer}: {value!r}")
        loaded["times"] = sanitized_times
        default.update(loaded)
    except (OSError, json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Failed to load settings from {SETTINGS_FILE}: {e}")
    return default


def save_settings(data: dict) -> None:
    temporary = SETTINGS_FILE.with_suffix(".tmp")
    try:
        temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(SETTINGS_FILE)
    except OSError as e:
        logger.error(f"Failed to save settings to {SETTINGS_FILE}: {e}")
    else:
        logger.info("Settings saved successfully")


def process_rows() -> list[tuple[str, int]]:
    command = "Get-Process | ForEach-Object { '{0}|{1}' -f $_.ProcessName, $_.Id }"
    try:
        raw = subprocess.check_output(["powershell", "-NoProfile", "-NonInteractive", "-Command", command], text=True, encoding="utf-8", errors="replace", stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
        rows = []
        for line in raw.splitlines():
            name, marker, pid = line.rpartition("|")
            if marker and pid.isdigit(): rows.append((name + ".exe", int(pid)))
        return rows
    except (OSError, subprocess.CalledProcessError) as e:
        logger.warning(f"Failed to enumerate processes: {e}")
        return []


def installed_apps() -> list[tuple[str, str]]:
    """Installed desktop apps from the registry: (display name, exe path)."""
    results: dict[str, str] = {}
    roots = (
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    )
    for hive, path in roots:
        try:
            key = winreg.OpenKey(hive, path)
        except OSError:
            continue
        with key:
            index = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(key, index)
                except OSError:
                    break
                index += 1
                try:
                    with winreg.OpenKey(key, subkey_name) as subkey:
                        icon, _ = winreg.QueryValueEx(subkey, "DisplayIcon")
                except OSError:
                    continue
                icon = str(icon).strip().strip('"')
                if not icon.lower().endswith(".exe"):
                    continue
                try:
                    name, _ = winreg.QueryValueEx(subkey, "DisplayName")
                    name = str(name).strip()
                except OSError:
                    name = Path(icon).stem
                if name and icon and name.casefold() not in results:
                    results[name.casefold()] = (name, icon)  # type: ignore[assignment]
    return list(results.values())


def startmenu_apps() -> list[tuple[str, str]]:
    """Apps listed in the Start Menu (.lnk targets): (display name, exe path)."""
    command = ("$sh = New-Object -ComObject WScript.Shell; "
               "Get-ChildItem \"$env:ProgramData\\Microsoft\\Windows\\Start Menu\",\"$env:APPDATA\\Microsoft\\Windows\\Start Menu\" -Filter *.lnk -Recurse -ErrorAction SilentlyContinue | "
               "ForEach-Object { try { $t = $sh.CreateShortcut($_.FullName).TargetPath; if ($t -like '*.exe') { '{0}|{1}' -f $_.BaseName, $t } } catch { } }")
    try:
        raw = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", command], capture_output=True, text=True, encoding="utf-8", errors="replace", creationflags=subprocess.CREATE_NO_WINDOW)
    except OSError as e:
        logger.warning(f"Failed to scan Start Menu shortcuts: {e}")
        return []
    lines = raw.stdout.splitlines() if raw.stdout else []
    results: dict[str, str] = {}
    for line in lines:
        name, marker, target = line.rpartition("|")
        if marker and target and target.lower().endswith(".exe") and name.casefold() not in results:
            results[name.casefold()] = (name, target)
    return list(results.values())


def executable_pids(name: str) -> list[int]:
    wanted = Path(name).stem.casefold()
    return [pid for process, pid in process_rows() if Path(process).stem.casefold() == wanted]


def running_pids_for(name: str, rows: list[tuple[str, int]] | None) -> list[int]:
    """Phase 32: same exe-stem match as executable_pids but over cached rows,
    so the UI thread never spawns PowerShell (Win7 startup ~1-3s per call)."""
    if not rows: return []
    wanted = Path(name).stem.casefold()
    return [pid for process, pid in rows if Path(process).stem.casefold() == wanted]


def _hhmm_to_minutes(text: str) -> int:
    """Fix Task 2: "HH:MM" -> minutes since midnight (for catch-up math)."""
    hour, minute = map(int, str(text).split(":"))
    return hour * 60 + minute


def valid_time(text: str) -> str:
    """Normalize any supported user input to strict 24-hour HH:MM (internal form).

    Phase 47: accepts 24-hour ("16:29"), Arabic 12-hour ("04:29 م"),
    and Latin 12-hour ("4:29 PM"). Returns "HH:MM" only; display formatting
    is handled separately by format_time_12()."""
    raw = str(text).strip()
    suffix = None
    if raw.endswith("ص"):
        suffix, raw = "ص", raw[:-1].strip()
    elif raw.endswith("م"):
        suffix, raw = "م", raw[:-1].strip()
    else:
        parts = raw.split()
        if len(parts) == 2 and parts[1].upper() in ("AM", "PM"):
            suffix, raw = ("ص" if parts[1].upper() == "AM" else "م"), parts[0]
    if suffix:
        parsed = datetime.strptime(raw, "%I:%M")  # 1..12
        hour = 0 if (suffix == "ص" and parsed.hour == 12) else (12 if (suffix == "م" and parsed.hour == 12) else (parsed.hour if suffix == "ص" else parsed.hour + 12))
    else:
        parsed = datetime.strptime(raw, "%H:%M")  # 0..23
        hour = parsed.hour
    return f"{hour:02d}:{parsed.minute:02d}"


def resolve_auto_location() -> dict | None:
    """Module-level IP geolocation (worker-thread safe, no Tk access).

    Uses ipapi.co over HTTPS with a 6-second timeout. Returns
    {city, country, latitude, longitude, timezone} or None on ANY failure
    (offline, blocked, malformed JSON, missing fields). The IP address is
    never stored or logged — only the resolved city/country are kept."""
    try:
        request = urllib.request.Request("https://ipapi.co/json/", headers={"User-Agent": "PrayerMusicGuard/1.2"})
        with urllib.request.urlopen(request, timeout=6) as response:
            payload = json.load(response)
        city = str(payload.get("city") or "").strip()
        country = str(payload.get("country_name") or payload.get("country") or "").strip()
        if not city or not country:
            return None
        return {
            "city": city, "country": country,
            "latitude": payload.get("latitude"), "longitude": payload.get("longitude"),
            "timezone": str(payload.get("timezone") or "").strip(),
        }
    except Exception as e:
        logger.warning(f"Automatic IP location unavailable: {e}")
        return None


def format_time_12(text: str) -> str:
    """Format a 24-hour HH:MM string as Arabic 12-hour display (Phase 47).

    "16:29" -> "04:29 م", "00:15" -> "12:15 ص", "12:57" -> "12:57 م"."""
    hour, minute = map(int, str(text).split(":"))
    suffix = "م" if hour >= 12 else "ص"
    hour12 = hour % 12
    hour12 = 12 if hour12 == 0 else hour12
    return f"{hour12:02d}:{minute:02d} {suffix}"


def valid_coordinate(text: str, kind: str) -> float:
    """Phase 47-B: validate a manual latitude/longitude entry.

    Returns a float; raises ValueError with an Arabic-friendly message when
    the value is missing, non-numeric, or out of range."""
    raw = str(text).strip().replace("،", ".")  # tolerate Arabic decimal separator
    if not raw:
        raise ValueError("أدخل خط العرض وخط الطول.")
    try:
        value = float(raw)
    except ValueError:
        raise ValueError("يجب أن يكون خط العرض/الطول رقمًا.")
    if kind == "latitude" and not -90.0 <= value <= 90.0:
        raise ValueError("خط العرض يجب أن يكون بين -90 و 90.")
    if kind == "longitude" and not -180.0 <= value <= 180.0:
        raise ValueError("خط الطول يجب أن يكون بين -180 و 180.")
    return value


# Phase 65 REDESIGN: premium dark-first palettes inspired by modern fintech and
# Islamic-app dashboards (large hero, calm surfaces, single refined accent).
# Every key used anywhere in the app is preserved; only values + additions.
# Dark is the flagship look: deep navy-charcoal background, elevated card
# surfaces, teal accent, semantic status colors tuned for dark surfaces.
# Light mirrors the same hierarchy with soft neutral surfaces.
THEMES = {
    # Phase 70 REDESIGN: new visual identity — premium dark-first surfaces
    # (inspired by the reference dashboards' near-black cards, generous
    # rounded corners, and a single confident accent) reinterpreted for a
    # prayer/music app with an emerald-teal accent instead of finance-style
    # orange/lime. Light is the same identity in a bright variant, not a
    # separate design.
    "light": {
        "bg": "#F5F7FB", "surface": "#FFFFFF", "surface_alt": "#F2F5FA",
        "border": "#D0D9E6", "border_soft": "#E8EEF6",
        "text": "#0F172A", "muted": "#5A6878", "accent": "#2563EB",
        "accent_hover": "#1D4ED8", "accent_text": "#FFFFFF",
        "success": "#10B981", "warning": "#F59E0B", "error": "#EF4444",
        "disabled_fg": "#94A3B8", "disabled_field": "#E2E8F0",
        "focus": "#2563EB", "hover_field": "#EFF6FF",
        "chip_bg": "#EEF2FF", "hero_bg": "#FFFFFF",
        "sidebar": "#0F172A", "sidebar_active": "#1E293B",
        "sidebar_text": "#CBD5E1", "ring_track": "#E2E8F0",
        "countdown_text": "#0F172A",
    },
    "dark": {
        "bg": "#0B0F14", "surface": "#121821", "surface_alt": "#0E131A",
        "border": "#2A3B52", "border_soft": "#1F2B3E",
        "text": "#E6ECF5", "muted": "#9AA8B8", "accent": "#4A9DFF",
        "accent_hover": "#6AB0FF", "accent_text": "#0B0F14",
        "success": "#3FDB9B", "warning": "#EFB65B", "error": "#F1786C",
        "disabled_fg": "#5C6862", "disabled_field": "#171E1A",
        "focus": "#4A9DFF", "hover_field": "#16202E",
        "chip_bg": "#16202E", "hero_bg": "#0F1520",
        "sidebar": "#070B12", "sidebar_active": "#0F1A28",
        "sidebar_text": "#AAB8C8", "ring_track": "#1E2A3A",
        "countdown_text": "#E6ECF5",
    },
}

FONTS = {
    # Consolas ships with Windows 7 (Cascadia Mono does not); Segoe UI is the
    # reference dashboard face. Display sizes push the hero hierarchy.
    "display": ("Segoe UI", 24, "bold"),
    "title": ("Segoe UI", 15, "bold"),
    "body": ("Segoe UI", 10),
    "caption": ("Segoe UI", 10),
    "countdown": ("Consolas", 34, "bold"),
    "countdown_big": ("Consolas", 84, "bold"),
    "mono": ("Consolas", 10),
}

# Phase 70: shared corner radius for every rounded card (dashboard, splash,
# secondary pages) — one number, reused everywhere, per the brand-consistency
# requirement. Pure-Tk polygon rounding (see App._round_rect); Win7-safe.
# Phase 72 (design-audit pass): radius now carries HIERARCHY instead of one
# flat value everywhere — the "identical border-radius on every card"
# pattern is exactly what generic AI dashboards default to. The hero
# countdown gets the largest radius (it's the one bold gesture on the
# page); ordinary cards a medium radius; nothing smaller needed since the
# times-strip pills sit inside their own card rather than being independently
# rounded.
CARD_RADIUS = 20
CARD_RADIUS_HERO = 32

# Phase 25b/65: Segoe UI Symbol glyph set (no new dependency, Win7-safe).
# Keys are referenced across the UI build and dashboard refresh — keep all.
ICONS = {
    "status": "●", "monitor": "⚙", "next": "◆", "times": "◷",
    "music": "♫", "adhan": "☪", "browse": "⌕", "refresh": "↻",
    "resume": "▶", "save": "✓", "test": "⇄", "exit": "✕", "open": "⧉",
    "play": "▶", "pin": "⧉",
    # Phase 63/65: sidebar navigation glyphs
    "nav_home": "⌂", "nav_clock": "◷", "nav_music": "♫", "nav_gear": "⚙", "nav_info": "ⓘ",
}


def pick_theme_name() -> str:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize") as key:
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return "vista" if value else "clam"
    except OSError:
        return "vista"


def resolve_theme_choice(saved_theme: str) -> str:
    """Fix Task 7: the app theme, honoring the user's MANUAL choice.

    "dark"/"light" — the explicit saved selection wins over the Windows system
    theme. "" — no manual choice yet: fall back to the historical system-driven
    behavior (pick_theme_name), preserving first-run behavior exactly."""
    if saved_theme in ("dark", "light"):
        return saved_theme
    return "dark" if pick_theme_name() != "vista" else "light"


def _ttk_theme_for(theme_choice: str) -> str:
    """Fix Task 7: map a dark/light choice to a ttk base theme name.
    Light -> "vista" (modern light), Dark -> "clam" — the same pairing the
    system-driven path has always used, so all existing styles keep working."""
    return "clam" if theme_choice == "dark" else "vista"


def apply_theme(style: ttk.Style, theme: str) -> None:
    """Phase 65 REDESIGN: premium surface styling. Layout unchanged; only
    colors, spacing, typography, and style definitions are upgraded.
    All legacy style names remain to avoid breakage; new names enrich the
    premium dashboard without removing any existing style."""
    dark = theme != "vista"
    name = "dark" if dark else "light"
    t = THEMES[name]
    bg, surface, surface_alt = t["bg"], t["surface"], t["surface_alt"]
    border, border_soft = t["border"], t["border_soft"]
    text, muted, accent = t["text"], t["muted"], t["accent"]
    field = t["hover_field"]
    # Base canvas/defaults
    style.configure(".", background=bg, foreground=text, fieldbackground=field,
                    troughcolor=bg, bordercolor=border, font=FONTS["body"])
    style.configure("TFrame", background=bg)
    style.configure("TLabel", background=bg, foreground=text)
    style.configure("TLabelFrame", background=bg, foreground=text,
                    bordercolor=border, relief="solid", borderwidth=1)
    style.configure("TLabelFrame.Label", background=bg, foreground=muted,
                    font=FONTS["caption"])
    # Titles / hints
    style.configure("Title.TLabel", font=FONTS["display"], foreground=accent)
    style.configure("Hint.TLabel", foreground=muted, font=FONTS["caption"])
    # Phase 70: card-surface variants of Title/Hint — a plain "TLabel" always
    # paints the PAGE background (bg) behind its text, which shows as a
    # mismatched patch once labels sit inside a rounded surface/surface_alt
    # card. Same size/weight/color as Title.TLabel and Hint.TLabel, just
    # matched to the card they're actually placed on.
    style.configure("HeroTitle.TLabel", font=FONTS["display"], foreground=accent,
                    background=surface)
    style.configure("SoftTitle.TLabel", font=FONTS["display"], foreground=accent,
                    background=surface_alt)
    style.configure("CardHint.TLabel", foreground=muted, font=FONTS["caption"],
                    background=surface)
    style.configure("SoftHint.TLabel", foreground=muted, font=FONTS["caption"],
                    background=surface_alt)
    style.configure("Status.TLabel", foreground=accent, font=("Segoe UI", 10, "bold"))
    # Buttons (quiet secondary + filled primary)
    style.configure("TButton", background=surface, foreground=text,
                    bordercolor=border, focuscolor=accent, padding=(10, 5))
    style.map("TButton",
        background=[("disabled", t["disabled_field"]),
                    ("pressed", t["hover_field"]),
                    ("active", t["hover_field"])],
        foreground=[("disabled", t["disabled_fg"])],
        bordercolor=[("disabled", t["disabled_field"]), ("active", accent)])
    style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"),
                    background=accent, foreground=t["accent_text"],
                    bordercolor=accent, padding=(12, 6))
    style.map("Accent.TButton",
        background=[("disabled", t["disabled_field"]),
                    ("pressed", accent),
                    ("active", t["accent_hover"])],
        foreground=[("disabled", t["disabled_fg"])],
        bordercolor=[("focus", t["focus"])])
    # Checkbox / radio
    style.configure("TCheckbutton", background=bg, foreground=text,
                    focuscolor=accent)
    style.map("TCheckbutton", background=[("active", bg)],
              foreground=[("disabled", t["disabled_fg"])])
    style.configure("TRadiobutton", background=bg, foreground=text,
                    focuscolor=accent)
    style.map("TRadiobutton", background=[("active", bg)],
              foreground=[("disabled", t["disabled_fg"])])
    # Entries
    style.configure("TEntry", fieldbackground=field, foreground=text,
                    bordercolor=border, insertcolor=accent,
                    lightcolor=border, darkcolor=border, padding=(6, 4))
    style.map("TEntry", fieldbackground=[("disabled", t["disabled_field"])],
              foreground=[("disabled", t["disabled_fg"])],
              bordercolor=[("focus", accent)])
    style.configure("TCombobox", fieldbackground=field, foreground=text,
                    bordercolor=border, lightcolor=border, darkcolor=border,
                    arrowcolor=muted, padding=(6, 4))
    style.map("TCombobox",
        fieldbackground=[("readonly", field),
                         ("disabled", t["disabled_field"])],
        foreground=[("disabled", t["disabled_fg"])],
        bordercolor=[("focus", accent)])
    style.configure("TSpinbox", fieldbackground=field, foreground=text,
                    bordercolor=border, arrowcolor=muted,
                    lightcolor=border, darkcolor=border, padding=(4, 2))
    style.map("TSpinbox",
        fieldbackground=[("readonly", field),
                         ("disabled", t["disabled_field"])],
        foreground=[("disabled", t["disabled_fg"])],
        bordercolor=[("focus", accent), ("readonly", border)])
    # Scrollbars
    style.configure("Vertical.TScrollbar", troughcolor=bg,
                    background=t["disabled_fg"], bordercolor=bg,
                    arrowcolor=muted)
    style.configure("Horizontal.TScrollbar", troughcolor=bg,
                    background=t["disabled_fg"], bordercolor=bg,
                    arrowcolor=muted)
    # Legacy cards (kept identical for regression safety)
    style.configure("Card.TLabelframe", background=surface,
                    bordercolor=border, relief="solid", borderwidth=1)
    style.configure("Card.TLabelframe.Label", background=surface,
                    foreground=muted, font=FONTS["caption"])
    style.configure("Card.TFrame", background=surface)
    style.configure("Card.TLabel", background=surface, foreground=text)
    style.configure("Hero.TLabel", background=surface, foreground=text,
                    font=("Segoe UI", 15, "bold"))
    style.configure("Sub.TLabel", background=surface, foreground=muted,
                    font=FONTS["body"])
    style.configure("Chip.TLabel", font=("Segoe UI", 9, "bold"),
                    foreground=muted, background=t["chip_bg"], padding=(10, 4))
    style.configure("Badge.TLabel", background=surface, foreground=muted,
                    font=("Segoe UI", 10, "bold"), padding=(10, 3))
    style.configure("Countdown.TLabel", background=surface_alt,
                    foreground=t["warning"], font=("Segoe UI", 13, "bold"))
    style.configure("CardTitle.TLabel", background=surface, foreground=text,
                    font=("Segoe UI", 12, "bold"))
    style.configure("SoftCardTitle.TLabel", background=surface_alt, foreground=text,
                    font=("Segoe UI", 12, "bold"))
    style.configure("PrayerTime.TLabel", background=surface, foreground=text,
                    font=("Consolas", 11))
    style.configure("PrayerNext.TLabel", background=t["hover_field"],
                    foreground=accent, font=("Segoe UI", 11, "bold"),
                    padding=(8, 4))
    style.configure("PrayerNextTime.TLabel", background=t["hover_field"],
                    foreground=accent, font=("Consolas", 11, "bold"),
                    padding=(8, 4))
    style.configure("PrayerNext.TEntry", fieldbackground=t["hover_field"],
                    foreground=accent, bordercolor=accent,
                    insertcolor=accent, lightcolor=accent, darkcolor=accent,
                    font=("Consolas", 10, "bold"))
    style.configure("CardHead.TFrame", background=surface)
    style.configure("Splash.TFrame", background=surface)
    style.configure("TRadiobutton", background=surface, foreground=text,
                    focuscolor=accent)
    style.map("TCheckbutton", background=[("active", surface)],
              foreground=[("disabled", t["disabled_fg"])])
    style.configure("Splash.Horizontal.TProgressbar", troughcolor=surface_alt,
                    background=accent, bordercolor=surface, lightcolor=accent,
                    darkcolor=accent, thickness=7)
    # Sidebar + navigation (premium)
    style.configure("Sidebar.TFrame", background=t["sidebar"])
    style.configure("SidebarLogo.TLabel", background=t["sidebar"],
                    foreground=accent, font=("Segoe UI", 12, "bold"))
    style.configure("SidebarFoot.TLabel", background=t["sidebar"],
                    foreground=t["disabled_fg"], font=FONTS["caption"])
    style.configure("Nav.TButton", background=t["sidebar"],
                    foreground=t["sidebar_text"], bordercolor=t["sidebar"],
                    focuscolor=t["sidebar"], font=("Segoe UI", 10),
                    padding=(14, 14), anchor="e", relief="flat")
    style.map("Nav.TButton",
        background=[("disabled", t["sidebar"]),
                    ("pressed", t["sidebar_active"]),
                    ("active", t["sidebar_active"])],
        foreground=[("disabled", t["disabled_fg"]),
                    ("pressed", accent), ("active", accent)])
    style.configure("NavActive.TButton", background=t["sidebar_active"],
                    foreground=accent,
                    bordercolor=t["sidebar_active"],
                    focuscolor=t["sidebar_active"],
                    font=("Segoe UI", 10, "bold"), padding=(14, 14),
                    anchor="e", relief="flat")
    style.map("NavActive.TButton",
        background=[("disabled", t["sidebar_active"]),
                    ("pressed", t["sidebar_active"]),
                    ("active", t["sidebar_active"])],
        foreground=[("disabled", t["disabled_fg"]),
                    ("pressed", accent), ("active", accent)])
    # Pages + header
    style.configure("Page.TFrame", background=bg)
    style.configure("Header.TFrame", background=bg)
    style.configure("HeaderTitle.TLabel", background=bg, foreground=text,
                    font=("Segoe UI", 28, "bold"))
    style.configure("HeaderSub.TLabel", background=bg, foreground=muted,
                    font=FONTS["caption"])
    # Ring / countdown
    style.configure("Ring.TFrame", background=surface)
    style.configure("RingCard.TLabelframe", background=surface,
                    bordercolor=border, relief="solid", borderwidth=1)
    style.configure("RingCard.TLabelframe.Label", background=surface,
                    foreground=muted, font=FONTS["caption"])
    style.configure("CountdownBig.TLabel", background=surface,
                    foreground=t["countdown_text"], font=FONTS["countdown_big"])
    style.configure("CountdownHint.TLabel", background=surface,
                    foreground=muted, font=FONTS["caption"])
    style.configure("CountdownTime.TLabel", background=surface,
                    foreground=accent, font=("Consolas", 12, "bold"))
    # Semantic badges
    style.configure("BadgeOk.TLabel", background=t["chip_bg"],
                    foreground=t["success"], font=("Segoe UI", 9, "bold"),
                    padding=(10, 4))
    style.configure("BadgeWarn.TLabel", background=t["chip_bg"],
                    foreground=t["warning"], font=("Segoe UI", 9, "bold"),
                    padding=(10, 4))
    style.configure("BadgeErr.TLabel", background=t["chip_bg"],
                    foreground=t["error"], font=("Segoe UI", 9, "bold"),
                    padding=(10, 4))
    style.configure("BadgeMut.TLabel", background=t["chip_bg"],
                    foreground=muted, font=("Segoe UI", 9, "bold"),
                    padding=(10, 4))
    # ---------- NEW PREMIUM STYLES (additive, not destructive) ----------
    # Soft card frames use surface_alt for subtle contrast
    style.configure("SoftCard.TLabelframe", background=surface_alt,
                    bordercolor=border_soft, relief="solid", borderwidth=1)
    style.configure("SoftCard.TLabelframe.Label", background=surface_alt,
                    foreground=muted, font=FONTS["caption"])
    style.configure("SoftCard.TFrame", background=surface_alt)
    style.configure("SoftCard.TLabel", background=surface_alt, foreground=text)
    # Pill chips / status
    style.configure("ChipAlt.TLabel", font=("Segoe UI", 9, "bold"),
                    foreground=accent, background=t["hover_field"],
                    padding=(8, 4))
    # Primary hero surface
    style.configure("HeroCard.TLabelframe", background=surface,
                    bordercolor=border, relief="solid", borderwidth=1)
    style.configure("HeroCard.TLabelframe.Label", background=surface,
                    foreground=muted, font=FONTS["caption"])
    style.configure("HeroCard.TFrame", background=surface)
    style.configure("HeroCard.TLabel", background=surface, foreground=text)
    # Key-value rows
    style.configure("KV.TLabel", background=surface, foreground=muted,
                    font=FONTS["caption"])


class App:
    def __init__(self, root: tk.Tk):
        self.root, self.saved = root, load_settings()
        self._tick_count = 0  # Fix Task 1: heartbeat counter (diagnostics only)
        self._wide_cards = None
        logger.info(f"Settings loaded: enabled={self.saved.get('enabled')}, music={self.saved.get('music')!r}, method={self.saved.get('method')!r}, times={self.saved.get('times')}")
        self.paused_player: int | None = None
        self.resume_at: datetime | None = None
        self.resume_fails = 0
        # Phase 61: True when the active pause was delivered through the global
        # media-key toggle (Win7 Chromium-family browser fallback). resume_now
        # must then resume with the SAME media-key method ONLY — never both
        # methods and never targeted APPCOMMAND to browser windows (which
        # ignore it there), or the toggle would be sent twice and undo itself.
        self.paused_via_media_key: bool = False
        # Fix Task 2: markers of handled (prayer, time) pairs for the CURRENT
        # day only. Previously a plain set cleared wholesale after 20 entries —
        # with catch-up enabled that could re-fire an already-handled prayer.
        # Date-keyed rotation at midnight keeps duplicates impossible and is
        # naturally Win7-safe.
        self.done: set[str] = set()
        self._done_date: str = datetime.now().strftime("%Y-%m-%d")
        self.tray = None
        self.root.title(f"صلاة وسكون - v{APP_VERSION}")
        scale = ui_scale(root)  # Phase 25c: keep fixed pixel sizes usable at high DPI
        # Phase 31: initial size fitted to the actual screen, centered, freely
        # resizable (never forced maximized), with a small-screen-safe minimum.
        # Phase 63: sidebar (~170px) + page column needs a slightly wider floor;
        # the scrollable page area keeps everything reachable at min size.
        min_w, min_h = int(720 * scale), int(560 * scale)
        screen_w, screen_h = root.winfo_screenwidth(), root.winfo_screenheight()
        init_w = max(min_w, min(int(880 * scale), int(screen_w * 0.92)))
        init_h = max(min_h, min(int(800 * scale), int(screen_h * 0.85)))
        pos_x, pos_y = max(0, (screen_w - init_w) // 2), max(0, (screen_h - init_h) // 2)
        self.root.geometry(f"{init_w}x{init_h}+{pos_x}+{pos_y}")
        self.root.minsize(min_w, min_h)
        self.root.protocol("WM_DELETE_WINDOW", self.hide_to_tray)
        if ICON_PATH.exists(): self.root.iconbitmap(default=str(ICON_PATH))
        self.music = tk.StringVar(value=self.saved["music"])
        self.adhan = tk.StringVar(value=self.saved["adhan"])
        self.minutes = tk.StringVar(value=str(self.saved["minutes"]))
        self.method = tk.StringVar(value=self.saved["method"])
        self.enabled = tk.BooleanVar(value=self.saved["enabled"])
        self.status = tk.StringVar(value="جاهز. اختر البرامج ثم فعّل المراقبة.")
        self.announce = tk.BooleanVar(value=bool(self.saved.get("announce", True)))  # Phase 34: default ON
        # Phase 47-B: location settings state (auto/manual + manual fallback fields).
        self.location_mode = tk.StringVar(value=self.saved.get("location_mode", "auto"))
        self.manual_city = tk.StringVar(value=self.saved.get("manual_city", ""))
        self.manual_country = tk.StringVar(value=self.saved.get("manual_country", ""))
        self.manual_latitude = tk.StringVar(value=self.saved.get("manual_latitude", ""))
        self.manual_longitude = tk.StringVar(value=self.saved.get("manual_longitude", ""))
        self.manual_timezone = tk.StringVar(value=self.saved.get("manual_timezone", ""))
        self.location_status = tk.StringVar(value="الموقع: تلقائي (تقريبي عبر IP)")
        # Task 2 / Phase 64: Tk state for the startup toggle. Source of truth is
        # the REAL HKCU Run entry (external edits via msconfig/registry are
        # reflected in the UI). Self-heal: if settings.json says enabled but
        # the registry entry is missing (e.g. cleaned by another tool), the
        # saved preference re-registers itself at launch — Win7-safe, no admin.
        saved_autostart = bool(self.saved.get("autostart", False))
        registry_autostart = autostart_enabled()
        self.autostart_enabled = tk.BooleanVar(value=registry_autostart)
        if saved_autostart and not registry_autostart:
            # settings say ON but registry entry is gone -> honor the saved
            # preference and re-register (idempotent, one named value)
            if set_autostart(True):
                self.autostart_enabled.set(True)
                logger.info("Autostart restored from saved settings (HKCU Run entry re-created)")
        autostart_source = "HKCU Run entry" if autostart_enabled() else "manual launch"
        logger.info(f"Launch source: {autostart_source}")
        self.times = {p: tk.StringVar(value=format_time_12(self.saved["times"][p]) if self.saved["times"].get(p) else "") for p in PRAYERS}
        # Fix Task 7: MANUAL theme selection (persisted in settings; independent
        # of the Windows system theme once chosen). Empty saved value keeps the
        # historical system-driven first-run behavior via resolve_theme_choice.
        self._theme_selection: str = self.saved.get("theme", "") or ""
        self.theme_choice: str = resolve_theme_choice(self._theme_selection)
        self.tokens = THEMES[self.theme_choice]
        self._player_state_cache = (None, False)  # (checked_music_name, running)
        # Phase 34: announcement duplicate protection — (date, prayer) pairs
        # announced today; shared with tick's done markers for one-shot semantics.
        self._announced: set[str] = set()
        self._announced_date: str = ""  # day the set belongs to (resets at midnight)
        # Phase 32: background cache of (exe name, pid) rows of running processes.
        # Written only by the worker thread, read by refresh_dashboard — the UI
        # thread never runs PowerShell Get-Process.
        self._process_rows: list[tuple[str, int]] = []
        self._process_rows_at = 0.0
        self._active_prayer: str | None = None  # display-only: prayer that triggered the current pause
        # Fix Task 8: live next-prayer countdown timer id — only one after() may
        # exist; cancelled safely at exit.
        self._countdown_after: str | None = None
        # Task 1 (runtime): last-log timestamps for throttled warnings (keyed
        # by message) — keeps the ~1 Hz data() callers from flooding the log.
        self._last_config_warn: dict[str, float] = {}
        # Phase 70 REDESIGN: registry of live rounded-canvas cards (see
        # _make_card) so apply_theme_selection can retint them on theme
        # switch — they are plain tk widgets, not ttk-styled, since a
        # Canvas-drawn rounded background needs an exact-match tk.Frame.
        self._rounded_cards: list[dict] = []
        logger.info("Application initialized")
        self.root.withdraw()  # hidden while the splash shows; the fade-in reveals it
        self.show_splash()

    def show_splash(self) -> None:
        """Phase 70 REDESIGN: branded startup splash on the SAME rounded-card
        identity as the dashboard — a Canvas-drawn rounded panel (real corner
        radius, not a plain rectangle) in the surface/border/accent tokens,
        with the app name, subtitle, progress bar, and developer credit.
        Fails gracefully to normal startup on any error (unchanged contract)."""
        splash = None
        try:
            t = self.tokens
            splash = tk.Toplevel(self.root)
            splash.title("صلاة وسكون")
            splash.overrideredirect(True)
            splash.attributes("-topmost", True)
            splash.configure(background=t["bg"])
            if ICON_PATH.exists():
                try: splash.iconbitmap(default=str(ICON_PATH))
                except tk.TclError: pass
            panel = tk.Canvas(splash, highlightthickness=0, background=t["bg"], bd=0)
            panel.pack(fill="both", expand=True)
            frame = ttk.Frame(panel, padding=(40, 36), style="Splash.TFrame")
            frame_win = panel.create_window(0, 0, window=frame, anchor="nw")

            def _paint_panel(_evt=None):
                try:
                    w = max(40, panel.winfo_width())
                    h = max(40, panel.winfo_height())
                    panel.delete("panel_bg")
                    self._round_rect(panel, 3, 3, w - 3, h - 3, 22,
                                     fill=t["surface"], outline=t["border"],
                                     width=1, tags=("panel_bg",))
                    panel.tag_lower("panel_bg")
                    panel.coords(frame_win, 3, 3)
                    panel.itemconfigure(frame_win, width=w - 6, height=h - 6)
                except tk.TclError:
                    pass
            panel.bind("<Configure>", _paint_panel)
            if PNG_ICON_PATH.exists():
                logo_error = None
                try:
                    # Phase 40: tk.PhotoImage decodes PNG natively (Tk 8.6) —
                    # no PIL needed, so a frozen build with a broken/missing
                    # PIL C extension still shows the logo. subsample scales
                    # the 1024px asset down without any imaging dependency.
                    raw = tk.PhotoImage(file=str(PNG_ICON_PATH))
                    target = max(1, int(72 * ui_scale(self.root)))
                    factor = max(1, raw.width() // target)
                    logo = raw.subsample(factor, factor)
                    ttk.Label(frame, image=logo, style="CardHint.TLabel").pack(pady=(0, 14))
                    splash.keep = logo  # type: ignore[attr-defined]  # keep a ref: Tk GC
                except Exception as e:
                    logo_error = e
                    logger.warning(f"Splash logo skipped (tk path): {e}")
                    try:  # last resort: PIL (works when _imaging is healthy)
                        from PIL import Image, ImageTk
                        with Image.open(PNG_ICON_PATH) as opened:
                            logo = ImageTk.PhotoImage(opened.resize((int(72 * ui_scale(self.root)),) * 2, Image.LANCZOS))
                        ttk.Label(frame, image=logo, style="CardHint.TLabel").pack(pady=(0, 14))
                        splash.keep = logo  # type: ignore[attr-defined]
                        logger.info("Splash logo loaded via PIL fallback")
                    except Exception as e2:
                        logger.warning(f"Splash logo skipped (PIL fallback): {e2}")
                if logo_error is not None:
                    pass  # fallback outcome already logged; never crash the splash
            ttk.Label(frame, text="صلاة وسكون", style="HeroTitle.TLabel", anchor="center").pack(fill="x")
            ttk.Label(frame, text="حامي الموسيقى وقت الصلاة", style="CardHint.TLabel", anchor="center").pack(fill="x", pady=(4, 0))
            bar = ttk.Progressbar(frame, style="Splash.Horizontal.TProgressbar", mode="indeterminate", maximum=100)
            bar.pack(fill="x", pady=(28, 0))
            bar.start(24)
            # Phase 26: subtle developer credit at the splash bottom
            credit = ttk.Label(frame, text=DEVELOPER_CREDIT, style="CardHint.TLabel", anchor="center")
            credit.pack(side="bottom", fill="x", pady=(18, 0))
            splash.update_idletasks()
            scale = ui_scale(self.root)  # Phase 25c: splash stays proportional at high DPI
            width, height = int(380 * scale), int(300 * scale)
            x = (splash.winfo_screenwidth() - width) // 2
            y = (splash.winfo_screenheight() - height) // 3
            splash.geometry(f"{width}x{height}+{x}+{y}")
            self._splash = splash
            self.root.after(900, self._close_splash)
        except Exception as e:
            logger.warning(f"Splash disabled: {e}")
            if splash is not None:
                try: splash.destroy()
                except tk.TclError: pass
            self._splash = None
            self._start_app()

    def _close_splash(self) -> None:
        """Hide the splash and hand over to the dashboard with a short fade."""
        splash = getattr(self, "_splash", None)
        if splash is None:
            self._start_app()
            return
        try:
            splash.attributes("-alpha", 0.0)
            self.root.attributes("-alpha", 0.0)
            self.root.deiconify()
            step = 0.12
            def fade(done: int) -> None:
                done += step
                try:
                    splash.attributes("-alpha", max(0.0, 1.0 - done))
                    self.root.attributes("-alpha", min(1.0, done))
                except tk.TclError:
                    pass
                if done < 1.0:
                    self.root.after(20, lambda: fade(done))
                else:
                    splash.destroy()
                    self.root.attributes("-alpha", 1.0)
            fade(0.0)
        except Exception as e:
            logger.warning(f"Splash transition fallback: {e}")
            try: splash.destroy()
            except tk.TclError: pass
            self.root.attributes("-alpha", 1.0)
        finally:
            self._start_app()

    def _start_app(self) -> None:
        """Original startup sequence, unchanged (dashboard, processes, tray, tick)."""
        if getattr(self, "_app_started", False):
            # Task 2 (diagnostics): the splash fallback path can call this
            # twice — the guard must be visible in the log, not silent.
            logger.info("Duplicate monitoring start prevented (startup already completed)")
            return
        self._app_started = True
        self.build_ui(); self.refresh_processes(); self.start_tray()
        logger.info(f"Monitoring started: scheduler armed (tick every {TICK_SECONDS}s, catch-up {TRIGGER_CATCHUP_MINUTES} min, first tick in 1s)")
        self.root.after(1000, self.tick)
        self._update_next_prayer_countdown()  # Fix Task 8: 1-second live countdown (Tk thread only)
        cache_thread = threading.Thread(target=self._process_rows_worker, daemon=True)  # Phase 32
        cache_thread.start()
        self._daemon_threads = [cache_thread]  # Task 2: joined with a bounded grace at exit
        logger.info("All monitoring workers started (tick, countdown, dashboard, process cache)")

    def _process_rows_worker(self) -> None:
        """Phase 32: refresh the running-process cache every ~15s in the
        background. Pure data collection — all UI updates stay on the Tk
        thread via variable reads in refresh_dashboard."""
        logger.info("Process-cache worker started")
        while not getattr(self, "_app_closed", False):
            try:
                rows = process_rows()
                if rows:  # [] means the PowerShell query failed — keep the last good cache
                    self._process_rows = rows
                    self._process_rows_at = time.monotonic()
            except Exception as e:
                import traceback
                logger.error(f"Process-cache refresh failed: {e}\n{traceback.format_exc()}")
            time.sleep(15)
        logger.info("Process-cache worker exiting (app closed)")

    def build_ui(self) -> None:
        """Phase 65 REDESIGN: premium dashboard layout — sidebar navigation,
        refined header, spacious hero countdown, status cards.

        Structure: root grid = [sidebar | main]. Main = header + a scrollable
        page area hosting the EXISTING cards (re-parented to premium variants).
        All controls, callbacks, variables, and logical flows are preserved;
        only the visual hierarchy and spacing are upgraded.
        Business logic (tick/pause/resume) is untouched."""
        style = ttk.Style(self.root)
        theme = _ttk_theme_for(self.theme_choice)
        style.theme_use(theme)
        apply_theme(style, theme)

        # ============ ROOT SHELL: sidebar (col 0) | main area (col 1) ============
        self.root.minsize(900, 600)
        self.root.geometry("1100x720")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        shell = ttk.Frame(self.root, style="TFrame")
        shell.grid(row=0, column=0, sticky="nsew")
        shell.columnconfigure(0, weight=0)
        shell.columnconfigure(1, weight=1)
        shell.rowconfigure(0, weight=1)

        # ---------------- SIDEBAR (Phase 65: premium, spacious navigation) ----------------
        sidebar = ttk.Frame(shell, style="Sidebar.TFrame", padding=(16, 24, 16, 20))
        sidebar.grid(row=0, column=0, sticky="ns")
        sidebar.configure(width=200)
        sidebar.grid_propagate(False)
        sidebar.columnconfigure(0, weight=1)
        self._sidebar = sidebar
        brand = ttk.Frame(sidebar, style="Sidebar.TFrame")
        brand.pack(fill="x", pady=(0, 24))
        ttk.Label(brand, text="◈ Prayer Music Guard", style="SidebarLogo.TLabel", anchor="e").pack(fill="x")
        ttk.Label(brand, text="صلاة وسكون", style="SidebarFoot.TLabel", anchor="e").pack(fill="x", pady=(4, 0))
        # nav buttons — each maps to a REAL page of existing cards, same keys as before
        self._nav_buttons = {}
        self._nav_bars = {}
        for key, label in (
            ("dashboard", f"{ICONS['nav_home']}  لوحة الصلاة"),
            ("times", f"{ICONS['nav_clock']}  المواقيت"),
            ("music", f"{ICONS['nav_music']}  المشغّل"),
            ("settings", f"{ICONS['nav_gear']}  الإعدادات"),
            ("about", f"{ICONS['nav_info']}  حول البرنامج"),
        ):
            container = ttk.Frame(sidebar, style="Sidebar.TFrame")
            container.pack(fill="x", pady=6)
            bar = tk.Frame(container, width=4, background=self.tokens["sidebar"])
            bar.pack(side="left", fill="y")
            btn = ttk.Button(container, text=label, style="Nav.TButton", width=22,
                              command=lambda k=key: self.show_page(k))
            btn.pack(side="left", fill="x", expand=True, padx=(4,0))
            self._nav_buttons[key] = btn
            self._nav_bars[key] = bar
        # sidebar footer: version chip, separated
        side_foot = ttk.Frame(sidebar, style="Sidebar.TFrame")
        side_foot.pack(side="bottom", fill="x", pady=(18, 0))
        ttk.Label(side_foot, text=f"الإصدار v{APP_VERSION}", style="SidebarFoot.TLabel", anchor="e").pack(fill="x", pady=(6, 0))

        # ---------------- MAIN AREA ----------------
        main = ttk.Frame(shell, style="TFrame", padding=(24, 20, 24, 16))
        main.grid(row=0, column=1, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(1, weight=1)

        # ===== HEADER (Phase 65: title + subtitle + date + chips + theme) =====
        header = ttk.Frame(main, style="Header.TFrame")
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        hrow = ttk.Frame(header, style="Header.TFrame"); hrow.pack(fill="x", pady=(8, 10))
        hrow.columnconfigure(0, weight=1)
        hleft = ttk.Frame(hrow, style="Header.TFrame"); hleft.grid(row=0, column=0, sticky="w")
        self.header_title = ttk.Label(hleft, text="Prayer Music Guard", style="HeaderTitle.TLabel", anchor="w")
        self.header_title.pack(side="left")
        self.header_version_chip = ttk.Label(hleft, text=f"v{APP_VERSION}", style="ChipAlt.TLabel", anchor="w")
        self.header_version_chip.pack(side="left", padx=(10, 0))
        hright = ttk.Frame(hrow, style="Header.TFrame"); hright.grid(row=0, column=1, sticky="e")
        # Phase 65: monitoring chip + theme toggle, visually separated
        self.monitor_chip = ttk.Label(hright, text="● المراقبة متوقفة", style="ChipAlt.TLabel", anchor="w")
        self.monitor_chip.pack(side="left", padx=(0, 8))
        self.theme_toggle_btn = ttk.Button(hright, text="☀ الوضع الفاتح", width=13, command=self.toggle_theme)
        self.theme_toggle_btn.pack(side="left")
        hsub = ttk.Frame(header, style="Header.TFrame"); hsub.pack(fill="x", pady=(0, 8))
        hsub.columnconfigure(0, weight=1)
        self.header_sub = ttk.Label(hsub, text="صلاة وسكون — حماية الموسيقى وقت الصلاة", style="HeaderSub.TLabel", anchor="w")
        self.header_sub.grid(row=0, column=0, sticky="w")
        self.header_date = ttk.Label(hsub, text="", style="HeaderSub.TLabel", anchor="e")
        self.header_date.grid(row=0, column=1, sticky="e")
        # Phase 71: thin accent divider under the header — a small, clearly
        # new signature line (not present before) separating header from
        # the scrollable card area, echoing the reference dashboards' tab
        # underline / divider treatment.
        header_rule = tk.Frame(header, background=self.tokens["accent"], height=3)
        header_rule.pack(fill="x", pady=(14, 0))
        self._header_rule = header_rule

        # ===== SCROLLABLE PAGE AREA (all pages hosted here) =====
        # Cards live inside a canvas so small windows scroll instead of clipping.
        page_canvas = tk.Canvas(main, highlightthickness=0, background=self.tokens["bg"])
        self._cards_canvas = page_canvas
        page_scroll = ttk.Scrollbar(main, orient="vertical", command=page_canvas.yview)
        page_canvas.configure(yscrollcommand=page_scroll.set)
        page_canvas.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        page_scroll.grid(row=1, column=1, sticky="ns", pady=(10, 0))
        main.columnconfigure(1, weight=0)
        page_host = ttk.Frame(page_canvas, style="Page.TFrame")
        self._page_host = page_host
        page_window = page_canvas.create_window(0, 0, window=page_host, anchor="nw")
        def _canvas_resized(event):
            page_canvas.itemconfigure(page_window, width=event.width)
            self._reflow_cards(event.width)
        page_canvas.bind("<Configure>", _canvas_resized)
        def _host_resized(_event):
            page_canvas.configure(scrollregion=page_canvas.bbox("all"))
        page_host.bind("<Configure>", _host_resized)
        # mouse wheel scrolls the page area only when the pointer is over it
        def _wheel(event):
            inside = False
            try:
                widget = page_canvas.winfo_containing(event.x_root, event.y_root)
                while widget is not None:
                    if widget is page_host or widget is page_canvas:
                        inside = True
                        break
                    widget = widget.master
            except tk.TclError:
                pass
            if inside:
                first, _last = page_canvas.yview()
                if event.delta > 0 and first > 0.0:
                    page_canvas.yview_scroll(-2, "units"); return "break"
                if event.delta < 0 and first < 1.0:
                    page_canvas.yview_scroll(2, "units"); return "break"
        page_canvas.bind_all("<MouseWheel>", _wheel, add="+")

        # ================= DASHBOARD PAGE (Phase 64 premium layout) =================
        # ===== DASHBOARD PAGE (Phase 65 premium layout — hero + cards) =====
        dash = ttk.Frame(page_host, style="Page.TFrame")
        self._page_frames = {"dashboard": dash}
        dash.columnconfigure(0, weight=1)
        dash.rowconfigure(0, weight=0)
        dash.rowconfigure(1, weight=0)
        dash.rowconfigure(2, weight=1)

        # ---- HERO ROW: next prayer + status ----
        # ---- HERO BAND (Phase 71 RESTRUCTURE): full-width — the countdown
        # is the single dominant element, as in the reference apps' top hero
        # sections, instead of sharing a row with the status card. ----
        hero_row = ttk.Frame(dash, style="Page.TFrame")
        hero_row.grid(row=0, column=0, sticky="nsew", pady=(0, 20))
        hero_row.columnconfigure(0, weight=1)

        ring_outer, ring_card = self._make_card(hero_row, f"{ICONS['next']}  الصلاة القادمة", variant="hero")
        ring_outer.grid(row=0, column=0, sticky="nsew")
        ring_card.columnconfigure(0, weight=1)
        ring_card.rowconfigure(0, weight=1)
        ring_info = ttk.Frame(ring_card, style="HeroCard.TFrame")
        ring_info.grid(row=0, column=0, sticky="nsew")
        ring_info.columnconfigure(0, weight=1)
        self.next_prayer_label = ttk.Label(ring_info, text="—", style="HeroTitle.TLabel", anchor="e")
        self.next_prayer_label.grid(row=0, column=0, sticky="ew")
        self.next_prayer_time = ttk.Label(ring_info, text="--:--", style="CountdownTime.TLabel", anchor="e")
        self.next_prayer_time.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        self.next_prayer_in = ttk.Label(ring_info, text="00:00:00", style="CountdownBig.TLabel", anchor="e")
        self.next_prayer_in.grid(row=2, column=0, sticky="ew", pady=(8, 4))
        ttk.Label(ring_info, text="الوقت المتبقي — Time Remaining", style="CardHint.TLabel", anchor="e").grid(row=3, column=0, sticky="ew")
        ttk.Label(ring_info, text="يقترب موعد الصلاة", style="CardHint.TLabel", anchor="e", foreground=self.tokens["muted"]).grid(row=4, column=0, sticky="ew", pady=(2, 0))
        self.ring_canvas = tk.Canvas(ring_card, width=280, height=280,
                                       highlightthickness=0, background=self.tokens["surface"])
        self.ring_canvas.grid(row=1, column=0, sticky="", padx=(0, 16))
        ring_card.rowconfigure(1, weight=0)

        # ---- TODAY'S TIMES: redesigned as 5 equal prayer cards with clear hierarchy ----
        times_header_outer, times_header = self._make_card(dash, f"{ICONS['times']}  مواقيت اليوم", variant="soft")
        times_header_outer.grid(row=1, column=0, sticky="nsew", pady=(0, 14))
        times_grid = ttk.Frame(times_header, style="Card.TFrame")
        times_grid.pack(fill="both", expand=True, padx=12, pady=12)
        times_grid.columnconfigure(tuple(range(len(PRAYERS))), weight=1)
        self.dash_time_labels = {}
        for c, prayer in enumerate(PRAYERS):
            card = ttk.Frame(times_grid, style="Card.TFrame")
            card.grid(row=0, column=c, sticky="nsew", padx=(0 if c == 0 else 10, 0))
            card.columnconfigure(0, weight=1)
            # label container with subtle background
            name_lbl = ttk.Label(card, text=AR[prayer], style="Card.TLabel", anchor="center", font=("Segoe UI", 11, "bold"))
            name_lbl.pack(fill="x", pady=(0,4))
            time_lbl = ttk.Label(card, text="--:--", style="PrayerTime.TLabel", anchor="center", padding=(0,6), font=("Segoe UI", 14, "bold"))
            time_lbl.pack(fill="x")
            self.dash_time_labels[prayer] = (name_lbl, time_lbl)

        # ---- STATUS / MUSIC / QUICK SETTINGS: three columns (Phase 71 — was
        # status+hero, then times+music, then a lone quick-settings strip;
        # now a single even row, a clearly different skeleton than before). --
        row3 = ttk.Frame(dash, style="Page.TFrame")
        row3.grid(row=2, column=0, sticky="nsew", pady=(0, 20))
        row3.columnconfigure(0, weight=1)
        row3.columnconfigure(1, weight=1)
        row3.columnconfigure(2, weight=1)
        self._dash_row3 = row3
        self._dash_row3_cards = {}

        status_outer, status_card = self._make_card(row3, f"{ICONS['status']}  الحالة", variant="soft")
        status_outer.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        self._dash_row3_cards['status'] = status_outer
        status_card.columnconfigure(0, weight=1)
        srow = ttk.Frame(status_card, style="SoftCard.TFrame"); srow.grid(row=0, column=0, sticky="ew")
        srow.columnconfigure(0, weight=1)
        self.state_dot = tk.Label(srow, text="●", font=("Segoe UI", 16),
                                  foreground=self.tokens["muted"], background=self.tokens["surface_alt"])
        self.state_dot.grid(row=0, column=1, sticky="w", padx=(0, 8))
        self.state_label = ttk.Label(srow, text="المراقبة متوقفة.", style="SoftTitle.TLabel", anchor="e")
        self.state_label.grid(row=0, column=0, sticky="ew")
        self.state_detail = ttk.Label(status_card, text="فعّل المراقبة من قسم «المراقبة والإعدادات» لبدء الحماية وقت الصلاة.", style="SoftHint.TLabel", anchor="e", wraplength=220)
        self.state_detail.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        sfoot = ttk.Frame(status_card, style="SoftCard.TFrame"); sfoot.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        sfoot.columnconfigure(0, weight=1)
        self.state_prayer = ttk.Label(sfoot, text="", style="BadgeMut.TLabel", anchor="e")
        self.state_prayer.grid(row=0, column=0, sticky="w")
        self.state_resume_time = ttk.Label(sfoot, text="", style="Countdown.TLabel", anchor="e")
        self.state_resume_time.grid(row=0, column=1, sticky="e")
        self.resume_btn = ttk.Button(status_card, text=f"{ICONS['resume']}  استئناف الآن", style="Accent.TButton", command=self.resume_now)
        self.resume_btn.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        self.resume_btn.state(["disabled"])
        self.test_btn = ttk.Button(status_card, text=f"{ICONS['test']}  اختبار إيقاف / استئناف", command=self.test)
        self.test_btn.grid(row=4, column=0, sticky="ew", pady=(6, 0))

        music_outer, music_card = self._make_card(row3, f"{ICONS['music']}  التحكم بالمشغّل", variant="soft")
        music_outer.grid(row=0, column=1, sticky="nsew", padx=12)
        self._dash_row3_cards['music'] = music_outer
        music_card.columnconfigure(0, weight=1)
        mhead = ttk.Frame(music_card, style="SoftCard.TFrame"); mhead.pack(fill="x", pady=(0, 8))
        mhead.columnconfigure(1, weight=1)
        self.music_state_label = ttk.Label(mhead, text="", style="BadgeMut.TLabel", anchor="w")
        self.music_state_label.grid(row=0, column=0, sticky="w")
        self.music_sel_label = ttk.Label(mhead, text="—", style="SoftCardTitle.TLabel", anchor="e")
        self.music_sel_label.grid(row=0, column=1, sticky="e", padx=(8, 0))
        self.music_box = ttk.Combobox(music_card, textvariable=self.music)
        self.music_box.pack(fill="x", pady=(0, 6))
        mbtns = ttk.Frame(music_card, style="SoftCard.TFrame"); mbtns.pack(fill="x")
        ttk.Button(mbtns, text=f"{ICONS['browse']}  استعراض…", width=12, command=self.browse_music).pack(side="left")
        self.refresh_btn_music = ttk.Button(mbtns, text=f"{ICONS['refresh']}  تحديث", command=self.refresh_processes)
        self.refresh_btn_music.pack(side="left", padx=(6, 0))
        self.dash_adhan_label = ttk.Label(music_card, text="", style="SoftHint.TLabel", anchor="e")
        self.dash_adhan_label.pack(fill="x", pady=(8, 0))

        quick_outer, quick_card = self._make_card(row3, f"{ICONS['monitor']}  إعدادات سريعة", variant="soft")
        quick_outer.grid(row=0, column=2, sticky="nsew", padx=(12, 0))
        self._dash_row3_cards['quick'] = quick_outer
        quick_card.columnconfigure(0, weight=1)
        ttk.Checkbutton(quick_card, text="تشغيل المراقبة", variable=self.enabled).pack(anchor="e", pady=(0, 4))
        ttk.Checkbutton(quick_card, text="الإعلان الصوتي وقت الصلاة", variable=self.announce).pack(anchor="e", pady=(0, 4))
        ttk.Checkbutton(quick_card, text="بدء التطبيق مع ويندوز", variable=self.autostart_enabled, command=self.toggle_autostart).pack(anchor="e", pady=(0, 8))
        qrow = ttk.Frame(quick_card, style="SoftCard.TFrame"); qrow.pack(fill="x")
        ttk.Label(qrow, text="الاستئناف بعد (دقيقة):", style="SoftCard.TLabel").pack(side="right")
        self.minutes_spin = ttk.Spinbox(qrow, from_=1, to=180, width=5, textvariable=self.minutes, justify="center")
        self.minutes_spin.pack(side="right", padx=5)

        # ================= TIMES PAGE =================
        times_page = ttk.Frame(page_host, style="Page.TFrame")
        self._page_frames["times"] = times_page
        times_page.columnconfigure(0, weight=1)
        times_card_outer, times_card = self._make_card(times_page, f"{ICONS['times']}  مواقيت اليوم (12 ساعة)")
        times_card_outer.grid(row=0, column=0, sticky="ew")
        times_card.columnconfigure(0, weight=1)
        self.prayer_rows = {}
        for r, prayer in enumerate(PRAYERS):
            prow = ttk.Frame(times_card, style="Card.TFrame"); prow.grid(row=r, column=0, sticky="ew", pady=6)
            prow.columnconfigure(0, weight=1)
            name_lbl = ttk.Label(prow, text=AR[prayer], style="Card.TLabel", width=8, anchor="e")
            name_lbl.pack(side="right")
            time_entry = ttk.Entry(prow, textvariable=self.times[prayer], width=8, justify="center", font=("Segoe UI", 10, "bold"))
            time_entry.pack(side="right", padx=8)
            self.prayer_rows[prayer] = (name_lbl, time_entry)
        # Phase 47-B: location section — identical widgets (auto/manual)
        loc = ttk.Frame(times_card, style="Card.TFrame")
        loc.grid(row=len(PRAYERS), column=0, sticky="ew", pady=(10, 0))
        loc.columnconfigure(0, weight=1)
        self.location_status_label = ttk.Label(times_card, textvariable=self.location_status, style="CardHint.TLabel", anchor="e")
        self.location_status_label.grid(row=len(PRAYERS) + 1, column=0, sticky="ew", pady=(4, 0))
        ttk.Radiobutton(loc, text="تحديد الموقع تلقائيًا (تقريبي عبر IP)", value="auto", variable=self.location_mode).grid(row=0, column=0, sticky="e")
        ttk.Radiobutton(loc, text="استخدام الموقع اليدوي", value="manual", variable=self.location_mode).grid(row=1, column=0, sticky="e")
        manual = ttk.Frame(times_card, style="Card.TFrame")
        manual.grid(row=len(PRAYERS) + 2, column=0, sticky="ew", pady=(6, 0))
        manual.columnconfigure((1, 3), weight=1)
        ttk.Label(manual, text="الدولة:", style="Card.TLabel").grid(row=0, column=0, sticky="e")
        self.manual_country_entry = ttk.Entry(manual, textvariable=self.manual_country, width=10, justify="center")
        self.manual_country_entry.grid(row=0, column=1, sticky="ew", padx=(0, 6))
        ttk.Label(manual, text="المدينة:", style="Card.TLabel").grid(row=0, column=2, sticky="e")
        self.manual_city_entry = ttk.Entry(manual, textvariable=self.manual_city, width=10, justify="center")
        self.manual_city_entry.grid(row=0, column=3, sticky="ew")
        ttk.Label(manual, text="خط العرض:", style="Card.TLabel").grid(row=1, column=0, sticky="e", pady=(4, 0))
        self.manual_latitude_entry = ttk.Entry(manual, textvariable=self.manual_latitude, width=10, justify="center")
        self.manual_latitude_entry.grid(row=1, column=1, sticky="ew", padx=(0, 6), pady=(4, 0))
        ttk.Label(manual, text="خط الطول:", style="Card.TLabel").grid(row=1, column=2, sticky="e", pady=(4, 0))
        self.manual_longitude_entry = ttk.Entry(manual, textvariable=self.manual_longitude, width=10, justify="center")
        self.manual_longitude_entry.grid(row=1, column=3, sticky="ew", pady=(4, 0))
        ttk.Label(manual, text="المنطقة الزمنية (اختياري):", style="Card.TLabel").grid(row=2, column=0, columnspan=2, sticky="e", pady=(4, 0))
        self.manual_timezone_entry = ttk.Entry(manual, textvariable=self.manual_timezone, width=24, justify="center")
        self.manual_timezone_entry.grid(row=2, column=2, columnspan=2, sticky="ew", pady=(4, 0))
        lbtns = ttk.Frame(times_card, style="Card.TFrame")
        lbtns.grid(row=len(PRAYERS) + 3, column=0, sticky="ew", pady=(6, 0))
        lbtns.columnconfigure((0, 1), weight=1)
        ttk.Button(lbtns, text=f"{ICONS['refresh']}  تحديد الموقع الآن", command=self.detect_location).grid(row=0, column=0, sticky="e")
        ttk.Button(lbtns, text=f"{ICONS['save']}  تطبيق الموقع", style="Accent.TButton", command=self.apply_location).grid(row=0, column=1, sticky="e")
        ttk.Button(times_card, text=f"{ICONS['refresh']}  جلب المواقيت", command=self.fetch_times).grid(row=len(PRAYERS) + 4, column=0, sticky="e", pady=(6, 0))

        # ================= MUSIC PAGE (adhan exclusion card) =================
        music_page = ttk.Frame(page_host, style="Page.TFrame")
        self._page_frames["music"] = music_page
        music_page.columnconfigure(0, weight=1)
        adhan_card_outer, adhan_card = self._make_card(music_page, f"{ICONS['adhan']}  برنامج المؤذن المستثنى")
        adhan_card_outer.grid(row=0, column=0, sticky="ew")
        adhan_card.columnconfigure(0, weight=1)
        ahead = ttk.Frame(adhan_card, style="CardHead.TFrame"); ahead.pack(fill="x", pady=(0, 6))
        ahead.columnconfigure(1, weight=1)
        self.adhan_sel_label = ttk.Label(ahead, text="—", style="CardTitle.TLabel", anchor="e")
        self.adhan_sel_label.grid(row=0, column=1, sticky="e")
        ttk.Label(ahead, text="مستثنى", style="BadgeMut.TLabel", anchor="w").grid(row=0, column=0, sticky="w")
        self.adhan_box = ttk.Combobox(adhan_card, textvariable=self.adhan)
        self.adhan_box.pack(fill="x", pady=(0, 6))
        abtns = ttk.Frame(adhan_card, style="Card.TFrame"); abtns.pack(fill="x")
        ttk.Button(abtns, text=f"{ICONS['browse']}  استعراض…", width=12, command=self.browse_adhan).pack(side="left")
        self.refresh_btn_adhan = ttk.Button(abtns, text=f"{ICONS['refresh']}  تحديث", command=self.refresh_processes)
        self.refresh_btn_adhan.pack(side="left", padx=(6, 0))

        # ================= SETTINGS PAGE (monitoring card — all controls kept) =================
        settings_page = ttk.Frame(page_host, style="Page.TFrame")
        self._page_frames["settings"] = settings_page
        settings_page.columnconfigure(0, weight=1)
        monitor_outer, monitor = self._make_card(settings_page, f"{ICONS['monitor']}  المراقبة")
        monitor_outer.grid(row=0, column=0, sticky="ew")
        ttk.Radiobutton(monitor, text="تعليق عملية المشغّل المحدد فقط (موصى به)", value="suspend", variable=self.method).pack(anchor="e", pady=(0, 4))
        ttk.Radiobutton(monitor, text="زر Play/Pause العام (جلسة الوسائط النشطة)", value="media", variable=self.method).pack(anchor="e")
        mrow = ttk.Frame(monitor, style="Card.TFrame"); mrow.pack(anchor="e", pady=(8, 0))
        ttk.Label(mrow, text="الاستئناف بعد (دقيقة):", style="Card.TLabel").pack(side="right")
        self.minutes_spin = ttk.Spinbox(mrow, from_=1, to=180, width=5, textvariable=self.minutes, justify="center")
        self.minutes_spin.pack(side="right", padx=5)
        ttk.Checkbutton(monitor, text="تشغيل المراقبة", variable=self.enabled).pack(anchor="e", pady=(8, 0))
        ttk.Checkbutton(monitor, text="الإعلان الصوتي وقت الصلاة", variable=self.announce).pack(anchor="e", pady=(4, 0))  # Phase 34
        # Task 2 (autostart): per-user launch-at-logon option (HKCU Run, no admin)
        ttk.Checkbutton(monitor, text="بدء التطبيق مع ويندوز", variable=self.autostart_enabled, command=self.toggle_autostart).pack(anchor="e", pady=(4, 0))
        ttk.Button(monitor, text=f"{ICONS['save']}  حفظ وتشغيل", style="Accent.TButton", command=self.save_and_enable).pack(anchor="e", pady=(8, 0), fill="x")

        # ================= ABOUT PAGE =================
        about_page = ttk.Frame(page_host, style="Page.TFrame")
        self._page_frames["about"] = about_page
        about_page.columnconfigure(0, weight=1)
        about_card_outer, about_card = self._make_card(about_page, f"{ICONS['nav_info']}  حول البرنامج — About")
        about_card_outer.grid(row=0, column=0, sticky="ew")
        about_card.columnconfigure(0, weight=1)
        ttk.Label(about_card, text="Prayer Music Guard — صلاة وسكون", style="CardTitle.TLabel", anchor="e").grid(row=0, column=0, sticky="ew")
        ttk.Label(about_card, text=f"الإصدار v{APP_VERSION} — {DEVELOPER_CREDIT}", style="Sub.TLabel", anchor="e").grid(row=1, column=0, sticky="ew", pady=(4, 0))
        ttk.Label(about_card, text="يوقف مشغّل الموسيقى المحدد تلقائيًا وقت الصلاة — بأوامر وسائط فقط، دون تعليق أو إنهاء أي عملية، ودون لمس برنامج المؤذن.", style="Sub.TLabel", anchor="e", wraplength=420, justify="right").grid(row=2, column=0, sticky="ew", pady=(8, 0))
        ttk.Label(about_card, text="متوافق مع ويندوز 7 SP1 x64 حتى ويندوز 11 x64.", style="CardHint.TLabel", anchor="e").grid(row=3, column=0, sticky="ew", pady=(2, 0))

        # Phase 65: card refs for responsive dashboard reflow
        self._row1_cards = (times_card, None, monitor)  # legacy refs
        self._row2_cards = (adhan_card, music_card)
        self._dash_widgets = (ring_card, times_grid, status_card, music_card)
        self._wide_cards = None  # force first reflow pass

        # ACTION BAR + STATUS + FOOTER (pinned below the scroll area — never clipped)
        actions = ttk.Frame(main, style="TFrame"); actions.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        actions.columnconfigure(1, weight=1)
        ttk.Button(actions, text=f"{ICONS['test']}  اختبار إيقاف / استئناف", command=self.test).grid(row=0, column=0, sticky="w")
        ttk.Label(actions, text="إغلاق النافذة يُخفي التطبيق بجوار الساعة، ولا يوقفه.", style="Hint.TLabel", anchor="e").grid(row=0, column=1, sticky="ew", padx=10)
        self.status_label = ttk.Label(main, textvariable=self.status, style="Status.TLabel", justify="right", anchor="e")
        self.status_label.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        # Phase 26 heritage: developer credit footer, visually secondary
        ttk.Label(main, text=f"Prayer Music Guard v{APP_VERSION} — {DEVELOPER_CREDIT}", style="Hint.TLabel", anchor="w").grid(row=4, column=0, sticky="ew", pady=(2, 0))
        # Phase 31: respond to window size — status wrap + card layout reflow
        self.root.bind("<Configure>", self._on_root_configure)
        self.root.after(500, self.refresh_dashboard)
        # Phase 63: open on the dashboard page (grids the pages, sets nav state)
        self.show_page("dashboard")
        self._refresh_header_date()

    # ------------------------------------------------------------------
    # Phase 63/64: page navigation (real sections only — no fake functionality)
    _PAGE_TITLES = {
        "dashboard": "لوحة الصلاة",
        "times": "المواقيت",
        "music": "التحكم بالمشغّل",
        "settings": "المراقبة والإعدادات",
        "about": "حول البرنامج",
    }
    _HEADER_SUBTITLE = "صلاة وسكون — حماية الموسيقى وقت الصلاة"

    def show_page(self, key: str) -> None:
        """Show one navigation page; hide the others. Purely visual — every
        page hosts existing widgets, and the countdown/tick chains never stop."""
        if key not in self._page_frames: return
        self._current_page = key
        for page_key, frame in self._page_frames.items():
            if page_key == key:
                frame.grid(row=0, column=0, sticky="nsew")
            else:
                frame.grid_remove()
        for page_key, btn in self._nav_buttons.items():
            btn.configure(style="NavActive.TButton" if page_key == key else "Nav.TButton")
        for page_key, bar in self._nav_bars.items():
            bar.configure(background=self.tokens["accent"] if page_key == key else self.tokens["sidebar"])
        if getattr(self, "header_title", None) is not None:
            self._set_text(self.header_title, "Prayer Music Guard")
            self._set_text(self.header_sub, f"{self._PAGE_TITLES.get(key, '')} • {self._HEADER_SUBTITLE}")
        self._cards_canvas.yview_moveto(0.0)

    def _refresh_header_date(self) -> None:
        """Phase 63: localized date + selected-location hint in the header."""
        try:
            now = datetime.now()
            days = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
            day = days[now.weekday()]
            text = f"{day}، {now.day}/{now.month}/{now.year}"
            self._set_text(self.header_date, text)
        except Exception:
            pass  # date is cosmetic; never interrupts the app

    # Phase 31: responsive dashboard helpers ---------------------------------

    def toggle_theme(self) -> None:
        """Fix Task 7: switch Dark <-> Light immediately and persist the choice.

        The selection is stored as an explicit "theme" value in settings.json,
        so it survives restarts and no longer follows the Windows system theme.
        Re-application covers every styled element plus the two widgets whose
        colors were set directly (canvas background, state dot)."""
        self._theme_selection = "light" if self.theme_choice == "dark" else "dark"
        self.theme_choice = self._theme_selection
        self.apply_theme_selection()
        self._persist_theme()

    def apply_theme_selection(self) -> None:
        """Apply the current theme_choice to the whole dashboard, live."""
        self.tokens = THEMES[self.theme_choice]
        style = ttk.Style(self.root)
        style.theme_use(_ttk_theme_for(self.theme_choice))
        apply_theme(style, _ttk_theme_for(self.theme_choice))
        # direct-colored widgets from build_ui that styles cannot reach:
        canvas = getattr(self, "_cards_canvas", None)
        if canvas is not None:
            canvas.configure(background=self.tokens["bg"])
        if getattr(self, "state_dot", None) is not None:
            self.state_dot.configure(foreground=self.tokens["muted"],
                                     background=self.tokens["surface_alt"])
        if getattr(self, "_header_rule", None) is not None:
            self._header_rule.configure(background=self.tokens["accent"])
        # Phase 63: ring canvas surface + immediate ring repaint in new tokens
        ring = getattr(self, "ring_canvas", None)
        if ring is not None:
            ring.configure(background=self.tokens["surface"])
            try:
                self._draw_countdown_ring(getattr(self, "_last_ring_fraction", 0.0))
            except Exception:
                pass
        # Phase 70: retint every rounded-canvas card (plain tk widgets —
        # apply_theme() above only reaches ttk-styled widgets).
        self._retint_rounded_cards()
        # header toggle label reflects the CURRENT theme (states the other one
        # as the action; sun/moon glyphs are Segoe UI Symbol, Win7-safe)
        if getattr(self, "theme_toggle_btn", None) is not None:
            if self.theme_choice == "dark":
                self.theme_toggle_btn.configure(text="☀ الوضع الفاتح")
            else:
                self.theme_toggle_btn.configure(text="☾ الوضع الداكن")
        # refresh_dashboard re-tints every state color on its next pass; force
        # one immediate pass so colors are consistent without waiting 2s.
        if getattr(self, "status", None) is not None:
            try:
                self.refresh_dashboard()
            except Exception:
                pass
        logger.info(f"Theme switched to {self.theme_choice}")

    def _persist_theme(self) -> None:
        """Save the manual theme choice through the existing settings file,
        preserving every other field via the standard data()/save path."""
        data = self.data(quiet=True)
        payload = data if data else self.saved
        payload["theme"] = self._theme_selection
        save_settings(payload)

    def _on_root_configure(self, event: tk.Event) -> None:
        """Re-wrap the status line and reflow the dashboard to the current width."""
        if event.widget is not self.root: return  # only the root window's own size
        wrap = max(160, event.width - 2 * int(18 * ui_scale(self.root)) - int(170 * ui_scale(self.root)))
        try:
            if abs(int(self.status_label.cget("wraplength") or 0) - wrap) > 8:
                self.status_label.configure(wraplength=wrap)
        except tk.TclError:
            pass
        # Fix Task 6 heritage: reflow decisions use the PAGE area width (canvas).
        page_canvas = getattr(self, "_cards_canvas", None)
        self._reflow_cards(page_canvas.winfo_width() if page_canvas else event.width)

    def _reflow_cards(self, width: int) -> None:
        """Phase 65: responsive dashboard. Reflow hero ring size and dashboard cards."""
        wide = width >= 1000
        if self._wide_cards == wide:
            return
        self._wide_cards = wide
        # Ring size adapts to available width
        self._size_ring(190 if wide else 132)
        # Reflow status/music/quick cards: 3 columns when wide, stacked when narrow
        row3 = getattr(self, "_dash_row3", None)
        cards = getattr(self, "_dash_row3_cards", {})
        if row3 is not None:
            try:
                if wide:
                    row3.columnconfigure(0, weight=1)
                    row3.columnconfigure(1, weight=1)
                    row3.columnconfigure(2, weight=1)
                    for idx, key in enumerate(["status", "music", "quick"]):
                        w = cards.get(key)
                        if w:
                            w.grid_configure(row=0, column=idx, sticky="nsew", padx=(0 if idx==0 else 12 if idx==1 else 12, 0), pady=0)
                else:
                    row3.columnconfigure(0, weight=1)
                    row3.columnconfigure(1, weight=0)
                    row3.columnconfigure(2, weight=0)
                    for idx, key in enumerate(["status", "music", "quick"]):
                        w = cards.get(key)
                        if w:
                            w.grid_configure(row=idx, column=0, sticky="nsew", padx=0, pady=(0, 12 if idx<2 else 0))
            except Exception:
                pass

    # ---- Phase 70 REDESIGN: real rounded-corner cards (Canvas-drawn) ------
    @staticmethod
    def _round_rect(canvas: tk.Canvas, x1: float, y1: float, x2: float, y2: float,
                     r: float, **kwargs):
        """Pure-Tk rounded rectangle (create_polygon + smooth=True) — the
        actual corner radius the reference dashboards use, with no PIL and
        no external image, so it stays Windows 7 SP1 x64 safe."""
        r = max(2.0, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
        pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
               x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
        return canvas.create_polygon(pts, smooth=True, **kwargs)

    def _make_card(self, parent: tk.Widget, title: str, variant: str = "card") -> tuple[tk.Canvas, tk.Frame]:
        """Build one rounded card: a Canvas-drawn background (real corner
        radius, matching border/spacing tokens) hosting a plain tk content
        frame. `variant` picks the surface tone — "card"/"soft" use the main
        surface color, "hero" also uses the main surface but is drawn with
        CARD_RADIUS_HERO (Phase 72: radius now carries hierarchy — the hero
        countdown is the one bold gesture on the page, everything else uses
        the standard radius, rather than one flat value everywhere).
        The title (icon + Arabic caption) replaces the native ttk.LabelFrame
        title bar. Returns (outer_canvas, content_frame) — build children
        into `content` with grid() or pack() exactly as any card body did
        before; the card auto-sizes to its content and reflows on resize.
        Registered in self._rounded_cards so theme switches retint it live.
        """
        t = self.tokens
        soft = variant == "soft"
        radius = CARD_RADIUS_HERO if variant == "hero" else CARD_RADIUS
        surface = t["surface_alt"] if soft else t["surface"]
        border = t["border_soft"] if soft else t["border"]
        outer = tk.Canvas(parent, highlightthickness=0, background=t["bg"], bd=0)
        inner = tk.Frame(outer, background=surface)
        win = outer.create_window(16, 16, window=inner, anchor="nw")
        title_lbl = None
        if title:
            title_lbl = tk.Label(inner, text=title, background=surface,
                                 foreground=t["muted"], font=FONTS["caption"], anchor="e")
            title_lbl.pack(fill="x", pady=(0, 12))
        content = tk.Frame(inner, background=surface)
        content.pack(fill="both", expand=True)

        def redraw(_evt=None):
            try:
                # tokens read fresh each call (not closured) so a theme
                # switch's redraw() call paints the NEW palette, not the one
                # captured at card-creation time.
                tt = self.tokens
                fill = tt["surface_alt"] if soft else tt["surface"]
                edge = tt["border_soft"] if soft else tt["border"]
                need_h = inner.winfo_reqheight() + 32
                if abs(int(outer.cget("height") or 0) - need_h) > 1:
                    outer.configure(height=need_h)
                w = max(40, outer.winfo_width())
                h = max(40, outer.winfo_height())
                outer.delete("panel")
                self._round_rect(outer, 1, 1, w - 2, h - 2, radius,
                                 fill=fill, outline=edge, width=1, tags=("panel",))
                outer.tag_lower("panel")
                outer.itemconfigure(win, width=max(10, w - 32))
            except tk.TclError:
                pass  # cosmetic only — a card mid-teardown must never raise

        outer.bind("<Configure>", redraw)
        inner.bind("<Configure>", redraw)
        outer.after(1, redraw)  # first paint once mapped (reqheight is known)
        self._rounded_cards.append({"outer": outer, "inner": inner, "content": content,
                                    "title": title_lbl, "variant": variant, "redraw": redraw})
        return outer, content

    def _retint_rounded_cards(self) -> None:
        """Phase 70: live-retint every rounded card on theme switch — these
        are plain tk widgets (not ttk-styled) so they need an explicit pass;
        ttk children inside them already follow apply_theme()'s new colors."""
        t = self.tokens
        for c in self._rounded_cards:
            soft = c["variant"] == "soft"
            surface = t["surface_alt"] if soft else t["surface"]
            border = t["border_soft"] if soft else t["border"]
            try:
                c["outer"].configure(background=t["bg"])
                c["inner"].configure(background=surface)
                c["content"].configure(background=surface)
                if c["title"] is not None:
                    c["title"].configure(background=surface, foreground=t["muted"])
                c["redraw"]()
            except tk.TclError:
                pass

    def _size_ring(self, size: int) -> None:
        """Phase 64: adapt the countdown ring to the layout (148 wide / 118
        narrow). Purely visual — the arc redraws from _last_ring_fraction."""
        ring = getattr(self, "ring_canvas", None)
        if ring is None:
            return
        try:
            if ring.winfo_reqwidth() != size:
                ring.configure(width=size, height=size)
                self._draw_countdown_ring(getattr(self, "_last_ring_fraction", 0.0))
        except tk.TclError:
            pass

    # Phase 32: skip configure() when the value did not actually change —
    # refresh_dashboard runs every 2s and used to re-set ~15 widgets blindly.
    @staticmethod
    def _set_text(widget: ttk.Label | ttk.Button, text: str) -> None:
        if widget.cget("text") != text: widget.configure(text=text)

    @staticmethod
    def _set_fg(widget: ttk.Label, color: str) -> None:
        if widget.cget("foreground") != color: widget.configure(foreground=color)

    @staticmethod
    def _set_style(widget: ttk.Label | ttk.Entry, style: str) -> None:
        if widget.cget("style") != style: widget.configure(style=style)

    def _next_prayer_target(self) -> tuple[str, str, datetime] | None:
        """Fix Task 8: (prayer, "HH:MM", target datetime) of the next prayer.

        Chronological selection identical to the trigger's view of the day:
        earliest prayer still ahead today; when all of today's have passed, the
        earliest prayer of TOMORROW (midnight rollover handled by the datetime
        arithmetic). Returns None when config/times are unavailable."""
        data = self.data(quiet=True)
        if not data or not data["times"]:
            return None
        now = datetime.now()
        current = now.hour * 60 + now.minute
        minutes = {}
        for prayer, t in data["times"].items():
            h, m = map(int, t.split(":"))
            minutes[prayer] = h * 60 + m
        upcoming = sorted((m, prayer) for prayer, m in minutes.items() if m > current)
        if upcoming:
            m_val, prayer = upcoming[0]
            target = now.replace(hour=m_val // 60, minute=m_val % 60, second=0, microsecond=0)
            return (prayer, data["times"][prayer], target)
        # all prayers passed today -> earliest one tomorrow (midnight handled)
        m_val, prayer = min((m, p) for p, m in minutes.items())
        target = (now + timedelta(days=1)).replace(hour=m_val // 60, minute=m_val % 60, second=0, microsecond=0)
        return (prayer, data["times"][prayer], target)

    def _update_next_prayer_countdown(self) -> None:
        """Fix Task 8 heritage + Phase 63 ring: 1-second live countdown with a
        circular progress indicator.

        Runs ONLY on the Tk main thread via root.after; never overlaps with
        itself (a single _countdown_after id, re-armed after each update).
        Never shows a negative value (clamped at 00:00:00)."""
        if getattr(self, "_app_closed", False):
            return
        # Task 1 (runtime): exception armor so the 1s chain can never die
        # silently (same guarantee as tick and refresh_dashboard).
        try:
            target_info = self._next_prayer_target()
            if target_info is None:
                self._set_text(self.next_prayer_label, "—")
                self._set_text(self.next_prayer_time, "--:--")
                self._set_text(self.next_prayer_in, "00:00:00")
                self._draw_countdown_ring(0.0)
            else:
                prayer, prayer_time, target = target_info
                now = datetime.now()
                remaining = int((target - now).total_seconds())
                is_tomorrow = target.date() > now.date()
                self._set_text(self.next_prayer_label, f"{AR[prayer]} (غدًا)" if is_tomorrow else f"{AR[prayer]}")
                self._set_text(self.next_prayer_time, format_time_12(prayer_time))
                # Fix Task 8: never negative — clamped at zero. The moment a prayer
                # becomes 'due', the next tick's target selection rolls forward, so
                # the clamp is only ever visible for a fraction of a second.
                secs = max(0, remaining)
                self._set_text(self.next_prayer_in, f"{secs // 3600:02d}:{(secs % 3600) // 60:02d}:{secs % 60:02d}")
                # Phase 63: ring progress — elapsed fraction of the full interval
                # between the PREVIOUS prayer (or this time yesterday-equivalent
                # anchor) and the target. Smooth per-second advance.
                self._draw_countdown_ring(self._ring_fraction(target, secs))
        except Exception as e:
            import traceback
            logger.error(f"countdown iteration failed: {e}\n{traceback.format_exc()}")
        finally:
            self._schedule_countdown()

    def _ring_fraction(self, target: datetime, remaining_secs: int) -> float:
        """Phase 63: elapsed fraction [0..1] of the countdown ring.

        The full arc spans from the previous prayer to the target. When the
        target is tomorrow (midnight rollover), the arc spans from today's
        LAST prayer to tomorrow's first; with only one configured prayer it
        spans a full 24h. Always clamped to [0, 1]."""
        data = self.data(quiet=True)
        minutes = {}
        if data and data["times"]:
            for p, t in data["times"].items():
                h, m = map(int, t.split(":"))
                minutes[p] = h * 60 + m
        now = datetime.now()
        now_minutes = now.hour * 60 + now.minute
        if minutes:
            upcoming = sorted(m for m in minutes.values() if m > now_minutes)
            target_minute = target.hour * 60 + target.minute
            earlier = [m for m in sorted(minutes.values()) if m < target_minute]
            if earlier and upcoming:
                span = target_minute - earlier[-1]
            elif earlier:
                span = (24 * 60 - earlier[-1]) + target_minute
            else:
                span = 24 * 60
        else:
            span = 24 * 60
        if span <= 0:
            return 1.0
        elapsed = span - remaining_secs / 60.0
        return max(0.0, min(1.0, elapsed / span))

    def _draw_countdown_ring(self, fraction: float) -> None:
        """Phase 63: circular progress around the countdown. Pure tk.Canvas
        arc drawing (Win7-safe, no images, no external canvas). Anti-aliasing
        is approximated by a 6px arc width; the arc advances every second."""
        canvas = getattr(self, "ring_canvas", None)
        if canvas is None:
            return
        t = self.tokens
        self._last_ring_fraction = fraction
        try:
            canvas.delete("ring")
            size = max(100, int(canvas.winfo_reqwidth() or 148))
            stroke = max(6, size // 16)
            pad = max(9, size // 12)
            bbox = (pad, pad, size - pad, size - pad)
            # track
            canvas.create_arc(bbox, start=90, extent=359.9, style="arc",
                              width=stroke, outline=t["ring_track"], tags=("ring",))
            # progress arc (top, clockwise as time elapses)
            extent = -min(359.9, max(0.1, fraction * 359.9))
            canvas.create_arc(bbox, start=90, extent=extent, style="arc",
                              width=stroke, outline=t["accent"], tags=("ring",))
            # center marker: remaining seconds in a subtle pill
            mins = int(fraction * 100)
            canvas.create_text(size // 2, size // 2, text=f"{mins}%",
                               font=("Segoe UI", 10, "bold"), fill=t["muted"], tags=("ring",))
        except tk.TclError:
            pass  # cosmetic only — never interrupts the countdown chain

    def _schedule_countdown(self) -> None:
        """Fix Task 8: (re)arm exactly ONE countdown timer. Cancels any pending
        id first — duplicate after() callbacks are impossible by construction."""
        if getattr(self, "_app_closed", False):
            return  # Task 2: no re-arm after a real exit
        if self._countdown_after is not None:
            try:
                self.root.after_cancel(self._countdown_after)
            except tk.TclError:
                pass
            self._countdown_after = None
        self._countdown_after = self.root.after(1000, self._update_next_prayer_countdown)

    def refresh_dashboard(self) -> None:
        """UI-only: sync dashboard indicators (monitoring chip, pause state, next prayer, player state). No logic changes."""
        # Task 1 (runtime): this chain reschedules itself ONLY at the end; any
        # exception mid-body would silently kill the dashboard updates forever
        # in a windowed build (Tk swallows callback errors). Same armor as tick().
        try:
            tokens = self.tokens
            data = self.data(quiet=True)  # Phase 32: computed once, reused everywhere below
            player = (data or {}).get("music", "")  # Phase 32: single source for the hero/cards
            # monitoring chip
            if self.enabled.get():
                self._set_text(self.monitor_chip, "● المراقبة تعمل"); self._set_fg(self.monitor_chip, tokens["success"])
            else:
                self._set_text(self.monitor_chip, "● المراقبة متوقفة"); self._set_fg(self.monitor_chip, tokens["muted"])
            # pause/resume state (reads existing state variables only)
            # Phase 61: a Win7 browser media-key pause also shows as an active
            # pause period (Resume button enabled) — it is a real pause.
            # Phase 63: states render as semantic badges (Paused/Resumed/Error).
            if (self.paused_player is not None or self.paused_via_media_key
                    or (self.method.get() == "media" and self.resume_at is not None)):
                is_media = self.method.get() == "media"
                if self.resume_at:
                    remaining = self.resume_at - datetime.now()
                    secs = max(0, int(remaining.total_seconds()))
                    prayer_name = AR.get(self._active_prayer, "")
                    who = f"«{player}»" if player else "المشغّل"
                    what = f" لصلاة {prayer_name}" if prayer_name else " للصلاة"
                    self._set_text(self.state_dot, "●"); self._set_fg(self.state_dot, tokens["warning"])
                    self._set_text(self.state_label, f"{who} متوقف مؤقتًا{what}.")
                    self._set_text(self.state_detail, f"استئناف تلقائي عند {format_time_12(self.resume_at.strftime('%H:%M'))} — أو اضغط «استئناف الآن» لإنهاء الإيقاف فورًا.")
                    self._set_text(self.state_prayer, f"صلاة {prayer_name}" if prayer_name else "فترة الصلاة"); self._set_style(self.state_prayer, "BadgeWarn.TLabel")
                    self._set_text(self.state_resume_time, f"↺ {secs // 60:02d}:{secs % 60:02d}")
                else:
                    self._set_text(self.state_dot, "●"); self._set_fg(self.state_dot, tokens["error"])
                    self._set_text(self.state_label, "تعذّر الاستئناف التلقائي.")
                    self._set_text(self.state_detail, "استخدم «استئناف الآن» لإنهاء فترة الإيقاف.")
                    self._set_text(self.state_prayer, "خطأ"); self._set_style(self.state_prayer, "BadgeErr.TLabel")
                    self._set_text(self.state_resume_time, "")
                self.resume_btn.state(["!disabled"])
            else:
                self._set_text(self.state_resume_time, "")
                self._set_text(self.state_prayer, ""); self._set_style(self.state_prayer, "BadgeMut.TLabel")
                if self.enabled.get():
                    self._set_text(self.state_dot, "●"); self._set_fg(self.state_dot, tokens["success"])
                    self._set_text(self.state_label, "المراقبة تعمل — لا توجد عملية معلّقة.")
                    self._set_text(self.state_detail, (f"المشغّل المحمي: {player}." if player else "اختر مشغّل الموسيقى.") + " سيتم الإيقاف مؤقتًا تلقائيًا وقت كل صلاة.")
                else:
                    self._set_text(self.state_dot, "●"); self._set_fg(self.state_dot, tokens["muted"])
                    self._set_text(self.state_label, "المراقبة متوقفة.")
                    self._set_text(self.state_detail, "فعّل المراقبة من قسم المراقبة والإعدادات لبدء الحماية وقت الصلاة.")
                self.resume_btn.state(["disabled"])
            # Fix Task 8: the next-prayer card (name/time/countdown) is now owned by
            # the 1-second _update_next_prayer_countdown timer — this 2s pass no
            # longer writes it (two writers with different formats fought before).
            # Only the row highlight key 'p' is still computed here.
            p = None
            if data and data["times"]:
                now = datetime.now()
                current = now.hour * 60 + now.minute
                minutes = {}
                for prayer, t in data["times"].items():
                    h, m = map(int, t.split(":"))
                    minutes[prayer] = h * 60 + m
                upcoming = sorted((m, prayer) for prayer, m in minutes.items() if m > current)
                p = upcoming[0][1] if upcoming else min(minutes, key=minutes.get)
            # highlight the relevant prayer row (display-only; p=None clears all)
            for prayer, (name_lbl, entry) in self.prayer_rows.items():
                if prayer == p:
                    self._set_style(name_lbl, "PrayerNext.TLabel")
                    self._set_style(entry, "PrayerNext.TEntry")
                else:
                    self._set_style(name_lbl, "Card.TLabel")
                    self._set_style(entry, "TEntry")
            # Phase 64: dashboard mini-times rows (read-only labels) + highlight
            for prayer, (name_lbl, time_lbl) in self.dash_time_labels.items():
                tval = (data or {}).get("times", {}).get(prayer)
                self._set_text(time_lbl, format_time_12(tval) if tval else "--:--")
                if prayer == p:
                    self._set_style(name_lbl, "PrayerNext.TLabel")
                    self._set_style(time_lbl, "PrayerNextTime.TLabel")
                else:
                    self._set_style(name_lbl, "Card.TLabel")
                    self._set_style(time_lbl, "PrayerTime.TLabel")
            # selected programs + running state (display-only, throttled)
            if data and data["music"]:
                self._set_text(self.music_sel_label, data["music"])
                # Phase 47-B: re-detect on EVERY refresh from the cached rows so a
                # player that starts/stops later flips the indicator automatically
                # (still no PowerShell here — _process_rows is the Phase-32 cache).
                self._player_state_cache = (data["music"], bool(running_pids_for(data["music"], self._process_rows)))
                # Phase 63: semantic status badge (Active / inactive).
                if self._player_state_cache[1]:
                    self._set_text(self.music_state_label, "● نشط — يعمل")
                    self._set_style(self.music_state_label, "BadgeOk.TLabel")
                else:
                    self._set_text(self.music_state_label, "● غير متصل — المشغل غير قيد التشغيل")
                    self._set_style(self.music_state_label, "BadgeMut.TLabel")
            if data and data["adhan"]:
                self._set_text(self.adhan_sel_label, data["adhan"])
            # Phase 64: dashboard music card — adhan exclusion info line
            if data is not None:
                adhan_name = data.get("adhan", "")
                self._set_text(self.dash_adhan_label,
                               f"{ICONS['adhan']}  برنامج المؤذن المستثنى: {adhan_name}" if adhan_name
                               else f"{ICONS['adhan']}  لا يوجد مؤذن محدد (اختره من صفحة التحكم بالمشغّل)")
            # Phase 63: keep the header date current (once per 2s pass is cheap)
            self._refresh_header_date()
        except Exception as e:
            # Task 1 (runtime): full traceback; the chain must survive.
            import traceback
            logger.error(f"refresh_dashboard iteration failed: {e}\n{traceback.format_exc()}")
        finally:
            # Task 2: never reschedule after a real exit; store the timer id so
            # exit_app can cancel the pending dashboard refresh.
            if not getattr(self, "_app_closed", False):
                self._refresh_after = self.root.after(2_000, self.refresh_dashboard)
            else:
                logger.info("Dashboard worker exiting (app closed)")

    def refresh_processes(self) -> None:
        def worker():
            # Task 1 (stability): a dying refresh thread used to vanish silently
            # (comboboxes never repopulated, nothing logged). Every failure is
            # now visible and never affects the timer chains.
            try:
                running = {name for name, _ in process_rows()}
                installed = {exe for _, exe in installed_apps() + startmenu_apps()}
                values = sorted(running | installed)
                self.root.after(0, lambda: self.apply_values(values))
            except Exception as e:
                import traceback
                logger.error(f"process list refresh failed: {e}\n{traceback.format_exc()}")
                self.root.after(0, lambda: self.status.set("تعذر تحديث قائمة البرامج. حاول «تحديث» مرة أخرى."))
        threading.Thread(target=worker, daemon=True).start()

    def apply_values(self, values: list[str]) -> None:
        self.music_box["values"] = self.adhan_box["values"] = values
        self.status.set(f"تم العثور على {len(values)} برنامجًا قابلاً للاختيار (قيد التشغيل + مثبتًا).")

    def browse_music(self) -> None:
        self.browse_exe(self.music)

    def browse_adhan(self) -> None:
        self.browse_exe(self.adhan)

    def browse_exe(self, variable: tk.StringVar) -> None:
        chosen = filedialog.askopenfilename(title="اختر ملف البرنامج", filetypes=[("برامج Windows", "*.exe"), ("كل الملفات", "*.*")])
        if chosen:
            variable.set(chosen)
            if chosen not in self.music_box["values"]:
                values = list(self.music_box["values"]) + [chosen]
                self.music_box["values"] = self.adhan_box["values"] = values

    def data(self, quiet=False) -> dict | None:
        try:
            music, adhan = self.music.get().strip(), self.adhan.get().strip()
            if not music or (adhan and music.casefold() == adhan.casefold()): raise ValueError("اختر مشغّل الموسيقى، ويجب ألا يكون هو برنامج المؤذن.")
            minutes = int(self.minutes.get())
            if not 1 <= minutes <= 180: raise ValueError("مدة الاستئناف من 1 إلى 180 دقيقة.")
            times = {p: valid_time(v.get()) for p, v in self.times.items() if v.get().strip()}
            if not times: raise ValueError("أدخل موعدًا واحدًا على الأقل أو اجلب المواقيت.")
            return {
                "music": music, "adhan": adhan, "minutes": minutes, "method": self.method.get(),
                "times": times, "enabled": self.enabled.get(), "announce": self.announce.get(),
                "theme": self._theme_selection,  # Fix Task 7: keep manual theme across every save path
                "autostart": self.autostart_enabled.get(),  # Task 2: persisted with every save
                # Phase 47-B: persist the location selection and manual fallback.
                "location_mode": self.location_mode.get(),
                "manual_city": self.manual_city.get().strip(),
                "manual_country": self.manual_country.get().strip(),
                "manual_latitude": self.manual_latitude.get().strip(),
                "manual_longitude": self.manual_longitude.get().strip(),
                "manual_timezone": self.manual_timezone.get().strip(),
            }
        except ValueError as error:
            # Fix Task 1: quiet mode used to swallow this completely; the tick
            # then silently skipped every prayer. Task 1 (runtime): data() runs
            # on three timer chains (tick/dashboard/countdown) — log the reason
            # once per minute per message instead of every call, so the log
            # stays readable and real events are not buried.
            key = str(error)
            now_s = time.monotonic()
            if now_s - self._last_config_warn.get(key, 0.0) > 60.0:
                self._last_config_warn[key] = now_s
                logger.warning(f"Trigger precondition FAILED (config invalid): {error}")
            if not quiet: messagebox.showerror("إعداد غير صالح", str(error))
            return None

    def save_and_enable(self) -> None:
        data = self.data()
        if data:
            data["enabled"] = True; self.enabled.set(True); save_settings(data); self.status.set("المراقبة تعمل في الخلفية. يمكنك إغلاق النافذة لتصغيرها بجوار الساعة.")

    def pause_target(self) -> bool:
        data = self.data(quiet=True)
        if not data: return False
        if data["method"] == "media":
            logger.info("Media paused")
            media_toggle(); self.status.set("أُرسل زر الوسائط العام."); return True
        # Phase 61: Windows 7 + Chromium-family browser fallback. Chromium
        # browsers have no in-window WM_APPCOMMAND media handler and Windows 7
        # has no SMTC shell routing, so targeted APPCOMMAND is delivered but
        # silently ignored there (Phase 60 root cause). The ONLY safe Win7
        # channel for these browsers is the existing global media-key toggle.
        # This branch runs INSTEAD of the targeted-APPCOMMAND path below —
        # never both (the toggle would double-fire and undo the pause).
        if win7_browser_fallback(data["music"]):
            logger.info(
                f"Win7 browser fallback selected: player {data['music']!r} is a Chromium-family browser on Windows 7 "
                f"(Windows major {windows_major()}); pausing via global media key ONLY (no targeted APPCOMMAND)"
            )
            try:
                media_toggle()
            except Exception as e:
                # keybd_event is Win7-safe, but a failure here must be visible.
                logger.error(f"Media-key pause FAILED for Win7 browser {data['music']!r}: {e}")
                return False
            logger.info("Media-key pause sent: VK_MEDIA_PLAY_PAUSE via keybd_event (Win7 browser fallback)")
            # No paused_player PID: the media key is session-global, not tied
            # to a browser window. paused_via_media_key drives resume instead.
            self.paused_player = None
            self.paused_via_media_key = True
            self.resume_fails = 0
            self.status.set("أُرسل زر الوسائط العام لمتصفح ويندوز 7.")
            return True
        # Phase 30A-2: targeted APPCOMMAND_MEDIA_PAUSE to the player's windows
        try:
            windows = player_hwnds(data["music"])
        except Exception:
            # Fix Task 3: detection failures must be visible with a traceback,
            # not just a Tk callback error on the manual path.
            import traceback
            logger.error(f"Player detection failed for {data['music']!r}:\n{traceback.format_exc()}")
            return False
        if not windows:
            # Fix Task 1: explicit outcome — this is the "trigger fired but nothing
            # paused" branch, previously only a UI status string.
            if running_pids_for(data["music"], self._process_rows):
                logger.warning(f"Pause action NOT executed: player {data['music']!r} is running but has no pausable window")
                self.status.set("لم يُوجد نافذة للمشغّل المحدد؛ لم يتم الإيقاف.")
            else:
                logger.info(f"Pause action NOT executed: player {data['music']!r} is not running")
                self.status.set("مشغّل الموسيقى المحدد غير مفتوح؛ لم يتم إيقاف أي برنامج.")
            return False
        # Fix Task 3: detected player logged WITH its pid(s), not just the name.
        pids = sorted({hwnd_pid(h) for h in windows})
        logger.info(f"Media player detected: {data['music']} (pid(s): {pids}, windows: {len(windows)})")
        # Fix Task 3: per-window delivery log + aggregate result. Delivery
        # success (SendMessageTimeoutW processed the message) is the strongest
        # signal available in-process; actual playback state is the player's
        # own business and cannot be queried cross-process without COM.
        delivered = 0
        for hwnd in windows:
            if send_appcommand(hwnd, APPCOMMAND_MEDIA_PAUSE):
                delivered += 1
                logger.info(f"Pause command sent: APPCOMMAND_MEDIA_PAUSE -> hwnd {hwnd} (pid {hwnd_pid(hwnd)}) delivered OK")
        if delivered:
            logger.info(f"Pause result: command delivered to {delivered}/{len(windows)} window(s) of {data['music']}")
        else:
            logger.warning(f"Pause result: FAILED — no window of {data['music']!r} accepted the pause command (see APPCOMMAND warnings above)")
        # Phase 32: the PID player_hwnds matched the window on — no extra process scan.
        self.paused_player = hwnd_pid(windows[0])
        self.paused_via_media_key = False  # Phase 61: normal targeted APPCOMMAND pause
        self.resume_fails = 0
        self.status.set(f"تم إيقاف {data['music']} مؤقتًا.")
        return True

    def resume_now(self) -> None:
        # Phase 61: Win7 browser media-key pause -> resume with the SAME
        # media-key method ONLY, exactly once. Never targeted APPCOMMAND
        # here (the browser ignores it on Win7) and never both methods
        # (the toggle would double-fire and re-pause the browser).
        if self.paused_via_media_key and self.paused_player is None:
            logger.info(f"Resume action: resuming Win7 browser pause via global media key at {datetime.now():%H:%M:%S}")
            try:
                media_toggle()
                logger.info("Media-key resume sent: VK_MEDIA_PLAY_PAUSE via keybd_event (Win7 browser fallback)")
            except Exception as e:
                logger.error(f"Media-key resume FAILED for Win7 browser fallback: {e}")
            # The flag is cleared either way: the pause period is over and the
            # next pause re-decides its own delivery method.
            self.paused_via_media_key = False
            self.resume_fails = 0
            self._active_prayer = None  # display-only
            self.resume_at = None; self.status.set("تم استئناف مشغّل الموسيقى.")
            return
        if self.paused_player is not None:
            # Fix Task 2: explicit resume-action log with target details.
            logger.info(f"Resume action: resuming paused player (pid {self.paused_player}) via APPCOMMAND at {datetime.now():%H:%M:%S}")
            # Phase 30A-2: targeted APPCOMMAND_MEDIA_PLAY to the player's windows
            data = self.data(quiet=True)
            if data and data["music"]:
                try:
                    windows = player_hwnds(data["music"])
                except Exception:
                    import traceback
                    logger.error(f"Resume player detection failed for {data['music']!r}:\n{traceback.format_exc()}")
                    windows = []
                if not windows:
                    # Fix Task 2: previously silent — resume claimed success even
                    # when no window could receive the PLAY command.
                    logger.warning(f"Resume action: no window found for player {data['music']!r} — PLAY command not delivered")
                else:
                    delivered = 0
                    for hwnd in windows:
                        if send_appcommand(hwnd, APPCOMMAND_MEDIA_PLAY):
                            delivered += 1
                            logger.info(f"Resume command sent: APPCOMMAND_MEDIA_PLAY -> hwnd {hwnd} (pid {hwnd_pid(hwnd)}) delivered OK")
                    if delivered:
                        logger.info(f"Resume result: command delivered to {delivered}/{len(windows)} window(s) of {data['music']}")
                    else:
                        logger.warning(f"Resume result: FAILED — no window of {data['music']!r} accepted the resume command (see APPCOMMAND warnings above)")
            else:
                logger.warning("Resume action: config invalid — PLAY command not sent (see prior warning)")
            self.resume_fails = 0
            self._active_prayer = None  # display-only
            self.paused_player, self.resume_at = None, None; self.paused_via_media_key = False; self.status.set("تم استئناف مشغّل الموسيقى.")
        elif self.method.get() == "media":
            logger.info("Resume action: media key sent"); media_toggle(); self.resume_at = None; self.status.set("أُرسل زر الوسائط العام للاستئناف.")
        else:
            logger.info("Resume action: nothing to resume (no paused player)")
            self.status.set("لا توجد عملية معلّقة بواسطة التطبيق.")

    def test(self) -> None:
        # Phase 61: a Win7 browser media-key pause keeps paused_player=None;
        # the test button must RESUME it (second toggle) rather than fire
        # pause_target() again — that would double-toggle and un-pause.
        self.resume_now() if (self.paused_player or self.paused_via_media_key) else self.pause_target()

    def detect_location(self) -> None:
        """Phase 47-B: explicit 'detect now' button. Runs IP geolocation on a
        worker thread and updates the status label. Never blocks the UI."""
        self.status.set("يجري تحديد الموقع تلقائيًا…")

        def worker():
            info = self._resolve_auto_location()
            self.root.after(0, lambda: self._show_auto_location(info))
        threading.Thread(target=worker, daemon=True).start()

    def _show_auto_location(self, info: dict) -> None:
        if info:
            label = f"{info['city']}، {info['country']}"
            self.location_status.set(f"الموقع المكتشف: {label} (تقريبي عبر IP)")
            self.status.set(f"تم تحديد الموقع تلقائيًا: {label}. اضغط «جلب المواقيت» للاستخدام.")
        else:
            self.location_status.set("تعذر التحديد التلقائي؛ سيُستخدم الموقع اليدوي عند توفره.")
            self.status.set("تعذر تحديد الموقع تلقائيًا. تحقق من الإنترنت أو استخدم الموقع اليدوي.")

    def _resolve_auto_location(self) -> dict | None:
        """UI-side wrapper; the real implementation is module-level and
        worker-thread safe."""
        return resolve_auto_location()

    def _manual_location_ready(self) -> bool:
        """A manual location is usable when city+country OR lat+lon exist."""
        has_names = bool(self.manual_city.get().strip() and self.manual_country.get().strip())
        has_coords = bool(self.manual_latitude.get().strip() and self.manual_longitude.get().strip())
        return has_names or has_coords

    def apply_location(self) -> None:
        """Phase 47-B: validate the manual fields, persist the location mode,
        then recalculate prayer times immediately from the new location."""
        try:
            lat_text = self.manual_latitude.get().strip()
            lon_text = self.manual_longitude.get().strip()
            if lat_text or lon_text:
                valid_coordinate(lat_text, "latitude")   # raises ValueError on bad input
                valid_coordinate(lon_text, "longitude")
        except ValueError as error:
            messagebox.showerror("موقع غير صالح", str(error))
            return
        data = self.data(quiet=True)
        if data: save_settings(data)
        if self.location_mode.get() == "manual" and not self._manual_location_ready():
            messagebox.showerror("موقع غير صالح", "أدخل المدينة والدولة أو خط العرض وخط الطول.")
            return
        self.fetch_times()

    def _location_snapshot(self) -> dict:
        """Phase 47-B: read Tk location state ON THE UI THREAD only, returning
        plain values safe to pass to the worker thread. Tk variables are not
        thread-safe and must never be read from a worker thread."""
        try:
            latitude = valid_coordinate(self.manual_latitude.get(), "latitude") if self.manual_latitude.get().strip() else None
        except ValueError:
            latitude = None
        try:
            longitude = valid_coordinate(self.manual_longitude.get(), "longitude") if self.manual_longitude.get().strip() else None
        except ValueError:
            longitude = None
        return {
            "mode": self.location_mode.get(),
            "city": self.manual_city.get().strip() or "Alexandria",
            "country": self.manual_country.get().strip() or "Egypt",
            "city_label": self.manual_city.get().strip() or "الإسكندرية",
            "country_label": self.manual_country.get().strip() or "مصر",
            "latitude": latitude,
            "longitude": longitude,
            "timezone": self.manual_timezone.get().strip() or None,
            "manual_ready": self._manual_location_ready(),
        }

    @staticmethod
    def _resolve_location(snapshot: dict) -> tuple:
        """Pure location-priority resolver (worker-thread safe).

        Priority: manual mode -> automatic IP -> saved manual -> default.
        Runs on the worker thread, so it uses only plain snapshot values and
        the module-level IP locator — never Tk widgets or variables."""
        if snapshot["mode"] == "manual":
            label = f"{snapshot['city_label']}، {snapshot['country_label']}"
            return (snapshot["city"], snapshot["country"], snapshot["latitude"], snapshot["longitude"], snapshot["timezone"], label, "manual")
        auto = resolve_auto_location()
        if auto:
            label = f"{auto['city']}، {auto['country']}"
            return (auto["city"], auto["country"], auto["latitude"], auto["longitude"], auto["timezone"], label, "auto")
        if snapshot["manual_ready"]:
            label = f"{snapshot['city_label']}، {snapshot['country_label']}"
            return (snapshot["city"], snapshot["country"], snapshot["latitude"], snapshot["longitude"], snapshot["timezone"], label, "manual-fallback")
        return ("Alexandria", "Egypt", None, None, None, "الإسكندرية، مصر (افتراضي)", "default")

    def _local_timezone(self) -> str:
        """Best-effort IANA timezone for the LOCAL machine (stdlib-only, Py3.8).

        1) Windows registry mapping (SystemTimezone -> IANA via the standard
           windows zone table shipped with tzdata, if available offline).
        2) UTC offset from the local clock as a safe last resort.
        The API accepts timezonestring; when we cannot resolve a name, we
        pass the UTC offset explicitly instead (AlAdhan supports this)."""
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\TimeZoneInformation") as key:
                windows_tz, _ = winreg.QueryValueEx(key, "TimeZoneKeyName")
            import importlib.resources as _resources
            try:
                resource = _resources.read_text("tzdata.zoneinfo", "windows_zones.json")
                mapping = json.loads(resource)
                iana = mapping.get("primary", {}).get(windows_tz)
                if iana: return iana
            except (ImportError, FileNotFoundError, json.JSONDecodeError, OSError):
                pass
        except Exception:
            pass
        # No third-party tz local package; derive a valid fixed-offset IANA
        # name safely. AlAdhan's timezonestring rejects "UTC+02:00" but
        # accepts "Etc/GMT-2". POSIX Etc zones use the INVERTED sign, so
        # UTC+02:00 is "Etc/GMT-2" and UTC-05:00 is "Etc/GMT+5".
        offset_seconds = datetime.now().astimezone().utcoffset().total_seconds()
        sign = "-" if offset_seconds >= 0 else "+"
        hours = abs(int(offset_seconds)) // 3600
        return f"Etc/GMT{sign}{hours}"

    def fetch_times(self) -> None:
        """Phase 47/47-B: fetch accurate prayer times for the CURRENT location.

        Location priority: automatic IP (if enabled and reachable) -> manual
        saved location -> documented Alexandria default. The request runs on a
        daemon worker thread; every failure path keeps the app responsive and
        leaves the existing/manual times untouched."""
        self.status.set("يجري جلب المواقيت…")
        # Snapshot location state on the UI thread; the worker must not touch Tk.
        snapshot = self._location_snapshot()

        def build_query(city: str, country: str, latitude, longitude, timezone: str | None) -> tuple:
            today = datetime.now().strftime("%d-%m-%Y")
            params = {"method": 5, "timezonestring": timezone or self._local_timezone()}
            if latitude is not None and longitude is not None:
                # Coordinates take precedence over city names for accuracy.
                params["latitude"] = f"{latitude}"
                params["longitude"] = f"{longitude}"
                base = f"https://api.aladhan.com/v1/timings/{today}"
            else:
                params["city"] = city
                params["country"] = country
                base = f"https://api.aladhan.com/v1/timingsByCity/{today}"
            query = urllib.parse.urlencode(params)
            request = urllib.request.Request(f"{base}?{query}", headers={"User-Agent": "PrayerMusicGuard/1.2"})
            return request

        def parse_timings(payload: dict) -> dict:
            result = payload["data"]["timings"]
            if not isinstance(result, dict) or any(not isinstance(result.get(p), str) for p in PRAYERS):
                raise ValueError("malformed prayer timings structure")
            return {p: valid_time(result[p][:5]) for p in PRAYERS}

        def worker(snapshot: dict):
            city, country, latitude, longitude, timezone, label, source = App._resolve_location(snapshot)
            try:
                request = build_query(city, country, latitude, longitude, timezone)
                with urllib.request.urlopen(request, timeout=12) as response:
                    values = parse_timings(json.load(response))
                logger.info(f"Prayer times loaded for {city}, {country} (source={source})")
                self.root.after(0, lambda: self.apply_times(values, label))
            except Exception as e:
                logger.error(f"Failed to fetch prayer times for {city}, {country} (source={source}): {e}")
                message = "تعذر الجلب. يمكنك إدخال المواقيت يدويًا."
                self.root.after(0, lambda: self.status.set(message))
        threading.Thread(target=worker, args=(snapshot,), daemon=True).start()

    def apply_times(self, values: dict, location_label: str = "الإسكندرية، مصر") -> None:
        logger.info(f"Prayer times loaded: {values} (location: {location_label})")
        for prayer, value in values.items(): self.times[prayer].set(format_time_12(value))
        self.location_status.set(f"الموقع المستخدم للمواقيت: {location_label}")
        self.status.set(f"تم جلب مواقيت {location_label}. اضغط «حفظ وتشغيل».")

    def tick(self) -> None:
        # Phase 30A-3: an unexpected error must never kill the 10-second scheduler.
        try:
            now = datetime.now()
            self._tick_count += 1
            # Task 1 (diagnostics): per-tick DEBUG line — current time + trigger
            # state on EVERY tick (the ~5-min INFO heartbeat stays for normal
            # operation). Enable with PMG_LOG_LEVEL=DEBUG in the environment.
            logger.debug(
                f"tick #{self._tick_count} at {now:%Y-%m-%d %H:%M:%S}; "
                f"enabled={self.enabled.get()}, paused={self.paused_player is not None}, "
                f"paused_via_media_key={self.paused_via_media_key}, "
                f"resume_at={self.resume_at.strftime('%H:%M:%S') if self.resume_at else None}"
            )
            # Fix Task 1: heartbeat once every ~5 minutes (every 60th tick at the
            # Fix Task 2 cadence of 5s) with the trigger inputs, so "loop alive /
            # time / next prayer" are answerable from the log.
            if self._tick_count % 60 == 1:
                data = self.data(quiet=True)
                enabled = self.enabled.get()
                if data and enabled and self.paused_player is None and not self.paused_via_media_key:
                    current = now.strftime("%H:%M")
                    nexts = sorted(
                        (t, p) for p, t in data["times"].items()
                        if t > current
                    )
                    if nexts:
                        nt, np_ = nexts[0]
                        logger.info(f"Monitoring tick #{self._tick_count}: alive at {now:%Y-%m-%d %H:%M:%S}; next prayer {np_} at {nt}")
                    else:
                        logger.info(f"Monitoring tick #{self._tick_count}: alive at {now:%Y-%m-%d %H:%M:%S}; all of today's prayers passed (next tomorrow)")
                elif not data:
                    logger.info(f"Monitoring tick #{self._tick_count}: alive at {now:%Y-%m-%d %H:%M:%S}; trigger blocked: config invalid (see prior warning)")
                elif not enabled:
                    logger.info(f"Monitoring tick #{self._tick_count}: alive at {now:%Y-%m-%d %H:%M:%S}; trigger blocked: monitoring disabled")
                else:
                    logger.info(f"Monitoring tick #{self._tick_count}: alive at {now:%Y-%m-%d %H:%M:%S}; trigger blocked: player already paused (period active)")
            if self.resume_at and now >= self.resume_at:
                logger.info(f"Resume action: resume time {self.resume_at:%H:%M:%S} reached at {now:%H:%M:%S}")
                self.resume_now()
            data = self.data(quiet=True)
            # Phase 61: a Win7 browser media-key pause has paused_player=None;
            # it must still count as "period active" here or a second prayer in
            # the same window would re-fire pause_target and double-toggle.
            if data and self.enabled.get() and self.paused_player is None and not self.paused_via_media_key:
                # Fix Task 2: day-bucketed duplicate prevention. Markers rotate
                # at midnight; the same prayer can never re-fire on the same
                # day, and yesterday's markers can never block today's.
                today = now.strftime("%Y-%m-%d")
                if today != self._done_date:
                    logger.info(f"Midnight rollover: rotating handled-prayer markers ({self._done_date} -> {today})")
                    self._done_date = today
                    self.done.clear()
                now_minutes = now.hour * 60 + now.minute
                # Pick the earliest prayer inside [now - catch-up, now] that was
                # not handled yet; several can overlap after sleep — only the
                # earliest unhandled one fires, once. (Both sides are minutes
                # since midnight.)
                due = sorted(
                    (t, p) for p, t in data["times"].items()
                    if 0 <= now_minutes - _hhmm_to_minutes(t) < TRIGGER_CATCHUP_MINUTES
                    and f"{today}-{p}-{t}" not in self.done
                )
                for prayer_time, prayer in due:
                    marker = f"{today}-{prayer}-{prayer_time}"
                    if marker in self.done:  # re-check inside loop: pause_target may recurse
                        continue
                    self.done.add(marker)
                    delay_s = (now_minutes - _hhmm_to_minutes(prayer_time)) * 60
                    if delay_s <= 0:
                        logger.info(f"Trigger detected: {prayer} time {prayer_time} == current {now.strftime('%H:%M')} — pause action reached")
                    else:
                        logger.info(f"Catch-up trigger detected: {prayer} time {prayer_time} fired {delay_s // 60}m {delay_s % 60}s late at {now.strftime('%H:%M:%S')} — pause action reached")
                    # Phase 44: pause FIRST (its completion is the anchor),
                    # then announce — one controlled 2s delay inside speak.
                    # The announcement still sounds when the pause found no
                    # running player (adhan must not depend on music state).
                    paused_ok = self.pause_target()
                    if paused_ok:
                        self._active_prayer = prayer  # display-only
                        self.resume_at = now + timedelta(minutes=data["minutes"])
                        resume_display = format_time_12(self.resume_at.strftime("%H:%M"))
                        self.status.set(f"بدأت فترة {AR[prayer]}؛ الاستئناف عند {resume_display}.")
                        logger.info(f"Prayer event triggered for {AR[prayer]} at {prayer_time} — music paused until {self.resume_at:%H:%M}.")
                        self.notify("صلاة وسكون", f"تم إيقاف الموسيقى حتى {resume_display}.")
                    self._announce_prayer(prayer, now)  # Phase 44: after pause attempt, ~2s delay inside
                    break
                else:
                    # Fix Task 2: visibility for "inside the window but already
                    # handled" — logged at most once per (prayer, time) via the
                    # marker set to avoid spamming every 5s tick.
                    for prayer, prayer_time in data["times"].items():
                        skipped_marker = f"skipped-{today}-{prayer}-{prayer_time}"
                        if (0 <= now_minutes - _hhmm_to_minutes(prayer_time) < TRIGGER_CATCHUP_MINUTES
                                and f"{today}-{prayer}-{prayer_time}" in self.done
                                and skipped_marker not in self.done):
                            self.done.add(skipped_marker)
                            logger.info(f"Trigger skipped: {prayer} time {prayer_time} already handled today (marker present)")
        except Exception as e:
            # Fix Task 1: full traceback — the message alone hid where ticks fail.
            import traceback
            logger.error(f"tick iteration failed: {e}\n{traceback.format_exc()}")
        finally:
            # Task 2: never reschedule after a real exit; store the timer id so
            # exit_app can cancel the pending tick.
            if not getattr(self, "_app_closed", False):
                self._tick_after = self.root.after(TICK_SECONDS * 1000, self.tick)
            else:
                logger.info("Tick worker exiting (app closed)")

    def _announce_prayer(self, prayer: str, now: datetime) -> None:
        """Phase 37: play the prayer's MP3 exactly once per (day, prayer).
        OFF setting / already announced / playback failure — all silent, never
        blocking and never changing the pause behavior."""
        if not self.announce.get(): return
        day = now.strftime("%Y-%m-%d")
        if day != self._announced_date:  # midnight rollover: fresh set
            self._announced_date = day
            self._announced.clear()
        marker = f"{day}-{prayer}"
        if marker in self._announced: return
        self._announced.add(marker)
        speak(prayer)
        logger.info(f"Prayer announcement started for {AR[prayer]}")

    def _tray_image(self):
        """Phase 40: tray icon with layered fallbacks — never silently missing.
        1) brand PNG via PIL (best quality)   2) brand ICO via PIL
        3) ICO via tk (no PIL)                4) generated solid-color icon
        Returns a PIL Image (pystray needs one) or None only if ALL failed."""
        def _pil_open(path):
            from PIL import Image
            im = Image.open(path); im.load()
            return im
        try:
            if PNG_ICON_PATH.exists():
                im = _pil_open(PNG_ICON_PATH)
                logger.info(f"Tray icon loaded from PNG: {PNG_ICON_PATH}")
                return im
        except Exception as e:
            logger.warning(f"Tray icon PNG load failed ({PNG_ICON_PATH}): {e}")
        try:
            if ICON_PATH.exists():
                im = _pil_open(ICON_PATH)
                logger.info(f"Tray icon loaded from ICO: {ICON_PATH}")
                return im
        except Exception as e:
            logger.warning(f"Tray icon ICO load failed ({ICON_PATH}): {e}")
        # PIL-free last resort: 16x16 solid brand-color square via raw RGBA bytes
        try:
            from PIL import Image as _I
            return _I.new("RGBA", (16, 16), (14, 124, 95, 255))  # brand accent green
        except Exception as e:
            logger.error(f"Tray icon fallback generation failed: {e}")
            return None

    def start_tray(self) -> None:
        if not TRAY_AVAILABLE:
            logger.warning("Tray unavailable: pystray/PIL not importable; close will exit the app.")
            return
        image = self._tray_image()
        if image is None:
            logger.error("Tray disabled: no icon could be loaded or generated.")
            return
        menu = pystray.Menu(
            pystray.MenuItem(f"{ICONS['open']}  فتح البرنامج", lambda icon, item: self.root.after(0, self.show_window), default=True),
            pystray.MenuItem(f"{ICONS['test']}  بدء/إيقاف المراقبة", lambda icon, item: self.root.after(0, self.toggle_monitor)),
            pystray.MenuItem(f"{ICONS['resume']}  استئناف الموسيقى الآن", lambda icon, item: self.root.after(0, self.resume_now)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(f"{ICONS['exit']}  خروج", lambda icon, item: self.root.after(0, self.exit_app)))
        self.tray = pystray.Icon("PrayerMusicGuard", image, "صلاة وسكون", menu)
        threading.Thread(target=self.tray.run, daemon=True).start()
        logger.info("Tray icon started")

    def notify(self, title: str, body: str) -> None:
        if self.tray:
            try: self.tray.notify(body, title)
            except Exception as e:
                logger.error(f"Tray notification failed: {e}")

    def hide_to_tray(self) -> None:
        # Phase 40: closing the window NEVER exits the app while the tray is
        # alive; the process stays resident and is re-openable from the tray.
        if self.tray:
            self.root.withdraw(); self.status.set("التطبيق يعمل بجوار الساعة.")
            logger.info("Window hidden to tray; process stays alive")
        else:
            # No tray (pystray/PIL unavailable): hiding would make the app
            # unreachable, so exit cleanly instead of vanishing.
            logger.warning("Close requested without a tray icon; exiting (app would otherwise be unreachable).")
            self.exit_app()

    def show_window(self) -> None:
        # Phase 27/40: robust restore — works for withdrawn AND minimized
        # (iconified) windows; logs the transition for diagnosis.
        try:
            if self.root.state() == "iconic" or not self.root.winfo_viewable():
                self.root.deiconify()
            self.root.lift(); self.root.focus_force()
            logger.info("Main window restored from tray")
        except tk.TclError as e:
            logger.warning(f"Window restore issue: {e}")
            try: self.root.deiconify()  # best-effort: still try to show it
            except tk.TclError: pass

    def toggle_autostart(self) -> None:
        """Task 2 / Phase 64 FIX: flip the per-user launch-at-logon option.

        Root cause of the old bug: ttk.Checkbutton flips the Tk variable FIRST,
        then invokes this command — the old code computed the target as
        NOT var.get(), inverting the user's click so the checkbox snapped back
        and the registry got the opposite of what was requested.

        Correct behavior: the (already flipped) variable IS the desired state.
        1. desired = self.autostart_enabled.get()
        2. registry write via set_autostart() (HKCU Run — Win7-safe, no admin)
        3. on success: persist "autostart" in settings.json through the
           standard save path (all other fields preserved)
        4. on failure: revert the variable to the REAL registry state and show
           a clear error — never silently report success."""
        desired = self.autostart_enabled.get()
        if set_autostart(desired):
            self.autostart_enabled.set(desired)
            data = self.data(quiet=True)
            payload = data if data else self.saved
            payload["autostart"] = desired
            save_settings(payload)
            self.status.set("سيبدأ التطبيق مع دخول ويندوز." if desired else "لن يبدأ التطبيق مع دخول ويندوز.")
            logger.info(f"Autostart {'enabled' if desired else 'disabled'} (HKCU Run entry {'written' if desired else 'removed'}); setting persisted")
        else:
            # registry operation failed — revert the checkbox to the REAL state
            real_state = autostart_enabled()
            self.autostart_enabled.set(real_state)
            error_text = "تعذّر تسجيل بدء التشغيل مع ويندوز — تعذر الكتابة في سجل النظام (HKCU Run). حاول مرة أخرى."
            self.status.set(error_text)
            logger.error(f"Autostart {'enable' if desired else 'disable'} FAILED; checkbox reverted to registry state ({real_state}); user notified")

    def toggle_monitor(self) -> None:
        self.enabled.set(not self.enabled.get()); data = self.data(quiet=True)
        if data: save_settings(data); self.status.set("تم تشغيل المراقبة." if self.enabled.get() else "تم إيقاف المراقبة.")

    def exit_app(self) -> None:
        logger.info("Application exiting")
        # Task 2 (lifetime): flag first so every timer chain and worker checks
        # it and stops rescheduling / iterating.
        self._app_closed = True
        # Task 2: cancel ALL pending after() timers — countdown (1s), tick (5s),
        # and dashboard (2s). after_cancel before destroy guarantees no
        # callback fires on a dead Tk and no timer errors.
        for attr in ("_countdown_after", "_tick_after", "_refresh_after"):
            timer_id = getattr(self, attr, None)
            if timer_id is not None:
                try:
                    self.root.after_cancel(timer_id)
                except tk.TclError:
                    pass
                setattr(self, attr, None)
        logger.info("All Tk timers cancelled")
        # Phase 61: also resume a Win7 browser media-key pause on exit —
        # otherwise the browser stays paused with no one left to resume it.
        if self.paused_player is not None or self.paused_via_media_key: self.resume_now()
        if self.tray:
            try: self.tray.stop()  # removes the tray icon before teardown
            except Exception as e:
                logger.warning(f"Tray stop issue during exit: {e}")
        # Task 2: brief grace period so the sleeping worker threads can notice
        # _app_closed and log their own exit lines. Bounded at 1.5s — never a
        # hang; daemon threads are NOT waited on beyond this.
        grace_deadline = time.monotonic() + 1.5
        for worker in getattr(self, "_daemon_threads", []):
            worker.join(timeout=max(0.0, grace_deadline - time.monotonic()))
        try: self.root.destroy()
        except tk.TclError: pass
        logger.info("Clean exit complete; terminating process")
        os._exit(0)  # Phase 40: guarantee process termination (daemon threads die)


if __name__ == "__main__":
    logger.info(f"Application starting: PrayerMusicGuard v{APP_VERSION} ({'frozen' if getattr(sys, 'frozen', False) else 'source'} run, python {sys.version.split()[0]})")
    # Task 2: single-instance guard — a second launch (autostart + manual click)
    # must never create duplicate monitoring workers or tray icons.
    if not acquire_single_instance():
        logger.warning("Second instance detected; exiting without starting monitoring")
        os._exit(0)
    # Task 2 (diagnostics): startup source — HKCU Run entry present means the
    # process very likely came from Windows logon autostart.
    logger.info(f"Launch source: {'logon autostart (HKCU Run entry present)' if autostart_enabled() else 'manual/direct launch (no autostart entry)'}")
    set_app_id()
    enable_dpi_awareness()  # Phase 25c: must run before the first Tk window
    window = tk.Tk()
    App(window)
    window.mainloop()