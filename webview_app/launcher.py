"""Phase 2/3 hybrid launcher for Prayer Music Guard.

Chooses the UI at startup without modifying main.py:

  * Windows 10/11 with a WORKING WebView2 runtime -> HTML/CSS/JS frontend
    hosted in pywebview (webview_main.py), run as a bounded child process.
  * Anything else (Windows 7 SP1 x64, missing WebView2, missing pywebview,
    a failed probe, or a hung/failed frontend startup) -> the existing
    Tkinter application in main.py, launched exactly as before.

The Tkinter path runs main.py as __main__ via runpy, so its startup
guard, single-instance mutex, tray, and monitoring all behave
identically to a normal launch. main.py itself is never edited.
"""
from __future__ import annotations

import os
import runpy
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)


def _frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def _bundle_dir() -> str:
    return getattr(sys, "_MEIPASS", PROJECT_ROOT)


def _main_py() -> str:
    """On-disk main.py path, used only by unfrozen source/development runs.

    A frozen PyInstaller build never reads main.py from disk: the Tkinter
    fallback runs the compiled ``main`` module from PYZ (runpy.run_module in
    _run_tkinter_fallback), so no readable .py ships inside the OneDir bundle
    (Phase 20.46.A).
    """
    return os.path.join(PROJECT_ROOT, "main.py")


def _webview_main() -> str:
    if _frozen():
        candidate = os.path.join(_bundle_dir(), "webview_app", "webview_main.py")
        if os.path.isfile(candidate):
            return candidate
    return os.path.join(HERE, "webview_main.py")


MAIN_PY = _main_py()
WEBVIEW_MAIN = _webview_main()

READY_TIMEOUT_SECONDS = float(os.environ.get("PMG_WEBVIEW_READY_TIMEOUT", "30"))

sys.path.insert(0, HERE)


def _log(message: str) -> None:
    print("[launcher] {0}".format(message))
    try:
        import tempfile
        with open(os.path.join(tempfile.gettempdir(), "pmg_launcher.log"), "a", encoding="utf-8") as f:
            f.write("[launcher] {0}\n".format(message))
    except Exception:
        pass


def _show_splash() -> None:
    """Phase 20.6: Show HTML/CSS splash before frontend selection.
    Uses robust file URL and waits for page load before auto-close.
    Falls back to Tkinter for Windows 7 or WebView issues.
    """
    # Determine splash path
    splash_path = os.path.join(HERE, "splash.html")
    if not os.path.isfile(splash_path):
        splash_path = os.path.join(_bundle_dir(), "webview_app", "splash.html")
    
    # Try HTML/CSS splash (preferred for Windows 10/11)
    if splash_path and os.path.isfile(splash_path):
        try:
            import webview
            
            # Use relative path with forward slashes for WebView compatibility
            # This matches the approach used in webview_main.py
            try:
                abs_path = os.path.abspath(splash_path)
                # Convert to forward slashes for WebView
                url = abs_path.replace(os.sep, "/")
                _log(f"Splash file exists: {splash_path}")
                _log(f"Splash URL: {url}")
            except Exception as e:
                _log(f"Splash path resolution failed: {e}")
                url = splash_path
            
            # Create splash window with HTML/CSS
            window = webview.create_window(
                "صلاة وسكون",
                url,
                width=440,
                height=360,
                resizable=False,
                frameless=True,
                x=640,  # Center approximately
                y=360,
            )
            
            # Wait for page to load before starting close timer
            # Use loaded event to ensure content renders
            splash_visible = [False]
            
            def on_loaded():
                _log("Splash page loaded")
                splash_visible[0] = True
            
            try:
                window.events.loaded += on_loaded
            except:
                pass
            
            # Close after 3 seconds from page load, with minimum 0.5s display
            def auto_close():
                # Wait for page to load or timeout after 3 seconds
                start_time = time.time()
                while not splash_visible[0] and time.time() - start_time < 3.0:
                    time.sleep(0.05)
                
                # Keep splash visible for approximately 3 seconds after load
                elapsed = time.time() - start_time
                display_time = max(0.5, 3.0 - elapsed)
                time.sleep(display_time)
                
                try:
                    _log("Closing splash window")
                    window.destroy()
                    try:
                        webview.stop()
                    except:
                        pass
                except Exception as e:
                    _log(f"Splash close error: {e}")
            
            # Run close timer in background
            import threading
            threading.Thread(target=auto_close, daemon=True).start()
            
            # Start WebView - blocks until window closed
            try:
                webview.start(gui="edgechromium")
                _log("HTML splash completed successfully")
                return  # Success
            except Exception as e:
                _log(f"WebView splash failed: {e}")
                # Fall through to Tkinter fallback
        except Exception as e:
            _log(f"HTML splash unavailable: {e}")
    
    # Fallback: Tkinter splash for Windows 7 or WebView problems
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        
        splash = tk.Toplevel(root)
        splash.overrideredirect(True)
        splash.attributes("-topmost", True)
        splash.configure(bg="#202024")
        
        width, height = 380, 300
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        x = (sw - width) // 2
        y = (sh - height) // 3
        splash.geometry(f"{width}x{height}+{x}+{y}")
        
        label = tk.Label(splash, text="صلاة وسكون", bg="#202024", fg="#ffffff", 
                        font=("Segoe UI", 24, "bold"))
        label.pack(expand=True)
        
        splash.update_idletasks()
        splash.deiconify()
        splash.lift()
        
        root.after(1000, splash.destroy)
        root.after(1100, root.quit)
        root.mainloop()
    except Exception as e:
        _log(f"Splash failed: {e}")


def _instance_already_running() -> bool:
    """Non-owning single-instance probe for the parent launcher.

    True when another PrayerMusicGuard process already holds the named mutex.
    The mutex is opened and immediately closed, so this NEVER takes ownership
    and cannot make the first valid instance exit. The authoritative gate is
    the WebView2 child's acquire_single_instance(); this probe just lets a
    second launch exit cleanly before spawning a child (and before the heavy
    Tkinter fallback). Defensive: any error -> False (the child still guards).
    """
    try:
        import ctypes
        if PROJECT_ROOT not in sys.path:
            sys.path.insert(0, PROJECT_ROOT)
        import main as _main
        handle = _main.kernel32.CreateMutexW(None, False, _main.MUTEX_NAME)
        if not handle:
            return False
        already = ctypes.get_last_error() == 183  # ERROR_ALREADY_EXISTS
        _main.kernel32.CloseHandle(handle)
        return already
    except Exception:
        return False


def _run_tkinter_fallback(reason: str) -> None:
    _log("using Tkinter fallback: {0}".format(reason))
    if _frozen():
        # Frozen build: main.py is not shipped in the bundle (Phase 20.46.A).
        # Run the compiled "main" module from PYZ as __main__ — same entry
        # semantics as runpy.run_path, without needing a .py file on disk.
        runpy.run_module("main", run_name="__main__")
        return
    if not os.path.isfile(MAIN_PY):
        _log("main.py not found at {0}; cannot start".format(MAIN_PY))
        sys.exit(1)
    runpy.run_path(MAIN_PY, run_name="__main__")


def _run_html_frontend() -> bool:
    ready = os.path.join(tempfile.gettempdir(), "pmg_webview_ready_{0}.flag".format(os.getpid()))
    try:
        os.remove(ready)
    except OSError:
        pass

    if _frozen():
        argv = [sys.executable, "--webview-child", "--ready-file", ready]
    else:
        argv = [sys.executable, WEBVIEW_MAIN, "--ready-file", ready]
    try:
        proc = subprocess.Popen(
            argv,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError as e:
        _log("could not start webview child ({0})".format(e))
        return False

    deadline = time.monotonic() + READY_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if os.path.isfile(ready):
            _log("HTML frontend ready; waiting for window to close")
            proc.wait()
            try:
                os.remove(ready)
            except OSError:
                pass
            _log("HTML frontend closed cleanly")
            return True
        if proc.poll() is not None:
            _log("webview child exited early (code {0}); falling back".format(proc.returncode))
            return False
        time.sleep(0.2)

    _log("webview startup timed out after {0}s; terminating child".format(READY_TIMEOUT_SECONDS))
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
    try:
        os.remove(ready)
    except OSError:
        pass
    return False


def main() -> None:
    # Phase 20.3 FIX: Show splash before frontend selection
    # Splash must be visible regardless of HTML/Tkinter choice
    _show_splash()
    
    if os.environ.get("PMG_FORCE_TK", "").strip().lower() in ("1", "true", "yes"):
        _run_tkinter_fallback("PMG_FORCE_TK set")
        return

    # Phase 1: single-instance guard for the parent launcher (non-owning probe).
    # The authoritative gate is the WebView2 child's acquire_single_instance().
    if _instance_already_running():
        _log("Another PrayerMusicGuard instance is already running; exiting launcher without starting a second instance.")
        return

    try:
        import platform_check
    except ImportError as e:
        _run_tkinter_fallback("platform_check unavailable ({0})".format(e))
        return

    if not platform_check.can_use_html_frontend():
        _run_tkinter_fallback("HTML frontend not supported (win major {0})".format(
            platform_check.windows_major()))
        return

    # The separate off-screen WebView2 "probe" is intentionally NOT used:
    # an off-screen host window can fail WebView2 initialization (E_ABORT),
    # and it spawned an extra WebView2 instance on every launch. The real
    # readiness signal is the ready-file watchdog below, which waits for the
    # ACTUAL frontend window to load and falls back to Tkinter if it does not.
    _log("starting HTML frontend (WebView2)")
    if not _run_html_frontend():
        _run_tkinter_fallback("HTML frontend did not start")


if __name__ == "__main__":
    main()