# PHASE 20.38 — Build & Visual Review Report

**Project:** `E:\prayer-music-guard`
**Date:** 2026-09-21
**Phase:** 20.38 — Build the CURRENT project state (post Phase 20.37) into a new independent OneDir build, launch the real EXE, and visually review every UI component changed in Phases 20.31 (checkboxes), 20.32 (radios), 20.33 (WhatsApp button), 20.34 (alert/message UI) and 20.37 (visual fixes)
**Mode:** Build + launch + visual verification only. **No source/UI code was modified and nothing was fixed.** A new isolated build folder was created; `dist\Phase20-28-Release`, `dist\Phase20-36-Visual-Review` and every prior release were left untouched.

---

## 0. Headline Result

| Question | Answer |
|---|---|
| Did the build succeed? | **YES** — PyInstaller exit 0, no errors |
| Does the real EXE start? | **YES** — full frozen pipeline runs, live `صلاة وسكون` window, `Responding=True`, real `window.pywebview` bridge attached |
| JS / runtime errors? | **NONE** — 0 in the page error hook and 0 error lines in `webview.log` during this session |
| 20.31 checkboxes render? | **YES** — used box **17×17px**, accent fill + white checkmark measured in pixels in **both themes** |
| 20.32 radios render? | **YES** — all 4 radios **34×34px**, 12px inner dot, accent disc + shadows |
| 20.33 WhatsApp button renders? | **YES** — **74.39×24px** at 12px font, brand-green border, exact hover sequence in **both themes** |
| 20.34 alert/message UI renders? | **YES** — all 4 types × 2 themes, 4px accent bar, masked icon, real-cursor hover scale 1.05 + tint rise |
| 20.37 fixes hold in the build? | **YES** — every 20.37 measurement reproduces inside the frozen EXE |
| **Overall** | **PASS** — build, runtime and visual review all clean; **zero defects found** |

---

## 1. Build Result — PASS

| Item | Value |
|---|---|
| **Output path (exact)** | `E:\prayer-music-guard\dist\Phase20-38-Visual-Review\PrayerMusicGuard\PrayerMusicGuard.exe` |
| **EXE SHA-256** | `74DFC7D15F779F0D8ACA2E9810AB50B2817D2D409E90183AF564CFAA55A0244B` |
| EXE size | 4,253,144 bytes |
| OneDir bundle | **1,028 files / 32,735,336 bytes (31.22 MB)** — folder `PrayerMusicGuard\` |
| Build mode | OneDir (`COLLECT` in `PrayerMusicGuard.spec`) — identical to the project's established build |
| Toolchain | `win7\venv` — Python **3.8.10 x64** + **PyInstaller 5.13.2** (the pinned Windows 7 toolchain; `vendor\` Python never used) |
| Build command | `win7\venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --distpath "dist\Phase20-38-Visual-Review" PrayerMusicGuard.spec` |
| Build exit code | 0 (clean log: `Building COLLECT COLLECT-00.toc completed successfully.`) |
| Built at | 2026-09-21 07:53 (local) |
| Source version | `VERSION` = 1.2.7 (unchanged); `PrayerMusicGuard.iss` untouched; `release.ps1` **not** run |

The build used the project's own spec and build system (`build_exe.bat` / `release.ps1` pattern), only with a **new** `--distpath`. Nothing was archived under `releases\` and no version was bumped.

### Bundle integrity — PASS

All 13 shipped data files are **byte-identical (SHA-256)** to the pre-build source snapshot (`reports\phases\phase20_38_prebuild_hashes.csv`), so the frozen frontend is exactly the post-20.37 UI state:

`main.py`, `uiverse_combobox.py`, `webview_app\{backend_api.py, launcher.py, platform_check.py, splash.html}`, `webview_app\frontend\{index.html, js\app.js, js\theme.js, css\components.css, css\layout.css, css\skins.css, css\theme.css}` — **13/13 MATCH**.

The pywebview bridge resources (`webview\js\{api,customize,finish,state}.js`) are bundled via the spec's explicit `collect_data_files('webview', subdir='js')`, so the frozen `window.pywebview` bridge is present — **proven at runtime** in §2 (bridge type `object`, API type `object`).

---

## 2. Real-EXE Launch & Startup — PASS

`PrayerMusicGuard.exe` was launched from the new bundle. The complete frozen pipeline executed:

| Check | Result | Evidence |
|---|---|---|
| Splash → launcher → WebView2 child | PASS | `Starting HTML frontend initialization` → `Configuring WebView2` → (`webview.log`) |
| BackendAPI bridge created & attached | PASS | `BackendAPI instance created` / `js_api attached to window` (`webview.log`) |
| Single-instance guard | PASS | `Single-instance guard: acquired (first instance)` |
| Frontend resolved from the new bundle | PASS | `Using relative frontend URL: webview_app/frontend/index.html (resolved from …\dist\Phase20-38-Visual-Review\PrayerMusicGuard\…)` |
| Window created + scheduler started | PASS | `Window created successfully` → `Scheduler started` → `Closed event handler attached` |
| WebView2 runtime | PASS | resolved from registry to `153.0.4234.48`, `gui=edgechromium`, storage path under `%APPDATA%\PrayerMusicGuard\webview2_data` |
| Ready flag | PASS | written ~0.6 s after window creation |
| Live window on screen | PASS | window **900×760**, title codepoints `0635 0644 0627 0629 0020 0648 0633 0643 0648 0646` = `صلاة وسكون`, both processes `Responding=True` |
| Rendered content (not a blank window) | PASS | **1,623 distinct colours** sampled in a real Win32 window capture (160,855-byte PNG) |
| **pywebview bridge live in the frozen EXE** | **PASS** | `typeof window.pywebview === "object"`, `typeof window.pywebview.api === "object"`, API keys incl. `browse_player`, `fetch_times`, `get_state`, `pause_now`, `save_settings`, `set_autostart` … |
| App boot state | PASS | `readyState: complete`, 5 prayer cards rendered, sidebar version `1.2.7`, `dir="rtl"`, `lang="ar"` |
| **Error hits in `webview.log`** | **0** | only `Settings saved successfully` / clean startup lines dated 2026-09-21 07:53–08:01 |
| Clean shutdown | PASS | `WM_CLOSE` → `webview.start() returned normally` → **0 leftover processes** |

---

## 3. Visual Review Method

The review ran against the **live EXE window**. Because the app ships a Chromium-based WebView2 (Edge `153.0.4234.48`), the running EXE was relaunched with the documented WebView2 remote-debugging switch (`WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS=--remote-debugging-port=9466` — a **test-environment launcher setting; no project file was modified**) and driven through the Chrome DevTools Protocol with a zero-dependency Node client.

Measurements: `Runtime.evaluate` for computed styles and used boxes, `Page.captureScreenshot` for element-region crops decoded **in-page through a canvas** (`data:` URLs never taint the canvas) with colour-distance pixel counting, and **real `Input.dispatchMouseEvent` cursor moves** to engage CSS `:hover` (synthetic JS events cannot). Every assertion below is a **measured computed style or a measured pixel**, not an impression. Direct image viewing is not available in this environment.

**Review total: 62 / 62 checks PASS.**

---

## 4. Per-Component Visual Results

### 4.1 Phase 20.31 / 20.37 — Settings checkboxes — PASS

The Phase 20.36 defect (`.checkmark` used box 0×0, nothing painted) is **fixed and confirmed inside the frozen EXE**.

| Check | Result | Measured |
|---|---|---|
| 3 checkboxes in `.uv-choice-list` | PASS | ids `set-enabled`, `set-announce`, `set-autostart` |
| `display` (the 20.36 root cause) | PASS | `inline-block` (was `inline` → 0×0) |
| Used box size | PASS | `offsetWidth 17`, `offsetHeight 17`; rect `16.89×16.89px` (1.3em @13px) |
| `::after` checkmark geometry when checked | PASS | `3.25 × 6.5 px`, transform `matrix(.707,.707,-.707,.707,0,0)` = rotate(45°) |
| Checked accent fill (light) | PASS | `rgb(47,109,246)` = `--accent #2f6df6` |
| Checked accent fill (dark) | PASS | `rgb(111,157,255)` = `--accent #6f9dff` |
| **Accent box painted (light)** | **PASS** | **938 accent px** in the exact-box crop |
| **White checkmark painted (light)** | **PASS** | **33 pure-white tick px** (`--accent-text #ffffff`) |
| **Accent box painted (dark)** | **PASS** | **936 accent px** |
| **Checkmark painted (dark)** | **PASS** | **25 dark tick px** (`--accent-text #0b0e15`) |
| Toggling through `<label>` | PASS | all 3 flip `checked` and repaint |

### 4.2 Phase 20.32 / 20.37 — Radio buttons — PASS

| Check | Result | Measured |
|---|---|---|
| 4 radios in 2 `.uv-radio-list` groups | PASS | `location_mode` auto/manual + `method` suspend/media |
| Container size (all 4) | PASS | **34 × 34 px** each (was 50×50 pre-20.37) |
| `.checkmark` disc | PASS | `34×34`, `border-radius 50%` (circular) |
| Inner dot size | PASS | **12 × 12 px** (proportional to the 34px disc; was 18px) |
| Inner dot when checked | PASS | `matrix(1,0,0,1,-6,-6)` = `translate(-50%,-50%) scale(1)` |
| Checked circle paints `--accent` | PASS | `rgb(47,109,246)` (light) / `rgb(111,157,255)` (dark) |
| Shadows retained | PASS | inset `0 6px 12px` + drop `0 4px 8px` still resolved |
| Transitions retained | PASS | `background-color 0.3s, box-shadow 0.3s` + `transform 0.3s` |
| **Rendered pixels (checked)** | **PASS** | **896 accent px + 1,410 white/anti-aliased ring px** in the disc crop |
| Selection works | PASS | one radio per group becomes `checked`, dot pops |

### 4.3 Phase 20.33 / 20.37 — WhatsApp button — PASS

| Check | Result | Measured |
|---|---|---|
| Anchor + link + target + rel | PASS | `href="https://wa.me/201010101182"`, `target="_blank"`, `rel="noopener noreferrer"`, `title="مراسلة المطور عبر واتساب"` |
| Structure `<p>` + `<svg>` | PASS | label text `WhatsApp` |
| **Size (the 20.37 fix)** | **PASS** | `font-size 12px` → **74 × 24 px** (`rect 74.39×24`), ratio 3.083 = same 6.2:2 shape |
| Fits inside sidebar footer | PASS | 74.4px button inside the footer, no overflow |
| Brand-green border | PASS | `rgb(37,211,102)` = `#25D366` in **both** themes |
| Rest state | PASS | label at `inset-inline-start 13.8px`, green; `svg opacity 0` |
| **Hover — label movement** | **PASS** | label slides `13.8px → 6px` and turns `#fff` |
| **Hover — SVG fade-in** | **PASS** | `svg opacity 0 → 1` |
| **Hover — background fill** | **PASS** | background → `rgb(37,211,102)` |
| **Hover — transition duration** | **PASS** | `0.5s` on button, `<p>` and `<svg>` (unchanged) |
| **Rendered pixels, rest** | **PASS** | **884 green px** (border) in the button crop |
| **Rendered pixels, hover** | **PASS** | **5,838 green px** (full fill) — light **and** dark |
| Hover restores after cursor leaves | PASS | back to white/green surface, `svg opacity 0` |

Hover was driven with the **real cursor** (`Input.dispatchMouseEvent`), which is required to engage `:hover`.

### 4.4 Phase 20.34 — Alert / message UI — PASS

All 4 types exercised through the same DOM operation the app itself uses (`setStatus()`-style class + text assignment on `settings-status`) in **light and dark**:

| Check | Result | Measured |
|---|---|---|
| Text + class + flex row | PASS | e.g. `تم حفظ الإعدادات.` / `card__hint is-success` / `display:flex` (×4 types) |
| 4px inline-start accent border | PASS | `borderInlineStartWidth 4px`; colour = the resolved token exactly (`--success rgb(15,157,110)`, `--warning rgb(217,138,0)`, `--error rgb(200,48,42)`, `--accent rgb(47,109,246)` light; `rgb(111,157,255)` dark) |
| Translucent tint | PASS | bg `color(srgb … / 0.13–0.16)` over the card surface |
| Masked icon glyph | PASS | `::before` icon `15.08×15.08 px` (1.15em) with `margin-inline-end 8px` |
| **Hover (real cursor)** | **PASS** | `matches(':hover') === true`; `transform matrix(1.05,0,0,1.05,0,0)`; tint opacity **0.13 → 0.23** |
| Dark theme | PASS | info alert accent `rgb(111,157,255)`, tint `/ 0.13` on dark surface |
| Message logic untouched | PASS | driven from outside, byte-identical shipped JS (`setStatus()` never re-implemented) |

### 4.5 Cross-cutting — PASS

| Check | Result |
|---|---|
| `dir="rtl"` `lang="ar"`, 4 nav items / 4 pages | PASS — pages switch with correct Arabic titles (`لوحة القيادة` / `المواقيت` / `المشغّل` / `الإعدادات`) |
| Theme tokens resolve in both themes | PASS — light `--accent #2f6df6 / --accent-text #ffffff`; dark `#6f9dff / #0b0e15` |
| Sidebar version | PASS — `1.2.7` |
| Phases 20.31/20.32/20.37 scoping intact | PASS — `.uv-choice-list` vs `.uv-radio-list` rules cannot reach each other's elements (computed styles verified per group) |
| App boots in dark theme then toggles | PASS — real `#theme-checkbox` toggles `data-theme` both ways |

---

## 5. JS / Runtime Errors — NONE

| Check | Result |
|---|---|
| `Runtime.exceptionThrown` during the whole review | **0** |
| `Runtime.consoleAPICalled` (error) during the whole review | **0** |
| Real EXE `webview.log` for this session | **0** error-pattern lines — only clean startup + `Settings saved successfully` |
| After all 4 pages, 3 checkboxes, 4 radios, 4 hover cycles, 4 message types × 2 themes | **0** errors |
| Final sweep | PASS — `errors: []`, `readyState: "complete"`, bridge live |

The only error-pattern lines found in the log directory are **dated earlier days/sessions** (e.g. `_MAIN load failed: No module named 'uiverse_combobox'` from 2026-09-20 pre-build runs, and a settings-load warning at 02:00 on 2026-09-21 during the 20.36 review session) — **none from the 20.38 session** (07:53–08:01).

One **harness-side** note: the first launch (without the debug switch) was closed with `CloseMainWindow()` before relaunching with remote debugging — both shutdowns were clean (`webview.start() returned normally`, 0 leftover processes). No application code is involved.

---

## 6. Constraints Compliance

| Rule | Status |
|---|---|
| Do NOT modify source files | **HELD** — 15/15 key source files byte-identical to the pre-build SHA-256 snapshot |
| Do NOT change CSS/HTML/JS/Python | **HELD** — zero edits to any file |
| Do NOT overwrite `Phase20-28-Release` | **HELD** — `dist\Phase20-28-Release\PrayerMusicGuard.exe` still hashes to `6D2E434F673948C684C66D91FE6249D998074825D2B31E3C7A1DADB7D64ACB18` (byte-identical to the value in the Phase 20.28 and 20.36 reports), folder mtime unchanged (2026-09-20 15:13) |
| Do NOT delete existing releases | **HELD** — `releases\v1.2.5 / v1.2.6 / v1.2.7` untouched (mtimes 2026-09-13/14/18) |
| Create a NEW independent build | **HELD** — new folder `dist\Phase20-38-Visual-Review\` (created 2026-09-21 07:53); `dist\Phase20-36-Visual-Review` untouched (mtime 02:15) |
| Use the existing project OneDir build system | **HELD** — `PrayerMusicGuard.spec` + pinned `win7\venv` toolchain, `COLLECT` mode, `VERSION` unchanged at 1.2.7 |
| Do NOT make fixes / rebuild repeatedly | **HELD** — one build only; zero source edits; nothing to fix |

---

## 7. Summary

| Layer | Result |
|---|---|
| Build | **PASS** — exit 0, new isolated OneDir build, 13/13 data files byte-identical to source |
| Runtime startup of the real EXE | **PASS** — live `صلاة وسكون` window 900×760, real pywebview bridge attached, scheduler + single-instance OK, `Responding=True`, clean `WM_CLOSE` shutdown, 0 leftover processes |
| Visual: 20.31/20.37 checkboxes | **PASS** — 17×17 box, accent + white checkmark measured in pixels in both themes |
| Visual: 20.32/20.37 radios | **PASS** — 34×34 discs, 12px dot, accent + shadows + transitions |
| Visual: 20.33/20.37 WhatsApp button | **PASS** — 74×24 at 12px font, brand-green border, exact label/SVG/background hover sequence (0.5s) in both themes |
| Visual: 20.34 alert/message UI | **PASS** — 4 types × 2 themes, exact-token 4px accent bar, masked icon, real-cursor hover scale 1.05 + tint 0.13→0.23 |
| JS / runtime errors | **PASS** — 0 everywhere |
| Review checks | **62 / 62 PASS** |

### Deliverables

| Item | Value |
|---|---|
| Build | `dist\Phase20-38-Visual-Review\PrayerMusicGuard\PrayerMusicGuard.exe` — PyInstaller exit 0 |
| **EXE SHA-256** | `74DFC7D15F779F0D8ACA2E9810AB50B2817D2D409E90183AF564CFAA55A0244B` |
| EXE size | 4,253,144 bytes |
| **File count** | **1,028 files** |
| **Total size** | **32,735,336 bytes (31.22 MB)** |
| Real-EXE startup | PASS — live window, real bridge, 0 runtime errors, clean shutdown |
| Visual review | 62/62 PASS — checkboxes, radios, WhatsApp button + hover, 4 alert types, light/dark, RTL all verified |
| Source integrity | 15/15 files byte-identical to the pre-build snapshot |
| Prior builds/releases | untouched — `Phase20-28-Release` EXE still `6D2E434F…64ACB18`; `Phase20-36-Visual-Review` and `releases\v1.2.5/v1.2.6/v1.2.7` unmodified |

**Overall: PASS** — the post-Phase-20.37 project state builds cleanly, the real EXE boots and runs with zero runtime errors, and every component from Phases 20.31, 20.32, 20.33, 20.34 and 20.37 renders correctly inside the frozen build in both themes and RTL. **No defects were found and no fixes are required.**

Evidence (`reports\phases\phase20_38_evidence\`): the real-window Win32 capture (`exe_live_window.png`), per-component screenshots (checkbox light/dark, radio, WhatsApp hover, all 4 alert types, dark alert) and the full JSON measurement sets (`qa20_38_live_result.json`, `tick_result.json`).
