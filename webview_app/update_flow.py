"""Phase 20.58: Shared auto-update flow controller (UI-agnostic).

A single state machine driving ``webview_app/updater.py`` — the ONLY module
that touches GitHub. Used by BOTH UIs so no update logic is duplicated:

  * the pywebview bridge (``webview_app/backend_api.py``) -> WebView2 frontend
  * the Tkinter fallback (``main.py`` App.check_for_updates)

Contract (Phase 20.58 requirements):

  * MANUAL CHECK ONLY. No background scheduling, no timers, no startup checks.
  * Nothing is downloaded before the user explicitly confirms an available
    update (``start_update()`` is a user action, and it is refused unless the
    flow is in the AVAILABLE state).
  * Every network operation (GitHub API query, download, SHA256 verification)
    runs on a daemon WORKER THREAD — never the UI thread. Both UIs marshal
    the callbacks back to their own event loop (Tk: root.after; WebView2: the
    frontend polls get_update_status(), a lock-protected snapshot read).
  * The installer is launched only AFTER download + dual SHA256 verification
    both succeed, and the application exits only AFTER the installer has
    actually spawned. A launch failure never exits the app.
  * No silent installation: the installer is launched interactively and the
    user controls it in the installer's own UI. No /SILENT flag is passed.

States are plain strings so they cross the pywebview JSON bridge unchanged:

    idle -> checking -> up-to-date | available | failed
    available -> downloading -> verifying -> ready -> launching -> done
                                (any step may fail -> failed)
"""
from __future__ import annotations

import threading

import updater

# ---------------------------------------------------------------------------
# Update states (plain strings: they cross the pywebview JSON bridge verbatim)
# ---------------------------------------------------------------------------
IDLE = "idle"
CHECKING = "checking"
UP_TO_DATE = "up-to-date"
AVAILABLE = "available"
DOWNLOADING = "downloading"
VERIFYING = "verifying"
READY = "ready"
LAUNCHING = "launching"
DONE = "done"
FAILED = "failed"

# States in which a worker thread is busy and a new operation must be refused.
_ACTIVE = frozenset({CHECKING, DOWNLOADING, VERIFYING, READY, LAUNCHING})

# Breathe before exiting so the "launching/done" state is visible to the user.
# The installer is already detached, so this only affects the app's own exit.
EXIT_DELAY_SECONDS = 0.8


def friendly_message(error):
    """Map a low-level updater error to a short, safe, user-facing message.

    NEVER exposes a Python traceback to the user. Unknown failures get a
    generic retry prompt.
    """
    text = (error or "").strip()
    low = text.lower()
    if not text:
        return "تعذر إكمال التحديث. حاول مرة أخرى لاحقًا."
    if ("unreachable" in low) or ("urlopen" in low) or ("name resolution" in low) \
            or ("timed out" in low) or ("timeout" in low) or ("interrupted" in low):
        return "لا يوجد اتصال بالإنترنت."
    if ("http 403" in low) or ("http 404" in low) or ("empty response" in low):
        return "تعذر الوصول إلى التحديثات."
    if ("size" in low) and ("sha256" not in low):
        return "فشل التحقق من التحديث — حجم الملف غير مطابق."
    if ("sha256" in low) or ("digest" in low) or ("verif" in low):
        return "فشل التحقق من التحديث."
    if "could not start" in low or "launch" in low or "installer" in low:
        return "تعذر بدء برنامج التثبيت."
    if "version unavailable" in low or "unparseable" in low:
        return "تعذر تحديد إصدار البرنامج."
    return "تعذر إكمال التحديث. حاول مرة أخرى لاحقًا."


class UpdateFlow:
    """UI-agnostic update state machine. Thread-safe; never raises to callers.

    Callbacks (``on_state``, ``on_progress``, ``on_exit``) are invoked from the
    WORKER thread — each UI marshals them onto its own event loop.
    """

    def __init__(self, on_state=None, on_progress=None, on_exit=None,
                 current_version=""):
        self._lock = threading.RLock()
        self._state = IDLE
        self._message = ""
        self._progress = 0
        self._current_version = str(current_version or "")
        self._latest_version = ""
        self._release = None
        self._thread = None
        self._on_state = on_state
        self._on_progress = on_progress
        self._on_exit = on_exit

    # ------------------------------------------------------------------
    # Snapshot (JSON-safe; crosses the pywebview bridge)
    # ------------------------------------------------------------------
    def status(self):
        return {
            "ok": True,
            "state": self._state,
            "message": self._message,
            "progress": self._progress,
            "current_version": self._current_version,
            "latest_version": self._latest_version,
            "busy": self._state in _ACTIVE,
        }

    def _set_state(self, state, message="", progress=None):
        with self._lock:
            self._state = state
            if message:
                self._message = message
            if progress is not None:
                self._progress = progress
        if self._on_state is not None:
            try:
                self._on_state(state, message)
            except Exception:
                pass

    def _set_progress(self, progress):
        with self._lock:
            self._progress = progress
        if self._on_progress is not None:
            try:
                self._on_progress(progress)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Manual check
    # ------------------------------------------------------------------
    def check_async(self, current_version=None):
        """Start an update check on a worker thread. Returns immediately.

        Returns {"ok": True} when the check started, or {"ok": False,
        "error": ...} when an operation is already running. Never raises.
        """
        with self._lock:
            if self._state in _ACTIVE:
                return {"ok": False, "error": "عملية تحديث جارية بالفعل"}
        self._set_state(CHECKING, "جارٍ التحقق عن التحديثات…", progress=0)
        self._thread = threading.Thread(
            target=self._check_work, args=(current_version,),
            name="pmg-update-check", daemon=True)
        self._thread.start()
        return {"ok": True}

    def _check_work(self, current_version):
        try:
            result = updater.check_for_update(current_version)
        except Exception as exc:
            self._set_state(FAILED, friendly_message(str(exc)))
            return
        if not result.get("ok"):
            self._set_state(FAILED, friendly_message(result.get("error", "")))
            return
        latest = result.get("latest") or {}
        with self._lock:
            self._current_version = str(result.get("current_version", "") or "")
            self._latest_version = str(latest.get("version", "") or "")
            self._release = latest
        if result.get("update_available"):
            self._set_state(
                AVAILABLE,
                "الإصدار {0} متاح." .format(self._latest_version))
        else:
            self._set_state(UP_TO_DATE, "أنت تستخدم أحدث إصدار.")

    # ------------------------------------------------------------------
    # Download + verify + launch (only after explicit user confirmation)
    # ------------------------------------------------------------------
    def start_update(self):
        """Begin downloading the verified update. A USER ACTION.

        Refused unless the flow is in the AVAILABLE state, so nothing is ever
        downloaded without explicit confirmation. Returns {"ok": True} when
        the download started, {"ok": False, "error": ...} otherwise.
        """
        with self._lock:
            if self._state in _ACTIVE:
                return {"ok": False, "error": "عملية تحديث جارية بالفعل"}
            if self._state != AVAILABLE or not self._release:
                return {"ok": False, "error": "لا يوجد تحديث متاح"}
            release = self._release
        self._set_state(DOWNLOADING, "جارٍ تنزيل التحديث…", progress=0)
        self._thread = threading.Thread(
            target=self._update_work, args=(release,),
            name="pmg-update-download", daemon=True)
        self._thread.start()
        return {"ok": True}

    def _update_work(self, release):
        asset = release.get("asset") or {}
        asset_url = asset.get("url")
        expected_size = asset.get("size")
        digest_hex = asset.get("digest_hex")
        sums_url = release.get("sha256sums_url")
        version = release.get("version")
        if not (asset_url and expected_size and digest_hex and sums_url and version):
            self._set_state(FAILED, "تعذر إكمال التحديث. حاول مرة أخرى لاحقًا.")
            return

        def _progress(total_bytes):
            try:
                if expected_size and int(expected_size) > 0:
                    pct = max(0, min(100, int(total_bytes) * 100 // int(expected_size)))
                    self._set_progress(pct)
            except Exception:
                pass

        # 1) Streamed download to a .part file; updater verifies size and the
        #    GitHub asset digest + same-release SHA256SUMS.txt before renaming.
        download = updater.download_update(
            asset_url, expected_size, digest_hex, sums_url, version,
            progress_callback=_progress)
        if not download.get("ok"):
            self._set_state(FAILED, friendly_message(download.get("error", "")))
            return
        installer_path = download.get("path", "")

        # 2) Explicit verification pass (state visible to the user) — re-checks
        #    the local hash against the API digest and the same release's
        #    SHA256SUMS.txt. An unverified installer is never launched.
        self._set_state(VERIFYING, "جارٍ التحقق من التحديث…", progress=100)
        verification = updater.verify_file(
            installer_path, digest_hex, sha256sums_url=sums_url)
        if not verification.get("ok"):
            self._set_state(FAILED, friendly_message(verification.get("error", "")))
            return

        # 3) Launch the VERIFIED installer (interactively — never silent).
        self._set_state(READY, "اكتمل التحقق. جارٍ تجهيز التثبيت…")
        self._set_state(LAUNCHING, "جارٍ بدء برنامج التثبيت…")
        launch = updater.launch_installer(installer_path)
        if not launch.get("ok"):
            # Launch failed: the app MUST stay alive and usable.
            self._set_state(FAILED, friendly_message(launch.get("error", "")))
            return

        # 4) The installer is detached and running. Close the app cleanly.
        self._set_state(
            DONE, "سيتم إغلاق البرنامج الآن لإكمال التثبيت.")
        if self._on_exit is not None:
            timer = threading.Timer(EXIT_DELAY_SECONDS, self._safe_exit)
            timer.daemon = True
            timer.start()

    def _safe_exit(self):
        try:
            self._on_exit()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------
    def reset(self):
        """Return to idle (e.g. the user dismissed the update panel)."""
        with self._lock:
            if self._state in _ACTIVE:
                return {"ok": False, "error": "عملية تحديث جارية بالفعل"}
            self._state = IDLE
            self._message = ""
            self._progress = 0
            self._release = None
            self._latest_version = ""
        return {"ok": True}
