# PHASE 20.35 — Visual Runtime Test Report

**Project:** `E:\prayer-music-guard`
**Date:** 2026-09-21
**Phase:** 20.35 — Visual runtime test of the current source after Phase 20.34 (Alert/Toast Message UI)
**Mode:** Launch the app from SOURCE (no build, no `dist`), keep it open, visually exercise the Success/Info/Warning/Error messages, and confirm Phases 20.31–20.33 are untouched. **No source file was modified.**

---

## 1. How the Source App Was Launched

| Item | Value |
|---|---|
| Entry point | `webview_app/frontend/index.html` served by the real `BackendAPI` bridge inside a live pywebview window — i.e. the same HTML/WebView2 frontend path the normal entry point `webview_app/app_entry.py` → `launcher.py` → `webview_main.py` uses, driven programmatically |
| Interpreter | `win7\venv\Scripts\python.exe` (Python 3.8.10) — the only interpreter in the project that has `pywebview` installed; `platform_check.can_use_html_frontend()` and `webview2_runtime_installed()` both return `True` |
| GUI backend | `edgechromium` (Microsoft Edge WebView2 runtime 153.x), resolved via `webview_main._gui_name()` / `_configure_webview()` |
| Source fidelity | The **real source frontend was copied byte-identically** into a temp dir (`js/app.js`, `js/theme.js`, all 4 CSS files verified with a byte comparison in-run: 6/6 identical). The only change is a 6-line JS error-hook prepended to the **copy** of `index.html` so `window.__pmgErrors` is installed before `app.js` runs — the same instrumentation used by `qa_phase20_28_runtime.py`. **No shipped file was modified.** |
| Real backend | `webview_main._build_api()` attached as `js_api`; the real scheduler started; live prayer cards rendered (5/5) |
| Window | 950×820, on-screen at (30,20) so timers are not throttled and real pixels are capturable |
| `dist` used | **NO** — nothing under `dist\` was read or executed |
| Build performed | **NO** |
| User settings | `%APPDATA%\PrayerMusicGuard\settings.json` snapshotted before the run and restored after |

**Message triggering:** the app's own message system was exercised through the exact DOM operation `setStatus()` (`app.js:563-573`) performs — same element ids, same `is-success/is-warning/is-error/is-info` classes, same Arabic message text taken verbatim from the app's own strings. Real UI handlers were also driven (nav clicks, theme toggle). Message *logic, text, show/hide and timing were not touched.*

---

## 2. Verification Method

Two layers, both against the **live window**:

1. **Runtime/computed-style checks (130/130 PASS)** — `getComputedStyle` on the live message element for layout, radius, border, colour tokens, transition, icon `::before` geometry/mask, plus `matches(':hover')` and `getComputedStyle().transform` while the **real Win32 cursor** was moved over the element (synthetic JS `mouseover` does not trigger CSS `:hover`, so `user32.SetCursorPos` was used).
2. **Rendered-pixel checks (64/64 PASS)** — actual compositor output captured to PNG via Win32 (`GetWindowRect` + `Graphics.CopyFromScreen`), including **element-only crops** (client→screen translated via `ClientToScreen`) so the accent bar, tint and glyph are analysed with no other UI in frame. Direct image viewing is not available in this environment, so the pixels were verified programmatically instead: strict colour-distance matching against the exact token colours, bar width/position geometry, and ink-density for the icon + Arabic text.

**Every failure seen during development was a harness bug, not an app bug** — fixed and re-run to a clean pass: wrong transition unit assertion (`300ms` vs Chromium's `0.3s`), wrong font-size unit (`0.82rem` = `13.12px`), loose colour tolerance (the message text `color-mix(accent 78%, fg)` was being misread as the border bar for green/red/amber), a hover crop that clipped the scaled element, and a hover test that initially ran in dark theme with a stale `is-error` class. None of these touched the application.

---

## 3. Message Type Results

| Type | Triggered | Rendered text | Accent border (computed) | Painted pixels | Verdict |
|---|---|---|---|---|---|
| **Success** | YES — `settings-status`, `is-success` | `تم حفظ الإعدادات.` | light `rgb(15,157,110)` / dark `rgb(69,214,162)` → `--success` ✓ | 106 px bar, 7px wide, right edge; tint `rgb(219,240,234)` | **PASS** |
| **Info** | YES — `is-info` | `جارٍ الحفظ…` | light `rgb(47,109,246)` / dark `rgb(111,157,255)` → `--accent` (blue) ✓ | 106 px bar; tint `rgb(226,235,254)` | **PASS** |
| **Warning** | YES — `is-warning` | `المشغّل غير مفتوح حاليًا؛ شغّله ثم أعد المحاولة.` | light `rgb(217,138,0)` / dark `rgb(240,178,60)` → `--warning` (amber) ✓ | 106 px bar; tint `rgb(247,235,214)` | **PASS** |
| **Error** | YES — `is-error` | `تعذر الحفظ: خطأ غير معروف` | light `rgb(200,48,42)` / dark `rgb(255,107,98)` → `--error` (red) ✓ | 106 px bar; tint `rgb(246,227,227)` | **PASS** |

Per-type measured geometry (identical across all 4 types and both themes):

| Property | Measured | Uiverse reference | Status |
|---|---|---|---|
| Layout | `display:flex; align-items:center` | `flex items-center` | ✓ icon + message row |
| Padding | `8px 10px` | `p-2` (8px) | ✓ compact |
| Radius | `11px` (from `--radius-ctrl` 10px + DPI) | `rounded-lg` | ✓ |
| Accent border | `borderInlineStartWidth 4px`, painted 6–7 px (4px + AA) | `border-l-4` | ✓ |
| Border side (RTL) | painted bar at the **right** edge = inline-start under `dir="rtl"` | `border-l-4` mirrors in RTL | ✓ correct mirroring |
| Background | tint at 14–16% accent opacity (e.g. `color(srgb 0.059 0.616 0.431 / 0.14)`) | `bg-*-100`/`bg-*-900` | ✓ |
| Text | `fontWeight 600`, `fontSize 13.12px` (0.82rem), colour mixes accent 78% + `--fg` | `text-xs font-semibold` | ✓ |
| Icon | `::before` 15.08×15.08 px, mask = exact Uiverse SVG path, `marginInlineEnd 8px` | `h-5 w-5 mr-2` | ✓ painted (227–623 ink px at inline-start) |
| Transition | `background-color 0.3s, transform 0.3s, border-color 0.3s ease-in-out` | `duration-300 ease-in-out` | ✓ |
| Message size | 585×36 px on a 950×820 window; crop 597×48 — a small, uncrowded slice | compact | ✓ not crowded, not oversized |

---

## 4. Light / Dark Result

| Check | Result |
|---|---|
| Theme applied to `<html>` | PASS — `data-theme="light"` and `"dark"` both set deterministically via the app's own `window.pmgTheme.set()` |
| Light theme | PASS — dark text on light tint, green/blue/amber/red all read correctly, interior tints measured `lum>190` with 30–430 colour distance from the accent (a soft tint, neither raw accent nor raw surface) |
| Dark theme | PASS — light text on dark translucent tint over the dark card, interior tints measured `lum<130`, same correct token resolution |
| No theme leak | PASS — every measured colour resolved through `--success`/`--warning`/`--error`/`--accent`/`--fg`; the dark-theme token set (`html[data-theme="dark"]`) was confirmed present |

---

## 5. RTL Result

| Check | Result |
|---|---|
| Document direction | PASS — `<html dir="rtl">` (never changed) |
| Accent bar side | PASS — `borderInlineStartWidth 4px` resolves to the **physical right** edge; painted bar found at the right edge of the message in every crop (RTL mirrors the Uiverse `border-l-4` correctly) |
| Icon placement | PASS — `marginInlineEnd 8px`; icon glyph painted at the inline-start (right) side of the message |
| Logical properties | PASS — `borderInlineStart`/`marginInlineEnd` used, no physical left/right in the hint rules |

---

## 6. Hover Result

A **real Win32 cursor** was positioned over the live message (synthetic events can't trigger `:hover`):

| Check | Result |
|---|---|
| `:hover` state engaged | PASS — `el.matches(':hover') === true` |
| Scale transform | PASS — `getComputedStyle().transform === "matrix(1.05, 0, 0, 1.05, 0, 0)"` (scale 1.05) |
| Background change | PASS — tint strengthened from 14% → 24% opacity (`0.14` → `0.24`); painted tint measurably closer to the accent colour (distance 411 → 366) |
| Painted result | PASS — bar 6 px wide at message-right, icon + text still painted (3271 ink px at inline-start) |

---

## 7. Protected Components (Phases 20.31 / 20.32 / 20.33)

| Check | Result |
|---|---|
| 20.31 settings checkboxes | PASS — 3 present (`set-enabled`, `set-announce`, `set-autostart`), `.uv-choice-list` checkmark geometry unchanged (16.9×16.9 px = `1.3em` @ 13px, radius 3.25px) |
| 20.32 radios | PASS — 4 present (`location_mode` auto/manual + `method` suspend/media), `.uv-radio-list` circle geometry unchanged (radius 50%) |
| 20.33 WhatsApp button | PASS — `.uv-wa` with `<p>` + `<svg>` intact; brand-green border painted `rgb(37,211,102)` confirmed in pixels at the sidebar footer (x 796–900, y 752–778) |

---

## 8. JS / Runtime Errors

| Check | Result |
|---|---|
| At startup | PASS — `window.__pmgErrors` = 0, bridge attached, 5 prayer cards rendered |
| After every message type (×2 themes) | PASS — 0 errors each |
| During hover, and on protected components | PASS — 0 errors |
| Final sweep | PASS — `errs: []`, `bridge: true`, `readyState: "complete"` |

---

## 9. Summary

| Layer | Checks | Result |
|---|---|---|
| Runtime / computed style | 130 | **130 / 130 PASS** |
| Rendered pixels (PNG analysis) | 64 | **64 / 64 PASS** |
| **Total** | **194** | **194 / 194 PASS** |

**Defects found: NONE.** Every message type renders correctly in both themes with correct RTL mirroring, the 300 ms hover scale-1.05 + background intensification works, the alerts are compact (36 px tall) and not crowded, the icon glyph and Arabic text paint cleanly, and Phases 20.31/20.32/20.33 are visually and structurally unchanged.

**Overall: PASS**

The application was left in a clean state: the QA window was destroyed, the temp frontend copy removed, and the user settings profile restored. No source file was modified and no build was produced.
