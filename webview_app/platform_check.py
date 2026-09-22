"""Phase 2: capability detection for the hybrid HTML/Tkinter launcher.

Decides, WITHOUT importing pywebview or Tkinter, whether the modern
HTML/CSS/JS frontend can run on this machine:

  * Windows major version must be >= 10 (Win7/8 have no WebView2 support).
  * The Microsoft Edge WebView2 Runtime must be installed.

Every function is defensive: any failure means "not supported" so the
caller falls back to the existing, reliable Tkinter application.
"""
from __future__ import annotations

import os
import subprocess
import sys

WEBVIEW2_CLIENT_GUID = "{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
WEBVIEW2_REG_PATHS = (
    r"SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\\" + WEBVIEW2_CLIENT_GUID,
    r"SOFTWARE\Microsoft\EdgeUpdate\Clients\\" + WEBVIEW2_CLIENT_GUID,
)
WEBVIEW2_MIN_WINDOWS_MAJOR = 10


def windows_major() -> int:
    try:
        return int(sys.getwindowsversion().major)
    except (AttributeError, ValueError, OSError):
        return 0


def is_modern_windows() -> bool:
    return windows_major() >= WEBVIEW2_MIN_WINDOWS_MAJOR


def webview2_runtime_installed() -> bool:
    try:
        import winreg
    except ImportError:
        return False
    for path in WEBVIEW2_REG_PATHS:
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
                version, _ = winreg.QueryValueEx(key, "pv")
                if version:
                    return True
        except OSError:
            continue
    return False


def pywebview_available() -> bool:
    try:
        import webview  # noqa: F401
        import clr  # noqa: F401
        return True
    except ImportError:
        return False


WEBVIEW2_PROBE_TIMEOUT = float(os.environ.get("PMG_WEBVIEW_PROBE_TIMEOUT", "30"))


def _probe_script_path() -> str:
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        candidate = os.path.join(base, "webview_app", "webview_main.py")
        if os.path.isfile(candidate):
            return candidate
        return os.path.join(base, "webview_main.py")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "webview_main.py")


WEBVIEW2_PROBE_SCRIPT = _probe_script_path()


def _probe_argv() -> list:
    if getattr(sys, "frozen", False):
        return [sys.executable, "--webview-child", "--probe"]
    return [sys.executable, WEBVIEW2_PROBE_SCRIPT, "--probe"]

PROBE_OK = "ok"
PROBE_NOT_MODERN = "not_modern_windows"
PROBE_PYWEBVIEW_MISSING = "pywebview_missing"
PROBE_RUNTIME_MISSING = "runtime_missing"
PROBE_INIT_FAILED = "init_failed"
PROBE_CHILD_TIMEOUT = "child_timeout"
PROBE_LOAD_TIMEOUT = "load_timeout"
PROBE_FRONTEND_MISSING = "frontend_missing"
PROBE_SCRIPT_MISSING = "probe_script_missing"
PROBE_SPAWN_FAILED = "spawn_failed"

PROBE_DESCRIPTIONS = {
    PROBE_OK: "WebView2 healthy; HTML frontend can start",
    PROBE_NOT_MODERN: "Not Windows 10/11; HTML frontend unsupported",
    PROBE_PYWEBVIEW_MISSING: "pywebview is not installed in this interpreter",
    PROBE_RUNTIME_MISSING: "WebView2 runtime is not installed",
    PROBE_INIT_FAILED: "WebView2 runtime present but initialization failed",
    PROBE_CHILD_TIMEOUT: "WebView2 probe child process timed out",
    PROBE_LOAD_TIMEOUT: "WebView2 page never became ready (readiness timeout)",
    PROBE_FRONTEND_MISSING: "frontend/index.html not found",
    PROBE_SCRIPT_MISSING: "webview_main.py probe script not found",
    PROBE_SPAWN_FAILED: "could not spawn the WebView2 probe child process",
}

WEBVIEW2_PROBE_EXIT_CODES = {
    0: PROBE_OK,
    3: PROBE_PYWEBVIEW_MISSING,
    4: PROBE_FRONTEND_MISSING,
    5: PROBE_RUNTIME_MISSING,
    6: PROBE_INIT_FAILED,
    7: PROBE_LOAD_TIMEOUT,
}


def describe_probe_result(result: str) -> str:
    return PROBE_DESCRIPTIONS.get(result, "unknown probe result: {0}".format(result))


def webview2_probe_result(timeout: float | None = None) -> str:
    if not is_modern_windows():
        return PROBE_NOT_MODERN
    if not pywebview_available():
        return PROBE_PYWEBVIEW_MISSING
    if not os.path.isfile(WEBVIEW2_PROBE_SCRIPT):
        return PROBE_SCRIPT_MISSING
    if not webview2_runtime_installed():
        return PROBE_RUNTIME_MISSING
    if timeout is None:
        timeout = WEBVIEW2_PROBE_TIMEOUT
    import tempfile as _tf
    _probe_log = os.path.join(_tf.gettempdir(), "pmg_probe.log")
    try:
        with open(_probe_log, "w", encoding="utf-8") as _flog:
            completed = subprocess.run(
                _probe_argv(),
                timeout=timeout,
                stdout=_flog,
                stderr=subprocess.STDOUT,
            )
    except subprocess.TimeoutExpired:
        return PROBE_CHILD_TIMEOUT
    except OSError:
        return PROBE_SPAWN_FAILED
    return WEBVIEW2_PROBE_EXIT_CODES.get(completed.returncode, PROBE_INIT_FAILED)


def webview2_health_probe(timeout: float | None = None) -> bool:
    return webview2_probe_result(timeout) == PROBE_OK


def can_use_html_frontend() -> bool:
    return is_modern_windows() and webview2_runtime_installed() and pywebview_available()


def describe_environment() -> str:
    lines = [
        "windows_major={0}".format(windows_major()),
        "is_modern_windows={0}".format(is_modern_windows()),
        "webview2_runtime={0}".format(webview2_runtime_installed()),
        "pywebview_available={0}".format(pywebview_available()),
        "can_use_html_frontend={0}".format(can_use_html_frontend()),
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    print(describe_environment())
    if "--probe" in sys.argv[1:]:
        result = webview2_probe_result()
        print("probe_result={0}".format(result))
        print("probe_detail={0}".format(describe_probe_result(result)))
        sys.exit(0 if result == PROBE_OK else 1)