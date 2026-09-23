"""Phase 4: pywebview JS bridge between the HTML frontend and main.py.

This module IMPORTS main.py as a library (it never starts Tkinter's
mainloop) and exposes a small, JSON-safe API to the HTML frontend through
pywebview's ``js_api``. main.py itself is never modified.

Bridge methods (JS: window.pywebview.api.<name>(...)):
  get_state()             -> full UI snapshot (prayers, countdown, flags)
  save_settings(payload)  -> validate + persist through main.save_settings
  set_theme(theme)        -> persist "dark" | "light"
  set_autostart(enabled)  -> HKCU Run entry + persist
  pause_now()             -> pause the configured music player
  resume_now()            -> resume it
  toggle_pause()          -> pause/resume based on the last known state
  fetch_times()           -> refresh prayer times for the current location
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import threading
import time
import urllib.parse
import urllib.request
import subprocess
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)


def _main_py() -> str:
    """On-disk main.py path. Used ONLY by unfrozen source/development runs.

    A frozen PyInstaller build never reads main.py from disk: ``_load_main``
    imports the compiled ``main`` module straight from the PYZ archive (it is
    a hiddenimport in PrayerMusicGuard.spec), so no readable application .py
    has to ship inside the OneDir bundle (Phase 20.46.A).
    """
    return os.path.join(PROJECT_ROOT, "main.py")


MAIN_PY = _main_py()

_ROWS_CACHE = {"at": 0.0, "rows": []}


def _log(msg: str) -> None:
    try:
        appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
        log_dir = os.path.join(appdata, "PrayerMusicGuard")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "backend_api.log")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat()}] {msg}\n")
    except Exception:
        pass


def _load_main():
    if getattr(sys, "frozen", False):
        # Frozen PyInstaller run: "main" is compiled into the PYZ archive
        # (hiddenimport in PrayerMusicGuard.spec). Import the compiled module
        # directly. Never fall back to sys._MEIPASS/main.py + exec_module here:
        # that would require shipping readable source, which Phase 20.46.A
        # removes from the bundle.
        _log("Loading main from PYZ (frozen build)")
        module = __import__("main")
        sys.modules.setdefault("pmg_main", module)
        _log("main loaded from PYZ successfully")
        return module
    # Unfrozen source/development run: keep loading the real file from disk so
    # editing main.py during development still takes effect without a build.
    _log(f"Loading main.py from: {MAIN_PY}")
    spec = importlib.util.spec_from_file_location("pmg_main", MAIN_PY)
    if spec is None or spec.loader is None:
        raise ImportError("cannot load {0}".format(MAIN_PY))
    module = importlib.util.module_from_spec(spec)
    sys.modules["pmg_main"] = module
    spec.loader.exec_module(module)
    _log("main.py loaded successfully")
    return module


try:
    _MAIN = _load_main()
    _LOAD_ERROR = ""
    _log(f"_MAIN loaded, APP_VERSION={getattr(_MAIN, 'APP_VERSION', 'unknown')}")
except Exception as _error:
    _MAIN = None
    _LOAD_ERROR = str(_error)
    _log(f"_MAIN load failed: {_error}")


class BackendAPI:
    """JSON-safe facade over the existing Prayer Music Guard backend."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.paused_player = None
        self.resume_at = None
        self.paused_via_media_key = False
        self.active_player = ""
        self._active_prayer = None
        self._done = set()
        self._done_date = datetime.now().strftime("%Y-%m-%d")
        self._announced = set()
        self._announced_date = ""
        self._scheduler_thread = None
        self._scheduler_stop = threading.Event()
        # Phase 20.65: set by _update_quit() so the window's close-to-tray
        # handler (webview_main._on_closing) allows this close for real instead
        # of hiding the window to the tray.
        self._allow_close = False

    def __getstate__(self):
        state = self.__dict__.copy()
        state.pop('_lock', None)
        state.pop('_scheduler_thread', None)
        state.pop('_scheduler_stop', None)
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self._lock = threading.RLock()
        self._scheduler_stop = threading.Event()
        self._scheduler_thread = None

    def _saved(self) -> dict:
        if _MAIN is None:
            return {}
        try:
            return _MAIN.load_settings()
        except Exception:
            return {}

    def _live_app(self):
        if _MAIN is None:
            return None
        app_cls = getattr(_MAIN, "App", None)
        if app_cls is None:
            return None
        for value in list(vars(_MAIN).values()):
            if isinstance(value, app_cls):
                return value
        return None

    def _pause_snapshot(self) -> dict:
        saved = self._saved()
        method = str(saved.get("method") or "suspend")
        app = self._live_app()
        if app is not None:
            try:
                method = app.method.get()
            except Exception:
                pass
            return {
                "source": "main_app",
                "method": method,
                "paused_player": getattr(app, "paused_player", None),
                "resume_at": getattr(app, "resume_at", None),
                "paused_via_media_key": bool(getattr(app, "paused_via_media_key", False)),
                "active_player": str(saved.get("music") or ""),
                "active_prayer": getattr(app, "_active_prayer", None),
            }
        if self.resume_at is not None and datetime.now() >= self.resume_at:
            self._clear_pause()
        return {
            "source": "bridge",
            "method": method,
            "paused_player": self.paused_player,
            "resume_at": self.resume_at,
            "paused_via_media_key": self.paused_via_media_key,
            "active_player": self.active_player or str(saved.get("music") or ""),
            "active_prayer": self._active_prayer,
        }

    def _paused_from(self, snap: dict) -> bool:
        if snap.get("paused_player") is not None or snap.get("paused_via_media_key"):
            return True
        return snap.get("method") == "media" and snap.get("resume_at") is not None

    def _mark_paused(self, music: str, paused_player, via_media_key: bool) -> None:
        saved = self._saved()
        try:
            minutes = int(saved.get("minutes", 15) or 15)
        except (TypeError, ValueError):
            minutes = 15
        with self._lock:
            self.paused_player = paused_player
            self.paused_via_media_key = via_media_key
            self.active_player = music
            self.resume_at = datetime.now() + timedelta(minutes=minutes)

    def _clear_pause(self) -> None:
        with self._lock:
            self.paused_player = None
            self.resume_at = None
            self.paused_via_media_key = False
            self._active_prayer = None

    def _pause_fields(self, snap: dict) -> dict:
        resume_at = snap.get("resume_at")
        return {
            "paused_player": snap.get("paused_player"),
            "resume_at": resume_at.strftime("%Y-%m-%dT%H:%M:%S") if hasattr(resume_at, "strftime") else None,
            "paused_via_media_key": bool(snap.get("paused_via_media_key", False)),
            "active_player": str(snap.get("active_player") or ""),
            "active_prayer": snap.get("active_prayer"),
            "pause_source": snap.get("source", "bridge"),
        }

    def scheduler_running(self) -> bool:
        thread = self._scheduler_thread
        return bool(thread is not None and thread.is_alive())

    def start_scheduler(self) -> bool:
        if _MAIN is None:
            return False
        if self.scheduler_running():
            return True
        self._scheduler_stop.clear()
        thread = threading.Thread(target=self._scheduler_loop, name="pmg-scheduler", daemon=True)
        self._scheduler_thread = thread
        thread.start()
        return True

    def stop_scheduler(self) -> None:
        self._scheduler_stop.set()
        thread = self._scheduler_thread
        if thread is not None and thread.is_alive() and thread is not threading.current_thread():
            try:
                thread.join(timeout=2.0)
            except RuntimeError:
                pass
        self._scheduler_thread = None

    def _scheduler_loop(self) -> None:
        interval = float(getattr(_MAIN, "TICK_SECONDS", 5)) if _MAIN is not None else 5.0
        while not self._scheduler_stop.wait(interval):
            try:
                self._tick_once()
            except Exception as error:
                print("[backend_api] scheduler tick failed: {0}".format(error))

    def _tick_once(self) -> None:
        if _MAIN is None:
            return
        now = datetime.now()
        with self._lock:
            resume_at = self.resume_at
        if resume_at is not None and now >= resume_at:
            self._scheduler_resume()
        saved = self._saved()
        if not saved.get("enabled", False):
            return
        times = dict(saved.get("times") or {})
        if not times:
            return
        with self._lock:
            if self.paused_player is not None or self.paused_via_media_key:
                return
        today = now.strftime("%Y-%m-%d")
        if today != self._done_date:
            self._done_date = today
            self._done.clear()
        now_minutes = now.hour * 60 + now.minute
        catchup = int(getattr(_MAIN, "TRIGGER_CATCHUP_MINUTES", 5))
        due = sorted(
            (t, p) for p, t in times.items()
            if 0 <= now_minutes - _MAIN._hhmm_to_minutes(t) < catchup
            and "{0}-{1}-{2}".format(today, p, t) not in self._done
        )
        if not due:
            return
        prayer_time, prayer = due[0]
        marker = "{0}-{1}-{2}".format(today, prayer, prayer_time)
        if marker in self._done:
            return
        self._done.add(marker)
        paused_ok = self._scheduler_pause(saved)
        if paused_ok:
            with self._lock:
                self._active_prayer = prayer
                try:
                    minutes = int(saved.get("minutes", 15) or 15)
                except (TypeError, ValueError):
                    minutes = 15
                self.resume_at = now + timedelta(minutes=minutes)
        self._scheduler_announce(prayer, now)

    def _scheduler_pause(self, saved: dict) -> bool:
        music = str(saved.get("music") or "").strip()
        if not music:
            return False
        if str(saved.get("method") or "suspend") == "media":
            try:
                _MAIN.media_toggle()
            except Exception as error:
                print("[backend_api] scheduler media pause failed: {0}".format(error))
                return False
            return True
        try:
            if hasattr(_MAIN, 'needs_media_key_fallback') and _MAIN.needs_media_key_fallback(music):
                _MAIN.media_toggle()
                with self._lock:
                    self.paused_player = None
                    self.paused_via_media_key = True
                return True
            if _MAIN.win7_browser_fallback(music):
                _MAIN.media_toggle()
                with self._lock:
                    self.paused_player = None
                    self.paused_via_media_key = True
                return True
        except Exception:
            pass
        try:
            windows = _MAIN.player_hwnds(music)
        except Exception as error:
            print("[backend_api] scheduler player detection failed: {0}".format(error))
            return False
        if not windows:
            return False
        delivered = 0
        for hwnd in windows:
            try:
                if _MAIN.send_appcommand(hwnd, _MAIN.APPCOMMAND_MEDIA_PAUSE):
                    delivered += 1
            except Exception:
                continue
        if not delivered:
            return False
        try:
            paused_pid = _MAIN.hwnd_pid(windows[0])
        except Exception:
            paused_pid = None
        with self._lock:
            self.paused_player = paused_pid
            self.paused_via_media_key = False
        return True

    def _scheduler_resume(self) -> None:
        if _MAIN is None:
            return
        saved = self._saved()
        music = str(saved.get("music") or "").strip()
        with self._lock:
            via_media_key = self.paused_via_media_key
            paused_player = self.paused_player
        needs_media = via_media_key and paused_player is None
        if not needs_media and music:
            try:
                if hasattr(_MAIN, 'needs_media_key_fallback') and _MAIN.needs_media_key_fallback(music):
                    needs_media = True
            except Exception:
                pass
        if needs_media:
            try:
                _MAIN.media_toggle()
            except Exception as error:
                print("[backend_api] scheduler media resume failed: {0}".format(error))
            self._clear_pause()
            return
        if paused_player is not None:
            if music:
                try:
                    windows = _MAIN.player_hwnds(music)
                except Exception:
                    windows = []
                for hwnd in windows:
                    try:
                        _MAIN.send_appcommand(hwnd, _MAIN.APPCOMMAND_MEDIA_PLAY)
                    except Exception:
                        continue
            self._clear_pause()
            return
        if str(saved.get("method") or "suspend") == "media":
            try:
                _MAIN.media_toggle()
            except Exception as error:
                print("[backend_api] scheduler media resume failed: {0}".format(error))
        self._clear_pause()

    def _scheduler_announce(self, prayer: str, now: datetime) -> None:
        if not self._saved().get("announce", True):
            return
        day = now.strftime("%Y-%m-%d")
        if day != self._announced_date:
            self._announced_date = day
            self._announced.clear()
        marker = "{0}-{1}".format(day, prayer)
        if marker in self._announced:
            return
        self._announced.add(marker)

        def worker():
            try:
                _MAIN.speak(prayer)
            except Exception as error:
                print("[backend_api] scheduler announcement failed: {0}".format(error))

        threading.Thread(target=worker, name="pmg-announce", daemon=True).start()

    def _process_rows(self) -> list:
        if _MAIN is None:
            return []
        now = time.monotonic()
        if now - _ROWS_CACHE["at"] > 15.0:
            try:
                _ROWS_CACHE["rows"] = _MAIN.process_rows()
            except Exception:
                _ROWS_CACHE["rows"] = []
            _ROWS_CACHE["at"] = now
        return _ROWS_CACHE["rows"]

    def _prayer_minutes(self, times: dict) -> dict:
        minutes = {}
        for prayer in _MAIN.PRAYERS:
            raw = times.get(prayer)
            if not raw:
                continue
            try:
                hour, minute = map(int, str(raw).split(":"))
            except ValueError:
                continue
            minutes[prayer] = hour * 60 + minute
        return minutes

    def _next_prayer(self, times: dict):
        now = datetime.now()
        current = now.hour * 60 + now.minute
        minutes = self._prayer_minutes(times)
        if not minutes:
            return None
        upcoming = sorted((value, prayer) for prayer, value in minutes.items() if value > current)
        if upcoming:
            value, prayer = upcoming[0]
            target = now.replace(hour=value // 60, minute=value % 60, second=0, microsecond=0)
            return prayer, times[prayer], target, False
        value, prayer = min((value, prayer) for prayer, value in minutes.items())
        target = (now + timedelta(days=1)).replace(hour=value // 60, minute=value % 60, second=0, microsecond=0)
        return prayer, times[prayer], target, True

    def _current_prayer(self, times: dict):
        now = datetime.now()
        current = now.hour * 60 + now.minute
        latest, latest_value = None, -1
        for prayer, value in self._prayer_minutes(times).items():
            if value <= current and value > latest_value:
                latest_value, latest = value, prayer
        return latest

    def _display(self, raw: str) -> str:
        if not raw:
            return "--:--"
        try:
            return _MAIN.format_time_12(raw)
        except Exception:
            return "--:--"

    def _location_label(self, saved: dict) -> str:
        city = str(saved.get("manual_city") or "").strip()
        country = str(saved.get("manual_country") or "").strip()
        if city and country:
            return "{0}، {1}".format(city, country)
        return ""

    def get_state(self) -> dict:
        if _MAIN is None:
            return {"ok": False, "error": _LOAD_ERROR or "backend unavailable"}
        saved = self._saved()
        times = dict(saved.get("times") or {})
        next_info = self._next_prayer(times)
        current = self._current_prayer(times)
        next_prayer = next_info[0] if next_info else None
        prayers = []
        for prayer in _MAIN.PRAYERS:
            raw = times.get(prayer, "")
            prayers.append({
                "key": prayer,
                "name": _MAIN.AR.get(prayer, prayer),
                "time": raw,
                "display": self._display(raw),
                "is_next": prayer == next_prayer,
                "is_current": prayer == current,
            })
        next_payload = None
        if next_info:
            prayer, raw, target, tomorrow = next_info
            remaining = int((target - datetime.now()).total_seconds())
            next_payload = {
                "key": prayer,
                "name": _MAIN.AR.get(prayer, prayer),
                "time": raw,
                "display": self._display(raw),
                "remaining_seconds": max(0, remaining),
                "tomorrow": bool(tomorrow),
            }
        music = str(saved.get("music") or "")
        running = None
        if music:
            try:
                running = bool(_MAIN.running_pids_for(music, self._process_rows()))
            except Exception:
                running = None
        snap = self._pause_snapshot()
        state = {
            "ok": True,
            "version": getattr(_MAIN, "APP_VERSION", ""),
            "prayers": prayers,
            "next": next_payload,
            "enabled": bool(saved.get("enabled", False)),
            "announce": bool(saved.get("announce", True)),
            "autostart": bool(saved.get("autostart", False)),
            "music": music,
            "adhan": str(saved.get("adhan") or ""),
            "minutes": int(saved.get("minutes", 15) or 15),
            "method": str(saved.get("method") or "suspend"),
            "theme": str(saved.get("theme") or ""),
            "location": self._location_label(saved),
            "location_mode": str(saved.get("location_mode") or "auto"),
            "manual_city": str(saved.get("manual_city") or ""),
            "manual_country": str(saved.get("manual_country") or ""),
            "manual_latitude": str(saved.get("manual_latitude") or ""),
            "manual_longitude": str(saved.get("manual_longitude") or ""),
            "manual_timezone": str(saved.get("manual_timezone") or ""),
            "paused": self._paused_from(snap),
            "player_running": running,
            "scheduler_running": self.scheduler_running(),
            "scheduler_active": self._paused_from(snap),
        }
        state.update(self._pause_fields(snap))
        return state

    def save_settings(self, payload) -> dict:
        if _MAIN is None:
            return {"ok": False, "error": _LOAD_ERROR or "backend unavailable"}
        if not isinstance(payload, dict):
            return {"ok": False, "error": "invalid payload"}
        saved = self._saved()
        merged = dict(saved)
        if "music" in payload:
            merged["music"] = str(payload["music"] or "").strip()
        if "adhan" in payload:
            merged["adhan"] = str(payload["adhan"] or "").strip()
        if "minutes" in payload:
            try:
                minutes = int(payload["minutes"])
            except (TypeError, ValueError):
                return {"ok": False, "error": "المدة يجب أن تكون رقمًا."}
            if not 1 <= minutes <= 180:
                return {"ok": False, "error": "المدة من 1 إلى 180 دقيقة."}
            merged["minutes"] = minutes
        if "method" in payload:
            if payload["method"] not in ("suspend", "media"):
                return {"ok": False, "error": "طريقة إيقاف غير صالحة."}
            merged["method"] = payload["method"]
        for flag in ("enabled", "announce", "autostart"):
            if flag in payload:
                if not isinstance(payload[flag], bool):
                    return {"ok": False, "error": "{0} يجب أن يكون صحيحًا/خطأ.".format(flag)}
                merged[flag] = payload[flag]
        if "theme" in payload:
            if payload["theme"] not in ("dark", "light", ""):
                return {"ok": False, "error": "وضع مظهر غير صالح."}
            merged["theme"] = payload["theme"]
        if "location_mode" in payload:
            if payload["location_mode"] not in ("auto", "manual"):
                return {"ok": False, "error": "وضع الموقع غير صالح."}
            # Phase 20.28: allow switching freely between manual and auto.
            merged["location_mode"] = payload["location_mode"]
        for field in ("manual_city", "manual_country", "manual_latitude", "manual_longitude", "manual_timezone"):
            if field in payload:
                merged[field] = str(payload[field] or "").strip()
        # Validate coordinates if provided
        if "manual_latitude" in payload or "manual_longitude" in payload:
            lat_str = merged.get("manual_latitude", "").strip()
            lon_str = merged.get("manual_longitude", "").strip()
            if lat_str:
                try:
                    lat_val = float(lat_str)
                    if not -90.0 <= lat_val <= 90.0:
                        return {"ok": False, "error": "خط العرض يجب أن يكون بين -90 و +90."}
                except ValueError:
                    return {"ok": False, "error": "خط العرض غير صالح."}
            if lon_str:
                try:
                    lon_val = float(lon_str)
                    if not -180.0 <= lon_val <= 180.0:
                        return {"ok": False, "error": "خط الطول يجب أن يكون بين -180 و +180."}
                except ValueError:
                    return {"ok": False, "error": "خط الطول غير صالح."}
        if "times" in payload:
            if not isinstance(payload["times"], dict):
                return {"ok": False, "error": "المواقيت يجب أن تكون كائنًا."}
            clean = {}
            for prayer, value in payload["times"].items():
                if prayer not in _MAIN.PRAYERS:
                    continue
                text = str(value or "").strip()
                if not text:
                    continue
                try:
                    clean[prayer] = _MAIN.valid_time(text)
                except ValueError:
                    return {"ok": False, "error": "وقت غير صالح لـ {0}: {1}".format(prayer, text)}
            merged["times"] = clean
        if merged.get("autostart") != saved.get("autostart"):
            try:
                _MAIN.set_autostart(bool(merged.get("autostart")))
            except Exception as error:
                return {"ok": False, "error": "تعذر ضبط التشغيل التلقائي: {0}".format(error)}
        _MAIN.save_settings(merged)
        return {"ok": True, "state": self.get_state()}

    def set_theme(self, theme) -> dict:
        if _MAIN is None:
            return {"ok": False, "error": _LOAD_ERROR or "backend unavailable"}
        if theme not in ("dark", "light"):
            return {"ok": False, "error": "وضع مظهر غير صالح."}
        saved = self._saved()
        saved["theme"] = theme
        _MAIN.save_settings(saved)
        return {"ok": True, "theme": theme}

    def set_autostart(self, enabled) -> dict:
        if _MAIN is None:
            return {"ok": False, "error": _LOAD_ERROR or "backend unavailable"}
        enabled = bool(enabled)
        try:
            _MAIN.set_autostart(enabled)
        except Exception as error:
            return {"ok": False, "error": str(error)}
        saved = self._saved()
        saved["autostart"] = enabled
        _MAIN.save_settings(saved)
        return {"ok": True, "autostart": enabled}

    def browse_player(self) -> dict:
        """Open the native Windows file picker and return the selected player exe.

        Reuses the existing v1.2.6 file dialog (main.filedialog.askopenfilename)
        without re-implementing a picker. Runs on the pywebview bridge worker
        thread; tkinter.filedialog is safe to open from a non-main thread on
        Windows. Cancel returns cancelled=True so the frontend shows a clear
        (non-error) message. Never silently fails.
        """
        if _MAIN is None:
            return {"ok": False, "error": _LOAD_ERROR or "backend unavailable"}
        try:
            import tkinter as tk
            root = tk._default_root
            created_root = False
            if root is None:
                root = tk.Tk()
                root.withdraw()
                created_root = True
            try:
                chosen = _MAIN.filedialog.askopenfilename(
                    parent=root,
                    title="اختر ملف برنامج المشغّل",
                    filetypes=[("برامج Windows", "*.exe"), ("كل الملفات", "*.*")],
                )
            finally:
                if created_root:
                    try:
                        root.destroy()
                    except Exception:
                        pass
        except Exception as error:
            return {"ok": False, "error": "تعذر فتح محدد الملفات: {0}".format(error)}
        if not chosen:
            return {"ok": False, "cancelled": True, "error": "أُلغي اختيار المشغّل."}
        return {"ok": True, "path": chosen}

    def browse_adhan(self) -> dict:
        """Open file picker for excluded/muezzin program."""
        if _MAIN is None:
            return {"ok": False, "error": _LOAD_ERROR or "backend unavailable"}
        try:
            import tkinter as tk
            root = tk._default_root
            created_root = False
            if root is None:
                root = tk.Tk()
                root.withdraw()
                created_root = True
            try:
                chosen = _MAIN.filedialog.askopenfilename(
                    parent=root,
                    title="اختر ملف برنامج المؤذن المستثنى",
                    filetypes=[("برامج Windows", "*.exe"), ("كل الملفات", "*.*")],
                )
            finally:
                if created_root:
                    try:
                        root.destroy()
                    except Exception:
                        pass
        except Exception as error:
            return {"ok": False, "error": "تعذر فتح محدد الملفات: {0}".format(error)}
        if not chosen:
            return {"ok": False, "cancelled": True, "error": "أُلغي اختيار البرنامج."}
        return {"ok": True, "path": chosen}

    def list_running_apps(self) -> dict:
        """Return list of currently running user applications with executable paths."""
        seen_paths = set()
        apps = []
        method_used = "none"
        try:
            # Helper to add app
            def add_app(name, path):
                nonlocal apps, seen_paths
                if not name:
                    return
                name = name.strip()
                path = (path or "").strip()
                if path and not path.lower().endswith(".exe"):
                    return
                if path and "prayermusicguard" in path.lower():
                    return
                key = path.lower() if path else name.lower()
                if key in seen_paths:
                    return
                seen_paths.add(key)
                display = os.path.basename(path) if path else name
                apps.append({"name": name or display, "path": path})

            # Method 1: CIM via PowerShell Get-CimInstance
            try:
                ps_cmd = (
                    "$p = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue; "
                    "$out = @(); "
                    "foreach ($proc in $p) { "
                    "  $name = $proc.Name; "
                    "  $path = $proc.ExecutablePath; "
                    "  if ($name) { $out += \"$name|$path\" } "
                    "}; "
                    "$out | Sort-Object -Unique"
                )
                raw = subprocess.check_output(
                    ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    stderr=subprocess.DEVNULL,
                    creationflags=0x08000000
                )
                for line in raw.splitlines():
                    if not line.strip():
                        continue
                    if "|" not in line:
                        continue
                    name, path = line.rsplit("|", 1)
                    # Only keep entries with a valid exe path
                    if path and path.lower().endswith(".exe"):
                        add_app(name, path)
                if apps:
                    method_used = "cim"
                    _log(f"list_running_apps method={method_used} found={len(apps)}")
                    return {"ok": True, "apps": apps[:200]}
                _log("list_running_apps cim returned no usable apps, falling back")
            except Exception as e:
                _log(f"list_running_apps cim error: {e}")

            # Method 2: WMI via PowerShell Get-WmiObject for older Windows
            try:
                ps_cmd_wmi = (
                    "$p = Get-WmiObject Win32_Process -ErrorAction SilentlyContinue; "
                    "$out = @(); "
                    "foreach ($proc in $p) { "
                    "  $name = $proc.Name; "
                    "  $path = $proc.ExecutablePath; "
                    "  if ($name) { $out += \"$name|$path\" } "
                    "}; "
                    "$out | Sort-Object -Unique"
                )
                raw = subprocess.check_output(
                    ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd_wmi],
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    stderr=subprocess.DEVNULL,
                    creationflags=0x08000000
                )
                for line in raw.splitlines():
                    if not line.strip() or "|" not in line:
                        continue
                    name, path = line.rsplit("|", 1)
                    if path and path.lower().endswith(".exe"):
                        add_app(name, path)
                if apps:
                    method_used = "wmi"
                    _log(f"list_running_apps method={method_used} found={len(apps)}")
                    return {"ok": True, "apps": apps[:200]}
                _log("list_running_apps wmi returned no usable apps, falling back")
            except Exception as e:
                _log(f"list_running_apps wmi error: {e}")

            # Method 3: tasklist fallback – process names only
            try:
                raw = subprocess.check_output(
                    ["tasklist", "/FO", "CSV", "/NH"],
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    stderr=subprocess.DEVNULL,
                    creationflags=0x08000000
                )
                for line in raw.splitlines():
                    if not line.strip():
                        continue
                    # CSV: "Image Name","PID",...
                    # Simple parse first quoted field
                    parts = line.split('","')
                    if not parts:
                        continue
                    name_field = parts[0].strip('"')
                    if not name_field or name_field.lower().endswith(".exe"):
                        name_field = name_field[:-4] if name_field.lower().endswith(".exe") else name_field
                    # Avoid adding duplicates and PrayerMusicGuard
                    if "prayermusicguard" in name_field.lower():
                        continue
                    add_app(name_field, "")
                if apps:
                    method_used = "tasklist"
                    _log(f"list_running_apps method={method_used} found={len(apps)}")
                    return {"ok": True, "apps": apps[:200]}
                _log("list_running_apps tasklist returned no apps")
            except Exception as e:
                _log(f"list_running_apps tasklist error: {e}")

            # Final fallback: empty but successful
            _log(f"list_running_apps method={method_used} found={len(apps)} fallback empty")
            return {"ok": True, "apps": apps[:200]}
        except Exception as error:
            _log(f"list_running_apps error: {error}")
            return {"ok": False, "error": str(error), "apps": []}

    def get_cities(self, country_code: str = "") -> dict:
        """Return cities for a given ISO country code from assets/data/cities.json.

        If country_code is empty, returns the entire dataset keyed by code.
        """
        try:
            if getattr(sys, "frozen", False):
                base = getattr(sys, "_MEIPASS", PROJECT_ROOT)
                cities_path = os.path.join(base, "assets", "data", "cities.json")
            else:
                cities_path = os.path.join(PROJECT_ROOT, "assets", "data", "cities.json")
            if not os.path.isfile(cities_path):
                return {"ok": False, "error": "cities.json not found"}
            with open(cities_path, "r", encoding="utf-8") as f:
                all_cities = json.load(f)
            if country_code:
                code = country_code.strip().upper()
                cities = all_cities.get(code, [])
                return {"ok": True, "code": code, "cities": cities}
            return {"ok": True, "data": all_cities}
        except Exception as error:
            return {"ok": False, "error": str(error)}

    def diag_report(self, payload) -> dict:
        """Diagnostic hook: frontend reports bridge/runtime state to a log file.

        Does not affect normal operation. The frontend calls this on
        pywebviewready and whenever a bridge call fails, so we can distinguish
        "bridge not injected", "injected late", "wrong frontend", "API method
        missing", and "API method raised" without guessing.
        """
        try:
            import json as _json
            log_dir = os.environ.get("APPDATA", os.path.expanduser("~"))
            log_dir = os.path.join(log_dir, "PrayerMusicGuard")
            os.makedirs(log_dir, exist_ok=True)
            path = os.path.join(log_dir, "bridge_diag.log")
            line = _json.dumps({"t": datetime.now().isoformat(), "payload": payload}, ensure_ascii=False)
            with open(path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass
        return {"ok": True, "diag": True}

    # ------------------------------------------------------------------
    # Phase 20.58: Auto Update UI bridge.
    #
    # The frontend NEVER talks to GitHub directly. These three methods are a
    # thin facade over update_flow.UpdateFlow, which in turn is the only
    # driver of webview_app/updater.py (the single source of update truth).
    #
    #   check_for_updates()  -> starts a manual check on a worker thread
    #   get_update_status()  -> lock-protected snapshot (the frontend polls
    #                           this for state/progress; it never blocks)
    #   start_update()       -> USER ACTION: download+verify+launch, refused
    #                           until the user has confirmed an available update
    #
    # All network work happens off the UI thread. Nothing is downloaded before
    # confirmation, no background scheduling exists here, and no method ever
    # raises to the JS side.
    # ------------------------------------------------------------------
    def _update_flow(self):
        """Lazily build the per-instance update flow, reusing updater.py only."""
        flow = getattr(self, "_update_flow_instance", None)
        if flow is not None:
            return flow
        try:
            import update_flow
            current = ""
            if _MAIN is not None:
                current = str(getattr(_MAIN, "APP_VERSION", "") or "").strip()
            flow = update_flow.UpdateFlow(
                current_version=current,
                on_exit=self._update_quit,
            )
        except Exception as error:
            _log("update_flow unavailable: {0}".format(error))
            flow = None
        self._update_flow_instance = flow
        return flow

    def _update_quit(self):
        """Close the WebView2 window after the installer has spawned.

        Reuses the existing shutdown path: window.destroy() ends
        webview.start(), which returns normally and lets webview_main.run()
        exit the process. Only ever called after launch_installer() succeeded.

        Phase 20.65: window.destroy() now trips the close-to-tray handler,
        which would hide the window instead of closing it. Setting
        _allow_close first signals that this close comes from the auto-update
        flow and must be honored, so the update exit behavior is unchanged.
        """
        window = getattr(self, "_webview_window", None)
        if window is None:
            _log("update quit requested but no window is attached")
            return
        self._allow_close = True
        try:
            window.destroy()
        except Exception as error:
            _log("update quit failed: {0}".format(error))

    def attach_webview_window(self, window) -> None:
        """webview_main attaches the window so the update flow can close it."""
        self._webview_window = window

    def check_for_updates(self) -> dict:
        """Start a manual update check on a worker thread. Never blocks.

        Returns {"ok": True, ...} immediately with the current status; the
        frontend then polls get_update_status() for the result.
        """
        flow = self._update_flow()
        if flow is None:
            return {"ok": False, "error": "التحديث غير متاح في هذا النظام."}
        return flow.check_async()

    def get_update_status(self) -> dict:
        """Lock-protected snapshot of the current update state/progress.

        Cheap and non-blocking — safe for the frontend to poll. Returns a
        plain {"ok": True, "state": ..., "progress": ..., ...} even when no
        flow exists, so the UI degrades gracefully.
        """
        flow = self._update_flow()
        if flow is None:
            return {"ok": False, "error": "التحديث غير متاح في هذا النظام."}
        return flow.status()

    def start_update(self) -> dict:
        """USER-ACTION: download, verify and launch the confirmed update.

        Refused unless the flow previously reported an available update, so
        nothing downloads without explicit confirmation. Returns
        {"ok": True} when the download started.
        """
        flow = self._update_flow()
        if flow is None:
            return {"ok": False, "error": "التحديث غير متاح في هذا النظام."}
        return flow.start_update()

    def dismiss_update(self) -> dict:
        """Return the flow to idle (the user chose 'Later' / closed the panel).

        Refused while an operation is in flight.
        """
        flow = self._update_flow()
        if flow is None:
            return {"ok": False, "error": "التحديث غير متاح في هذا النظام."}
        return flow.reset()

    def pause_now(self) -> dict:
        if _MAIN is None:
            return {"ok": False, "error": _LOAD_ERROR or "backend unavailable"}
        saved = self._saved()
        music = str(saved.get("music") or "").strip()
        if not music:
            return {"ok": False, "error": "لم يتم اختيار مشغّل موسيقى."}
        if str(saved.get("method") or "suspend") == "media":
            try:
                _MAIN.media_toggle()
            except Exception as error:
                return {"ok": False, "error": str(error)}
            self._mark_paused(music, None, True)
            return {"ok": True, "method": "media"}
        try:
            if hasattr(_MAIN, 'needs_media_key_fallback') and _MAIN.needs_media_key_fallback(music):
                _log(f"Player {music!r} requires media-key fallback (no WM_APPCOMMAND support)")
                _MAIN.media_toggle()
                self._mark_paused(music, None, True)
                return {"ok": True, "method": "media-key"}
            if _MAIN.win7_browser_fallback(music):
                _MAIN.media_toggle()
                self._mark_paused(music, None, True)
                return {"ok": True, "method": "media-key"}
        except Exception:
            pass
        try:
            windows = _MAIN.player_hwnds(music)
        except Exception as error:
            return {"ok": False, "error": str(error)}
        if not windows:
            return {"ok": False, "error": "لم يتم العثور على نافذة المشغّل."}
        delivered = 0
        for hwnd in windows:
            try:
                if _MAIN.send_appcommand(hwnd, _MAIN.APPCOMMAND_MEDIA_PAUSE):
                    delivered += 1
            except Exception:
                continue
        if not delivered:
            return {"ok": False, "error": "لم يقبل المشغّل أمر الإيقاف."}
        try:
            paused_pid = _MAIN.hwnd_pid(windows[0])
        except Exception:
            paused_pid = None
        self._mark_paused(music, paused_pid, False)
        return {"ok": True, "method": "appcommand", "windows": delivered}

    def resume_now(self) -> dict:
        if _MAIN is None:
            return {"ok": False, "error": _LOAD_ERROR or "backend unavailable"}
        saved = self._saved()
        music = str(saved.get("music") or "").strip()
        if not music:
            return {"ok": False, "error": "لم يتم اختيار مشغّل موسيقى."}
        snap = self._pause_snapshot()
        if snap.get("source") == "main_app":
            app = self._live_app()
            if app is not None:
                try:
                    app.resume_now()
                except Exception as error:
                    return {"ok": False, "error": str(error)}
                return {"ok": True, "method": "main_app"}
        if snap.get("paused_via_media_key"):
            try:
                _MAIN.media_toggle()
            except Exception as error:
                return {"ok": False, "error": str(error)}
            self._clear_pause()
            return {"ok": True, "method": "media-key"}
        if str(saved.get("method") or "suspend") == "media":
            try:
                _MAIN.media_toggle()
            except Exception as error:
                return {"ok": False, "error": str(error)}
            self._clear_pause()
            return {"ok": True, "method": "media"}
        try:
            if hasattr(_MAIN, 'needs_media_key_fallback') and _MAIN.needs_media_key_fallback(music):
                _log(f"Player {music!r} resume via media-key fallback (no WM_APPCOMMAND support)")
                _MAIN.media_toggle()
                self._clear_pause()
                return {"ok": True, "method": "media-key"}
            if _MAIN.win7_browser_fallback(music):
                _MAIN.media_toggle()
                self._clear_pause()
                return {"ok": True, "method": "media-key"}
        except Exception:
            pass
        try:
            windows = _MAIN.player_hwnds(music)
        except Exception as error:
            return {"ok": False, "error": str(error)}
        if not windows:
            return {"ok": False, "error": "لم يتم العثور على نافذة المشغّل."}
        delivered = 0
        for hwnd in windows:
            try:
                if _MAIN.send_appcommand(hwnd, _MAIN.APPCOMMAND_MEDIA_PLAY):
                    delivered += 1
            except Exception:
                continue
        if not delivered:
            return {"ok": False, "error": "لم يقبل المشغّل أمر الاستئناف."}
        self._clear_pause()
        return {"ok": True, "method": "appcommand", "windows": delivered}

    def toggle_pause(self) -> dict:
        snap = self._pause_snapshot()
        if self._paused_from(snap):
            return self.resume_now()
        return self.pause_now()

    def fetch_times(self, location_data=None) -> dict:
        if _MAIN is None:
            return {"ok": False, "error": _LOAD_ERROR or "backend unavailable"}
        saved = self._saved()
        today = datetime.now().strftime("%d-%m-%Y")
        params = {"method": 5}
        label = ""
        info = None
        # Determine effective location mode and values
        loc_mode = (location_data or {}).get("location_mode") or saved.get("location_mode", "auto")
        manual_city = (location_data or {}).get("manual_city") if (location_data or {}).get("manual_city") is not None else saved.get("manual_city", "")
        manual_country = (location_data or {}).get("manual_country") if (location_data or {}).get("manual_country") is not None else saved.get("manual_country", "")
        manual_latitude = (location_data or {}).get("manual_latitude") if (location_data or {}).get("manual_latitude") is not None else None
        manual_longitude = (location_data or {}).get("manual_longitude") if (location_data or {}).get("manual_longitude") is not None else None
        try:
            info = _MAIN.resolve_auto_location()
        except Exception:
            info = None
        # Only use coords if explicitly provided in location_data
        use_coords = False
        lat_val = 0.0
        lon_val = 0.0
        if manual_latitude is not None and manual_longitude is not None:
            try:
                lat_val = float(str(manual_latitude).strip())
                lon_val = float(str(manual_longitude).strip())
                if -90.0 <= lat_val <= 90.0 and -180.0 <= lon_val <= 180.0:
                    use_coords = True
            except Exception:
                use_coords = False
        if loc_mode == "manual":
            if use_coords:
                params["latitude"] = f"{lat_val}"
                params["longitude"] = f"{lon_val}"
                city = str(manual_city or "").strip()
                country = str(manual_country or "").strip()
                label = f"{city}، {country}" if city and country else f"{lat_val},{lon_val}"
                base = "https://api.aladhan.com/v1/timings/{0}".format(today)
            elif manual_city and manual_country:
                params["city"] = manual_city
                params["country"] = manual_country
                label = f"{manual_city}، {manual_country}"
                base = "https://api.aladhan.com/v1/timingsByCity/{0}".format(today)
            else:
                return {"ok": False, "error": "يرجى اختيار الدولة والمدينة يدويًا."}
        elif info and info.get("city") and info.get("country"):
            params["city"] = info["city"]
            params["country"] = info["country"]
            if info.get("timezone"):
                params["timezonestring"] = info["timezone"]
            label = "{0}، {1}".format(info["city"], info["country"])
            base = "https://api.aladhan.com/v1/timingsByCity/{0}".format(today)
        else:
            return {"ok": False, "error": "لا يوجد موقع متاح لجلب المواقيت."}
        query = urllib.parse.urlencode(params)
        request = urllib.request.Request("{0}?{1}".format(base, query), headers={"User-Agent": "PrayerMusicGuard/1.2"})
        try:
            with urllib.request.urlopen(request, timeout=12) as response:
                payload = json.load(response)
            timings = payload["data"]["timings"]
            values = {p: _MAIN.valid_time(str(timings[p])[:5]) for p in _MAIN.PRAYERS}
        except Exception as error:
            return {"ok": False, "error": "تعذر جلب المواقيت: {0}".format(error)}
        saved["times"] = values
        # Phase 20.28: persist the location actually used, otherwise get_state()
        # keeps reporting a stale saved location (e.g. a previously stored
        # Jeddah/Saudi Arabia) and the UI reverts to it after every fetch.
        if loc_mode == "manual":
            saved["location_mode"] = "manual"
            saved["manual_city"] = str(manual_city or "").strip()
            saved["manual_country"] = str(manual_country or "").strip()
            # Coordinates are no longer entered in the UI; clear any stale
            # values so they can never shadow the city/country on a later fetch.
            saved["manual_latitude"] = ""
            saved["manual_longitude"] = ""
            saved["manual_timezone"] = ""
        else:
            saved["location_mode"] = "auto"
            saved["manual_city"] = str((info or {}).get("city") or "").strip()
            saved["manual_country"] = str((info or {}).get("country") or "").strip()
            saved["manual_latitude"] = ""
            saved["manual_longitude"] = ""
            saved["manual_timezone"] = str((info or {}).get("timezone") or "").strip()
        _MAIN.save_settings(saved)
        state = self.get_state()
        state["location"] = label
        return {"ok": True, "location": label, "state": state}