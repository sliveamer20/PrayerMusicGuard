# PHASE 20.36 — Build & Visual Review Report

**Project:** `E:\prayer-music-guard`
**Date:** 2026-09-21
**Phase:** 20.36 — Build the CURRENT project state into a new independent OneDir build and visually review the real EXE, including the UI changes of Phases 20.31 (checkboxes), 20.32 (radios), 20.33 (WhatsApp button) and 20.34 (alert/message UI)
**Mode:** Build + launch + visual verification only. **No source/UI code was modified and nothing was fixed.** A new isolated build folder was created; `dist\Phase20-28-Release` and every prior release were left untouched.

---

## 0. Headline Result

| Question | Answer |
|---|---|
| Did the build succeed? | **YES** — PyInstaller exit 0, no errors |
| Does the real EXE start? | **YES** — full frozen pipeline runs, live window, `Responding=True` |
| JS / runtime errors? | **NONE** — 0 at startup, 0 across the whole review, 0 error lines in `webview.log` |
| 20.31 checkboxes render? | **NO — DEFECT FOUND** (see §6). The custom checkbox box has a **0×0 used box** and never paints |
| 20.32 radios render? | **YES** — 50×50 accent circle + inner dot, verified in pixels |
| 20.33 WhatsApp button renders? | **YES** — brand-green border painted in both themes, verified in pixels |
| 20.34 alert/message UI renders? | **YES** — all 4 types × 2 themes, accent bar + masked icon + hover, verified in pixels |
| **Overall** | **FAIL (visual)** — build/runtime PASS; one real UI defect in Phase 20.31. Per the phase rules the defect is **reported, not fixed** |

---

## 1. Build Result — PASS

| Item | Value |
|---|---|
| **Output path (exact)** | `E:\prayer-music-guard\dist\Phase20-36-Visual-Review\PrayerMusicGuard\PrayerMusicGuard.exe` |
| **EXE SHA-256** | `8C26FEDB86B199184BDF97812F0C90BDFA830342F7CC26A5C724A86541AC2BA4` |
| EXE size | 4,253,152 bytes |
| OneDir bundle | **1,028 files / 32,734,579 bytes (31.22 MB)** — folder `PrayerMusicGuard\` |
| Build mode | OneDir (`COLLECT` in `PrayerMusicGuard.spec`) — identical to the project's established build |
| Toolchain | `win7\venv` — Python **3.8.10 x64** + **PyInstaller 5.13.2** (the pinned Windows 7 toolchain; `vendor\` Python never used) |
| Build command | `win7\venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --distpath "dist\Phase20-36-Visual-Review" PrayerMusicGuard.spec` |
| Build exit code | 0 (18 log lines, zero `ERROR`/`Traceback`; only benign `WARNING: Unable to find package for requirement Pillow/six from package pystray`, also present in the 20.28 release build) |
| Built at | 2026-09-21 02:15 (local) |
| Source version | `VERSION` = 1.2.7 (unchanged); `PrayerMusicGuard.iss` untouched |

The build was produced with the project's own spec and build system (`build_exe.bat` / `release.ps1` pattern), only with a **new** `--distpath`. `release.ps1` was **not** run with `-Release`, so nothing was archived under `releases\` and no version was bumped.

### Bundle integrity — PASS

All 13 shipped data files are **byte-identical (SHA-256)** to the current source, so the frozen frontend is exactly the current UI state:

`webview_app/frontend/{index.html, js/app.js, js/theme.js, css/components.css, css/layout.css, css/skins.css, css/theme.css}`, `webview_app/{backend_api.py, launcher.py, platform_check.py, splash.html}`, `main.py`, `uiverse_combobox.py` — **13/13 MATCH**. The pywebview bridge resources (`webview/js/{api,customize,finish,state}.js`) are bundled via the spec's explicit `collect_data_files('webview', subdir='js')`, so the frozen `window.pywebview` bridge is present (proven at runtime in §3–§5).

---

## 2. Real-EXE Launch & Startup — PASS

`PrayerMusicGuard.exe` was launched with no arguments from the new bundle. The complete frozen pipeline executed:

| Check | Result | Evidence |
|---|---|---|
| Splash → launcher → WebView2 child | PASS | `[launcher] HTML splash completed successfully` → `starting HTML frontend (WebView2)` → `HTML frontend ready` (`pmg_launcher.log`) |
| BackendAPI bridge created & attached | PASS | `BackendAPI instance created` / `js_api attached to window` (`webview.log`) |
| Single-instance guard | PASS | `Single-instance guard: acquired (first instance)` |
| Frontend resolved from the bundle | PASS | `Using relative frontend URL: webview_app/frontend/index.html` (cwd changed to the bundle dir) |
| Window created + scheduler started | PASS | `Window created successfully` → `Scheduler started` → `Closed event handler attached` |
| WebView2 runtime | PASS | resolved from registry to `153.0.4234.48`, `gui=edgechromium`, storage path under `%APPDATA%\PrayerMusicGuard\webview2_data` |
| Ready flag | PASS | written 0.6 s after window creation |
| Live window on screen | PASS | window 900×760, title `صلاة وسكون` (U+0635 U+0644 U+0627 U+0629 U+0020 U+0648 U+0633 U+0643 U+0648 U+0646), process `Responding=True` |
| Time to live window | **5.0 s** | measured from process start to window handle found |
| Rendered content (not a blank window) | PASS | 1,347 distinct colours sampled in a window capture |
| **Error hits in `webview.log`** | **0** | 18 new log lines, none matching `ERROR`/`Traceback`/`failed`/`unavailable`/`Exception` |
| Clean shutdown | PASS | `WM_CLOSE` → child + parent exited → `HTML frontend closed cleanly`; **0 leftover processes** |
| User profile | PASS | `%APPDATA%\PrayerMusicGuard\settings.json` snapshotted before the run and restored after |

---

## 3. Visual Review Method

Two layers, both against the **live window**:

1. **Real-EXE capture** — the launched EXE's window was captured to PNG via Win32 (`GetWindowRect` + `Graphics.CopyFromScreen`) and analysed programmatically (1,347 distinct colours, real compositor output). Direct image viewing is not available in this environment, so every visual assertion below is a **measured computed style or a measured pixel**, not an impression.
2. **Frozen-artifact review** — the frontend shipped **inside the new bundle** was copied byte-identically into a temp dir (6/6 files verified byte-identical), an error hook was prepended **before** `js/app.js` loads (so any init error would be captured), and it was opened in a live WebView2 window with the **real `BackendAPI` bridge loaded from the same bundle** and the real scheduler running (5/5 prayer cards). This is the same technique the Phase 20.28 release UAT used to test the built artifact.

Measurements: `getComputedStyle` on live elements (layout, colour tokens, transitions, `::before`/`::after` geometry, `:hover` state), plus **rendered-pixel analysis** of element-only crops (client→screen translated via Win32 `ClientToScreen`) with strict colour-distance matching against the resolved theme tokens. Hover was driven with the **real Win32 cursor** (`SetCursorPos`), because synthetic JS events cannot engage CSS `:hover`. No shipped file was modified; all instrumentation lived in the temp copy.

**Review total: 78 / 80 checks PASS.** The 2 failures are the same defect (§6).

---

## 4. Per-Phase Visual Results

### 4.1 Phase 20.31 — Settings checkboxes — **FAIL (defect)**

Everything structural and specified is correct; the **used box size** is not.

| Check | Result | Measured |
|---|---|---|
| 3 checkboxes present in `.uv-choice-list` | PASS | ids `["set-enabled","set-announce","set-autostart"]` |
| DOM order for the `~` combinator | PASS | `label.choice > .container > input(first child) + .checkmark` in all 3 |
| Specified box / radius / transition | PASS | `width/height = 16.9px` (1.3em @13px), `border-radius 3.25px` (0.25em), `transition 0.25s` |
| Native input hidden | PASS | `display: none` |
| Checked box resolves `--accent` | PASS | bg `rgb(111,157,255)` = `--accent` `#6f9dff` (dark) |
| Checkmark `::after` rotates 45° when checked | PASS | `matrix(0.707107, 0.707107, -0.707107, 0.707107, 0, 0)` |
| **Used box size** | **FAIL** | `offsetWidth 0`, `offsetHeight 0`, `getBoundingClientRect() 0×0`, `clientWidth 0`, `scrollWidth 0` — while `display: inline`, `position: relative` |
| **Accent box painted in pixels** | **FAIL** | 0 accent-coloured pixels in the whole settings choice-list region after checking the box |

See §6 for the root cause and the proven one-line fix direction (not applied).

### 4.2 Phase 20.32 — Radio buttons — PASS

| Check | Result | Measured |
|---|---|---|
| 4 radios in 2 `.uv-radio-list` groups | PASS | `location_mode` auto/manual + `method` suspend/media |
| Container geometry | PASS | `50×50px`, `.checkmark` `position:absolute; width/height 100%; border-radius 50%` |
| Native input kept renderable | PASS | `opacity: 0` (not `display:none`), so `:checked` still repaints — matches the JS that sets `radio.checked` programmatically |
| Checked circle paints `--accent` | PASS | bg `rgb(111,157,255)` = `--accent` |
| Inner dot `scale(1)` | PASS | `matrix(1,0,0,1,-9,-9)` = `translate(-50%,-50%) scale(1)` on an 18×18 px dot |
| **Rendered pixels** | **PASS** | **1,638 accent-coloured px** in the circle crop (`radio_checked.png`), used box 50×50 |

### 4.3 Phase 20.33 — WhatsApp button — PASS

| Check | Result | Measured (light / dark) |
|---|---|---|
| Anchor + link + target | PASS | `href="https://wa.me/201010101182"`, `target="_blank"`, `rel="noopener noreferrer"`, `title`/`aria-label` intact |
| Structure `<p>` + `<svg>` | PASS | both present, label text `WhatsApp` |
| Brand-green border | PASS | `border-color: rgb(37,211,102)` = `#25D366` in **both** themes |
| Size `6.2em × 2em` @17px | PASS | `105.39 × 34 px` in both themes |
| **Rendered pixels** | **PASS** | **443 green px (light) / 510 green px (dark)** in the button crop (`whatsapp_light.png`, `whatsapp_dark.png`) — the border paints in the sidebar footer on every page |

### 4.4 Phase 20.34 — Alert / message UI — PASS

All 4 types exercised through the exact DOM operation `setStatus()` (`app.js:563-573`) — same element id, same `is-success/is-warning/is-error/is-info` classes, same Arabic strings — in **light and dark** themes:

| Check | Result | Measured |
|---|---|---|
| Text + class + flex row | PASS | e.g. `تم حفظ الإعدادات.` / `card__hint is-success` / `display:flex; align-items:center` (×4 types × 2 themes) |
| 4px inline-start accent border | PASS | `borderInlineStartWidth 4px`; colour equals the resolved token exactly (`--success #0f9d6e`, `--accent #2f6df6`, `--warning #d98a00`, `--error #c8302a` light; `#45d6a2/#6f9dff/#f0b23c/#ff6b62` dark) |
| Translucent tint + transition + icon | PASS | bg `color(srgb … / 0.13–0.16)` tint over the card surface; transition `background-color/transform/border-color 0.3s ease-in-out`; `::before` masked icon `15.08×15.08 px` (1.15em) with `margin-inline-end 8px` |
| **Accent bar painted (RTL)** | **PASS** | exact token colour found at the inline-start = **physical right** edge of every message (nearest colour distance 0.0), correctly mirroring `border-l-4` under `dir="rtl"` |
| **Icon glyph painted** | **PASS** | 243–261 ink px in the icon zone per type/theme (masked `::before` glyph) |
| **Hover (real Win32 cursor)** | **PASS** | `matches(':hover') === true`; `transform: matrix(1.05,0,0,1.05,0,0)`; tint opacity rises 0.14 → 0.24 (light) / 0.14 → 0.24 (dark) |
| Message logic untouched | PASS | `setStatus()` never re-implemented in the app; driven from outside, byte-identical shipped JS |

### 4.5 Cross-cutting

| Check | Result |
|---|---|
| `dir="rtl"` `lang="ar"`, 4 nav items / 4 pages | PASS |
| App version in sidebar | PASS — `1.2.7` |
| Theme tokens resolve in both themes | PASS — light `--accent #2f6df6 / --success #0f9d6e / --warning #d98a00 / --error #c8302a`; dark `#6f9dff / #45d6a2 / #f0b23c / #ff6b62` |
| Phases 20.31/20.32 scoping intact | PASS — `.uv-choice-list` vs `.uv-radio-list` rule sets cannot reach each other's elements (DOM + computed styles verified separately) |

---

## 5. JS / Runtime Errors — NONE

| Check | Result |
|---|---|
| Real EXE `webview.log` on launch | PASS — 18 lines, **0** error hits |
| Error hook (`window.__pmgErrors`) at startup | PASS — **0** errors, bridge attached, 5 prayer cards |
| After every 20.34 message type × 2 themes | PASS — 0 errors |
| During hover and on 20.31/20.32/20.33 components | PASS — 0 errors |
| Final sweep | PASS — `errs: []`, `bridge: true`, `readyState: "complete"` |

One **harness-side** (not app-side) shutdown message was seen once: pywebview could not delete its own `webview2_data` cache folder because a still-running test instance held a file handle. It concerns the throwaway test profile only; it does not involve application code and the folder is regenerated on next start.

---

## 6. Defect Found — Phase 20.31 custom checkbox does not render

**Severity: visible UI defect (the control's box never appears).** Discovered by the rendered-pixel layer of this review; it was **not** caught by the static Phase 20.31 harness or by Phase 20.35's computed-style re-check, because `getComputedStyle().width` returns the *specified* `16.9px` even though the *used* value is `0`.

### Root cause

`.uv-choice-list .checkmark` (`components.css:706`) is a plain `<span>` with **no `display` declaration**, so it stays `display: inline`. For a non-replaced inline element, `width`/`height` do not apply, so its border box collapses to **0×0** and nothing is painted — the accent background, the 1.3em box and the rotated checkmark are all invisible in the running app. The Phase 20.32 radio `.checkmark` works precisely because it is `position: absolute` (blockified), which is why the two controls behave differently.

### Proof (all measured live, on the frozen frontend from the new bundle)

| Measurement | Value |
|---|---|
| `getComputedStyle(.checkmark).display` | `inline` |
| `getComputedStyle(.checkmark).width/height` | `16.9px` / `16.9px` (specified — misleading) |
| `.checkmark.offsetWidth` / `offsetHeight` | `0` / `0` |
| `getBoundingClientRect().width/height` | `0` / `0` |
| `.checkmark.clientWidth` / `scrollWidth` | `0` / `0` |
| Accent-coloured pixels in the settings choice-list after checking the box | **0** |
| Same element with `display: inline-block` forced on the fly | `16.89 × 16.89 px`, `offsetWidth 17` — box and accent paint correctly |
| Control: `.uv-radio-list .checkmark` (absolute) | used box `50 × 50`, 1,638 accent px |

### Fix direction (proposed only — NOT applied, per the phase rules)

Adding `display: inline-block;` (or `block`) to the `.uv-choice-list .checkmark` rule restores the intended 1.3em box; the on-the-fly experiment above proves it yields exactly `16.89 × 16.89 px`. The scoped selector stays untouched, so no other component can be affected. This is a **CSS-only, additive, one-line change** — but per the instruction *"Do NOT fix anything during this phase"* it is recorded here and left for a dedicated phase.

Functional impact is limited to visuals: the native input is `display:none` and no JS listens on these checkboxes (`collectCommon()` only reads `.checked` at save time), so ticking still works through the `<label>` and settings still save — the user simply cannot see the box.

---

## 7. Constraints Compliance

| Rule | Status |
|---|---|
| Do NOT modify source/UI code | **HELD** — 17/17 key source files (main.py, uiverse_combobox.py, webview_app/*, all frontend files) byte-identical to the pre-build SHA-256 snapshot |
| Do NOT fix anything | **HELD** — the §6 defect was measured and reported only |
| Do NOT delete/overwrite existing releases | **HELD** — `dist\Phase20-28-Release\PrayerMusicGuard.exe` still hashes to `6D2E434F…64ACB18` (byte-identical to the value in the Phase 20.28 report) and its folder mtime is unchanged (2026-09-20 15:13); `releases\v1.2.5/v1.2.6/v1.2.7` untouched |
| Use the existing project build/versioning system | **HELD** — `PrayerMusicGuard.spec` + pinned `win7\venv` toolchain, `VERSION` unchanged at 1.2.7 |
| New independent build under `dist\` | **HELD** — new folder `dist\Phase20-36-Visual-Review\` (created 2026-09-21 01:36, final build 02:15); nothing else under `dist\` was modified |
| OneDir build | **HELD** — `COLLECT` mode; output is a `PrayerMusicGuard\` folder (1,028 files), not a single file |
| No further UI changes | **HELD** — zero edits to any frontend file |

---

## 8. Summary

| Layer | Result |
|---|---|
| Build | **PASS** — exit 0, new isolated OneDir build, 13/13 data files byte-identical to source |
| Runtime startup of the real EXE | **PASS** — boots in ~5 s, live `صلاة وسكون` window, bridge + scheduler + single-instance all OK, `Responding=True`, clean `WM_CLOSE` shutdown, 0 leftover processes |
| Visual: 20.31 checkboxes | **FAIL** — `.checkmark` used box is 0×0 (missing `display`), so the custom checkbox box never renders |
| Visual: 20.32 radios | **PASS** — 50×50 accent disc + dot, 1,638 accent px |
| Visual: 20.33 WhatsApp button | **PASS** — `#25D366` border painted in both themes, 443/510 green px |
| Visual: 20.34 alert/message UI | **PASS** — 4 types × 2 themes, exact-token accent bar at the RTL inline-start edge, masked icon glyph, real-cursor hover scale 1.05 + tint 0.14→0.24 |
| JS / runtime errors | **PASS** — 0 everywhere (harness error hook + `webview.log`) |
| Review checks | **78 / 80 PASS** (the 2 failures are the single §6 defect) |

### Deliverables

| Item | Value |
|---|---|
| Build | `dist\Phase20-36-Visual-Review\PrayerMusicGuard\PrayerMusicGuard.exe` — PyInstaller exit 0 |
| **EXE SHA-256** | `8C26FEDB86B199184BDF97812F0C90BDFA830342F7CC26A5C724A86541AC2BA4` |
| EXE size | 4,253,152 bytes |
| Bundle | 1,028 files / 32,734,579 bytes (31.22 MB) OneDir |
| Real-EXE startup | PASS — live window in 5.0 s, 0 runtime errors, clean shutdown |
| Visual review | 78/80 PASS — 20.32 / 20.33 / 20.34 PASS, **20.31 FAIL (checkbox box does not paint)** |
| Source integrity | 17/17 files byte-identical to the pre-build snapshot |
| Prior builds | untouched — `Phase20-28-Release` EXE still `6D2E434F…64ACB18` |

**Overall: FAIL (one real visual defect)** — the build itself and the runtime are fully healthy, and Phases 20.32, 20.33 and 20.34 all render correctly in the built EXE. Phase 20.31's custom checkbox needs the additive `display` fix described in §6; per the phase rules it was **not** applied. Evidence captures (element crops for the WhatsApp button, the radio disc, the settings choice-list, all 8 alert states and a full window shot) are retained from the review run.
