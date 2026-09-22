# PHASE 20.44 — BUILD + REAL EXE VISUAL REVIEW

**Project:** `E:\prayer-music-guard`
**Date:** 2026-09-22
**Phase:** 20.44 — Build the CURRENT project state (post Phase 20.43) into ONE new independent OneDir build, launch the REAL EXE, and visually review Phases 20.40 (Lucide icons), 20.41 (Park UI buttons) and 20.43 (Uiverse "Saved" save-animation), plus all frozen components.
**Mode:** Build + launch + visual verification only. **No source/UI code was modified and nothing was fixed.** A new isolated build folder was created; every prior `dist\` build and `releases\` entry was left untouched.

---

## 0. Headline Result

| Question | Answer |
|---|---|
| Did the build succeed? | **YES** — PyInstaller exit 0, clean log |
| Does the real EXE start? | **YES** — splash → launcher → WebView2 child, live `صلاة وسكون` window, full frozen pipeline |
| pywebview bridge works? | **YES** — `window.pywebview.api` object, 16 methods, live `get_state` round-trip in 205 ms |
| JS / runtime errors? | **NONE** — 0 CDP exceptions, 0 console errors, 0 error lines in the 2,048-line `webview.log` |
| 20.40 Lucide icons in frozen EXE? | **YES** — 10 icons, all with vector geometry (logo 28×28, nav 18.23, chip 13.11), both themes |
| 20.41 Park UI buttons? | **YES** — 14 buttons, 43px row height, 11px radius, hover tint confirmed live |
| **20.43 Save animation?** | **YES — 130/130 checks pass.** All 3 save buttons: exact Uiverse animation on success only, ~1s, once, no hover, text restored, clickable again; **no animation on failure** |
| Clean shutdown? | **YES** — `CloseMainWindow()` → 0 processes; `webview.start() returned normally` in log |
| **Overall** | **PASS — zero defects found** |

---

## 1. Build Result — PASS

| Item | Value |
|---|---|
| **Output path (exact)** | `E:\prayer-music-guard\dist\Phase20-44-Visual-Review\PrayerMusicGuard\PrayerMusicGuard.exe` |
| **EXE SHA-256** | `C8DBF268CF48C0AF23022FF54AFE9CB952FB35F5B94F3087532B19840B23DC6F` |
| EXE size | 4,253,129 bytes (4.06 MB) |
| OneDir bundle | **1,028 files / 32,750,789 bytes (31.23 MB)** — folder `PrayerMusicGuard\` |
| Build mode | OneDir (`COLLECT` in `PrayerMusicGuard.spec`), identical to the project's established build |
| Toolchain | `win7\venv` — Python **3.8.10 x64** + **PyInstaller 5.13.2** (the pinned Windows 7 toolchain) |
| Build command | `win7\venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --distpath "dist\Phase20-44-Visual-Review" PrayerMusicGuard.spec` |
| Build exit code | 0 (clean log: `Building COLLECT COLLECT-00.toc completed successfully.`) |
| Built at | 2026-09-22 00:02 (local) |
| Source version | `VERSION` = 1.2.7 (unchanged); `PrayerMusicGuard.iss` untouched; `release.ps1` **not** run |

The build used the project's own spec and build system (`build_exe.bat` / `release.ps1` pattern) with only a **new** `--distpath`. Nothing was archived under `releases\` and no version was bumped.

### Bundle integrity — PASS

The three files changed in Phase 20.43 are **byte-identical (SHA-256)** between source and the frozen bundle, so the shipped frontend is exactly the post-20.43 state:

| File | Source ↔ Frozen |
|---|---|
| `webview_app\frontend\index.html` | **MATCH** |
| `webview_app\frontend\css\skins.css` | **MATCH** |
| `webview_app\frontend\js\app.js` | **MATCH** |

Full pre-build source hash snapshot: `reports\phases\phase20_44_prebuild_hashes.csv` (14 files). The pywebview bridge resources (`webview\js\*.js`) are bundled via the spec's explicit `collect_data_files('webview', subdir='js')` — the frozen `window.pywebview` bridge is present and **proven live at runtime** in §2.

### Prior builds untouched — PASS

`dist\Phase20-28-Release`, `dist\Phase20-36-Visual-Review`, `dist\Phase20-38-Visual-Review`, `dist\Phase20-42-Visual-Review` (EXE still stamped 2026-09-21 11:33) and all `releases\` entries are unmodified. Only `dist\Phase20-44-Visual-Review` was created.

---

## 2. Real-EXE Launch & Startup — PASS

`PrayerMusicGuard.exe` was launched from the new bundle with the documented WebView2 remote-debugging switch (`WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS=--remote-debugging-port=9488` — a **test-environment launcher setting; no project file was modified**). The complete frozen pipeline executed:

| Check | Result | Evidence |
|---|---|---|
| Splash → launcher → WebView2 child | PASS | `Splash page loaded` → `HTML splash completed successfully` (`pmg_launcher.log`) |
| HTML frontend started | PASS | `starting HTML frontend (WebView2)` → `HTML frontend ready; waiting for window to close` |
| WebView2 runtime | PASS | `Starting webview gui=edgechromium`, Edge/153.0.4234.48 via CDP `Browser` header |
| Window created + scheduler | PASS | `Scheduler started` / `Closed event handler attached` (`webview.log`) |
| Ready flag | PASS | written 0.6 s after window creation |
| Live window on screen | PASS | 2 PrayerMusicGuard processes (parent launcher + WebView2 child, by design), `Responding=True`, CDP page target `http://127.0.0.1:31969/index.html`, title `صلاة وسكون` |
| Rendered content (not blank) | PASS | 470 chars of rendered body text; full-window PNGs 81–88 KB captured |
| **pywebview bridge live** | **PASS** | `typeof window.pywebview === "object"`, `typeof window.pywebview.api === "object"`, **16 API methods** incl. `save_settings`, `get_state`, `browse_player`, `pause_now`, `toggle_pause`, `set_autostart` … |
| **Real backend round-trip** | **PASS** | `get_state()` returned `ok,version,prayers,next,enabled,announce,autostart,music,adhan,minutes,method,theme` in **205 ms** |
| **JS / runtime errors** | **PASS** | 0 CDP `pageerror`, 0 `console.error`, **0 error-like lines across the entire 2,048-line `webview.log`** |
| Clean shutdown | PASS | `CloseMainWindow()` → 0 processes left; log ends `webview.start() returned normally` + `HTML frontend closed cleanly` |

---

## 3. Phase 20.40 — Lucide Icons — PASS

Measured live in the frozen EXE over CDP (every page visited so all icons are visible):

| Check | Result |
|---|---|
| Icon count | **10** `svg.icon` elements |
| Vector geometry present | **10/10** (path/rect/circle/line/polygon ≥ 1 each) |
| Visible icons sized | logo **28×28**, nav icons **18.23×18.23**, monitor-chip icon **13.11×13.11** |
| Stroke = `currentColor` | **10/10** (theme-aware, no hardcoded colors) |
| Both themes | PASS — light + dark verified |

Note: the dashboard "layout" icon uses four `<rect>` elements rather than `<path>` — this is valid Lucide geometry and renders correctly.

## 4. Phase 20.41 — Park UI Buttons — PASS

| Check | Result |
|---|---|
| Button count | **14** `.btn` elements |
| Border radius | 11px (`--radius-ctrl`) on all |
| Visible row height | **43px** (Park UI spec target) |
| Park UI hover state | PASS — live bg change to `color(srgb 0.13 0.16 0.22)` accent tint on hover |
| 3 save buttons with Arabic labels | PASS — `حفظ المواقيت` / `حفظ إعدادات المشغّل` / `حفظ الإعدادات` |
| Both themes | PASS |

## 5. Phase 20.43 — Save Animation (REAL EXE, real backend) — PASS

This is the core of the phase. All three save buttons were clicked in the **live frozen EXE**, through the **real** `window.pywebview.api.save_settings` bridge (no stub), in **light + dark** themes, with every Uiverse value read from computed style.

### Per-button results (5 runs: times/light, settings/light, music/light, times/dark, settings/dark)

| Check | Result |
|---|---|
| Arabic text visible at rest | PASS — `حفظ المواقيت` / `حفظ الإعدادات` / `حفظ إعدادات المشغّل` |
| Not animating at rest; icon `display:none` | PASS (all runs) |
| **Success → `.is-saving` applied with NO hover** | PASS — 249–285 ms after click (pure click trigger) |
| Label hidden + Saved icon shown during anim | PASS (all runs) |
| **Easing** | PASS — `cubic-bezier(0.5, 0, 0.25, 1)` (computed `animation-timing-function`) |
| **Zoom** 1.75 / 0.75 / 1 | PASS — `--zoom-from 1.75`, `--zoom-via 0.75`, `--zoom-to 1` |
| **Duration** | PASS — `--duration 1s` + computed `animation-duration 1s` |
| **Animation name + once** | PASS — `has-saved`, `animation-iteration-count: 1` |
| Icon container square | PASS — exactly **40×40 px** on every run |
| No double animation on rapid re-click | PASS — mid-animation re-click does not restart (guard flag) |
| **Animation lasts ~1s** | PASS — measured **992 / 998 / 998 / 1015 / 1016 ms** |
| Original Arabic text restored | PASS (all runs) |
| Icon hidden again after anim | PASS (all runs) |
| Clickable again (guard cleared) | PASS (all runs) |
| No layout shift of surrounding controls | PASS — button width restored to 132–182 px, button row 535×43 stable |

### Failed save — PASS

`save_settings` was made to return a realistic backend failure (`{ok:false, error:"simulated backend failure"}` — matching how the real backend reports failure, since `call()` at app.js:520 converts a throw into `{ok:false}`):

| Check | Result |
|---|---|
| **Saved animation must NOT appear** | PASS — no `.is-saving` class, no guard flag |
| Arabic label intact | PASS — `حفظ الإعدادات` unchanged |
| Existing error/status behavior kept | PASS — `تعذر الحفظ: simulated backend failure` with `card__hint is-error` |

### Theme + RTL — PASS

- **Light theme:** all checks pass.
- **Dark theme:** all checks pass (identical measured values).
- **RTL:** `dir="rtl"`, `lang="ar"` on `<html>`; layout direction preserved during the animation; icon container stays square; surrounding controls unaffected.

### Visual evidence

Screenshots captured from the **live EXE** at `reports\phases\phase20_44_shots\`: `normal_{light,dark}.png`, `anim_icon_{light,dark}.png`, `anim_full_{light,dark}.png`, `restored_{light,dark}.png`. SHA-1 digests confirm **normal ≠ anim ≠ restored** for both themes — the animation genuinely renders and the UI genuinely returns to the text state.

---

## 6. Frozen Components — PASS

| Component | Result |
|---|---|
| **WhatsApp button + hover animation** | PASS — 84×24, `transition: 0.5s` hover animation present |
| **Alert / message UI** | PASS — `is-error` vs `is-success` use distinct token colors (`color(srgb .63 .17 .17)` / `color(srgb .06 .50 .37)`) |
| **Checkboxes** | PASS — 16 total, visible 17×17 boxes with checkmarks |
| **Radios** | PASS — 16 total, visible 34×34 discs |
| **Lucide sidebar icons** | PASS — §3 |
| **Dropdown icons** | PASS — present with vector geometry |
| **Monitor chip** | PASS — 118×30, live text `المراقبة تعمل` |
| **Theme switch** | PASS — toggles light → dark → light (real `data-theme` change) |
| **Navigation** | PASS — 4 items, page switching works |
| **Pause/resume buttons** | PASS — `btn-pause`, `btn-resume`, `btn-pause-2`, `btn-resume-2` all present |
| **No clipping during animation** | PASS — svg `overflow: visible`, renders non-zero, nearest card does not clip |
| **No layout shift to surrounding controls** | PASS — row width/height stable, all neighbors keep positions |

---

## 7. Automated Score

The real-EXE review harness executed **130 checks** against the live frozen process:

```
Total: 130   Passed: 130   Failed: 0
```

Two initial "failures" were harness artifacts, not product defects, and were corrected in the harness (never in the product):
1. Lucide icons on **hidden pages** measured 0×0 — fixed by visiting each page before measuring.
2. The failure-injection initially used a *rejected promise*, which is not how the backend fails; `call()` converts a sync throw to `{ok:false}`. Re-modelled as `{ok:false}` — the app's real failure path.

No source file, stylesheet, script or Python module was modified at any point in this phase.

---

## 8. Defects Found

**None.** Build, frozen pipeline, bridge, backend, all three save-button animations (success + failure paths), both themes, RTL, and every frozen component are clean. Zero JS/runtime errors.

**Review complete. No changes made. Stopping here.**

---

### Appendix — verification artifacts

| Artifact | Path |
|---|---|
| Report | `reports\phases\PHASE20_44_BUILD_VISUAL_REVIEW.md` |
| Pre-build source hashes | `reports\phases\phase20_44_prebuild_hashes.csv` |
| Live-EXE screenshots | `reports\phases\phase20_44_shots\` (8 PNGs) |
| Launcher log | `%TEMP%\pmg_launcher.log` |
| WebView log | `%APPDATA%\PrayerMusicGuard\webview.log` (2,048 lines, 0 errors) |
| Build dir | `dist\Phase20-44-Visual-Review\PrayerMusicGuard\` |
