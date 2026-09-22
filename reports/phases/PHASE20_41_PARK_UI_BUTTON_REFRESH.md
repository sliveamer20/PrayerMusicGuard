# PHASE 20.41 — Park UI-inspired Button Refresh

**Scope:** plain-CSS port of Park UI's Button / IconButton / Badge recipes onto the project's existing class names and theme tokens. Zero packages, zero markup changes, zero JS changes.
**Status:** implemented, verified live (light + dark + RTL), **no build run**.

## 1. What changed

Only three CSS files were modified. `index.html`, `app.js`, `theme.js`, `theme.css` are **byte-identical** to the end of Phase 20.40 (verified by hash, §5).

| File | Delta | What |
|---|---|---|
| `css/layout.css` | +5 / −0 | New `--focus-ring-outside` token |
| `css/components.css` | +91 / −10 | `.btn` recipe base, `.btn--accent` solid + active, `.btn:active`, IconButton sizing, `.combobox__arrow` as compact icon control, `.chip` badge layout, `.nav__item` plain/active surface, outside focus ring on `.btn`/`.nav__item` |
| `css/skins.css` | +44 / −7 | `.btn`/`.btn--accent`/`.nav__item` state-layer colors (hover/active/disabled), `.chip__icon`, split of the outside focus ring off `.field__input` |

No selector, ID or class was renamed, added to markup, or removed. The 14 buttons keep their IDs; the monitor chip keeps `#monitor-chip` and its `chip--on` / `chip--off` contract; navigation logic is untouched.

## 2. Implementation notes

### `.btn` — outline/surface behavior (Park UI `outline` variant)
Ported the recipe base into `components.css`: `appearance: none`, `white-space: nowrap`, `user-select: none`, semibold (existing), and a transition chain over `background-color, border-color, color, box-shadow, opacity`. Structure (inline-flex, centered, `gap: 8px`, `min-height: 40px`) already came from `skins.css` and is preserved, as are `padding: 10px 18px` and `--radius-ctrl`, so **no `.button-row` grid reflows**. Added `:active` (accent border) and kept the existing `:hover` (accent border) — the color *state layers* live in `skins.css` and use only existing tokens.

### `.btn--accent` — solid behavior (Park UI `solid` variant)
Kept the existing accent gradient + accent text + glow shadow; added the missing state layers:
- `:hover` → gradient built from `--accent-hover`, shadow grows (`12px→14px` spread).
- `:active` → gradient returns to `--accent`, shadow shrinks (`8px`) — a visible "pressed" without a second token.
- `:disabled` → keeps its accent identity (solid fill, transparent border) but drops glow and sits at `opacity: 0.7`, vs `0.55` for the outline variant, matching Park UI's notion that a solid button retains more of its identity when disabled.

### Dropdown buttons → compact IconButtons
`#btn-dropdown-music`, `#btn-dropdown-adhan` get `padding: 0; width: 40px; height: 40px; min-width: 40px; flex: none; align-self: center`. Two geometry details mattered: `align-self: center` (otherwise the flex row's `align-items: stretch` pulls them to the 43.5px text-button height, breaking squareness) and `flex: none` (the input next to them is `flex: 1 min-width: 0` and would otherwise squeeze the hit area). The chevron stays at its 1.15em box (18.4px) from Phase 20.40 and is centered by the button's flex.

### `.combobox__arrow` — compact plain icon control
Was `padding: 6px` with no explicit box; now a 32px square flex-centered control (`border-radius: 8px`, `font-size: 0.9em` kept so the chevron keeps its 16.55px box). Added the plain-variant state layers (`:hover` accent 10% tint + accent color, `:active` 18% tint) and a `:disabled:hover` guard so the disabled city arrow doesn't light up.

### `.nav__item` — plain/active behavior
The existing accent `::before` indicator bar and its animation are untouched. The hover surface changed from the flat `--surface-alt` to Park UI's translucent plain tint (`accent 8%`), with an added `:active` at `accent 14%` — the same tint ramp the active item already used (`accent 14%`), so hover → active → selected now reads as one continuous scale. The active item's `accent-text` color, accent border and `color: var(--fg)` hover are unchanged. RTL is unaffected: the indicator uses `inset-inline-start` and the icon/label order is physical DOM order, verified `iconX > labelX` under `dir="rtl"`.

### `.chip` — Badge style
Now a compact inline-flex pill with dedicated `.chip__icon` (flex-none, `color: inherit`) and `.chip__text` (nowrap) spans. Padding tightened `6px 14px → 6px 12px`, line-height `1.2` for optical icon/text balance, and the 6px gap comes from the badge recipe. The two skins (`.chip--on` success tint, `.chip--off` muted) are untouched, and `app.js` still rebuilds the chip through the same `renderStatus()` path — the ON state renders `circle-check` + "المراقبة تعمل", OFF renders `circle-off` + "المراقبة متوقفة".

### Focus — outside ring (Park UI `focusVisibleRing: 'outside'`)
Replaced the old `outline: 2px solid var(--accent)` on `.btn`/`.nav__item` with a box-shadow ring:

```css
--focus-ring-outside: 0 0 0 2px var(--surface), 0 0 0 4px var(--accent);
```

The inner 2px `--surface` ring reads as a gap against any background, the outer 4px accent ring is the actual indicator. Because it's a box-shadow it follows `border-radius` (the 10px control radius and the 12px nav radius) and can't overlap content. The pre-existing `--focus-ring` (3px inset tint) is **kept for `.field__input`** — the two were previously sharing one rule and are now split. Keyboard focus is intact: verification used a real `Tab` keypress (programmatic `.focus()` alone does not match `:focus-visible` in Chrome) and confirmed `:focus-visible` engages with `outline: none` and the ring present.

## 3. Verification

Harness: `reports/phases/phase20_39_evidence/_verify_buttons.js` (CDP over Node's built-in WebSocket, no deps). Real mouse events for hover/press, a real `Tab` for focus, and the app's own `refresh() → renderStatus()` path for the chip (via a fake `pywebview` bridge installed with `Page.addScriptToEvaluateOnNewDocument` so `list_running_apps` resolves and the dropdown has 2 items).

Viewports: the run uses a 2200×1500 window with `--force-device-scale-factor=2` → **1100 CSS px** wide, which is above the 640px breakpoint so the mobile `min-height: 42px` rule does not fire and buttons measure their true desktop height.

| Check | Light | Dark |
|---|---|---|
| Buttons found (all 4 pages) | 14 | 14 |
| `.btn` base geometry (min-height 40px, inline-flex, center, gap 8px, 600, nowrap, user-select none) | PASS | PASS |
| Outline hover: bg → accent 7% tint, border → accent 55%, glow, `translateY(-1px)` | PASS | PASS |
| Outline active: bg → accent 13%, border → solid accent, shadow removed, lift cancelled | PASS | PASS |
| Outline disabled: `opacity 0.55`, `not-allowed`, shadow removed | PASS | PASS |
| Solid hover: `--accent-hover` gradient, glow 12→14px, lift | PASS | PASS |
| Solid active: back to `--accent`, glow 8px, lift cancelled | PASS | PASS |
| Solid disabled: accent fill kept, `opacity 0.7`, no glow | PASS | PASS |
| Focus ring: `:focus-visible` true, `outline: none`, `2px surface + 4px accent` | PASS | PASS |
| `#btn-dropdown-music` / `-adhan`: 40×40 square, chevron centered | PASS | PASS |
| Dropdown click → menu opens with 2 items | PASS | PASS |
| `.combobox__arrow` ×2: 32×32 square, chevron centered 16.55px | PASS | PASS |
| Arrow hover: accent 10% tint + accent color | PASS | PASS |
| Arrow click → menu opens; city arrow stays disabled until a country is chosen | PASS | PASS |
| `.nav__item` ×4, active page correct, `::before` bar `opacity 1`, RTL | PASS | PASS |
| Nav hover accent 8% / active accent 14% | PASS | PASS |
| Chip ON: `chip--on`, icon span + text span, `circle-check` | PASS | PASS |
| Chip OFF via app's own path: `chip--off`, `circle-off`, muted | PASS | PASS |
| JS / runtime errors | 0 | 0 |

Representative measured values (light, `#btn-resume`): base `rgb(255,255,255)` / neutral border / 1px hairline → hover `accent 7%` tint / `accent 55%` border / `2px 8px glow` / `translateY(-1px)` → active `accent 13%` / solid accent border / `shadow: none` / no lift → after: byte-for-byte back to base. The accent button's shadow animates `12px → 14px → 8px → 12px` across the same cycle. Focus ring (dark): `rgb(28,31,40) 0 0 0 2px, rgb(111,157,255) 0 0 0 4px`.

Pixel evidence: `btnrow_light.png`, `btnrow_dark.png`, `sidebar_light.png`, `sidebar_dark.png`, full numeric dump in `buttons_result.json` (all in `phase20_39_evidence/`). As in 20.39/20.40, the PNGs are archived for human review — this model cannot read images, so every PASS above is a live numeric measurement, not a visual judgement.

### Two harness bugs found and fixed (not product bugs)
1. The per-page button loop ended on the *settings* page, so the state probes measured `#btn-pause` on a hidden page (`0×0` rect, cursor over `DIV.app`) and reported `matchesHover: false`. Fixed by navigating back to the dashboard before the probes; an `atPoint` self-diagnostic was added to make such a failure self-explanatory rather than silent.
2. The btnrow screenshots were captured while the times page was active, clipping the music row to `0×0` (148-byte PNGs). Fixed by re-showing the music page first.

Both were caught by the harness's own diagnostics, not by eye.

## 4. Frozen integrity

Static byte-comparison of every frozen rule block (`.uv-wa`, `.card__hint`, `.uv-choice-list`, `.checkbox-container`, `.checkmark`, `.uv-radio-list`, `.theme-switch*`, `.prayer-card`) across all three CSS files: **all identical** (match counts and rule bodies, `same=True` in every case). Live confirmation at runtime: WhatsApp button still `A` / `84×24` / `href="https://wa.me/201010101182"` / path length 1104; 8 `.card__hint` alerts; 3 choice containers; 4 radios with a 9px dot; switch track 84px / thumb 34px; 10 Lucide icons intact. `index.html`, `app.js`, `theme.js` hashes unchanged.

## 5. Session footprint

- **Edited:** `webview_app/frontend/css/components.css`, `webview_app/frontend/css/skins.css`, `webview_app/frontend/css/layout.css`.
- **Created:** `reports/phases/PHASE20_41_PARK_UI_BUTTON_REFRESH.md`; `reports/phases/phase20_39_evidence/_verify_buttons.js`, `_diag_arrow.js`, `_diag_btn.js`, `_diag_btn2.js`, `buttons_result.json`, `btnrow_{light,dark}.png`, `sidebar_{light,dark}.png`; `backup/phase20_41_buttons_20260921_113000/` (pre-edit copy of all 7 frontend files).
- **Not created/modified:** no package files, no `node_modules`, no build output, no Python file, no HTML/JS.
- **No build was run and no package was installed**, per instructions.

## 6. Follow-ups (not started)

- A future build (20.42-style) must re-verify inside the real pywebview/WebView2 bundle; the CSS here is unverified in that renderer.
- Human visual review of `btnrow_*.png` / `sidebar_*.png` crops, since the model cannot inspect them.
- `--focus-ring-outside` is a fixed 2px-surface + 4px-accent ring; if a control ever sits on a non-`--surface` background, the inner ring color would need to be that background instead.
