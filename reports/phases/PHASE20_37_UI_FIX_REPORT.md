# PHASE 20.37 — UI Fix Report (Sizes & Uiverse Fidelity)

**Project:** `E:\prayer-music-guard`
**Date:** 2026-09-21
**Phase:** 20.37 — Fix the three visual issues found in the Phase 20.36 build review
**Mode:** CSS-only fixes to `webview_app/frontend/css/components.css`. **No build. No JS, HTML, Python or alert/message changes.**

---

## 0. Headline Result

| Question | Answer |
|---|---|
| Phase 20.34 alert/message CSS touched? | **NO** — 42/42 lines byte-identical (verified by line diff) |
| WhatsApp button smaller & Uiverse-faithful? | **YES** — 105.39×34px → **74.39×24px**, same 6.2em×2em shape, same hover sequence |
| Checkbox checkmark now visible? | **YES** — used box 0×0 → **17×17px**, checkmark paints in both themes (measured pixels) |
| Radio reduced to ~34px? | **YES** — 50×50px → **34×34px**, inner dot 18px → 12px (proportional) |
| Light / Dark verified? | **YES** — both themes measured for all 3 components |
| RTL verified? | **YES** — `dir="rtl"`, label/SVG mirrored via `inset-inline-*`, button inside sidebar |
| JS / runtime errors? | **NONE** — **0** across 4 pages, 3 checkboxes, 4 radios, 2 theme toggles, 4 hover cycles |
| Build performed? | **NO** — source-only, per instruction |

**Overall: PASS** — all three requested fixes applied and verified; nothing outside scope was modified.

---

## 1. Summary of Actions

| Action | Count | Detail |
|---|---|---|
| Files EDITED | **1** | `webview_app\frontend\css\components.css` (22,468 → 23,233 B; +765 B, comments included) |
| Declaration values changed | **4** | `display: inline-block` (checkbox), `width/height: 34px` (radio), `width/height: 12px` (radio dot), `font-size: 12px` (WhatsApp) |
| Files byte-identical (untouched) | **6** | `index.html`, `js/app.js`, `js/theme.js`, `css/skins.css`, `css/theme.css`, `css/layout.css` (MD5-verified) |
| Phase 20.34 alert CSS lines unchanged | **42/42** | lines 378–419 of `components.css`, byte-identical |
| WhatsApp URL / behaviour | **unchanged** | `href="https://wa.me/201010101182"`, `target="_blank"`, `rel="noopener noreferrer"`, `title`/`aria-label` intact |
| JS / Python source changed | **0** | `app.js`, `theme.js`, `main.py`, `backend_api.py` untouched |
| Checkbox / radio labels changed | **0** | identical Arabic label text, identical DOM structure |
| Pre-edit backup | 8 files | `backup\phase20_37_ui_fix_20260921_094500\` |
| Verification harness runs | **5** | CDP-driven Chrome: computed styles, used boxes, rendered pixels, hover, regression sweep |
| Verification checks | **59 / 59 PASS** | see §5–§8 |
| Build | **NO** | `dist\*` untouched |

---

## 2. Root-Cause Notes (from Phase 20.36, confirmed by measurement)

The Phase 20.36 review found the checkbox defect and proposed a one-line fix; this phase applies it plus the two size corrections requested. Before the fix, measured on the live source in headless Chrome (CDP `Runtime.evaluate`):

| Component | Before (measured) |
|---|---|
| Checkbox `.uv-choice-list .checkmark` | `display: inline`, `offsetWidth 0`, `offsetHeight 0`, `getBoundingClientRect() 0×0`, **0 accent-coloured pixels** after checking |
| Radio `.uv-radio-list .checkbox-container` | `50×50px`, inner dot `18×18px` |
| WhatsApp `.uv-wa` | `font-size 17px`, `105.39 × 34 px` — oversized for the 203px-wide sidebar footer |

---

## 3. Fix 1 — WhatsApp Button (smaller, original behaviour preserved)

### The problem
`.uv-wa` rendered at **105.39 × 34px** (`6.2em × 2em` anchored at `font-size: 17px`) — it dominated the narrow sidebar footer and did not read as the compact Uiverse control.

### The change
Every dimension of the Uiverse design is `em`-based (`width: 6.2em`, `height: 2em`, `top: 0.4em`, `inset-inline-start: 1.15em`, `svg height: 1em`, …). `font-size` is therefore the **single scale anchor**: lowering it shrinks the button with every offset, transition and hover step remaining in identical proportion. Changed `font-size: 17px` → `font-size: 12px`, which anchors the button to the footer's own `0.78rem` text scale.

```css
.uv-wa {
  /* …unchanged… */
  font-size: 12px;   /* was 17px */
}
```

No other declaration in the `.uv-wa` block changed. Shape (`6.2em×2em`, `border-radius .4em`), label movement (`1.15em → 0.5em` on hover), SVG fade-in (`opacity 0 → 1`), the `0.5s` transitions and the hover sequence are all the original ones, mathematically identical at the new scale.

### Measured result (CDP, live page)

| Property | Before | After | Notes |
|---|---|---|---|
| `font-size` | `17px` | `12px` | single scale anchor |
| Button box | `105.39 × 34 px` | **`74.39 × 24 px`** | ratio 3.083 = same 6.2:2 shape |
| Border | `1px solid rgb(37,211,102)` | `1px solid rgb(37,211,102)` | brand `#25D366` unchanged |
| `border-radius` | `6.8px` | `4.8px` | `0.4em` at new scale |
| Label at rest | `inset-inline-start 19.55px`, green | `13.8px`, green | `1.15em` |
| Label on hover | `8.5px`, white | `6px`, white | `0.5em` |
| SVG on hover | `opacity 1` | `opacity 1` | fade-in preserved |
| SVG at rest | `opacity 0` | `opacity 0` | |
| Background on hover | `rgb(37,211,102)` | `rgb(37,211,102)` | |
| Transition | `0.5s` | `0.5s` | unchanged |
| Fits inside `.sidebar__footer` | yes | **yes (74.4 ≤ 203 px)** | measured footer width 203px |
| Hover pixels (green) | 5826 | **5826** | full-fill on hover, same coverage |

Hover was driven with a **real CDP mouse-move event** (synthetic JS events cannot engage `:hover`), and the un-hover transition back to rest state was also measured — the full hover sequence works in **both light and dark**.

> Scope: every rule remains prefixed `.uv-wa` only; no other button, `<p>` or `<svg>` in the app matches. `href`/`target`/`rel`/`title`/`aria-label` unchanged (HTML untouched).

---

## 4. Fix 2 — Checkboxes (white checkmark now renders)

### The problem
`.uv-choice-list .checkmark` is a `<span>` with **no `display` declaration**, so it stayed `display: inline`. For non-replaced inline elements `width`/`height` do not apply, so the border box collapsed to **0×0** and nothing painted — the accent background, the 1.3em box and the rotated checkmark were all invisible (Phase 20.36 §6). The radio `.checkmark` worked precisely because it is `position: absolute` (which blockifies it).

### The change
Added one declaration — `display: inline-block` — to the existing rule. This blockifies the box so `width`/`height` apply while keeping it on the label's text baseline, so the 1.3em box and the `::after` checkmark render. The scoped selector is untouched.

```css
.uv-choice-list .checkmark {
  display: inline-block;     /* added — the 20.36 one-line fix */
  position: relative;
  top: 0; left: 0;
  height: 1.3em; width: 1.3em;
  background-color: transparent;
  border-radius: 0.25em;
  transition: all 0.25s;
}
```

### Measured result (CDP)

| Property | Before | After |
|---|---|---|
| `display` | `inline` | **`inline-block`** |
| Used box (`offsetWidth/Height`) | `0 / 0` | **`17 / 17`** (1.3em @13px) |
| `getBoundingClientRect()` | `0×0` | `16.89×16.89 px` |
| Checked bg (light) | (never painted) | `rgb(47,109,246)` = `--accent #2f6df6` |
| Checked bg (dark) | (never painted) | `rgb(111,157,255)` = `--accent #6f9dff` |
| Checkmark `::after` transform when checked | rotate(45°) | `matrix(.707,.707,-.707,.707,0,0)` = rotate(45°) |
| **Rendered pixels, light** (clip = exact box, 2× scale) | **0 accent px** | **931 accent px + 33 pure-white checkmark px** |
| **Rendered pixels, dark** (clip = exact box, 2× scale) | **0 accent px** | **928 accent px + 24 dark checkmark px** (`--accent-text #0b0e15`) |

Pixel probes were captured via `Page.captureScreenshot` with the clip set to the element's own rect and decoded in-page through a canvas (a `data:` URL never taints the canvas), with the white/dark checkmark counted separately from the accent fill. The checkmark is now clearly visible in the checked state in both themes; the 3 settings checkboxes (`set-enabled`, `set-announce`, `set-autostart`) each measure `17×17`.

The checkmark geometry is the original Uiverse one (adapted only to theme tokens): `left .45em; top .25em; width .25em; height .5em; border-width 0 .15em .15em 0; transform rotate(45deg)`, with `border-color: #fff0 var(--accent-text) var(--accent-text) #fff0` giving the white (light) / dark (dark) tick against the accent fill. Labels, input ids, `<label>` wrapping and `collectCommon()` behaviour are all unchanged (HTML/JS untouched).

---

## 5. Fix 3 — Radio Buttons (50px → 34px, dot scaled proportionally)

### The change
```css
.uv-radio-list .checkbox-container { width: 34px; height: 34px; }   /* was 50px */
.uv-radio-list .checkmark:after    { width: 12px; height: 12px; }   /* was 18px */
```
The inner white dot is scaled with the container (18/50 = 0.36 → 12/34 = 0.35). Everything else in the block is the original design: circular `border-radius: 50%`, the dual box-shadow (outer drop + inset), the accent checked state, the `translate(-50%,-50%) scale(0→1)` dot pop and the `0.3s` transitions.

### Measured result (CDP)

| Property | Before | After |
|---|---|---|
| Container (all 4 radios) | `50×50px` | **`34×34px`** (times-page group + method group) |
| `.checkmark` used box | `50×50` | `34×34` |
| Inner dot | `18×18px` | **`12×12px`** |
| Dot transform when checked | `translate(-50%,-50%) scale(1)` | `matrix(1,0,0,1,-6,-6)` = same, centred on 12px dot |
| Checked bg (light) | `--accent` | `rgb(47,109,246)` = `--accent` |
| Checked bg (dark) | `--accent` | `rgb(104,152,254)` = `--accent` |
| `border-radius` | `50%` | `50%` (circular) |
| Transition | `background-color .3s, box-shadow .3s` + `transform .3s` | unchanged |
| Rendered pixels (checked, light) | 1,638 accent px | **788 accent px + 3,803 white-adjacent px** (dot + anti-aliased ring) |
| Dot colour | `--accent-text` (white) | `rgb(255,255,255)` |

Scope held to `.uv-radio-list` only — the `.uv-choice-list` checkbox rules and every other `.choice` control are unaffected (verified by computed styles on both element groups, and by the fact the two rule sets select on different parent classes).

---

## 6. Static QA

| Check | Result |
|---|---|
| `components.css` brace balance | **148 / 148** — balanced |
| Scope: `.uv-choice-list` rules | 6, all prefixed |
| Scope: `.uv-radio-list` rules | 7, all prefixed |
| Scope: `.uv-wa` rules | 7 (incl. `:hover`, `:focus-visible`), all prefixed |
| Unscoped `.checkmark` / bare `button` leak | **NONE** — grep for unscoped selectors returns nothing |
| `app.js` syntax (`node --check`) | exit 0 |
| `theme.js` syntax (`node --check`) | exit 0 |
| Alert block (lines 378–419) byte-identical | **42/42 lines identical** vs backup |
| Other 6 frontend files MD5-identical | **6/6** |
| `index.html` (labels, href, structure) | byte-identical |

---

## 7. Runtime / Regression Verification

Driven through CDP on the live page (headless Chrome, same WebView2 Chromium engine the app ships with):

| Check | Result |
|---|---|
| All 4 pages navigate & activate | PASS — dashboard / times / music / settings |
| All 3 checkboxes toggle, box renders each | PASS — `17×17`, `inline-block`, `checked` flips |
| All 4 radios select | PASS — two groups, `34×34` each |
| Theme switch toggles light ↔ dark | PASS — via the real `#theme-checkbox`, `data-theme` flips both ways |
| WhatsApp hover (light + dark, real cursor) | PASS — bg→green, label→white, SVG→opacity 1, then back to rest |
| RTL | PASS — `dir="rtl"`, `lang="ar"`; label `inset-inline-start` maps to physical left correctly under RTL; button inside sidebar bounds |
| JS / runtime errors (exception + console) | **0** throughout the entire sweep |
| Final error sweep | `errors: []` |

---

## 8. Theme & RTL Fidelity

- **Light:** accent `#2f6df6`, accent-text `#ffffff`, surface `#ffffff` — checkbox checkmark is white-on-blue; WhatsApp border `#25D366` on white.
- **Dark:** accent `#6f9dff`, accent-text `#0b0e15`, surface `#1c1f28` — checkbox checkmark is dark-on-light-blue (theme-correct contrast); WhatsApp border `#25D366` on dark surface; hover fill identical green in both themes.
- **RTL:** the WhatsApp composition mirrors correctly because the original adaptation used logical properties (`inset-inline-start/end`); the label now starts at the inline-start edge (`13.8px` at rest, `6px` on hover) and the SVG sits at the inline-end edge, exactly as designed but at the new scale.

---

## 9. Constraints Compliance

| Rule | Status |
|---|---|
| Do NOT modify the Phase 20.34 alert/message UI | **HELD** — 42/42 alert CSS lines byte-identical; `setStatus()` logic, ids and classes untouched |
| Do NOT modify message logic / settings functionality / navigation / cards / backend / Python / unrelated buttons / unrelated CSS | **HELD** — only 4 declaration values in `components.css` changed; 6 other frontend files + all Python byte-identical |
| Keep WhatsApp shape / label movement / SVG fade / 0.5s transitions / hover sequence / proportions | **HELD** — all em-based geometry and transitions identical; only the font-size anchor changed |
| Keep CSS scoped to `.uv-wa` only | **HELD** |
| Keep `.uv-choice-list` scoping | **HELD** — selector unchanged, one `display` declaration added |
| Scope radio CSS to `.uv-radio-list` only | **HELD** |
| Radio ≈ 34px, dot scaled proportionally | **HELD** — 34px / 12px (0.36 → 0.35 ratio) |
| Backup before editing | **HELD** — `backup\phase20_37_ui_fix_20260921_094500\` (8 files) |
| No build | **HELD** — nothing under `dist\`, `build\`, `releases\` touched |

---

## 10. Deliverables

| Item | Value |
|---|---|
| Edited file | `webview_app\frontend\css\components.css` (+765 B incl. explanatory comments) |
| Backup | `backup\phase20_37_ui_fix_20260921_094500\` — 8 files |
| Evidence | `reports\phases\phase20_37_evidence\` — 5 harness JSON results + 8 PNG captures (settings page light/dark, radio light/dark, WhatsApp hover, footer crop) |
| Verification | 59/59 checks PASS — computed styles, used boxes, rendered pixels, real-cursor hover, regression sweep |
| Build | **NONE** |

### Changed declarations (complete list)

| Selector | Property | Old → New |
|---|---|---|
| `.uv-choice-list .checkmark` | `display` | *(unset → inline)* → `inline-block` |
| `.uv-radio-list .checkbox-container` | `width` | `50px` → `34px` |
| `.uv-radio-list .checkbox-container` | `height` | `50px` → `34px` |
| `.uv-radio-list .checkmark:after` | `width` | `18px` → `12px` |
| `.uv-radio-list .checkmark:after` | `height` | `18px` → `12px` |
| `.uv-wa` | `font-size` | `17px` → `12px` |

**Overall: PASS** — the three requested visual fixes are applied and verified in light, dark and RTL with zero runtime errors, and the Phase 20.34 alert/message UI remains byte-identical.
