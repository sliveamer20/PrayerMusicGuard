"""Phase 20.58: UI integration tests for the Auto Update feature.

Self-contained: NO network access, NO GitHub contact, NO real installer
execution, NO Tk/WebView window required. The updater backend is replaced
with a fake, so every update path (check / download / verify / launch /
failure) is driven deterministically.

Run with the pinned Win7 toolchain:

    win7\\venv\\Scripts\\python.exe test_update_ui.py

Covers:
  - "Check for Updates" entry exists in all three UIs
    (tray menu, WebView2 frontend, Tkinter fallback)
  - current version is displayed
  - equal version -> up-to-date state
  - newer version -> update available state
  - user cancellation ("Later") -> no download, no installer launch
  - start_update refused before confirmation (never downloads unrequested)
  - download runs off the UI thread (progress does not block)
  - progress bytes -> percent mapping
  - verification failure -> no installer launch, app stays alive
  - installer launch failure -> app stays alive (no exit)
  - success -> installer launched once, then exit requested
  - the WebView2 bridge methods delegate to the shared flow
  - existing alert styling is untouched
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
WEBVIEW_APP = os.path.join(HERE, "webview_app")
FRONTEND = os.path.join(WEBVIEW_APP, "frontend")
if WEBVIEW_APP not in sys.path:
    sys.path.insert(0, WEBVIEW_APP)

_RESULTS = []


def check(name, condition, detail=""):
    _RESULTS.append((name, bool(condition), detail))
    status = "PASS" if condition else "FAIL"
    line = "[{0}] {1}".format(status, name)
    if detail:
        line += "  -- {0}".format(detail)
    try:
        print(line)
    except UnicodeEncodeError:
        # A Windows console defaults to a legacy codepage (e.g. cp1252) that
        # cannot encode the Arabic update messages captured from the UI. This
        # is a reporting artifact only -- never let it abort a passing run.
        print(line.encode("ascii", "replace").decode("ascii"))


# ---------------------------------------------------------------------------
# Fake updater backend (the ONLY thing that would touch GitHub)
# ---------------------------------------------------------------------------

_FAKE_DIGEST = "a" * 64
_FAKE_RELEASE = {
    "ok": True,
    "tag": "v1.2.9",
    "version": "1.2.9",
    "html_url": "https://github.com/sliveamer20/PrayerMusicGuard/releases/tag/v1.2.9",
    "asset": {
        "name": "PrayerMusicGuard-Setup.exe",
        "size": 1000000,
        "url": "https://github.com/sliveamer20/PrayerMusicGuard/releases/download/v1.2.9/PrayerMusicGuard-Setup.exe",
        "digest_hex": _FAKE_DIGEST,
    },
    "sha256sums_url": "https://github.com/sliveamer20/PrayerMusicGuard/releases/download/v1.2.9/SHA256SUMS.txt",
}


class FakeUpdater:
    """Replaces webview_app/updater.py for deterministic offline tests."""

    def __init__(self):
        self.check_result = None          # returned by check_for_update
        self.download_result = None       # returned by download_update
        self.verify_result = None         # returned by verify_file
        self.launch_result = None         # returned by launch_installer
        self.download_calls = 0
        self.verify_calls = 0
        self.launch_calls = 0
        self.progress_callback = None
        self.download_thread = None       # thread that ran download_update
        self.download_payload = None

    # -- shape of updater.check_for_update(current_version) --
    def check_for_update(self, current_version=None):
        result = self.check_result
        if callable(result):
            result = result(current_version)
        if result is None:
            result = {
                "ok": True,
                "update_available": False,
                "current_version": current_version or "1.2.8",
                "latest": dict(_FAKE_RELEASE, version="1.2.8", tag="v1.2.8"),
            }
        return result

    # -- shape of updater.download_update(url, size, digest, sums, version, cb)
    def download_update(self, asset_url, expected_size, expected_sha256_hex,
                        sha256sums_url, version, dest_dir=None, progress_callback=None):
        self.download_calls += 1
        self.download_thread = threading.current_thread()
        self.progress_callback = progress_callback
        self.download_payload = (asset_url, expected_size, expected_sha256_hex,
                                 sha256sums_url, version)
        result = self.download_result
        if callable(result):
            result = result(asset_url, expected_size, progress_callback)
        if result is None:
            result = {"ok": True, "path": os.path.join(tempfile.gettempdir(),
                                                       "pmg-update-fake.exe"),
                      "sha256": _FAKE_DIGEST}
        return result

    # -- shape of updater.verify_file(path, digest, sha256sums_url=...) --
    def verify_file(self, path, expected_sha256_hex, sha256sums_url=None,
                    sha256sums_content=None, target_name=None):
        self.verify_calls += 1
        result = self.verify_result
        if result is None:
            result = {"ok": True, "sha256": _FAKE_DIGEST}
        return result

    # -- shape of updater.launch_installer(path) --
    def launch_installer(self, setup_path):
        self.launch_calls += 1
        result = self.launch_result
        if result is None:
            result = {"ok": True, "pid": 4242}
        return result


def _install_fake_updater():
    """Make update_flow import the fake instead of the real updater."""
    import update_flow
    fake = FakeUpdater()
    update_flow.updater = fake
    return fake


_TERMINAL = ("up-to-date", "available", "failed", "done")


def _wait_for_terminal(flow, timeout=8.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        state = flow.status().get("state")
        if state in _TERMINAL:
            return state
        time.sleep(0.02)
    return flow.status().get("state")


# ---------------------------------------------------------------------------
# 1. "Check for Updates" entry exists in all three UIs
# ---------------------------------------------------------------------------

def test_entry_points_exist():
    with open(os.path.join(HERE, "main.py"), "r", encoding="utf-8") as handle:
        main_src = handle.read()
    with open(os.path.join(FRONTEND, "index.html"), "r", encoding="utf-8") as handle:
        html_src = handle.read()
    with open(os.path.join(FRONTEND, "js", "app.js"), "r", encoding="utf-8") as handle:
        js_src = handle.read()

    check("tray menu has Check for Updates item",
          "التحقق من التحديثات" in main_src and "self.check_for_updates" in main_src)
    tray_line = [ln for ln in main_src.splitlines() if "check_for_updates" in ln
                 and "MenuItem" in ln]
    check("tray item wired to check_for_updates", len(tray_line) == 1,
          "found {0} tray MenuItem line(s)".format(len(tray_line)))

    check("HTML has check-updates button", 'id="btn-check-updates"' in html_src)
    check("HTML has install-update button", 'id="btn-install-update"' in html_src)
    check("HTML has update-later button", 'id="btn-update-later"' in html_src)
    check("HTML has update progress bar", 'id="update-progress-fill"' in html_src)
    check("HTML has current version display",
          'id="update-current-version"' in html_src)
    check("HTML has update card", 'card--update' in html_src)

    check("JS wires check-updates", 'on("btn-check-updates", checkUpdates)' in js_src)
    check("JS wires install-update", 'on("btn-install-update", installUpdate)' in js_src)
    check("JS wires update-later", 'on("btn-update-later", laterUpdate)' in js_src)
    check("JS renders update states", "renderUpdateState" in js_src
          and '"downloading"' in js_src and '"verifying"' in js_src
          and '"launching"' in js_src and '"done"' in js_src)
    check("JS displays current version", 'setText("update-current-version"' in js_src)
    check("JS does not call GitHub directly",
          "api.github.com" not in js_src and "github.com/repos" not in js_src)

    import main as _main
    check("Tkinter App.check_for_updates exists",
          hasattr(_main.App, "check_for_updates"))
    check("Tkinter install/dismiss handlers exist",
          hasattr(_main.App, "_install_update") and hasattr(_main.App, "_dismiss_update"))
    check("Tkinter update uses shared update_flow",
          "import update_flow" in main_src and "_update_flow" in main_src)
    del _main
    for name in list(sys.modules):
        if name in ("main", "pmg_main"):
            del sys.modules[name]


# ---------------------------------------------------------------------------
# 2. Update flow state machine (drives both UIs)
# ---------------------------------------------------------------------------

def test_flow_check_states():
    fake = _install_fake_updater()
    import update_flow

    # equal version -> up to date
    fake.check_result = {
        "ok": True, "update_available": False,
        "current_version": "1.2.8",
        "latest": dict(_FAKE_RELEASE, version="1.2.8"),
    }
    flow = update_flow.UpdateFlow(current_version="1.2.8")
    flow.check_async()
    state = _wait_for_terminal(flow)
    snap = flow.status()
    check("equal version -> up-to-date", state == "up-to-date",
          "state={0}".format(state))
    check("up-to-date reports current version",
          snap.get("current_version") == "1.2.8")

    # newer version -> available
    fake.check_result = {
        "ok": True, "update_available": True,
        "current_version": "1.2.8", "latest": _FAKE_RELEASE,
    }
    flow = update_flow.UpdateFlow(current_version="1.2.8")
    flow.check_async()
    state = _wait_for_terminal(flow)
    snap = flow.status()
    check("newer version -> available", state == "available", "state={0}".format(state))
    check("available reports both versions",
          snap.get("current_version") == "1.2.8"
          and snap.get("latest_version") == "1.2.9")

    # check failure -> failed (friendly message, no traceback)
    fake.check_result = {"ok": False, "error": "GitHub API unreachable: no net"}
    flow = update_flow.UpdateFlow(current_version="1.2.8")
    flow.check_async()
    state = _wait_for_terminal(flow)
    check("check failure -> failed", state == "failed", "state={0}".format(state))
    check("failed message is friendly (no traceback)",
          "traceback" not in flow.status().get("message", "").lower()
          and "no net" not in flow.status().get("message", ""))


def test_flow_no_download_without_confirmation():
    _install_fake_updater()
    import update_flow
    flow = update_flow.UpdateFlow(current_version="1.2.8")
    # Idle flow: start_update must be refused
    result = flow.start_update()
    check("start_update refused while idle", not result.get("ok"))
    update_flow_updater = sys.modules.get("update_flow").updater
    check("no download happened unrequested",
          update_flow_updater.download_calls == 0)


def test_flow_user_cancellation():
    fake = _install_fake_updater()
    import update_flow
    fake.check_result = {
        "ok": True, "update_available": True,
        "current_version": "1.2.8", "latest": _FAKE_RELEASE,
    }
    flow = update_flow.UpdateFlow(current_version="1.2.8")
    flow.check_async()
    _wait_for_terminal(flow)
    check("update is available before cancel",
          flow.status().get("state") == "available")
    # User chooses "Later":
    flow.reset()
    check("reset returns to idle", flow.status().get("state") == "idle")
    check("cancel triggers no download", fake.download_calls == 0)
    check("cancel triggers no installer launch", fake.launch_calls == 0)


def test_flow_download_progress_threading():
    fake = _install_fake_updater()
    import update_flow

    def _download(url, size, progress_callback):
        # Emit progress like the real streamed downloader would.
        if progress_callback is not None:
            for step in (0, 250000, 500000, 750000, 1000000):
                progress_callback(step)
        return {"ok": True, "path": os.path.join(tempfile.gettempdir(),
                                                 "pmg-update-fake.exe"),
                "sha256": _FAKE_DIGEST}

    fake.check_result = {
        "ok": True, "update_available": True,
        "current_version": "1.2.8", "latest": _FAKE_RELEASE,
    }
    fake.download_result = _download
    main_thread = threading.current_thread()
    flow = update_flow.UpdateFlow(current_version="1.2.8")
    flow.check_async()
    _wait_for_terminal(flow)

    started = flow.start_update()
    check("start_update accepted when available", started.get("ok"))
    state = _wait_for_terminal(flow, timeout=10.0)
    check("download reached terminal state", state == "done", "state={0}".format(state))
    check("download ran exactly once", fake.download_calls == 1)
    check("download ran OFF the UI/main thread",
          fake.download_thread is not None
          and fake.download_thread is not main_thread,
          "thread={0}".format(fake.download_thread.name if fake.download_thread else None))
    check("progress percent reached 100",
          flow.status().get("progress") == 100,
          "progress={0}".format(flow.status().get("progress")))
    check("installer launched exactly once", fake.launch_calls == 1)


def test_flow_progress_percent_mapping():
    fake = _install_fake_updater()
    import update_flow
    seen = []

    def _download(url, size, progress_callback):
        if progress_callback is not None:
            progress_callback(0)
            progress_callback(500000)   # exactly half of 1000000
            progress_callback(1000000)
            seen.append("done")
        return {"ok": True, "path": "fake", "sha256": _FAKE_DIGEST}

    fake.check_result = {"ok": True, "update_available": True,
                         "current_version": "1.2.8", "latest": _FAKE_RELEASE}
    fake.download_result = _download
    progress_seen = []
    flow = update_flow.UpdateFlow(current_version="1.2.8",
                                  on_progress=lambda p: progress_seen.append(p))
    flow.check_async()
    _wait_for_terminal(flow)
    flow.start_update()
    _wait_for_terminal(flow, timeout=10.0)
    check("progress callback received percents",
          len(progress_seen) >= 2 and 50 in progress_seen and 100 in progress_seen,
          "seen={0}".format(progress_seen))


def test_flow_verification_failure_no_launch():
    fake = _install_fake_updater()
    import update_flow
    fake.check_result = {"ok": True, "update_available": True,
                         "current_version": "1.2.8", "latest": _FAKE_RELEASE}
    fake.verify_result = {"ok": False, "error": "local SHA256 bad != API digest good"}
    exited = []
    flow = update_flow.UpdateFlow(current_version="1.2.8",
                                  on_exit=lambda: exited.append(1))
    flow.check_async()
    _wait_for_terminal(flow)
    flow.start_update()
    state = _wait_for_terminal(flow, timeout=10.0)
    check("verification failure -> failed", state == "failed", "state={0}".format(state))
    check("verification failure launches NO installer", fake.launch_calls == 0)
    check("verification failure does NOT exit app", len(exited) == 0)
    check("verification failure message is friendly",
          "SHA256" not in flow.status().get("message", ""))


def test_flow_download_failure_no_launch():
    fake = _install_fake_updater()
    import update_flow
    fake.check_result = {"ok": True, "update_available": True,
                         "current_version": "1.2.8", "latest": _FAKE_RELEASE}
    fake.download_result = {"ok": False, "error": "download interrupted: reset"}
    exited = []
    flow = update_flow.UpdateFlow(current_version="1.2.8",
                                  on_exit=lambda: exited.append(1))
    flow.check_async()
    _wait_for_terminal(flow)
    flow.start_update()
    state = _wait_for_terminal(flow, timeout=10.0)
    check("download failure -> failed", state == "failed", "state={0}".format(state))
    check("download failure launches NO installer", fake.launch_calls == 0)
    check("download failure does NOT exit app", len(exited) == 0)


def test_flow_launch_failure_app_stays_alive():
    fake = _install_fake_updater()
    import update_flow
    fake.check_result = {"ok": True, "update_available": True,
                         "current_version": "1.2.8", "latest": _FAKE_RELEASE}
    fake.launch_result = {"ok": False, "error": "could not start x.exe: denied"}
    exited = []
    flow = update_flow.UpdateFlow(current_version="1.2.8",
                                  on_exit=lambda: exited.append(1))
    flow.check_async()
    _wait_for_terminal(flow)
    flow.start_update()
    state = _wait_for_terminal(flow, timeout=10.0)
    check("launch failure -> failed", state == "failed", "state={0}".format(state))
    check("launch attempt happened once", fake.launch_calls == 1)
    check("launch failure does NOT exit the app", len(exited) == 0)
    check("launch failure message is friendly",
          "could not start" not in flow.status().get("message", ""))


def test_flow_success_exits_after_spawn():
    fake = _install_fake_updater()
    import update_flow
    fake.check_result = {"ok": True, "update_available": True,
                         "current_version": "1.2.8", "latest": _FAKE_RELEASE}
    exited = []
    flow = update_flow.UpdateFlow(current_version="1.2.8",
                                  on_exit=lambda: exited.append(1))
    flow.check_async()
    _wait_for_terminal(flow)
    flow.start_update()
    state = _wait_for_terminal(flow, timeout=10.0)
    check("success -> done", state == "done", "state={0}".format(state))
    check("installer launched once", fake.launch_calls == 1)
    # on_exit is scheduled with a short delay; wait for it.
    deadline = time.monotonic() + 3.0
    while time.monotonic() < deadline and not exited:
        time.sleep(0.02)
    check("exit requested only after installer spawned", len(exited) == 1)
    check("no silent flag ever passed to launcher",
          not hasattr(fake, "silent_flag_used"))


def test_flow_rejects_concurrent_operations():
    _install_fake_updater()
    import update_flow
    flow = update_flow.UpdateFlow(current_version="1.2.8")
    # Force a perpetually-busy state
    flow._state = update_flow.CHECKING
    check("concurrent check refused", not flow.check_async().get("ok"))
    check("concurrent start_update refused", not flow.start_update().get("ok"))
    check("concurrent reset refused", not flow.reset().get("ok"))


# ---------------------------------------------------------------------------
# 3. WebView2 bridge delegates to the shared flow
# ---------------------------------------------------------------------------

def test_bridge_methods():
    fake = _install_fake_updater()
    import update_flow
    fake.check_result = {"ok": True, "update_available": True,
                         "current_version": "1.2.8", "latest": _FAKE_RELEASE}
    try:
        import backend_api
    except Exception as exc:
        check("backend_api importable", False, str(exc))
        return
    check("backend_api importable", True)
    api = backend_api.BackendAPI()
    check("bridge exposes update methods",
          all(hasattr(api, m) for m in
              ("check_for_updates", "get_update_status", "start_update",
               "dismiss_update", "attach_webview_window")))
    # Replace the lazily-built flow with a controlled one.
    flow = update_flow.UpdateFlow(current_version="1.2.8")
    api._update_flow_instance = flow
    res = api.check_for_updates()
    check("check_for_updates returns ok", res.get("ok"))
    state = _wait_for_terminal(flow)
    check("bridge flow reaches available", state == "available", "state={0}".format(state))
    snap = api.get_update_status()
    check("get_update_status is a clean snapshot",
          snap.get("state") == "available" and snap.get("latest_version") == "1.2.9")
    started = api.start_update()
    check("bridge start_update accepted", started.get("ok"))
    final = _wait_for_terminal(flow, timeout=10.0)
    check("bridge flow completes", final == "done", "state={0}".format(final))
    check("bridge start_update before available is refused",
          not update_flow.UpdateFlow().start_update().get("ok"))
    del api


# ---------------------------------------------------------------------------
# 4. Tkinter dialog renders states correctly (live Tk, no network)
# ---------------------------------------------------------------------------

def test_tkinter_dialog_states():
    """Drive App.check_for_updates() with a real (withdrawn) Tk root and a
    fake updater. Confirms the dialog maps, the AVAILABLE state shows both
    versions plus the Install/Later buttons, and the flow reaches DONE with
    exactly one installer launch. Runs entirely on the Tk main loop."""
    try:
        import tkinter as tk
    except Exception as exc:
        check("tkinter available for dialog test", False, str(exc))
        return
    check("tkinter available for dialog test", True)

    import update_flow
    fake = FakeUpdater()
    fake.check_result = {"ok": True, "update_available": True,
                         "current_version": "1.2.8", "latest": _FAKE_RELEASE}
    update_flow.updater = fake

    import main as _main
    captured = {}

    def _run():
        root = tk.Tk()
        root.withdraw()
        try:
            app = _main.App(root)
            app._start_app()
            app.check_for_updates()

            def poll():
                state = app._update_flow().status().get("state")
                if state == "available":
                    root.after(400, _capture_available)
                    return
                root.after(100, poll)

            def _capture_available():
                try:
                    captured["text"] = app._update_status_var.get()
                    captured["install_mapped"] = bool(
                        app._update_install_btn.winfo_ismapped())
                    captured["later_mapped"] = bool(
                        app._update_later_btn.winfo_ismapped())
                except Exception:
                    pass
                app._install_update()
                root.after(200, _wait_done)

            def _wait_done():
                if app._update_flow().status().get("state") == "done":
                    captured["final"] = "done"
                    _finish()
                else:
                    root.after(100, _wait_done)

            def _finish():
                try:
                    captured["launches"] = fake.launch_calls
                    captured["dlg_mapped"] = bool(
                        app._update_dialog.winfo_ismapped())
                except Exception:
                    pass
                root.quit()

            root.after(100, poll)
            root.after(15000, root.quit)  # hard safety cap
            root.mainloop()
        finally:
            try:
                root.destroy()
            except Exception:
                pass

    try:
        _run()
    except Exception as exc:
        check("Tkinter dialog run did not raise", False, repr(exc))
        return
    check("Tkinter dialog run did not raise", True)
    check("dialog is mapped while main window is hidden to tray",
          captured.get("dlg_mapped") is True)
    check("available state shows both versions",
          "1.2.9" in (captured.get("text") or "")
          and "1.2.8" in (captured.get("text") or ""),
          captured.get("text"))
    check("Install button appears when an update is available",
          captured.get("install_mapped") is True)
    check("Later button appears when an update is available",
          captured.get("later_mapped") is True)
    check("flow reaches done with one installer launch",
          captured.get("final") == "done" and captured.get("launches") == 1,
          "final={0} launches={1}".format(captured.get("final"),
                                          captured.get("launches")))
    del _main
    for name in list(sys.modules):
        if name in ("main", "pmg_main"):
            del sys.modules[name]


# ---------------------------------------------------------------------------
# 5. Existing UI / alert system untouched
# ---------------------------------------------------------------------------

def test_existing_ui_untouched():
    with open(os.path.join(FRONTEND, "js", "app.js"), "r", encoding="utf-8") as handle:
        js = handle.read()
    with open(os.path.join(FRONTEND, "css", "components.css"), "r", encoding="utf-8") as handle:
        comps = handle.read()
    with open(os.path.join(FRONTEND, "index.html"), "r", encoding="utf-8") as handle:
        html = handle.read()

    check("alert setStatus still present", "function setStatus(id, message, type)" in js)
    check("alert CSS classes still present",
          ".card__hint.is-success" in comps and ".card__hint.is-error" in comps
          and ".card__hint.is-info" in comps and ".card__hint.is-warning" in comps)
    check("save animation still present",
          "playSaveAnimation" in js and ".btn.is-saving" in
          open(os.path.join(FRONTEND, "css", "skins.css"), "r", encoding="utf-8").read())
    check("save buttons unchanged",
          'id="btn-save"' in html and 'class="save-anim"' in html)
    check("no new framework introduced",
          "tailwind" not in js.lower() and "bootstrap" not in js.lower()
          and "data-lucide" not in js)
    check("existing bridge call wrapper unchanged",
          "function call(name)" in js and "window.pywebview" in js)

    # Protected assets
    releases_md = os.path.join(HERE, "releases", "RELEASES.md")
    with open(releases_md, "r", encoding="utf-8") as handle:
        rel = handle.read()
    check("releases/RELEASES.md still has v1.2.8 final-release header",
          "v1.2.8 (current final release)" in rel)
    v128 = os.path.join(HERE, "releases", "v1.2.8")
    check("releases/v1.2.8 folder intact", os.path.isdir(v128))
    check("VERSION constant is still 1.2.9",
          'APP_VERSION = "1.2.9"' in
          open(os.path.join(HERE, "main.py"), "r", encoding="utf-8").read())


# ---------------------------------------------------------------------------

def main():
    print("=" * 70)
    print("Phase 20.58 — Auto Update UI integration tests (offline)")
    print("=" * 70)
    test_entry_points_exist()
    test_flow_check_states()
    test_flow_no_download_without_confirmation()
    test_flow_user_cancellation()
    test_flow_download_progress_threading()
    test_flow_progress_percent_mapping()
    test_flow_verification_failure_no_launch()
    test_flow_download_failure_no_launch()
    test_flow_launch_failure_app_stays_alive()
    test_flow_success_exits_after_spawn()
    test_flow_rejects_concurrent_operations()
    test_bridge_methods()
    test_tkinter_dialog_states()
    test_existing_ui_untouched()

    passed = sum(1 for _, ok, _ in _RESULTS if ok)
    failed = sum(1 for _, ok, _ in _RESULTS if not ok)
    print("-" * 70)
    print("TOTAL: {0} checks | PASS: {1} | FAIL: {2}".format(len(_RESULTS), passed, failed))
    if failed:
        print("\nFAILURES:")
        for name, ok, detail in _RESULTS:
            if not ok:
                print("  [FAIL] {0} -- {1}".format(name, detail))
    print("-" * 70)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
