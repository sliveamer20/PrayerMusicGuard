"""Phase 2/3/4: HTML frontend host for Windows 10/11 (WebView2 backend).

Serves webview_app/frontend/index.html in a native pywebview window.
This module is only imported when platform_check.can_use_html_frontend()
is True; it is never loaded on Windows 7 or when WebView2 is missing.

Phase 3 additions (additive, reversible):
  * ``--probe`` mode: opens a small visible window and reports success ONLY when
    the page actually loads. Used by the bounded WebView2 health probe.
  * ``--ready-file PATH``: writes PATH once the page has loaded, so the
    launcher can detect a stuck/broken WebView2 startup and fall back.

Phase 4 addition (additive, reversible):
  * ``js_api`` bridge: webview_app/backend_api.py is attached to the window
    so the frontend can read the real backend state and save settings.
    main.py is imported as a library only; it is never modified or run.
"""
from __future__ import annotations

import os
import sys
import threading
import traceback
import tempfile
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))

LOG_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "PrayerMusicGuard")
try:
    os.makedirs(LOG_DIR, exist_ok=True)
except Exception:
    pass
WEBVIEW_LOG = os.path.join(LOG_DIR, "webview.log")

def _log(msg: str) -> None:
    try:
        with open(WEBVIEW_LOG, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat()}] {msg}\n")
    except Exception:
        pass


def _frontend_dir() -> str:
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", os.path.dirname(HERE))
        candidate = os.path.join(base, "webview_app", "frontend")
        if os.path.isdir(candidate):
            return candidate
    return os.path.join(HERE, "frontend")


FRONTEND_DIR = _frontend_dir()
INDEX = os.path.join(FRONTEND_DIR, "index.html")

PROBE_HARD_LIMIT_SECONDS = 20.0

PROBE_EXIT_OK = 0
PROBE_EXIT_PYWEBVIEW_MISSING = 3
PROBE_EXIT_FRONTEND_MISSING = 4
PROBE_EXIT_RUNTIME_MISSING = 5
PROBE_EXIT_INIT_FAILED = 6
PROBE_EXIT_LOAD_TIMEOUT = 7


def _gui_name() -> str:
    return os.environ.get("PMG_WEBVIEW_GUI", "edgechromium").strip() or "edgechromium"


def _configure_webview():
    """Configure WebView2 runtime and storage path BEFORE any window creation.

    Returns (storage_path, runtime_path) tuple.
    Both must be set before webview.create_window() or webview.start().
    """
    storage_path = None
    runtime_path = None
    try:
        _log("Configuring WebView2")
        import webview
        appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
        storage = os.path.join(appdata, "PrayerMusicGuard", "webview2_data")
        os.makedirs(storage, exist_ok=True)
        storage_path = storage
        _log(f"Storage path set to: {storage_path}")

        # Set WebView2 runtime path in pywebview settings so the edgechromium
        # backend uses our specific runtime instead of searching.
        # The runtime folder contains msedgewebview2.exe.
        runtime = r"C:\Program Files (x86)\Microsoft\EdgeWebView\Application\153.0.4234.32"
        if os.path.isdir(runtime):
            runtime_path = runtime
            webview.settings["WEBVIEW2_RUNTIME_PATH"] = runtime_path
            _log(f"WebView2 runtime path set to: {runtime_path}")
        else:
            _log("Default WebView2 runtime path not found, trying registry")
            # Fallback: try to detect from registry
            try:
                import winreg
                for path in (
                    r"SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}",
                    r"SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}",
                ):
                    try:
                        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
                            pv, _ = winreg.QueryValueEx(key, "pv")
                            if pv:
                                candidate = os.path.join(
                                    r"C:\Program Files (x86)\Microsoft\EdgeWebView\Application", pv
                                )
                                if os.path.isdir(candidate):
                                    runtime_path = candidate
                                    webview.settings["WEBVIEW2_RUNTIME_PATH"] = runtime_path
                                    _log(f"WebView2 runtime path set from registry to: {runtime_path}")
                                    break
                    except OSError:
                        continue
            except Exception as e:
                _log(f"Registry detection failed: {e}")
                pass

    except Exception as e:
        _log(f"WebView2 configuration failed: {e}")
        traceback.print_exc()

    _log(f"WebView2 configuration complete: storage_path={storage_path}, runtime_path={runtime_path}")
    return storage_path, runtime_path


def _start(webview, storage_path: str | None = None) -> None:
    gui = _gui_name()
    start_kwargs = {"gui": gui}
    if storage_path:
        start_kwargs["storage_path"] = storage_path
    _log(f"Starting webview gui={gui}, storage_path={storage_path}")
    try:
        webview.start(**start_kwargs)
        _log("webview.start() returned normally")
    except TypeError:
        _log("storage_path not supported by this pywebview version; retrying without it")
        # Older pywebview version - storage_path not supported
        webview.start(gui=gui)
        _log("webview.start() without storage_path returned normally")
    except Exception as e:
        _log(f"webview.start() failed: {e}")
        traceback.print_exc()
        raise


def _build_api():
    _log("Building backend API bridge")
    try:
        from backend_api import BackendAPI
        api = BackendAPI()
        _log("BackendAPI instance created")
        return api
    except Exception as error:
        msg = "[webview_main] backend bridge unavailable: {0}".format(error)
        _log(msg)
        traceback.print_exc()
        return None


def _acquire_single_instance() -> bool:
    """Acquire the single-instance mutex via the already-loaded main module.

    This is the authoritative single-instance gate for the WebView2 path.
    main.py defines acquire_single_instance() but it is only invoked inside its
    ``__main__`` block; here the WebView2 child imports main.py as a library
    (through backend_api), so the mutex was never taken. This call reuses the
    existing function (no rewritten mutex logic).

    Returns True when this process may continue (first instance, or the guard
    is unavailable), False when another PrayerMusicGuard instance already holds
    the mutex (caller must exit without opening the UI).
    """
    try:
        from backend_api import _MAIN
        if _MAIN is None:
            _log("Single-instance guard: backend main module not loaded; skipping guard")
            return True
        ok = bool(_MAIN.acquire_single_instance())
        _log("Single-instance guard: {0}".format(
            "acquired (first instance)" if ok else "ALREADY RUNNING (second instance)"))
        return ok
    except Exception as error:
        # Mirror main.py's own behavior: a broken guard never blocks a launch.
        _log("Single-instance guard unavailable ({0}); continuing".format(error))
        return True


def run(ready_file: str | None = None) -> int:
    try:
        import webview
    except ImportError:
        _log("pywebview is not installed; cannot start the HTML frontend.")
        return 1

    if not os.path.isfile(INDEX):
        _log(f"Frontend entry not found: {INDEX}")
        return 1

    # Change cwd to bundle dir so relative URLs are resolved by pywebview's HTTP server
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", os.path.dirname(HERE))
        try:
            os.chdir(base)
            _log(f"Changed cwd to {base}")
        except Exception as e:
            _log(f"Failed to chdir to {base}: {e}")

    _log("Starting HTML frontend initialization")
    storage_path, runtime_path = _configure_webview()

    kwargs = {}
    api = _build_api()
    if api is not None:
        kwargs["js_api"] = api
        _log(f"js_api attached to window: {api}")
    else:
        _log("WARNING: js_api is None - frontend bridge will be unavailable")

    # Phase 1: single-instance protection. The WebView2 child is the real app
    # process; it must own the mutex. If another instance already runs, exit
    # gracefully here without creating the window.
    if not _acquire_single_instance():
        _log("Another PrayerMusicGuard instance is already running; this launch will exit without opening the UI.")
        return 0

    if not os.path.isfile(INDEX):
        _log("Frontend index missing despite earlier check: {0}".format(INDEX))
        return 1
    rel_url = os.path.relpath(INDEX, os.getcwd()).replace(os.sep, "/")
    _log("Using relative frontend URL: {0} (resolved from {1})".format(rel_url, INDEX))
    url = rel_url

    window = webview.create_window(
        "\u0635\u0644\u0627\u0629 \u0648\u0633\u0643\u0648\u0646",
        url,
        width=900,
        height=760,
        min_size=(640, 520),
        **kwargs
    )
    _log("Window created successfully")

    if api is not None:
        try:
            api.start_scheduler()
            _log("Scheduler started")
        except Exception as error:
            _log(f"scheduler start failed: {error}")
        try:
            window.events.closed += lambda: api.stop_scheduler()
            _log("Closed event handler attached")
        except Exception as e:
            _log(f"Failed to attach closed event: {e}")

    if ready_file:
        def _mark_ready():
            try:
                with open(ready_file, "w", encoding="utf-8") as fh:
                    fh.write("ready")
                _log("Ready flag written")
            except OSError:
                pass
        try:
            window.events.loaded += _mark_ready
        except Exception:
            pass
        try:
            window.events.shown += _mark_ready
        except Exception:
            pass

    _start(webview, storage_path=storage_path)
    return 0


def probe() -> int:
    _log("probe started, INDEX=" + INDEX)
    _log("frozen=" + str(getattr(sys, "frozen", False)) + " _MEIPASS=" + str(getattr(sys, "_MEIPASS", "none")))

    try:
        import webview
    except ImportError as e:
        _log("pywebview import failed: " + str(e))
        return PROBE_EXIT_PYWEBVIEW_MISSING

    if not os.path.isfile(INDEX):
        _log("INDEX not found: " + INDEX)
        return PROBE_EXIT_FRONTEND_MISSING
    _log("INDEX exists")

    try:
        import platform_check
        if not platform_check.webview2_runtime_installed():
            _log("runtime missing")
            return PROBE_EXIT_RUNTIME_MISSING
    except Exception as e:
        _log(f"platform_check failed: {e}")

    storage_path, runtime_path = _configure_webview()

    state = {"loaded": False}
    try:
        window = webview.create_window(
            "PMG Probe",
            INDEX,
            width=200,
            height=200,
            x=-3000,
            y=-3000,
        )
        _log("window created (visible, off-screen)")
        _log("storage_path=" + str(storage_path) + " runtime_path=" + str(runtime_path))
    except Exception as e:
        _log("create_window failed: " + str(e))
        return PROBE_EXIT_INIT_FAILED

    def _on_loaded():
        _log("loaded event fired")
        state["loaded"] = True
        try:
            window.destroy()
        except Exception:
            pass

    def _on_shown():
        _log("shown event fired")
        state["loaded"] = True
        try:
            window.destroy()
        except Exception:
            pass

    try:
        window.events.loaded += _on_loaded
        _log("loaded handler registered")
    except Exception as e:
        _log("loaded event registration failed: " + str(e))

    try:
        window.events.shown += _on_shown
        _log("shown handler registered")
    except Exception as e:
        _log("shown event registration failed: " + str(e))

    def _hard_stop():
        _log("hard stop reached, loaded=" + str(state["loaded"]))
        try:
            window.destroy()
        except Exception:
            pass

    threading.Timer(PROBE_HARD_LIMIT_SECONDS, _hard_stop).start()

    try:
        _log("starting webview gui")
        _start(webview, storage_path=storage_path)
        _log("webview gui returned, loaded=" + str(state["loaded"]))
    except Exception as e:
        _log("start failed: " + str(e))
        return PROBE_EXIT_INIT_FAILED

    if state["loaded"]:
        _log("probe SUCCESS")
        return PROBE_EXIT_OK
    _log("probe FAILED: load timeout")
    return PROBE_EXIT_LOAD_TIMEOUT


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--probe" in args:
        sys.exit(probe())
    ready = None
    if "--ready-file" in args:
        idx = args.index("--ready-file")
        if idx + 1 < len(args):
            ready = args[idx + 1]
    sys.exit(run(ready))