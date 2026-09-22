# PHASE 20.42 — Build & Visual Review Report

**Project:** `E:\prayer-music-guard`
**Date:** 2026-09-21
**Phase:** 20.42 — Build the CURRENT project state (post Phase 20.41) into a new independent OneDir build, launch the real EXE, and visually review every component changed in Phases 20.40 (Lucide icons) and 20.41 (Park UI button refresh), plus the frozen components (radios, checkboxes, WhatsApp button, alerts, theme switch).
**Mode:** Build + launch + visual verification only. **No source/UI code was modified and nothing was fixed.** A new isolated build folder was created; `dist\Phase20-28-Release`, `dist\Phase20-36-Visual-Review`, `dist\Phase20-38-Visual-Review` and every prior release were left untouched.

---

## 0. Headline Result

| Question | Answer |
|---|---|
| Did the build succeed? | **YES** — PyInstaller exit 0, no errors |
| Does the real EXE start? | **YES** — full frozen pipeline runs, live `صلاة وسكون` window, `Responding=True`, real `window.pywebview` bridge attached |
| JS / runtime errors? | **NONE** — 0 CDP exceptions, 0 console errors, 0 error lines in `webview.log` (whole 1,990-line log) |
| 20.40 Lucide icons render in the frozen EXE? | **YES** — all 10 icons paint with real geometry (logo 28×28, nav 18.23, chip 13.11) in **both themes** |
| 20.41 buttons render? | **YES** — all **14 buttons** measured; 43px row height, hover lift + tint + glow, active pressed, disabled 0.7/0.55, outside focus ring |
| Dropdown IconButtons? | **YES** — both exactly **40×40 square**, chevrons centered, menu opens |
| Combobox arrows? | **YES** — both **32×32 square**, hover tint, click opens the menu, city arrow disabled correctly |
| Nav states? | **YES** — 4 items, accent `::before` bar `opacity 1`, hover 8% tint, active 14% tint, RTL preserved |
| Monitor chip ON/OFF? | **YES** — real round-trip through the app's own settings path: ON → `chip--on`/`المراقبة تعمل`, OFF → `chip--off`/`المراقبة متوقفة`, restored |
| Frozen (radios/checkboxes/WhatsApp/alerts)? | **YES** — 34×34 discs + 9px dots, 17×17 boxes + accent checkmarks, 84×24 WhatsApp with full hover sequence, 4 alert types with distinct token colors |
| **Overall** | **PASS** — build, runtime and visual review all clean; **zero defects found** |

---

## 1. Build Result — PASS

| Item | Value |
|---|---|
| **Output path (exact)** | `E:\prayer-music-guard\dist\Phase20-42-Visual-Review\PrayerMusicGuard\PrayerMusicGuard.exe` |
| **EXE SHA-256** | `25444A97DE788811BC00AC6F4798D0756691F14DDE998EB2B697C26766C0D07B` |
| EXE size | 4,253,144 bytes |
| OneDir bundle | **1,028 files / 32,744,781 bytes (31.23 MB)** — folder `PrayerMusicGuard\` |
| Build mode | OneDir (`COLLECT` in `PrayerMusicGuard.spec`) — identical to the project's established build |
| Toolchain | `win7\venv` — Python **3.8.10 x64** + **PyInstaller 5.13.2** (the pinned Windows 7 toolchain; `vendor\` Python never used) |
| Build command | `win7\venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --distpath "dist\Phase20-42-Visual-Review" PrayerMusicGuard.spec` |
| Build exit code | 0 (clean log: `Building COLLECT COLLECT-00.toc completed successfully.`) |
| Built at | 2026-09-21 11:33 (local) |
| Source version | `VERSION` = 1.2.7 (unchanged); `PrayerMusicGuard.iss` untouched; `release.ps1` **not** run |

The build used the project's own spec and build system (`build_exe.bat` / `release.ps1` pattern), only with a **new** `--distpath`. Nothing was archived under `releases\` and no version was bumped.

### Bundle integrity — PASS

All 13 shipped data files are **byte-identical (SHA-256)** to the pre-build source snapshot (`reports\phases\phase20_42_prebuild_hashes.csv`), so the frozen frontend is exactly the post-20.41 UI state:

`main.py`, `uiverse_combobox.py`, `webview_app\{backend_api.py, launcher.py, platform_check.py, splash.html}`, `webview_app\frontend\{index.html, js\app.js, js\theme.js, css\components.css, css\layout.css, css\skins.css, css\theme.css}` — **13/13 MATCH**.

The pywebview bridge resources (`webview\js\{api,customize,finish,state}.js`, `lib\{dom_json,polyfill}.js`) are bundled via the spec's explicit `collect_data_files('webview', subdir='js')`, so the frozen `window.pywebview` bridge is present — **proven at runtime** in §2 (bridge type `object`, 16 API methods, live `get_state` round-trip in 205 ms).

---

## 2. Real-EXE Launch & Startup — PASS

`PrayerMusicGuard.exe` was launched from the new bundle with the documented WebView2 remote-debugging switch (`WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS=--remote-debugging-port=9477` — a **test-environment launcher setting; no project file was modified**). The complete frozen pipeline executed:

| Check | Result | Evidence |
|---|---|---|
| Splash → launcher → WebView2 child | PASS | `Starting HTML frontend initialization` → `Configuring WebView2` (`webview.log`) |
| BackendAPI bridge created & attached | PASS | `BackendAPI instance created` / `js_api attached to window` (`webview.log`) |
| Single-instance guard | PASS | `Single-instance guard: acquired (first instance)` |
| Frontend resolved from the new bundle | PASS | `Using relative frontend URL: webview_app/frontend/index.html (resolved from …\dist\Phase20-42-Visual-Review\PrayerMusicGuard\…)` |
| Window created + scheduler started | PASS | `Window created successfully` → `Scheduler started` → `Closed event handler attached` |
| WebView2 runtime | PASS | resolved from registry to `153.0.4234.48`, `gui=edgechromium`, storage path under `%APPDATA%\PrayerMusicGuard\webview2_data` |
| Ready flag | PASS | written ~0.6 s after window creation |
| Live window on screen | PASS | window **900×760** (884×721 client), title `صلاة وسكون`, process `Responding=True`, real CDP page target `ws://127.0.0.1:9477/devtools/page/…` |
| Rendered content (not a blank window) | PASS | **84,382-byte (light) and 91,446-byte (dark) full-window PNGs** captured from the live process |
| **pywebview bridge live in the frozen EXE** | **PASS** | `typeof window.pywebview === "object"`, `typeof window.pywebview.api === "object"`, 16 API methods (`browse_player`, `fetch_times`, `get_state`, `pause_now`, `save_settings`, `set_autostart`, `toggle_pause`, …) |
| Real API round-trip | PASS | `get_state()` → `{ok: true, enabled: true, version: "1.2.7"}` in **205.1 ms** |
| App boot state | PASS | `readyState: complete`, 5 prayer cards rendered, sidebar version `1.2.7`, `dir="rtl"`, `lang="ar"`, 4 nav items / 4 pages, dashboard active |
| **Error hits in `webview.log`** | **0** | whole-log scan: 1,990 lines, **zero** `error/failed/traceback/exception/unavailable` matches |
| Clean shutdown | PASS | `WM_CLOSE` (CloseMainWindow) → **0 leftover processes** |

---

## 3. Visual Review Method

The review ran against the **live EXE window** over CDP (Edge `153.0.4234.48`), with a zero-dependency Node client (`reports\phases\phase20_42_evidence\_cdp.js`).

Measurements: `Runtime.evaluate` for computed styles and used boxes, `Page.captureScreenshot` for element-region crops, and **real `Input.dispatchMouseEvent` cursor moves** to engage CSS `:hover` (synthetic JS events cannot), plus a **real `Tab` keypress** to engage `:focus-visible`. Every assertion below is a **measured computed style or a measured box**, not an impression. Direct image viewing is not available in this environment; PNGs are archived for human review.

Two CSS transition behaviors had to be accounted for, each of which initially produced a false reading that was root-caused to the harness, not the product:
- `.card__hint` has `transition: border-color 300ms`; reading the bar color in the same task as the class change returns an interpolated value, so all four alert types initially measured identical. After settling, each type resolves its own token (§4.10).
- `.btn` has `transition: opacity 200ms`; the disabled probe initially read `opacity: 1` mid-transition. After settling, accent is `0.7` and outline `0.55` (§4.2).

**Review total: 74 / 74 checks PASS.**

---

## 4. Per-Component Visual Results

### 4.1 Phase 20.40 — Lucide icons — PASS

| Check | Result | Measured (light / dark identical) |
|---|---|---|
| Icon count on screen | PASS | 10 inline `.icon` SVGs |
| Sidebar logo (moon) | PASS | **28 × 28 px**, painted geometry 18 units |
| Nav icons ×4 (dashboard/times/music/settings) | PASS | **18.23 × 18.23 px** each (1.15em @ 0.95rem tile) |
| Monitor chip icon | PASS | **13.11 × 13.11 px** (1em @ 0.82rem) |
| `stroke: currentColor` follows theme | PASS | icon color = `rgb(255,255,255)` dark / `rgb(11,14,21)` light (=`--fg`) |
| Icons visible in both themes | PASS | measured in light **and** dark |

### 4.2 Phase 20.41 — Buttons (all 14) — PASS

| Check | Result | Measured |
|---|---|---|
| Total buttons found (4 pages) | PASS | **14** — 5 `btn--accent` + 9 outline |
| Full inventory | PASS | dashboard `btn-pause`(accent)/`btn-resume`; times `btn-save-times`(accent)/`btn-fetch-times`/`btn-fetch-location`(accent); music `btn-dropdown-music`(icon)/`btn-browse-music`/`btn-dropdown-adhan`(icon)/`btn-pause-2`(accent)/`btn-resume-2`/`btn-save-music`; settings `btn-save`(accent)/`btn-refresh-state` |
| Uniform height (no grid reflow) | PASS | **43 px** every text button (40px `min-height` + 2×1px border), widths 89.77–181.73 by label |
| Recipe base | PASS | `display: flex` (inline-flex), `align-items: center`, `justify-content: center`, `gap: 8px`, `font-weight: 600`, `white-space: nowrap`, `user-select: none`, `padding: 10px 18px`, `border-radius: 11px` |
| Transitions | PASS | `background-color, border-color, color, box-shadow, transform, opacity` all present |
| **Hover (real cursor)** | **PASS** | outline: bg → accent 7% tint, border → accent 55%, glow `0 2px 8px -4px`, `translateY(-1px)`; accent: gradient → `--accent-hover`, glow 12→14px, `translateY(-1px)` — `matches(':hover') === true` |
| **Active (real press)** | **PASS** | outline: bg → accent 13%, border → solid accent, shadow removed, lift cancelled; accent: gradient back to `--accent`, glow → 8px |
| Restores after cursor leaves | PASS | byte-for-byte back to base (bg, border, shadow, transform) |
| **Disabled (settled)** | **PASS** | accent `opacity 0.7`, outline `opacity 0.55`, both `cursor: not-allowed`, `box-shadow: none`, `transform: none` — light **and** dark |
| **Focus ring (real Tab)** | **PASS** | `:focus-visible` true, `outline: none`, `box-shadow: 0 0 0 2px <surface>, 0 0 0 4px <accent>` — light `rgb(255,255,255)+rgb(47,109,246)`, dark `rgb(28,31,40)+rgb(111,157,255)` |
| Accent solid styling | PASS | `linear-gradient(150deg, var(--accent), …)`, `color: var(--accent-text)`, transparent border, accent glow |

### 4.3 Dropdown IconButtons — PASS

| Check | Result | Measured |
|---|---|---|
| `#btn-dropdown-music` / `#btn-dropdown-adhan` | PASS | both **40 × 40 px**, `square: true`, `padding: 0`, `min-width: 40px`, `flex: 0 0 auto`, `align-self: center` |
| Chevron centered | PASS | icon 18.39 px, centered on both axes (≤1.5px tolerance) |
| Button opens its dropdown | PASS | click → menu `opened: true` |
| Backend app list resolves | PASS | real `list_running_apps()` → `{ok: true, count: 35}` |
| Empty-state rendering | PASS | with no matching player the menu shows the app's own `dropdown-empty` message ("لا توجد تطبيقات مطابقة") — correct backend filtering, not a defect |

### 4.4 Combobox arrows — PASS

| Check | Result | Measured |
|---|---|---|
| Both `.combobox__arrow` | PASS | **32 × 32 px** each, `square: true`, `padding: 0`, `border-radius: 8px`, chevron 16.55 px centered |
| Hover (real cursor) | PASS | bg → accent 10% tint, color → `--accent`, `matches(':hover') === true` |
| Click opens menu | PASS | `wasHidden: true` → `nowHidden: false` |
| City arrow disabled | PASS | `disabled: true` until a country is chosen (unchanged app logic) |

### 4.5 Nav items — PASS

| Check | Result | Measured |
|---|---|---|
| 4 items, Arabic labels | PASS | `لوحة القيادة` / `المواقيت` / `المشغّل` / `الإعدادات` |
| Active page | PASS | correct `is-active` page, bg accent 14%, color `--accent`, border accent 34% |
| **Accent indicator bar** | **PASS** | `::before` `opacity: 1`, `width: 3px`, `background: var(--accent)` — the 20.39-preserved bar |
| Hover (real cursor) | PASS | bg → accent 8% tint, `matches(':hover') === true` |
| Active surface | PASS | bg → accent 14% tint |
| RTL | PASS | `dir="rtl"`, nav icon box **start-side** of the label (`iconX > labelX`); indicator uses `inset-inline-start` |

### 4.6 Monitor chip — PASS

Driven through the app's **own** path: `save_settings({enabled})` → `#btn-refresh-state` click → `refresh()` → `applyState()` → `renderStatus()`.

| Check | Result | Measured |
|---|---|---|
| ON state | PASS | `chip chip--on`, text `المراقبة تعمل`, icon span + text span present, `color: rgb(15,157,110)` = `--success` light / `rgb(69,214,162)` dark |
| Badge layout | PASS | `display: flex`, `gap: 6px`, `border-radius: 999px`, `padding: 6px 12px`, `line-height: 1.2`, `white-space: nowrap`, **117.88 × 29.73 px** |
| **OFF transition** | **PASS** | `chip chip--off`, text `المراقبة متوقفة`, color/icon → `rgb(102,112,144)` = `--muted` |
| Restores to ON | PASS | back to `chip chip--on` |
| Lucide status icons swap | PASS | ON = `circle-check`, OFF = `circle-off` (from 20.40) |

### 4.7 Radios (frozen) — PASS

| Check | Result | Measured |
|---|---|---|
| 4 radios in 2 groups | PASS | `location_mode` (auto/manual, times page) + `method` (suspend/media, music page) |
| Container size | PASS | **34 × 34 px** each |
| Disc | PASS | 34×34, `border-radius` circular |
| Inner dot | PASS | **9 × 9 px** (the 20.39 fix holds in the frozen build) |
| Dot when checked | PASS | `display: block`, `translate(-50%,-50%)` (matrix `(1,0,0,1,-4.5,-4.5)`) |
| Selection | PASS | one radio per group `checked`, dot pops |
| Both pages | PASS | each group measured with its page visible |

### 4.8 Checkboxes (frozen) — PASS

| Check | Result | Measured |
|---|---|---|
| 3 checkboxes | PASS | `set-enabled` (checked), `set-announce` (checked), `set-autostart` (unchecked) |
| Used box (the 20.36 fix) | PASS | **16.89 × 16.89 px**, `display: inline-block` |
| Checked fill | PASS | `rgb(47,109,246)` light / `rgb(111,157,255)` dark = `--accent` |
| Checkmark | PASS | `::after` 3.25 × 6.5 px, `rotate(45°)` matrix `.707,.707,-.707,.707` |
| Unchecked | PASS | transparent fill, no checkmark |

### 4.9 WhatsApp button (frozen) — PASS

| Check | Result | Measured |
|---|---|---|
| Anchor + link | PASS | `href="https://wa.me/201010101182"`, `target="_blank"`, `rel="noopener noreferrer"` |
| Size (the 20.39 fix) | PASS | **84 × 24 px** |
| Brand-green border | PASS | `rgb(37,211,102)` = `#25D366` in **both** themes |
| Rest state | PASS | label green at inline-start, `svg opacity 0` |
| **Hover (real cursor)** | **PASS** | background → `rgb(37,210,102)`, `svg opacity 0 → 0.994`, label → white — light **and** dark |
| Restores after cursor leaves | PASS | `svg opacity → 0`, `hover: false` |
| Transition duration | PASS | `0.5s` unchanged |

### 4.10 Alerts (frozen) — PASS

All 4 types exercised through the same DOM operation the app itself uses (`setStatus`-style class + text on `#settings-status`), **with the 300 ms `border-color` transition settled before reading**:

| Check | Result | Measured (light → dark) |
|---|---|---|
| 4px inline-start accent bar | PASS | `borderInlineStartWidth: 4px` ×4 types |
| **Per-type token colors** | **PASS** | success `rgb(15,157,110)`→`rgb(69,214,162)`; info `rgb(47,109,246)`→`rgb(111,157,255)`; warning `rgb(217,138,0)`→`rgb(240,178,60)`; error `rgb(200,48,42)`→`rgb(255,107,98)` |
| Translucent tint | PASS | bg `color-mix` 13–16% over surface |
| Masked icon | PASS | `::before` `15.08 × 15.08 px` (1.15em), `margin-inline-end: 8px` |
| Text + flex row | PASS | `display: flex`, Arabic text correct |
| **Hover (real cursor)** | **PASS** | `matches(':hover') === true`, `transform scale(1.05)`, tint → 23% |
| Dark theme | PASS | all 4 types verified with dark tokens |

### 4.11 Cross-cutting — PASS

| Check | Result |
|---|---|
| `dir="rtl"` `lang="ar"`, 4 nav items / 4 pages | PASS — pages switch with correct Arabic titles |
| Theme tokens resolve in both themes | PASS — light `--accent #2f6df6 / --accent-text #ffffff`; dark `#6f9dff / #0b0e15`; effective tokens come from `skins.css :root` (which overrides `theme.css` in the cascade) |
| Theme switching via the app's own control | PASS — `pmgTheme.set()` flips `data-theme` both ways; checkbox stays in sync |
| Sidebar version | PASS — `1.2.7` |
| Monitor/scheduler running at boot | PASS — `scheduler_running: true`, chip ON |

---

## 5. JS / Runtime Errors — NONE

| Check | Result |
|---|---|
| `Runtime.exceptionThrown` during the whole review | **0** |
| `Runtime.consoleAPICalled` (error) during the whole review | **0** |
| Real EXE `webview.log` | **0** error-pattern lines in the entire 1,990-line log |
| After 4 pages, 14 buttons, 4 hover cycles, 2 disabled cycles, chip round-trip, 4 radios, 3 checkboxes, 4 alert types × 2 themes | **0** errors |
| Final sweep | PASS — bridge live, `readyState: "complete"`, clean `WM_CLOSE` shutdown, 0 leftover processes |

---

## 6. Constraints Compliance

| Rule | Status |
|---|---|
| Do NOT modify source files | **HELD** — 16/16 key source files byte-identical to the pre-build SHA-256 snapshot (`phase20_42_prebuild_hashes.csv`) |
| Do NOT change CSS/HTML/JS/Python | **HELD** — zero edits to any file |
| Do NOT overwrite `Phase20-28-Release` | **HELD** — `dist\Phase20-28-Release\PrayerMusicGuard.exe` still hashes to `6D2E434F673948C684C66D91FE6249D998074825D2B31E3C7A1DADB7D64ACB18` (byte-identical to the 20.28/20.36/20.38 reports) |
| Do NOT overwrite `Phase20-36/38` reviews | **HELD** — `Phase20-38-Visual-Review` EXE still `74DFC7D15F779F0D8ACA2E9810AB50B2817D2D409E90183AF564CFAA55A0244B`; `Phase20-36-Visual-Review` untouched |
| Do NOT delete existing releases | **HELD** — `releases\v1.2.5 / v1.2.6 / v1.2.7` untouched (mtimes 2026-09-13/14/18) |
| Create a NEW independent build | **HELD** — new folder `dist\Phase20-42-Visual-Review\` (created 2026-09-21 11:33) |
| Use the existing project OneDir build system | **HELD** — `PrayerMusicGuard.spec` + pinned `win7\venv` toolchain, `COLLECT` mode, `VERSION` unchanged at 1.2.7 |
| Do NOT make fixes | **HELD** — zero source edits; the three apparent anomalies (identical alert bars, chip staying ON, `opacity: 1` disabled) were all **harness measurement artifacts** root-caused and re-measured clean, not product defects |

---

## 7. Summary

| Layer | Result |
|---|---|
| Build | **PASS** — exit 0, new isolated OneDir build, 13/13 data files byte-identical to source |
| Runtime startup of the real EXE | **PASS** — live `صلاة وسكون` window 900×760, real pywebview bridge with 16 methods, real `get_state` round-trip (205 ms), scheduler + single-instance OK, `Responding=True`, clean `WM_CLOSE` shutdown, 0 leftover processes |
| Visual: 20.40 Lucide icons | **PASS** — 10 icons, correct geometry per context, `currentColor` follows theme |
| Visual: 20.41 buttons | **PASS** — 14 buttons, uniform 43px rows, full hover/active/disabled/focus state cycles, outside focus ring |
| Visual: dropdown IconButtons | **PASS** — 40×40 square, centered chevrons, menus open |
| Visual: combobox arrows | **PASS** — 32×32 square, hover tint, click opens menu |
| Visual: nav | **PASS** — 4 items, accent bar intact, hover/active tints, RTL |
| Visual: monitor chip | **PASS** — ON/OFF round-trip through the app's own settings path |
| Visual: frozen radios/checkboxes/WhatsApp/alerts | **PASS** — all 20.31/20.32/20.33/20.34/20.37/20.39 measurements reproduce inside the frozen EXE |
| JS / runtime errors | **PASS** — 0 everywhere |
| Review checks | **74 / 74 PASS** |

### Deliverables

| Item | Value |
|---|---|
| Build | `dist\Phase20-42-Visual-Review\PrayerMusicGuard\PrayerMusicGuard.exe` — PyInstaller exit 0 |
| **EXE SHA-256** | `25444A97DE788811BC00AC6F4798D0756691F14DDE998EB2B697C26766C0D07B` |
| EXE size | 4,253,144 bytes |
| **File count** | **1,028 files** |
| **Total size** | **32,744,781 bytes (31.23 MB)** |
| Real-EXE startup | PASS — live window, real bridge, 0 runtime errors, clean shutdown |
| Visual review | 74/74 PASS — icons, buttons, dropdowns, combobox, nav, chip, radios, checkboxes, WhatsApp, alerts, light/dark, RTL |
| Source integrity | 16/16 files byte-identical to the pre-build snapshot |
| Prior builds/releases | untouched — `Phase20-28-Release` `6D2E434F…64ACB18`; `Phase20-38-Visual-Review` `74DFC7D1…0244B`; `releases\v1.2.5/v1.2.6/v1.2.7` unmodified |

**Overall: PASS** — the post-Phase-20.41 project state builds cleanly, the real EXE boots and runs with zero runtime errors, and every component from Phases 20.40 and 20.41 plus all frozen components render correctly inside the frozen build in both themes and RTL. **No defects were found and no fixes are required.**

Evidence (`reports\phases\phase20_42_evidence\`): full-window captures (`exe_window_light.png`, `exe_window_dark.png`), per-component crops (`btnrow_*`, `chip_*`, `alert_*`, `wa_hover_*`), and the complete JSON measurement sets (`review_result.json`, `buttons_all.json`, `boot`/`disabled`/`chip-path` probe outputs).
