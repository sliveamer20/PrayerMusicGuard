# Phase 20.46.A — Verification Build ONLY

**Project:** `E:\prayer-music-guard`
**Date:** 2026-09-22
**Mode:** READ / BUILD / QA **only**. No source code was modified, no UI or behavior changed. A single new isolated build folder was created; every prior `dist\` build and every `releases\` entry was left untouched. Phases 20.46.B (PYZ encryption), 20.46.C (signing), 20.46.D (hygiene) and 20.46.E (Cython/Nuitka) were **not** started.

---

## 0. Headline Result

| Question | Answer |
|---|---|
| Build succeeded with the current `PrayerMusicGuard.spec`? | **YES** — PyInstaller exit 0, clean log |
| The six Phase 20.46.A `.py` files present in the bundle? | **NO — 0 of 6.** Zero application `.py` of any kind on disk |
| Real EXE starts? | **YES** — splash → launcher → WebView2 child, live `صلاة وسكون` window |
| pywebview bridge works? | **YES** — `window.pywebview.api`, 16 methods, live `get_state` round-trip |
| Prayer data / UI loads? | **YES** — 5 prayer cards (Arabic names + times), live next-prayer countdown |
| Save buttons + Phase 20.43 animation? | **YES** — all 3 buttons, exact Uiverse values, ~1 s, success-only; no animation on real backend rejection |
| Light/dark + RTL? | **YES** — both themes switch, `dir="rtl"`, `lang="ar"` |
| JS / runtime errors? | **NONE** — 0 CDP exceptions, 0 console.error, 0 error lines in the 2,162-line `webview.log` |
| Tkinter fallback (20.46.A-changed path)? | **YES** — frozen `runpy.run_module("main")` ran the full app with **no `main.py` on disk** |
| Phase 20.42/20.44 frozen-component regression | **PASS** — 0 harness errors; icons/buttons/radios/checkboxes/alerts/chip/WhatsApp all match 20.44 |
| **Overall** | **PASS** |

---

## 1. Build Result — PASS

| Item | Value |
|---|---|
| **Output path (exact)** | `E:\prayer-music-guard\dist\Phase20-46A-Verification\PrayerMusicGuard\PrayerMusicGuard.exe` |
| **EXE SHA-256** | `8035180C1A37F56B001F8EB697348F740CEC09741EC81EB485DACF4D6E706E37` |
| EXE size | 4,253,573 bytes (4.06 MB) |
| OneDir bundle | **1,022 files / 32,460,402 bytes (30.96 MB)** |
| Build mode | OneDir (`COLLECT`), current unmodified `PrayerMusicGuard.spec` |
| Toolchain | `win7\venv` — Python **3.8.10 x64** + **PyInstaller 5.13.2** (the pinned Win7 toolchain; verified by the same checks `release.ps1` runs) |
| Build command | `win7\venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --distpath "dist\Phase20-46A-Verification" --workpath "build\Phase20-46A-Verification" PrayerMusicGuard.spec` |
| Build exit code | 0 — log ends `Building COLLECT COLLECT-00.toc completed successfully.` |
| Isolation | A **new** `--distpath` and a **new** `--workpath`; `releases\` untouched, no version bumped, `release.ps1` not run |

`PYTHONNOUSERSITE=1` / `PYTHONPATH` cleared, exactly as `release.ps1` does for a real release build.

### Bundle accounting — the six modules moved from disk into PYZ

| Metric | Phase 20.44 build | Phase 20.46.A build | Delta |
|---|---|---|---|
| Files in `PrayerMusicGuard\` | 1,028 | 1,022 | **−6** |
| Total bundle bytes | 32,750,789 | 32,460,402 | −290,387 |
| `PrayerMusicGuard.exe` | 4,253,129 | 4,253,573 | **+444** |

The arithmetic closes exactly: the six removed on-disk `.py` files totaled 290,831 B in the 20.44 bundle, and the EXE grew by 444 B because their compiled bytecode is now embedded in the bundled `PYZ-00.pyz` (via the preserved `hiddenimports`). −290,831 + 444 = **−290,387**, and the file count drops by exactly 6. This is direct evidence the application modules now ship **only** as embedded bytecode, not as readable text.

---

## 2. Source-File Inspection — PASS

### Requirement 1 — the six Phase 20.46.A `.py` files are absent

Recursive search of `dist\Phase20-46A-Verification\PrayerMusicGuard\` for `main.py`, `launcher.py`, `webview_main.py`, `backend_api.py`, `platform_check.py`, `uiverse_combobox.py`:

```
PASS: none of the six application .py files present
```

### Requirement 2 — accidental shipped application source / loose `.py` / `.pyc`

```
new build, non-pystray .py count:  0     (stable 20.44 build: 6)
new build, pystray .py count:     13    (stable 20.44 build: 13 — identical)
```

The **only** `.py` files shipped are 13 files under `pystray\` — a **public third-party dependency** collected by the spec's `collect_all("pystray")`, byte-identical to the stable 20.44 build (pre-existing, audit §11 row 2 — "public library, not sensitive"). **Zero application source ships.**

Loose `.pyc`: 5 files under `pystray\__pycache__` (cpython-38) — also pre-existing dependency artifacts identical to the 20.44 build (audit finding **2.3**, deferred to Phase **20.46.D** hygiene; not a 20.46.A regression and not introduced here).

### Requirement 3 — required assets / frontend / data still present

| Path (relative to bundle root) | Present |
|---|---|
| `assets\icons\prayer_music_guard.ico` | YES |
| `assets\images\prayer-music-guard.png` | YES |
| `assets\data\cities.json` | YES |
| `assets\data\countries.json` | YES |
| `assets\audio\` (adhan WAV/MP3 per prayer) | YES — 10 files |
| `webview_app\splash.html` | YES |
| `webview_app\frontend\index.html` | YES |
| `webview\js\` (pywebview bridge resources) | YES — 4 files |

No frontend, asset or data file was removed.

---

## 3. Real-EXE Runtime Result — PASS

`PrayerMusicGuard.exe` launched with the documented WebView2 remote-debugging switch (`WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS=--remote-debugging-port=9501` — a **test-environment launcher setting only; no project file was modified**). The CDP harness (`reports\phases\phase20_46a_evidence\_verify.js`, reusing the project's existing `_cdp.js` client) drove the live frozen process. Automated score:

```
Total: 66   Passed: 66   Failed: 0
```

### Startup / WebView2 frontend

| Check | Result |
|---|---|
| Page target reachable (frontend `index.html`, pywebview loopback `127.0.0.1:19478`) | PASS |
| Window title `صلاة وسكون` | PASS |
| `document.readyState === "complete"` | PASS |
| Rendered content present (not blank) | PASS — 478–500 chars of body text |
| Frozen pipeline (splash → launcher → WebView2 child, 2 processes, ready flag) | PASS — `pmg_launcher.log` + `webview.log` |
| Frontend resolved from the bundle | PASS — `webview_app/frontend/index.html` under the bundle dir |

### Backend bridge

| Check | Result |
|---|---|
| `window.pywebview` + `window.pywebview.api` objects | PASS |
| Bridge methods | PASS — **16** (`get_state`, `save_settings`, `pause_now`, `resume_now`, `browse_player`, `browse_adhan`, `fetch_times`, `get_cities`, `list_running_apps`, `set_theme`, `set_autostart`, scheduler …) |
| Real `get_state()` round-trip | PASS — `ok=true`, **2–228 ms** |
| State payload | PASS — `version=1.2.7`, 5 prayers, `next` |

### Prayer data / UI

| Check | Result |
|---|---|
| 5 prayer cards rendered, keyed `Fajr..Isha` | PASS |
| Arabic names + 12h display times | PASS — `الفجر / الظهر / العصر / المغرب / العشاء`, `05:20 ص … 08:16 م` |
| Exactly one next prayer flagged | PASS — `Dhuhr` |
| Next-prayer ring populated + live countdown | PASS — `الظهر`, `12:53 م`, countdown ticking (e.g. `00:48:21`) |

### Save buttons + Phase 20.43 animation (real EXE, real backend, real mouse clicks)

All three save buttons (`#btn-save-times` / `#btn-save-music` / `#btn-save`), light theme, plus one dark-theme run — every check passed:

| Check | Result |
|---|---|
| Arabic label + `svg.save-anim` icon; icon hidden at rest | PASS (all) |
| `.is-saving` applied after a **real click, no hover** | PASS — 63–65 ms after click |
| Label hidden + icon shown during animation | PASS (all) |
| `animation-name: has-saved`, `iteration-count: 1` | PASS (all) |
| Easing `cubic-bezier(0.5, 0, 0.25, 1)` | PASS (all) |
| Duration `1s` (`--duration`) | PASS (all) |
| Zoom `1.75 / 0.75 / 1` | PASS (all) |
| Button becomes the square **40×40** icon container | PASS (all) — 40×40 (inner svg 28×28) |
| Animation lasts ~1 s | PASS — **953 / 1000 / 983 ms** (dark: 967 ms) |
| Original Arabic label restored; icon hidden; guard cleared (clickable again) | PASS (all) |
| Real backend save success | PASS — status `تم حفظ الإعدادات.` per button |
| Dark theme: identical animation | PASS — `has-saved / 1s / 967 ms / 40×40` |
| **Failed save → NO animation** | PASS — real backend validation rejection (`minutes=999` → `المدة من 1 إلى 180 دقيقة.`), no `.is-saving`, no guard, Arabic label intact, `is-error` status kept |

### Themes + RTL

| Check | Result |
|---|---|
| Light / dark switch via the app's own `pmgTheme.set()` | PASS — `data-theme` flips both ways; styling changes with it |
| RTL + Arabic document | PASS — `dir="rtl"`, `lang="ar"` |

### Errors / shutdown

| Check | Result |
|---|---|
| CDP `Runtime.exceptionThrown` | **0** |
| CDP `console.error` | **0** |
| Error-like lines in `webview.log` (whole 2,162-line log) | **0** |
| Clean shutdown (`CloseMainWindow`) | PASS — `webview.start() returned normally`, `HTML frontend closed cleanly`, 0 processes left |

### Harness corrections (harness bugs, not product defects — same discipline as Phase 20.44)

Three issues were found and fixed **in the verification harness only**; no project file was ever modified:

1. **Clicks missed hidden pages.** Each save button lives on its own page (`times` / `music` / `settings`); on an inactive page the rect is 0×0 so CDP mouse events missed. Fixed by navigating to each page first (the Phase 20.42 lesson).
2. **Failure injection was not restorable.** Overriding `window.pywebview.api.save_settings` persisted and could not be undone on pywebview's api proxy, contaminating the success path. Replaced with the app's **real** backend validation failure (invalid `minutes`) — no bridge override at all.
3. **Animation metrics measured on the wrong element.** The animation lives on `path[data-path="box"]`, the CSS vars on `svg.save-anim`, and the 40×40 box is the button itself. Measurement targets corrected.

After these harness fixes: **66/66 PASS**.

---

## 4. Frozen-Component Regression (existing Phase 20.42/20.44 checks) — PASS

The project's existing review script (`_review.js`, re-pointed at this build's debug port, run as `reports\phases\phase20_46a_evidence\_regress.js`) executed against the same live EXE: **`errors: []`**, exit 0.

| Component | Live measurement | vs Phase 20.44 |
|---|---|---|
| Lucide icons | **10**, logo **28×28**, nav **18.23**, chip **13.11**, `currentColor` strokes | identical |
| Buttons | 11 px radius, **43 px** row height, hover tint, real-cursor hover/active states | identical |
| Nav | 4 items, switching works | identical |
| Radios | 34×34 discs, 9 px dots | identical |
| Checkboxes | 16.89×17 boxes with checkmark pseudo-element | identical |
| Alerts | 4 variants (`is-success/is-info/is-warning/is-error`) with distinct token colors, 4 px bars | identical |
| Monitor chip | `chip chip--on`, **المراقبة تعمل**, 117.88×29.75, green icon | identical |
| WhatsApp button | 84×24, `transition: 0.5s`, hover animation | identical |
| Theme toggles + RTL | dark↔light both stick; `dir="rtl"`, `lang="ar"` | identical |

Live-EXE screenshots captured: `reports\phases\phase20_46a_evidence\` (`normal_light.png`, `normal_dark.png`, `anim_mid_light.png`, plus the regression suite's captures).

---

## 5. Tkinter Fallback (the 20.46.A-changed frozen path) — PASS

The project's supported fallback (`PMG_FORCE_TK=1`, read by `launcher.main()`) was used. In frozen mode this now executes `runpy.run_module("main", run_name="__main__")` — the exact code Phase 20.46.A changed — with **no `main.py` anywhere in the bundle**:

| Check | Result | Evidence |
|---|---|---|
| Fallback taken | PASS | `pmg_launcher.log`: `using Tkinter fallback: PMG_FORCE_TK set` |
| Tk window appeared | PASS | 1 process, `MainWindowTitle = "صلاة وسكون - v1.2.7"`, `Responding=True` |
| **main ran as `__main__` from PYZ in frozen mode** | **PASS** | `prayer-music-guard.log`: `Application starting: PrayerMusicGuard v1.2.7 (frozen run, python 3.8.10)` |
| Full app startup (mutex → tray → monitoring) | PASS | `Tray icon loaded from PNG: <bundle>\assets\images\prayer-music-guard.png`, `Monitoring started`, `Monitoring tick #1 … next prayer Dhuhr at 12:53` |
| Bundle assets resolve in the fallback too | PASS | tray PNG resolved from inside the bundle |
| Clean termination | PASS | 0 processes after close |

This directly proves the Phase 20.46.A launcher change: the frozen Tkinter fallback needs no on-disk `main.py`.

---

## 6. No Side Effects

- **Prior builds untouched** — every `dist\Phase20-*` folder and `releases\v*` entry retains its original timestamp; the stable 20.44 EXE is still 4,253,129 B stamped 2026-09-22 00:02. Only the new `dist\Phase20-46A-Verification` was created.
- **No source modified** — `main.py`, `uiverse_combobox.py`, `webview_app\*`, `PrayerMusicGuard.spec`, `release.ps1`, `.iss` all unchanged (READ/BUILD/QA only).
- **User settings** — prayer times, player path, enabled flag unchanged; the theme-toggle tests flipped `settings.json` `theme` to `light`, which was **restored to `dark`** (pre-test value) with the app's own atomic serialization. No other state was written by testing.
- **No 20.46.B/C/D/E work** — `block_cipher` untouched (`None`), no signing, no packers, no Cython/Nuitka.

---

## 7. Errors Encountered

| # | Issue | Nature | Resolution |
|---|---|---|---|
| 1 | Save-button clicks produced no animation (run 1) | Harness — buttons on inactive pages have 0×0 rects | Navigate to each page before clicking |
| 2 | Success-path saves returned failure on re-run (run 2) | Harness — pywebview api-proxy override could not be restored | Use the app's real validation failure instead of a bridge override |
| 3 | Animation name/easing/duration/box measured wrong (run 3) | Harness — measured the button instead of `path`/`svg` | Measure `path[data-path="box"]`, `svg.save-anim`, button box |

All three were harness defects, diagnosed and corrected in the evidence scripts only. **No product defect was found.** Per phase rules, nothing was fixed in the application source.

---

## 8. Verdict

**Phase 20.46.A verification build — PASS**

- The current `PrayerMusicGuard.spec` builds cleanly with the pinned Win7 toolchain (Python 3.8.10 x64 + PyInstaller 5.13.2).
- The frozen OneDir bundle contains **zero** application `.py` files (all six removed from disk; present only as embedded PYZ bytecode), while every required frontend/asset/data file is present.
- The real EXE starts, renders the WebView2 frontend, exposes a live 16-method bridge, serves real `get_state` data with the prayer UI, runs the Phase 20.43 save animation exactly on all three save buttons (success-only, both themes, RTL), reports a real backend validation failure with no animation, and shows **zero** JS/runtime errors.
- The frozen Tkinter fallback runs the compiled `main` from PYZ with no `main.py` on disk.
- All applicable Phase 20.42/20.44 frozen-component regression measurements match the stable build.
- No source file, prior build, release, or UI behavior was changed.

Remaining gates before the audit's CRITICAL 2.1 is fully closed (future phases): the `.pyc`/`.bak` hygiene purge (20.46.D), PYZ encryption (20.46.B), and code signing (20.46.C).

**STOP — verification complete. Not continuing to Phase 20.46.B.**

---

### Appendix — verification artifacts

| Artifact | Path |
|---|---|
| Report | `reports\phases\PHASE20_46A_VERIFICATION_BUILD.md` |
| CDP verification script (66 checks) | `reports\phases\phase20_46a_evidence\_verify.js` |
| Verification result JSON | `reports\phases\phase20_46a_evidence\verify_result.json` |
| Regression script (existing 20.42 suite) | `reports\phases\phase20_46a_evidence\_regress.js` |
| Regression result JSON | `reports\phases\phase20_46a_evidence\review_result.json` |
| Live-EXE screenshots | `reports\phases\phase20_46a_evidence\*.png` |
| Build output | `dist\Phase20-46A-Verification\PrayerMusicGuard\` |
| Launcher log | `%TEMP%\pmg_launcher.log` |
| WebView log | `%APPDATA%\PrayerMusicGuard\webview.log` (2,162 lines, 0 errors) |
| App log (Tkinter fallback) | `%APPDATA%\PrayerMusicGuard\prayer-music-guard.log` |
