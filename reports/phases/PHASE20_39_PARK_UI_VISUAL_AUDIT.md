# PHASE 20.39 — Park UI Visual Audit + Part A UI Fixes

**Project:** `E:\prayer-music-guard`
**Date:** 2026-09-21
**Phase:** 20.39 — (A) Fix two visual defects in the current post-20.37 UI; (B) audit the existing frontend against [Park UI](https://park-ui.com/) and define the exact next phase for an icon/button refresh.
**Mode:** PART A implemented + verified (CSS-only, 1 file). PART B is **research and a written plan only** — no code was written for it.
**Hard constraints respected:** no React/Ark UI/Panda CSS migration, no `@park-ui/cli` or package installation, no build, no pywebview/WebView2 or Python change, no JS selector/ID change, RTL + dark/light preserved, approved alert/message UI (`.card__hint`) and checkboxes (`.uv-choice-list`) untouched, WhatsApp URL and hover animation untouched.

---

## 0. Headline Result

| Question | Answer |
|---|---|
| PART A1 — radio dot reduced? | **YES** — `.uv-radio-list .checkmark::after` 12px → **9px** in the unchanged 34px disc; verified in both themes |
| PART A2 — WhatsApp icon defect fixed? | **YES** — label/SVG hover overlap **6.72px → −2.88px (2.88px clearance)**; button 74.4px → **84px**, still compact in the sidebar footer |
| Hover animation preserved? | **YES** — label slide 1.15em→0.5em, SVG opacity 0→1, fill `#25D366`, all at 0.5s; `href`/`target`/`rel` and RTL intact |
| Scope kept? | **YES** — only `components.css` changed; 6 other frontend files **byte-identical** to the 20.38 pre-build snapshot |
| PART B report delivered? | **YES** — sections 4–9 below; implementation proposed as **PHASE 20.40 (icons)** + **20.41 (buttons)** |
| **Overall** | **PASS** — both Part A fixes verified numerically + pixel-wise in light and dark |

---

## 1. PART A — Diagnosis (before)

### A1. Radio dot too heavy
`.uv-radio-list .checkbox-container` is a **34×34px** disc (computed style, confirmed in 20.38). The selected indicator `.checkmark::after` was **12×12px**, i.e. **35.3%** of the disc diameter, leaving only an 11px accent ring. Visually the dot read as a full stop rather than a centered pip, and the 20.38 visual review flagged it as heavy.

### A2. WhatsApp icon overlapped the label on hover
The Uiverse `alshahwan` button was rescaled in 20.37 from `font-size: 17px` to `12px` (anchor of the sidebar footer's 0.78rem scale), keeping the original `width: 6.2em`. Measured at 12px:

| Quantity | Value |
|---|---|
| button box | 74.4 × 24px (6.2em × 2em) |
| label text "WhatsApp" | **55.12px = 4.59em** |
| label `inset-inline-start` (rest → hover) | 13.8px → 6px (1.15em → 0.5em) |
| SVG | 12 × 12px (1em) at `inset-inline-end: 0.5em`, `opacity 0 → 1` on hover |
| **hover overlap** | **+6.72px** — the fading WhatsApp glyph painted **over the label's first letters** |

Root cause: at 12px, font hinting renders the glyphs wider than at 17px (**4.59em vs 4.28em** — measured against the reconstructed 17px original, `textWidth 72.71px / 17 = 4.28em`). The content stack needs `0.5em + 4.59em + 1em + 0.5em = 6.59em`, which the original `6.2em` box cannot hold. This is a small-size rendering artifact, not a regression from 20.37's logic.

---

## 2. PART A — Fixes applied (CSS only, `webview_app\frontend\css\components.css`)

**A1 — radio dot** (`.uv-radio-list .checkmark:after`):
```diff
-  width: 12px;
-  height: 12px;
+  width: 9px;
+  height: 9px;
```
9px = **26.5%** of the 34px disc → a **12.5px accent ring** on selection. The dot is centered with `transform: translate(-50%,-50%)`, so a size change needs no position adjustment.

**A2 — WhatsApp button** (`.uv-wa`):
```diff
-  width: 6.2em;   /* 74.4px @ 12px */
+  width: 7em;     /* 84px @ 12px */
```
Rejected alternative: shrinking the label to 10px — breaks the 1:1 icon:text ratio that the original design has (SVG is 1em). Widening keeps that ratio and is the minimal change. The comment block above the rule was updated to document the 6.2em → 7em rationale.

Nothing else changed: padding, height, border, border-radius, all hover rules, transitions, and the `--wa` brand token are untouched.

---

## 3. PART A — Verification (live CDP, headless Chrome, real cursor)

Evidence: `reports\phases\phase20_39_evidence\` — `_cdp_lib.js`, `_measure_baseline.js`, `baseline_result.json`, `_verify_after.js`, `after_result.json`, and PNG crops for both themes.

### Radio — both themes

| Check | light | dark | result |
|---|---|---|---|
| dot size | **9 × 9px** | **9 × 9px** | PASS |
| dot transition | `transform 0.3s` | `transform 0.3s` | PASS |
| checkmark transition | `background-color 0.3s, box-shadow 0.3s` | same | PASS |
| `:checked` turns disc accent | `rgb(47,109,246)` | `rgb(111,157,255)` | PASS |
| dot color (contrast on accent) | `rgb(255,255,255)` | `rgb(11,14,21)` | PASS |
| group / container count | 2 / 4 | 2 / 4 | PASS (same as baseline) |
| checkbox list untouched | 3 `.uv-choice-list` containers | 3 | PASS (scope) |
| alert icons untouched | `.card__hint` present | present | PASS (scope) |

Crops: `radio_light.png`, `radio_dark.png` (3× scale).

### WhatsApp — both themes

| Check | baseline | after | result |
|---|---|---|---|
| button width | 74.4px | **84px** | PASS (planned) |
| button height | 24px | 24px | PASS |
| hover overlap | **+6.72px** | **−2.88px (clearance)** | **FIXED** |
| label `inset-inline-start` hover | 6px | 6px | PASS (animation intact) |
| SVG opacity hover | 0 → 1 | 0 → 1 | PASS |
| hover background | `rgb(37,211,102)` | `rgb(37,211,102)` | PASS |
| label color hover | `#fff` | `#fff` | PASS |
| base background | `var(--surface)` per theme | same | PASS |
| `href` | `https://wa.me/201010101182` | same | PASS |
| direction | `rtl` | `rtl` | PASS |
| transition | `0.5s` | `0.5s` | PASS |

Crops: `wa_rest_light/dark.png`, `wa_hover_light/dark.png` (2× scale).

### Scope — byte-level

| File | SHA-256 vs `phase20_38_prebuild_hashes.csv` |
|---|---|
| `frontend\css\components.css` | **changed** (the two intended edits only) — `67EF1BEA…29EB` |
| `frontend\index.html` | identical — `4FA5B6ED…9CC0` |
| `frontend\js\app.js` | identical — `3ED308E7…77F1` |
| `frontend\js\theme.js` | identical — `6BA158BC…708E` |
| `frontend\css\layout.css` | identical — `2270DBCF…EC51` |
| `frontend\css\skins.css` | identical — `CF7E9796…F74D` |
| `frontend\css\theme.css` | identical — `31EEA469…9277` |

Backup of the pre-edit state: `backup\phase20_39_ui_fix_20260921_094500\` (all 7 files).

Note: `containerBox` reads 0×0 in **both** baseline and after runs because the radio list sits in a panel that is not laid out during headless boot; the computed style (34×34px) and the pixel crops confirm the true rendered size. Not a regression.

---

# PART B — Park UI Visual Audit

Reference: https://park-ui.com/ (Chakra Systems; components built on Ark UI + Panda CSS). Audited pages: home, `/docs/components/button`, `/docs/components/icon-button`, `/docs/components/icon`. **Nothing was installed and no React/Panda code is proposed** — the recipes below are ported to the project's existing plain-CSS + custom-property architecture.

## 4. Park UI design tokens worth porting

From the Button recipe (`packages/preset/src/recipes/button.ts`):

- **Variants:** `solid` | `surface` | `subtle` | `outline` | `plain` — each with `_hover`, `_active`, `_on` state layers.
- **Sizes:** `2xs … 2xl`, each a fixed height + `minW` + `px` + a paired `_icon` boxSize (`3.5` → `6`).
- **Base:** `inline-flex`, `align-items: center`, `justify-content: center`, `gap: 2`, `font-weight: semibold`, `border-radius: l2`, `transition-property: background-color, border-color, color, box-shadow`, `white-space: nowrap`, `focusVisibleRing: outside` (a **box-shadow ring**, not an outline), `isolation: isolate`.

From the Icon recipe: `color: currentcolor`, `display: inline-block`, `flex-shrink: 0`, `line-height: 1em`, boxSize scale `3 / 4 / 4.5 / 5 / 5.5 / 6`. Icon library of record: **Lucide** (https://lucide.dev).

## 5. Files that would need visual changes

| File | Why | Size of change |
|---|---|---|
| `webview_app\frontend\index.html` | Replace 5 text glyphs + 4 arrow chars + chip dot with inline Lucide `<svg>`; add `aria-hidden` + class hooks | moderate |
| `webview_app\frontend\css\components.css` | Add `.icon` utility (Icon recipe port); restyle `.btn`, `.btn--accent`, `.combobox__arrow`, `.chip`, `.nav__item/.nav__icon`, `.sidebar__logo` | moderate |
| `webview_app\frontend\css\skins.css` | Theme-dependent overrides for those same selectors (dark/light parity) | moderate |
| `webview_app\frontend\css\layout.css` | Nav icon vertical alignment / box sizing now that icons are SVG | small |
| `webview_app\frontend\js\app.js` | **One line only** — line 871 writes the `●` glyph into `#monitor-chip` via `textContent` (see §8, risk R3) | trivial |
| `webview_app\frontend\js\theme.js` | none (writes status text, no glyphs) | none |
| Python / backend / `webview_main.py` | **none** | none |

## 6. Current dashboard/sidebar icons → recommended Lucide replacements

| # | Location | Current rendering | Element | Recommended Lucide icon | Notes |
|---|---|---|---|---|---|
| 1 | Sidebar brand | `☾` (text moon) | `.sidebar__logo` | **`moon`** (or `moon-star`) | brand mark; keep the concept, gain crisp vector edges |
| 2 | Nav — Dashboard | `⌂` | `.nav__icon` | **`layout-dashboard`** | glyph fallback varies by font; SVG is deterministic |
| 3 | Nav — Times (المواقيت) | `◷` | `.nav__icon` | **`clock`** | `calendar-clock` is the alternative if dates are emphasized |
| 4 | Nav — Player (المشغّل) | `♫` | `.nav__icon` | **`music`** | direct semantic match |
| 5 | Nav — Settings | `⚙` | `.nav__icon` | **`settings`** | Lucide `settings` is the gear; do not use `sliders-horizontal` |
| 6 | Monitor status chip | `●` (written by JS) | `#monitor-chip` | **`circle-off`** (stopped) / **`circle-check`** (running) | off/on pair; alternatively `radio` for both states |
| 7 | Combobox arrow ×2 | `▼` | `.combobox__arrow` | **`chevron-down`** | symmetric → RTL-safe |
| 8 | Player dropdown | `▼` | `#btn-dropdown-music` | **`chevron-down`** | becomes an IconButton |
| 9 | Adhan dropdown | `▼` | `#btn-dropdown-adhan` | **`chevron-down`** | becomes an IconButton |
| 10 | Theme switch | hand-rolled sun + moon SVG (already vector) | `.theme-switch__icon` | **`sun`** / **`moon`** | geometry already matches Lucide; swap paths 1:1 for consistency |
| 11 | WhatsApp button | official WhatsApp glyph (brand path) | `.uv-wa svg` | **keep as-is** | brand mark + approved 20.33 animation — do NOT replace |
| 12 | Alert/message icons | masked Lucide-style SVG | `.card__hint` | **keep as-is** | approved in 20.34, explicitly out of scope |
| 13 | Checkbox checkmark | SVG path | `.uv-choice-list` | **keep as-is** | approved in 20.31, explicitly out of scope |

Icons 1–9 are the migration set (11 icon instances). Icons 10 can be aligned for consistency; 11–13 are frozen.

## 7. Buttons that should receive Park UI-inspired styling

| Current selector | Instances | Park UI mapping | What changes |
|---|---|---|---|
| `.btn` (default) | 8: `btn-resume`, `btn-fetch-times`, `btn-fetch-location`, `btn-browse-music`, `btn-browse-adhan`, `btn-resume-2`, `btn-save-music`, `btn-refresh-state` | **`outline` variant, size `sm`** | 1px border + transparent/surface bg, hover bg tint (`outline.bg.hover`), keep current `--radius-ctrl` as the `l2` equivalent |
| `.btn--accent` | 5: `btn-pause`, `btn-save-times`, `btn-fetch-location`, `btn-pause-2`, `btn-save` | **`solid` variant, size `sm`** | `bg: var(--accent)`, `color: var(--accent-text)`, hover `var(--accent-hover)` — already the current values; add Park UI state layers (`_active`, `_disabled`) and `gap` for future icon+label buttons |
| `#btn-dropdown-music`, `#btn-dropdown-adhan` | 2 (icon-only `▼`) | **`IconButton`** (`px: 0`, square `minW`, `chevron-down`) | square hit area, icon 1:1 with text scale, `subtle` or `outline` variant |
| `.combobox__arrow` | 2 | **`IconButton`, size `2xs`/`xs`, `plain` variant** | replace the `▼` char with `chevron-down`; disabled state maps to Park UI `disabled` layer style |
| `.nav__item` | 4 | **`plain` variant with `_on`/active layer** | `is-active` → `surface.bg.active` + accent indicator bar (the existing `::before` indicator in `layout.css` stays); full-width, `justify-content: flex-start` |
| `.chip` / `.chip--on` / `.chip--off` | 2 (`#monitor-chip`, `#resume-countdown`) | **`Badge`** pattern | pill + icon + label; status color tokens map to existing `--accent` / `--ok` / `--warn` semantics |
| `.theme-switch` | 1 | **`Switch`** pattern | already close (track + thumb + sun/moon); only needs icon swap, geometry frozen |
| `.uv-wa` | 1 | **no Park UI mapping** | Uiverse brand button with an approved hover animation (20.33) and a just-fixed layout (20.39); leave untouched |

Focus treatment: replace `outline: 2px solid var(--accent)` on `.btn`/`.nav__item` with Park UI's **outside box-shadow ring** (`box-shadow: 0 0 0 2px var(--surface), 0 0 0 4px var(--accent)`) — visible in both themes without the outline-gap artifacts the 20.38 review noted.

## 8. Risks

| ID | Risk | Severity | Mitigation |
|---|---|---|---|
| R1 | **Win7/WebView2 font fallback** — the current text glyphs (`⌂ ◷ ♫ ⚙`) already render inconsistently across system fonts; SVG removes that risk but adds ~0.4–0.7KB per icon to `index.html` (≈ +6KB total for 11 icons) | low | inline SVG is the mitigation, not the risk; no packaging change since `index.html` is already a data file of the bundle |
| R2 | Text glyphs auto-inherit `color`/`font-size`; SVG must be given explicit sizing and `color: currentColor` | low | port the Icon recipe verbatim into a `.icon` class (`display:inline-block; flex-shrink:0; color:currentcolor; line-height:1em`) with a boxSize scale |
| R3 | **`app.js:871` writes the chip glyph**: `chip.textContent = on ? "● المراقبة تعمل" : "● المراقبة متوقفة"` — `textContent` would erase an inline SVG | **high** | restructure to `chip.innerHTML` with an icon span + text span, or keep the `●` char in JS and only style it; must be handled in the same phase, and `#monitor-chip`/`monitor-chip` IDs and the `setMonitorState(on)` contract stay identical |
| R4 | RTL mirroring — all chosen icons are symmetric (`chevron-down`, `circle-*`, `clock`, `music`, `settings`, `layout-dashboard`, `moon`, `sun`); no directional arrow is introduced | low | if an arrow is ever added, mirror with `transform: scaleX(-1)` under `[dir="rtl"]`, not by swapping the path |
| R5 | Theme parity — Park UI uses Panda `colorPalette.*` semantic tokens; the project uses `--accent`, `--surface`, `--border`, `--fg` custom properties | medium | hand-map each variant state to the existing tokens in `theme.css`; verify both themes with the CDP harness (as done in 20.39) |
| R6 | Regression surface — `.btn` is used by 13 buttons across 4 pages; a variant refactor can shift heights/alignment in the `.button-row` grids | medium | keep the current `padding: 10px 18px` and `--radius-ctrl` for size parity, then re-measure every page with the harness |
| R7 | Frozen components — alert icons (20.34), checkbox checkmark (20.31), WhatsApp button (20.33/20.39) must not be touched | high | scope the phase to the §6 migration set and §7 selectors only; add a byte-hash check of those rules to the phase's exit criteria |
| R8 | No build is run in this phase; a future build (20.42+) must re-verify, since pywebview/WebView2 on the target machine is the real renderer | low | re-run the 20.38 build + visual review pattern after 20.40/20.41 |

## 9. Proposed next phases (exact scope)

**PHASE 20.40 — Lucide icon migration (inline SVG, zero packages).**
1. In `index.html`, replace the 5 nav/brand glyphs, 2 combobox arrows and 2 dropdown arrows with inline Lucide `<svg class="icon" aria-hidden="true">` paths (`viewBox="0 0 24 24"`, `fill="none"`, `stroke="currentColor"`, `stroke-width="2"`, `stroke-linecap="round"`, `stroke-linejoin="round"`).
2. Add a plain-CSS port of the Park UI Icon recipe to `components.css`: `.icon { color: currentcolor; display: inline-block; flex-shrink: 0; line-height: 1em; }` plus a boxSize scale (`2xs: 0.75em; xs: 1em; sm: 1.125em; md: 1.25em; lg: 1.375em; xl: 1.5em`) so icons scale with their context's font-size — the same em-based anchor that made the 20.37 rescale safe.
3. Fix `app.js:871` so the monitor chip holds an icon span + text span (IDs and `setMonitorState(on)` contract unchanged).
4. Swap the theme-switch sun/moon paths for Lucide `sun`/`moon` (geometry already matches).
5. Exit criteria: CDP verification in light + dark + RTL — icon `width/height` match the intended boxSize, `color: currentcolor` resolves to the theme token, nav active state unaffected, and byte-hash check confirming `.card__hint`, `.uv-choice-list` and `.uv-wa` rules are untouched. Then a build + visual review (20.42-style).

**PHASE 20.41 — Park UI-inspired button refresh (plain-CSS port of the Button recipe).**
1. Port the five variants (`solid` / `surface` / `subtle` / `outline` / `plain`) with `_hover` / `_active` / `_disabled` / `_on` state layers into `skins.css`, mapped to `--accent`, `--accent-hover`, `--surface`, `--border`, `--fg` per theme.
2. Map `.btn` → `outline@sm`, `.btn--accent` → `solid@sm`, keeping today's `padding: 10px 18px` and `--radius-ctrl` so no grid reflows.
3. Add the `IconButton` pattern (square `min-width`, `padding: 0`, centered icon) and apply to `#btn-dropdown-music`, `#btn-dropdown-adhan` and `.combobox__arrow`.
4. Replace `outline` focus with the outside box-shadow ring on `.btn` and `.nav__item`.
5. Restyle `.nav__item` as `plain` + `_on` active layer (keep the `::before` accent bar from `layout.css`), and `.chip` as a Badge (icon + label pill).
6. Exit criteria: every one of the 13 buttons measured in both themes (height, min-width, icon box size, hover/active/disabled state colors), `#monitor-chip` on/off pair verified, RTL intact, and `.uv-wa` / `.theme-switch` rules byte-identical.

**Frozen for both phases:** `.card__hint` alert icons (20.34), `.uv-choice-list` checkmarks (20.31), `.uv-wa` brand button (20.33, fixed 20.39), `theme-switch` geometry, all Python/backend files, all JS IDs and selectors.

---

## 10. Session footprint

- Edited: `webview_app\frontend\css\components.css` (2 hunks: radio dot 12→9px, `.uv-wa` width 6.2em→7em + comment).
- Created: `reports\phases\phase20_39_evidence\` (`_cdp_lib.js`, `_measure_baseline.js`, `_verify_after.js`, `baseline_result.json`, `after_result.json`, 8 PNG crops), this report, and `backup\phase20_39_ui_fix_20260921_094500\`.
- Not created/modified: no package files, no `node_modules`, no build output, no Python file, no `index.html`/JS change.
- **No build was run and no package was installed**, per instructions.
