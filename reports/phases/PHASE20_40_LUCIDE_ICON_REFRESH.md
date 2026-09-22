# PHASE 20.40 — Lucide Icon Refresh Report

**Project:** `E:\prayer-music-guard`
**Date:** 2026-09-21
**Phase:** 20.40 — Replace text-glyph icons with inline Lucide-style SVGs across the sidebar, topbar, times page and music page, plus a scoped Park UI-inspired `.icon` utility. Scope per the PHASE 20.39 audit (§9, PHASE 20.40).
**Mode:** Implemented + verified. **CSS/HTML/JS only. No build, no package install, no React/Park UI/Panda CSS.**
**Note on verification:** this model cannot read image files, so the pixel-crop PNGs produced during verification (`reports\phases\phase20_39_evidence\sidebar_*.png`, `topbar_*.png`) are archived for human review but were not visually inspected here. All pass/fail conclusions below come from **live numeric CDP measurements** (bounding boxes, `getBBox()` painted extents, computed styles, and functional state assertions), which are stricter than visual inspection.

---

## 0. Headline Result

| Check | Result |
|---|---|
| All 11 target glyphs replaced with inline Lucide SVG? | **YES** — 0 stray glyphs remain (`strayGlyphs: "none"`, both themes) |
| Icons render with correct geometry? | **YES** — every icon reports non-zero box **and** non-zero painted extent |
| `currentColor` follows the theme? | **YES** — icon `stroke`/`color` resolves to theme tokens in light and dark |
| Em-based sizing scales with context? | **YES** — measured sizes match `1em × context font-size` to within sub-pixel rounding |
| Sidebar active state unchanged? | **YES** — 4 items, `dashboard` active, accent box `22.80px`, labels intact |
| Dropdown arrows work? | **YES** — click opens `#dropdown-music`, 2 items rendered, icon centered in button |
| Combobox arrows work? | **YES** — click opens `.combobox__menu` (`wasHidden: true → opened: true`) |
| Monitor chip ON/OFF works? | **YES** — ON → `chip--on` + `circle-check` + "المراقبة تعمل"; OFF → `chip--off` + `circle-off` + "المراقبة متوقفة" |
| Theme switch still works? | **YES** — toggle flips `data-theme`, sun/moon opacity + rotate transitions intact, `pmgTheme` API intact |
| Zero JS/runtime errors? | **YES** — `errors: []` (0 page exceptions, 0 console errors) |
| Frozen components unchanged? | **YES** — `.uv-wa`, `.card__hint`, `.uv-choice-list`, radio rules byte-identical (verified by block diff) |
| **Overall** | **PASS** |

---

## 1. What changed

### 1.1 New `.icon` utility — `webview_app\frontend\css\components.css`

A plain-CSS port of Park UI's Icon recipe (https://park-ui.com/docs/components/icon), which is:

```js
color: 'currentcolor', display: 'inline-block', flexShrink: '0',
verticalAlign: 'middle', lineHeight: '1em',   // + boxSize scale 3/4/4.5/5/5.5/6
```

This project has no Panda token scale, so boxSize is expressed in **em relative to each icon's own context font-size** — the same em-anchored pattern already used by `.uv-wa`. That gives one utility that scales everywhere and inherits theme color for free:

```css
.icon { display: inline-block; flex-shrink: 0; color: currentColor;
        line-height: 1em; width: 1em; height: 1em; vertical-align: middle; }
.sidebar__logo .icon        { width: 1.4em;  height: 1.4em; }
.nav__icon .icon            { width: 1.2em;  height: 1.2em; }
.combobox__arrow .icon,
#btn-dropdown-music .icon,
#btn-dropdown-adhan .icon   { width: 1.15em; height: 1.15em; }
.chip .icon                 { width: 1em;    height: 1em; }
```

Every selector is prefixed with `.icon` (or a specific context), so it cannot leak into the frozen UI. Verified: the `.uv-wa`, `.card__hint`, `.uv-choice-list`, radio and theme-switch rule blocks are **byte-identical** before/after (block-level diff, §4).

### 1.2 `index.html` — 11 glyph → SVG replacements

All SVGs use the mandated inline attributes: `viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"`, with `aria-hidden="true"` where the adjacent text already labels the control.

| Location | Was | Now | Lucide path source |
|---|---|---|---|
| Sidebar brand | `☾` | `moon` | lucide-static v0.544.0 |
| Nav: Dashboard | `⌂` | `layout-dashboard` | " |
| Nav: Times | `◷` | `clock` | " |
| Nav: Player | `♫` | `music` | " |
| Nav: Settings | `⚙` | `settings` | " |
| Combobox arrows ×2 | `▼` | `chevron-down` | " |
| Music/Adhan dropdowns ×2 | `▼` | `chevron-down` | " |
| Monitor chip | `●` (text) | `circle-off` / `circle-check` (via JS) | " |

Path data was **copied verbatim from the official `lucide-static` package** (fetched from `unpkg.com/lucide-static@0.544.0`), not hand-drawn, so the geometry is exactly Lucide's.

### 1.3 Monitor chip — restructured to icon span + text span

`index.html` (initial OFF state) and `js\app.js` `renderStatus()` were updated together so the markup the JS writes is identical to the static markup:

```js
var ICON_ON  = '<span class="chip__icon" aria-hidden="true"><svg class="icon" …>' +
               '<circle cx="12" cy="12" r="10" /><path d="m9 12 2 2 4-4" /></svg></span>';
var ICON_OFF = '<span class="chip__icon" aria-hidden="true"><svg class="icon" …>' +
               '<path d="m2 2 20 20" />…</svg></span>';
chip.innerHTML = (on ? ICON_ON : ICON_OFF) +
                 '<span class="chip__text">' + (on ? "المراقبة تعمل" : "المراقبة متوقفة") + "</span>";
chip.className = "chip " + (on ? "chip--on" : "chip--off");
```

The R3 risk from the 20.39 audit (`textContent` would erase an inline SVG) is resolved by switching to `innerHTML`. **`#monitor-chip`, `renderStatus(data)`, the `enabled` contract and the `chip--on`/`chip--off` classes are unchanged.**

### 1.4 Theme switch — Lucide geometry, existing CSS behavior

Only the sun/moon path geometry was swapped (sun `r=4` + 8 ray paths; moon = the Lucide crescent). No attributes were added to those two SVGs, because the existing theme-switch CSS already sets `fill`/`stroke` from the `--icon-sun`/`--icon-moon` tokens — adding `stroke="currentColor"` there would have *overridden* the intended token coloring (moon has no CSS `stroke` rule, so a presentation attribute would win and add an unwanted outline). **Switch geometry (84×42 track, 34px thumb) and behavior (opacity + rotate transitions, `:checked` transform) are untouched.**

### 1.5 Files touched

| File | Change |
|---|---|
| `frontend\index.html` | 11 glyph → SVG swaps; chip markup restructure |
| `frontend\css\components.css` | +58 lines: the `.icon` utility block only |
| `frontend\js\app.js` | 3 lines in `renderStatus()` (textContent → innerHTML with icon spans) |
| `frontend\css\layout.css`, `skins.css`, `theme.css`, `js\theme.js` | **unchanged** (byte-identical) |
| Python / backend / `webview_main.py` | **unchanged** |

---

## 2. Verification method

Live CDP harness (zero external deps; Node's built-in WebSocket to an isolated headless Chrome, RTL, both themes):

- `reports\phases\phase20_39_evidence\_verify_lucide.js` — driver
- `reports\phases\phase20_39_evidence\lucide_result.json` — full measurements

Key harness design points worth recording, because they were the difference between a false fail and a true pass:

1. **Theme is applied via the app's own `pmgTheme.set()`**, not by writing `data-theme` directly — setting the attribute alone leaves the switch checkbox stale and desyncs the sun/moon transform state.
2. **Combobox/dropdown icons are measured on their own pages** — `.nav__item` click to Times/Music first, and `#manual-fields` revealed via the app's own `location_mode` radio path. On the dashboard their boxes read 0×0 purely because the pages are hidden.
3. **The dropdown open test needs a bridge.** `openAppDropdown()` is async (`call("list_running_apps").then(…)`); with no bridge it correctly stays closed. A fake `window.pywebview.api` (installed via `Page.addScriptToEvaluateOnNewDocument` *before* page scripts run) drives the app's real `whenReady() → refresh() → applyState() → renderStatus({enabled:true})` path — so the chip ON state was verified through production code, not a mock.
4. **Frozen components verified by block-level text diff** of the CSS between the pre-edit backup and the current file, not just by eye.

---

## 3. Results (both themes, `dir="rtl"`)

### 3.1 Icon geometry and scaling

| Context | Expected (em × font-size) | Light measured | Dark measured |
|---|---|---|---|
| Sidebar logo `moon` | 1.4em × 20px = 28.0px | **28 × 28** | 28 × 28 |
| Nav icons ×4 | 1.2em × 15.2px = 18.24px | **18.23 × 18.23** | 18.23 × 18.23 |
| Combobox `chevron-down` ×2 | 1.15em × 14.4px = 16.56px | **16.55 × 16.55** | 16.55 × 16.55 |
| Dropdown buttons ×2 | 1.15em × 16px = 18.4px | **18.4 × 18.4** | 18.4 × 18.4 |
| Monitor chip icon | 1em × 13.12px = 13.12px | **13.12 × 13.12** | 13.12 × 13.12 |
| Switch sun (visible state) | fixed 20px | **20 × 20** | 20 × 20 |

Painted extents (`getBBox`) are non-zero for every icon — e.g. nav `layout-dashboard` paints 18×18 inside its 18.23 box, `clock` paints 20×20 (the circle fills the viewBox), chip `circle-off` paints 20.01. **No icon is rendering as 0×0 or blank.**

### 3.2 `currentColor` follows the theme

| Context | Light `stroke` | Dark `stroke` | Resolves to |
|---|---|---|---|
| Nav icons | `rgb(47,109,246)` | `rgb(111,157,255)` | `--accent` (light / dark) ✓ |
| Combobox arrows | `rgb(102,112,144)` | `rgb(154,162,184)` | `--muted` ✓ |
| Dropdown buttons | `rgb(19,26,43)` | `rgb(242,244,249)` | `--fg` ✓ |
| Chip OFF | `rgb(102,112,144)` | `rgb(154,162,184)` | `--muted` via `.chip--off` ✓ |
| Chip ON | `rgb(15,157,110)` | `rgb(69,214,162)` | `--success` via `.chip--on` ✓ |
| Logo | `rgb(255,255,255)` / `rgb(242,244,249)` | same | `--accent-text` on the gradient tile ✓ |
| Switch sun/moon | token-driven | token-driven | `--icon-sun` `#f5a623`, `--icon-moon` `#6b7bd6` ✓ |

Every icon's `stroke` matches its parent's text color, so icons participate in theme switching with **zero icon-specific color rules**.

### 3.3 Functional checks

| Check | Light | Dark |
|---|---|---|
| Sidebar: 4 nav items, `dashboard` active, labels `[لوحة القيادة, المواقيت, المشغّل, الإعدادات]` | ✓ | ✓ |
| Active nav icon box `22.80px`, accent tint background | ✓ | ✓ |
| `#btn-dropdown-music` click → dropdown opens, 2 items, icon centered in 56.4px button | ✓ | ✓ |
| `.combobox__arrow` click → menu opens (`wasHidden: true → opened: true`) | ✓ | ✓ |
| Chip via real `renderStatus({enabled:true})` → `chip chip--on`, "المراقبة تعمل", `circle-check` | ✓ | ✓ |
| Chip via `enabled:false` → `chip chip--off`, "المراقبة متوقفة", `circle-off` | ✓ | ✓ |
| No `●` character anywhere in chip text (`hasUglyDot: false`) | ✓ | ✓ |
| Theme toggle: `light → dark → light`, sun `opacity 1→0`, moon `0→1`, rotate matrices fire | ✓ | ✓ |
| Switch geometry: track 84px, thumb 34px | ✓ | ✓ |
| Frozen: `#monitor-chip` id, `.uv-wa` anchor + href + 1104-char brand path, 84×24px | ✓ | ✓ |
| Frozen: 8 `.card__hint`, 3 `.uv-choice-list` containers, 4 radio containers | ✓ | ✓ |
| Page exceptions / console errors | **0** | **0** |

### 3.4 Static / encoding checks

- `components.css` brace balance: **153 / 153**; file grew 23,670 → 24,991 bytes (the `.icon` block only, confirmed by line diff).
- CSS diff vs backup: **only additions**, all inside the new `.icon` block — no existing line was modified.
- Frozen rule blocks byte-identical (block diff): `.uv-wa` (321 B), `.card__hint` (178 B), `.uv-choice-list .container` (195 B), `.uv-radio-list .checkbox-container` (178 B), `.theme-switch` (215 B), `.uv-radio-list .checkmark:after` (297 B).
- `app.js` diff: exactly 3 lines changed (the `renderStatus` swap); file is UTF-8 **without BOM**; non-ASCII count went **2730 → 2728** — precisely the two removed `●` characters, confirming all Arabic text survived intact.
- `index.html`: 40 changed line groups across 11 icon swaps + chip restructure; no stray `☾ ⌂ ◷ ♫ ⚙ ▼ ●` anywhere.
- Hashes: `layout.css`, `skins.css`, `theme.css`, `theme.js` unchanged; `app.js.bak` (a stale pre-existing backup file) untouched.

### 3.5 Byte sizes / hashes (for the record)

| File | SHA-256 (after 20.40) |
|---|---|
| `frontend\index.html` | `acc8f017…1627` |
| `frontend\css\components.css` | `c39d80cd…8e35` |
| `frontend\js\app.js` | `1c75694e…6b7b` |
| `frontend\css\layout.css` | `2270dbcf…ec51` (unchanged) |
| `frontend\css\skins.css` | `cf7e9796…f74d` (unchanged) |
| `frontend\css\theme.css` | `31eea469…9277` (unchanged) |
| `frontend\js\theme.js` | `6ba158bc…708e` (unchanged) |

Pre-edit backup: `backup\phase20_40_lucide_20260921_103000\` (all frontend files).

---

## 4. Risks and how they landed

| Risk (from 20.39 audit) | Outcome |
|---|---|
| R3 — `app.js` `textContent` would erase the chip SVG | **Handled** — `renderStatus` now writes `innerHTML` with dedicated `.chip__icon` / `.chip__text` spans; verified through the app's own `refresh()` path |
| R1 — font-glyph inconsistency on Win7/WebView2 | **Eliminated** — icons are now deterministic inline SVG; the last rendering-dependency on system fonts for UI icons is gone (Arabic text remains font-dependent, as before) |
| R2 — SVG needs explicit sizing/color | **Handled** — the `.icon` utility sets `color: currentColor` + em sizing; measured values match intent in both themes |
| R4 — RTL mirroring | **Safe** — every icon used is symmetric; `chevron-down` and the `circle-*` pair render identically LTR/RTL. Verified in `dir="rtl"` |
| R5 — theme parity | **Pass** — no icon-specific color rules exist; `currentColor` resolves to the correct token per theme |
| R7 — regressing frozen components | **Pass** — block-diff proof above; WhatsApp button, alerts, checkboxes, radios and the theme switch are untouched |
| Bundle size | +11 inline SVGs ≈ **+1.6 KB** total across `index.html`/`app.js`; no new requests, no fonts, no JS |

---

## 5. Remaining follow-ups (explicitly NOT done in this phase)

- **PHASE 20.41** (Park UI-inspired *button* refresh: `.btn`/`.btn--accent` variant mapping, IconButton pattern for the two dropdown buttons and the combobox arrow, box-shadow focus ring) — not started, per instructions.
- The combobox arrow buttons still use the generic `.combobox__arrow` styling rather than an IconButton pattern; that is a 20.41 cosmetic change, and the arrow is already verified functional with its Lucide icon.
- A future build (20.42-style) should re-verify inside the frozen EXE, since pywebview/WebView2 on the target machine is the real renderer.
- The pixel crops in `reports\phases\phase20_39_evidence\` (`sidebar_light.png`, `sidebar_dark.png`, `topbar_light.png`, `topbar_dark.png`) are available for human visual review — they were **not** inspected by this model (no image input support); all conclusions here are from numeric measurements.

---

## 6. Session footprint

- Edited: `webview_app\frontend\index.html`, `webview_app\frontend\css\components.css`, `webview_app\frontend\js\app.js`.
- Created: `reports\phases\phase20_39_evidence\_verify_lucide.js`, `lucide_result.json`, 4 PNG crops; `backup\phase20_40_lucide_20260921_103000\`; this report.
- Not created/modified: no package files, no `node_modules`, no build output, no Python/backend change.
- **No build was run and no package was installed**, per instructions. Verification stopped after the report, as requested.
