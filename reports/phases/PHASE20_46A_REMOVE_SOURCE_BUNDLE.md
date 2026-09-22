# Phase 20.46.A — Remove Python Source from Release Bundle

**Date:** 2026-09-22
**Goal:** Stop shipping readable application `.py` files inside the OneDir release.
**Fixes:** Audit finding **2.1 (CRITICAL)** from `PHASE20_45_SECURITY_HARDENING_AUDIT.md` (§11 — "the central finding").
**Scope guard:** 20.46.B/C/D/E are NOT implemented. No code signing, no PYZ encryption, no packers/obfuscation, no UI or behavior change, no new release build.

---

## 1. Exact Files Changed

| File | Change | Backup |
|---|---|---|
| `webview_app/backend_api.py` | `_main_py()` simplified; `_load_main()` split into frozen / source branches | `backup\phase20_46a_remove_source_bundle_20260922_102204\backend_api.py` |
| `webview_app/launcher.py` | `_main_py()` simplified; `_run_tkinter_fallback()` frozen branch runs the compiled `main` from PYZ | `backup\phase20_46a_remove_source_bundle_20260922_102204\launcher.py` |
| `PrayerMusicGuard.spec` | Six application `.py` entries removed from `datas` | `backup\phase20_46a_remove_source_bundle_20260922_102204\PrayerMusicGuard.spec` |

Pre-change copies were taken **before** any edit (timestamped folder, project convention). No other source file was modified (verified by last-write-time sweep: only the three files above carry today's date). `main.py`, `uiverse_combobox.py`, `webview_app/app_entry.py`, `webview_main.py`, `platform_check.py`, `splash.html`, the frontend, `release.ps1`, `PrayerMusicGuard.iss` and `build_exe.bat` are byte-identical to before.

---

## 2. Old vs New `_load_main` Behavior (`webview_app/backend_api.py`)

### Old (root cause of source shipping)

```python
def _main_py() -> str:
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", PROJECT_ROOT)
        candidate = os.path.join(base, "main.py")
        if os.path.isfile(candidate):          # <- required main.py ON DISK in the bundle
            return candidate
    return os.path.join(PROJECT_ROOT, "main.py")

def _load_main():
    spec = importlib.util.spec_from_file_location("pmg_main", MAIN_PY)
    ...
    spec.loader.exec_module(module)            # <- exec'd plain text from disk, both modes
```

In a frozen run the module was loaded by `exec_module`-ing `sys._MEIPASS\main.py`, which is exactly why `main.py` had to be declared as `datas` — i.e. why 181 KB of readable core logic shipped.

### New

```python
def _main_py() -> str:
    """On-disk main.py path. Used ONLY by unfrozen source/development runs."""
    return os.path.join(PROJECT_ROOT, "main.py")

def _load_main():
    if getattr(sys, "frozen", False):
        # "main" is compiled into PYZ (hiddenimport). Import the compiled module
        # directly. Never fall back to sys._MEIPASS/main.py + exec_module here.
        module = __import__("main")
        sys.modules.setdefault("pmg_main", module)
        return module
    # Unfrozen source/development run: keep loading the real file from disk so
    # edits during development still take effect without a build.
    spec = importlib.util.spec_from_file_location("pmg_main", MAIN_PY)
    ...
```

| Mode | Old | New |
|---|---|---|
| Source / dev | `exec_module(PROJECT_ROOT/main.py)` as `pmg_main` | **unchanged** — `exec_module(PROJECT_ROOT/main.py)` as `pmg_main` |
| Frozen (PyInstaller) | `exec_module(sys._MEIPASS/main.py)` as `pmg_main` (forced `.py` on disk) | `__import__("main")` — **compiled module from PYZ**, no file access; `pmg_main` alias preserved in `sys.modules` |

`MAIN_PY` no longer probes `_MEIPASS`/`isfile`; it is only consulted on the source path, so nothing in a frozen run reads `main.py` from disk. The returned object still exposes the identical surface (`_MAIN.APP_VERSION`, `PRAYERS`, `save_settings`, `media_toggle`, `player_hwnds`, …), so every `BackendAPI` method is untouched.

**Consequential fix — launcher Tkinter fallback (`webview_app/launcher.py`).**
The audit's removal of `main.py` from `datas` would have broken the frozen Tkinter fallback (Windows 7 / no-WebView2 / `PMG_FORCE_TK` / failed HTML startup), because it ran `runpy.run_path(MAIN_PY)` and first asserted `os.path.isfile(MAIN_PY)`. That was a genuine frozen-mode **disk dependency on `main.py`**, so it had to be fixed for this phase to be regression-free:

```python
def _run_tkinter_fallback(reason: str) -> None:
    _log("using Tkinter fallback: {0}".format(reason))
    if _frozen():
        # main.py is not shipped in the bundle. Run the compiled "main" module
        # from PYZ as __main__ — same entry semantics as runpy.run_path.
        runpy.run_module("main", run_name="__main__")
        return
    if not os.path.isfile(MAIN_PY):            # source-run guard kept as-is
        _log("main.py not found at {0}; cannot start".format(MAIN_PY))
        sys.exit(1)
    runpy.run_path(MAIN_PY, run_name="__main__")
```

Entry semantics are identical to the old frozen path (`run_path` of `_MEIPASS/main.py`): the code object executes with `__name__ == "__main__"`, `sys.argv[0]` and `__file__` both resolve to `_MEIPASS/main.py` (PyInstaller's PYZ origin), so the startup guard, single-instance mutex, tray and mainloop behave the same. Source-run behavior is byte-identical (guard + `run_path`).

---

## 3. Spec `datas` Changes (`PrayerMusicGuard.spec`)

Removed (application source — now compiled into PYZ via `hiddenimports`):

```python
(os.path.join(PROJECT_ROOT, "main.py"), ".")
(os.path.join(PROJECT_ROOT, "uiverse_combobox.py"), ".")
(os.path.join(WEBVIEW_APP, "launcher.py"), "webview_app")
(os.path.join(WEBVIEW_APP, "webview_main.py"), "webview_app")
(os.path.join(WEBVIEW_APP, "backend_api.py"), "webview_app")
(os.path.join(WEBVIEW_APP, "platform_check.py"), "webview_app")
```

Kept (required runtime resources — NOT removed):

```python
datas = [
    ("assets", "assets"),                                          # icons, audio, cities.json, countries.json
    (os.path.join(WEBVIEW_APP, "splash.html"), "webview_app"),     # startup splash
    (os.path.join(WEBVIEW_APP, "frontend"), os.path.join("webview_app", "frontend")),  # HTML/CSS/JS UI
]
# unchanged afterwards: collect_all("pystray") and collect_data_files("webview", subdir="js")
```

Net effect on the future COLLECT: 6 readable application `.py` files (≈ 291 KB: `main.py` 181,764 B, `uiverse_combobox.py` 33,753 B, `backend_api.py` 45,473 B, `launcher.py` 10,815 B, `platform_check.py` 5,815 B, `webview_main.py` 13,211 B) no longer land in the OneDir folder; the frontend, splash, all assets and all dependency data (pystray, webview/js) still do.

---

## 4. hiddenimports Preserved

Untouched, so all six modules still compile into `PYZ-00.pyz`:

```python
hiddenimports = [
    "webview", "clr", "clr_loader", "pystray",
    "main",            # <- webview_app/backend_api + launcher import it as a bare name
    "launcher",        # webview_app/launcher.py   (imported as `launcher` by app_entry)
    "app_entry",       # entry script
    "platform_check",  # webview_app/platform_check.py
    "backend_api",     # webview_app/backend_api.py
    "webview_main",    # webview_app/webview_main.py
    "uiverse_combobox",
]
```

Bare names are deliberate and match the import statements (`from backend_api import BackendAPI`, `import launcher`, `import main as _main`, `from uiverse_combobox import CountryCitySelector`); `pathex=[PROJECT_ROOT, WEBVIEW_APP]` makes them resolve identically in source and frozen modes. All six required modules are present (verified programmatically).

---

## 5. Source-Run Result

Live import from the project root (unfrozen branch executed — `exec_module` of `PROJECT_ROOT/main.py`):

```
SOURCE-RUN _MAIN is None: False
SOURCE-RUN _LOAD_ERROR: ''
SOURCE-RUN APP_VERSION: 1.2.7
SOURCE-RUN PRAYERS: ('Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha')
SOURCE-RUN MAIN_PY: E:\prayer-music-guard\main.py
SOURCE-RUN main.__name__: pmg_main
```

Development workflow is unchanged: edit `main.py`, re-run, changes apply without a build. `webview_app/test_webview.py` (source-mode `from backend_api import BackendAPI`) is covered by the same path.

---

## 6. Static Frozen-Import Verification

1. **Frozen branch never touches disk.** AST-level check of `_load_main`: the `if getattr(sys, "frozen", False):` branch contains exactly one import (`__import__("main")`) plus logging and the `pmg_main` alias — **no `exec_module` call, no `_MEIPASS` attribute access**.
2. **Mechanical frozen simulation.** Ran a subprocess with `sys.frozen = True` and `sys._MEIPASS` = a fresh **empty** temp dir (asserted `main.py` absent there):
   ```
   FROZEN-SIM _MAIN is None: False
   FROZEN-SIM _LOAD_ERROR: ''
   FROZEN-SIM module __name__: main            (compiled-module import, not pmg_main exec)
   FROZEN-SIM APP_VERSION: 1.2.7
   FROZEN-SIM pmg_main alias in sys.modules: True
   ```
   The bridge loads with no `main.py` on disk — the PYZ `hiddenimport` is the only requirement.
3. **Launcher fallback resolution without a file.** After `main` was already imported (as in the real launcher flow), `importlib.util.find_spec("main").loader.get_code("main")` returns a code object — that is exactly what `runpy.run_module` uses, so the Tkinter fallback starts without any `.py` on disk. (In the simulation the origin is the source file; in a real frozen build PyInstaller's importer supplies the same code object from PYZ with origin `_MEIPASS/main.py`.)
4. **`__file__` / asset resolution is unchanged in frozen mode.** Under PyInstaller a PYZ module's `__file__` is `_MEIPASS/main.py` — the same value the old data-file copy had — so `main.py`'s module-level `APP_DIR = Path(sys._MEIPASS)`, `ICON_PATH`, `PNG_ICON_PATH`, `AUDIO_DIR` and the `VENDOR` path logic behave identically. `launcher._instance_already_running()` (`import main as _main`) now resolves to the PYZ module instead of a disk module — functionally identical.

---

## 7. Static COLLECT Verification (requirement 6)

Parsed `PrayerMusicGuard.spec` with `ast` and evaluated the real `datas`/`hiddenimports` literals:

```
final literal datas list:
    assets -> assets
    webview_app/splash.html -> webview_app
    webview_app/frontend -> webview_app/frontend
RESULT datas:        PASS (none of main.py, uiverse_combobox.py, backend_api.py,
                        launcher.py, platform_check.py, webview_main.py)
RESULT hiddenimports: PASS (all six required modules present)
RESULT spec-text:     PASS (none of the six filenames appears anywhere in the spec)
```

Additional confirmations:

- `assets/` and `webview_app/frontend/` contain **zero** `.py` files, so the remaining directory-copy entries cannot ship application source indirectly.
- The only other `datas` contributors — `collect_all("pystray")` and `collect_data_files("webview", subdir="js")` — return dependency files only (public libraries), never the six application modules.
- `PrayerMusicGuard.spec` is the sole spec consumed by the release pipeline (`release.ps1:133` and `build_exe.bat:14` both invoke it; the other two `.spec` files are unused by the release).
- `main`, `launcher`, `backend_api`, `platform_check`, `webview_main` are never listed as `binaries`, `zipfiles`, or extra `a.datas` anywhere else in the spec.

Conclusion: the future COLLECT configuration will **not** intentionally copy `main.py`, `uiverse_combobox.py`, `webview_app/backend_api.py`, `webview_app/launcher.py`, `webview_app/platform_check.py`, or `webview_app/webview_main.py`.

---

## 8. Tests Performed (focused only)

Focused suite written for this phase — no app launch, no GUI, no network, no full build (kept outside the repo, per "focused tests only"): `C:\Users\slive\AppData\Local\Temp\opencode\test_phase20_46a.py`.

```
[PASS] 1.  syntax of the modified files (ast.parse on both .py + spec)
[PASS] 2.  source-run import loads main.py from disk (pmg_main, APP_VERSION 1.2.7)
[PASS] 3.  frozen-sim import of compiled main (empty _MEIPASS, pmg_main alias kept)
[PASS] 4.  launcher fallback: frozen -> runpy.run_module / source -> run_path; code resolvable
[PASS] 5a. datas contains none of the six application .py
[PASS] 5b. hiddenimports keeps all six modules
[PASS] 5c. no forbidden filename string anywhere in the spec
[PASS] 6a. _load_main frozen branch imports main (no exec_module, no _MEIPASS)  [AST]
[PASS] 6b. _run_tkinter_fallback checks _frozen() before any isfile(MAIN_PY)
[PASS] 6c. MAIN_PY computed without a filesystem probe (no isfile in _main_py)
[PASS] 7a. assets/ remains in datas (icons, audio, cities.json)
[PASS] 7b. splash.html + webview_app/frontend remain in datas
[PASS] 7c. main.py resolves assets via sys._MEIPASS
[PASS] 7d. webview_main frontend dir resolves via sys._MEIPASS

14/14 checks passed — ALL PHASE 20.46.A FOCUSED CHECKS PASSED
```

Also run: `python -m py_compile` on both edited modules and the spec (exit 0), and live imports of `launcher` + `app_entry` in source mode.

---

## 9. Regressions Checked

| Item | Check |
|---|---|
| Source-run bridge | Unchanged — `exec_module(PROJECT_ROOT/main.py)` as `pmg_main`; `_MAIN` populated, `_LOAD_ERROR` empty, `APP_VERSION=1.2.7` |
| Frozen bridge | `__import__("main")` from PYZ; `pmg_main` alias kept; all `BackendAPI` methods see the same module surface |
| Frozen Tkinter fallback | `runpy.run_module("main", run_name="__main__")` — same `__main__` entry, `argv[0]`, `__file__`; mutex/tray/mainloop unchanged |
| Single-instance probe | `launcher._instance_already_running()` unchanged (`import main as _main`) — resolves via PYZ |
| `app_entry` dispatch | Unchanged; `import launcher` / `import webview_main` resolve via PYZ by bare name |
| `_MEIPASS` asset paths | `main.py` (`APP_DIR`, icons, audio), `backend_api.get_cities` (`assets/data/cities.json`), `webview_main._frontend_dir` and `os.chdir(_MEIPASS)`, splash lookup — all still backed by remaining `datas` |
| Frontend / UI | No HTML/CSS/JS or Tkinter code touched; zero UI or behavior change |
| Stable Phase 20.44 build | Untouched — `dist\Phase20-44-Visual-Review\PrayerMusicGuard\PrayerMusicGuard.exe` and its folder intact |
| Existing releases | Not modified; no new build produced |
| Unrelated files | Only the three intended files carry today's mtime |

### Frozen-path residual `.py` lookups — verified harmless (documented, not changed)

- `launcher._webview_main()` still checks `_MEIPASS\webview_app\webview_main.py` under `_frozen()`. **Dead in frozen mode**: `WEBVIEW_MAIN` is used only in the `else` branch of `_run_html_frontend` (frozen spawns `sys.executable --webview-child`), so no frozen runtime path depends on `webview_main.py` on disk.
- `platform_check._probe_script_path()` computes a frozen path for `WEBVIEW2_PROBE_SCRIPT`. Consumed only by `webview2_probe_result()`, which is reachable solely from `platform_check.__main__` / `webview2_health_probe` — never invoked in the frozen EXE (entry is `app_entry.py`; the launcher calls only `can_use_html_frontend()`). No functional impact.

Both can be cleaned up in a later phase; leaving them avoids out-of-scope changes.

---

## 10. Explicitly NOT Done (phase boundary)

- **20.46.B** — PYZ encryption (`block_cipher`) — not started; `cipher=block_cipher` with `block_cipher = None` as before.
- **20.46.C** — Authenticode signing (`release.ps1`, `.iss`) — not started.
- **20.46.D** — hygiene: `*.bak`/loose `*.pyc`/`pystray\__pycache__` purge from COLLECT, `app.js.bak` (audit 2.3/2.5), WebView2 version pin, `diag_report` cap, `LOCAL_DIR` fallback. The audit also lists the `.bak`/`.pyc` purge under its 20.46.A step 4, but per this phase's defined scope ("remove the application `.py` files from the spec `datas` list; do not remove required frontend/assets/data files") it belongs with the 20.46.D hygiene work and is **deferred** — nothing here purges or excludes dependency/backup files.
- **20.46.E** — Cython/Nuitka assessment — not started; UPX/PyArmor/VMProtect explicitly rejected (packer + AV constraints), none used.
- No final release build (a full PyInstaller run + real-EXE review is the 20.46 gate, not this phase).

---

## 11. Verdict

**Phase 20.46.A — PASS**

- `_load_main()` imports the compiled `main` module from PYZ in frozen mode; no `sys._MEIPASS/main.py` + `exec_module`.
- The six application `.py` files are removed from `datas`; all required hiddenimports, frontend, asset and data files are preserved.
- No runtime code depends on `main.py` existing on disk in frozen mode (launcher fallback fixed; remaining `.py` lookups verified unreachable in frozen runtime).
- Source-run behavior, `_MEIPASS` asset resolution, UI and application behavior are unchanged.
- 14/14 focused checks pass; no regressions identified; stable Phase 20.44 build and existing releases untouched.

Remaining before the audit's CRITICAL 2.1 is fully closed at the bundle level: execute the release build and confirm the COLLECT output contains zero application `.py` (Phase 20.46 verification gate), then proceed to 20.46.B/C/D.

**STOP — Phase 20.46.A complete.**
