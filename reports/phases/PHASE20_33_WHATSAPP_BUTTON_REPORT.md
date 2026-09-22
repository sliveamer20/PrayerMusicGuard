# PHASE 20.33 — Developer WhatsApp Button Report

**Project:** `E:\prayer-music-guard`
**Date:** 2026-09-20
**Phase:** 20.33 — Developer WhatsApp Button (follows Phase 20.32, which PASSED)
**Mode:** Add exactly one developer-contact button using the provided Uiverse design. No JS change, no build.

---

## 1. Summary of Actions

| Action | Count | Detail |
|---|---|---|
| Frontend files EDITED | **2** | `webview_app\frontend\index.html` (+1,461 B), `webview_app\frontend\css\components.css` (+1,541 B) |
| Uiverse rules added | 8 | Scoped to `.uv-wa` (this button only) |
| Buttons added | **1** | WhatsApp → `https://wa.me/201010101182` |
| JS written to open it | **0** | Plain `<a target="_blank">`; pywebview opens it natively |
| JS / Python source changed | **0** | `app.js`, `theme.js`, `main.py` byte-identical to Phase 20.32 |
| Other CSS files changed | **0** | `skins.css`, `theme.css`, `layout.css` byte-identical |
| Phase 20.31 / 20.32 controls changed | **0** | Both CSS blocks byte-identical (verified, not assumed) |
| Existing buttons modified | **0** | All 14 button ids present and unmoved |
| Pre-edit backup created | 7 files + harness | `cleanup_backup_phase20_33\` |
| Verification checks | **39 / 39 PASS** | `cleanup_backup_phase20_33\_verify_whatsapp.js` |
| Regression (20.31 / 20.32) | **26/26 + 31/31 PASS** | re-run against the edited files |
| Build performed | **NO** | `dist\Phase20-28-Release` untouched |

---

## 2. Placement Decision

**Chosen: the sidebar footer** — immediately below the developer attribution line that is already there.

```html
<div class="sidebar__footer">
  <div class="sidebar__divider sidebar__divider--footer"></div>
  <span>الإصدار <span id="app-version">—</span></span>
  <div …>اسم مبرمج البرنامج: أيمن علاء أبو ليلة</div>
  <a class="uv-wa" href="https://wa.me/201010101182" …>   <!-- NEW -->
</div>
```

Why this location, against each stated constraint:

| Requirement | How it is satisfied |
|---|---|
| *Most natural, balanced* | The footer is the app's existing "developer zone" — it already carries the programmer's name and version. A contact button beside that attribution is the most semantically natural spot, and it sits in a low-visibility area, not on a working surface. |
| *Do not overcrowd* | The footer was 3 short lines in a ~228 px-wide sidebar. One 105 px button appended below them leaves ample whitespace; nothing is competing for space. |
| *Do not move existing controls* | The button is **appended** as the last child of the footer. The divider, version span, and name div keep identical markup, order, and offsets — verified byte-for-byte. |
| *Responsive layout and RTL* | The sidebar is a flex column, so the button simply stacks; at ≤820 px the whole footer is hidden by the existing `layout.css:247` rule, so mobile is unchanged. Positioning uses logical `inset-inline-*` so the composition mirrors under `dir="rtl"`. |
| *Persistent* | The sidebar is present on all 4 pages, so the developer is reachable anywhere — unlike a page-specific placement (e.g. the Settings card), which would only exist on one page and would crowd a form. |

Rejected alternatives: the topbar (already holds the monitor chip + theme switch — overcrowded), the Settings card (page-local, and would sit among form controls), and the nav list (would read as a 5th page).

---

## 3. Click Behavior — Zero JS

The button is a real hyperlink, not a script-driven element:

```html
<a class="uv-wa" href="https://wa.me/201010101182" target="_blank"
   rel="noopener noreferrer" title="مراسلة المطور عبر واتساب"
   aria-label="مراسلة المطور عبر واتساب">
  <p>WhatsApp</p>
  <svg …/>
</a>
```

This works because of how the app's own runtime handles external links. pywebview 6.2.1's EdgeChromium backend registers a `NewWindowRequested` handler (`webview\platforms\edgechromium.py:255-261`):

```python
def on_new_window_request(self, sender, args):
    args.set_Handled(True)
    if webview_settings['OPEN_EXTERNAL_LINKS_IN_BROWSER']:   # defaults to True
        webbrowser.open(str(args.get_Uri()))
    else:
        self.load_url(str(args.get_Uri()))
```

So a `target="_blank"` click is intercepted and handed to the OS browser — **no `onclick`, no `window.open`, no `app.js` change**. This is the *lowest-risk* implementation available: it cannot throw a JS error, cannot break the bridge, and cannot be shadowed by any existing handler. `rel="noopener noreferrer"` prevents tab-reverse-link access.

---

## 4. The Design Used

The provided Uiverse snippet (Uiverse.io by alshahwan) was applied with its structure intact:

```css
.uv-wa { width:6.2em; height:2em; border:1px solid #25D366; border-radius:.4em; padding:5px; font-size:17px; transition:.5s; }
.uv-wa p  { position:absolute; top:.4em;  inset-inline-start:1.15em; transition:.5s; }
.uv-wa svg{ position:absolute; top:.45em; inset-inline-end:0.5em;   opacity:0; transition:.5s; height:1em; fill:#fff; }
.uv-wa:hover p   { inset-inline-start:0.5em; color:#fff; }
.uv-wa:hover svg { opacity:1; }
.uv-wa:hover     { background-color:#25D366; }
```

### 4.1 Adaptations (each deliberate, each documented)

The instruction was *"adapt only colors if needed for the theme"* and *"keep RTL"*. Two adaptations were needed:

| Change | Why | Impact on the design |
|---|---|---|
| `background-color: #fff` → `var(--surface)` | `--surface` is `#ffffff` in light and `#29292d` in dark. A literal `#fff` would render as a glaring white slab on the dark sidebar. | **None in light theme** (the token resolves to the same `#ffffff`). Dark theme gains a surface-matched fill instead of pure white. |
| `left`/`right` → `inset-inline-start`/`inset-inline-end` | The app is `dir="rtl"`. Physical offsets would keep the label pinned to the visual left edge even in RTL, breaking the composition's mirroring. | Geometry is identical in LTR; in RTL the label/icon correctly swap sides. |

**Retained deliberately:** the brand green `#25D366` is kept as the button's own token (`--wa`) for border, label, and hover fill. WhatsApp's green is the recognizable affordance — replacing it with the app's blue accent would defeat the button's purpose, and green reads well on both light and dark surfaces. The inner-dot/label white on hover is likewise kept literal.

### 4.2 Preserved exactly

6.2em × 2em box, 0.4em radius, 5px padding, 17px font, all `0.5s` transitions (three of them), the label slide on hover, the SVG fade-in, `fill: #fff`, and the `opacity: 0 → 1` mechanism.

### 4.3 Additions (not in the snippet, no design change)

- `text-decoration: none` — required because the element is an `<a>`, not a `<button>` (the original styled a `<button>`).
- `display: inline-block` + `flex: none` — so the fixed `em` box is honored inside the flex-column sidebar.
- `.uv-wa:focus-visible { outline: 2px solid var(--accent) }` — matches the app's existing `.btn:focus-visible` convention for keyboard users.
- `title` / `aria-label` (Arabic: "مراسلة المطور عبر واتساب") and `aria-hidden="true"` on the decorative SVG.

### 4.4 Official WhatsApp logo

The SVG uses the standard 24×24 WhatsApp glyph (the same path shipped by the brand's own assets / Simple Icons):

```html
<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M17.472 14.382c-.297-.149-1.758-.867 …"/></svg>
```

---

## 5. Scoping

The provided snippet uses bare `button`, `button p`, `button svg` selectors — applied verbatim, they would have restyled **every button in the app**. Every selector was therefore prefixed with `.uv-wa`:

| Provided | Implemented |
|---|---|
| `button` | `.uv-wa` |
| `button p` | `.uv-wa p` |
| `button svg` | `.uv-wa svg` |
| `button:hover p` | `.uv-wa:hover p` |
| `button:hover svg` | `.uv-wa:hover svg` |
| `button:hover` | `.uv-wa:hover` |

Verified: **zero** bare `button`/`button p`/`button svg` selectors remain in the added block, and `.uv-wa` appears on exactly one element in the document. The class name was chosen to not collide with any existing class.

---

## 6. Verification — 39 / 39 PASS

Harness: `cleanup_backup_phase20_33\_verify_whatsapp.js` (Node, zero dependencies).

| Group | Checks | Result |
|---|---|---|
| **1. Presence / placement** | exactly one button; inside `.sidebar__footer`; developer name + version still present and before it; footer is original prologue + appended button; 4 nav items unchanged | **5/5 PASS** |
| **2. URL / click behavior** | href exactly `https://wa.me/201010101182`; phone digits-only, no `+`/`0020`; `target="_blank"`; `rel="noopener noreferrer"`; element is an `<a>`; **no JS references the URL or the button**; `app.js` byte-identical; no inline `onclick`/`window.open` | **8/8 PASS** |
| **3. Uiverse fidelity** | label exactly `WhatsApp`; official glyph + single path + `viewBox 0 0 24 24`; geometry (6.2em/2em/0.4em/5px/17px) preserved; all `0.5s` transitions; hover slide + fade + fill; SVG opacity/fill behavior | **6/6 PASS** |
| **4. Theme + RTL** | brand green token retained; `--surface` resting bg (no literal `#fff`); green hover fill; label color token + white hover; **logical `inset-inline-*` with no physical left/right remaining**; `dir="rtl"` intact; `--surface` resolves in both themes and differs between them; fits sidebar width; a11y attributes; focus ring | **11/11 PASS** |
| **5. Scoping** | no bare selectors leaked; `.uv-wa` on one element only; **20.31 checkbox + 20.32 radio CSS byte-identical**; all 14 existing button ids present; other frontend files byte-identical | **5/5 PASS** |
| **6. Syntax / runtime** | CSS braces balanced; every `var()` resolves; HTML tag balance matches the original; URL well-formed; **only `index.html` + `components.css` changed** | **5/5 PASS** |

### 6.1 Runtime / syntax safety

| Check | Result |
|---|---|
| `node --check js/app.js` | **OK** (exit 0) |
| `node --check js/theme.js` | **OK** (exit 0) |
| Python `ast.parse` (read-only): `main.py`, `webview_main.py`, `backend_api.py`, `app_entry.py`, `launcher.py` | **5/5 OK** |
| New `__pycache__` generated | **none** |

### 6.2 Regression: Phases 20.31 and 20.32

Both prior harnesses were **re-run against the now-edited files**:

- Phase 20.31 checkbox harness: **26 / 26 PASS**
- Phase 20.32 radio harness: **31 / 31 PASS**

The checkbox and radio CSS blocks are byte-identical to their Phase 20.32 state, so the two Uiverse controls are provably untouched.

### 6.3 Nothing outside the two intended files changed

| File | Status |
|---|---|
| `index.html` | **edited** (+1,461 B) — button appended in sidebar footer |
| `css\components.css` | **edited** (+1,541 B) — the `.uv-wa` block appended after the radio block |
| `css\skins.css`, `css\theme.css`, `css\layout.css`, `js\app.js`, `js\theme.js` | **5/5 byte-identical** |

Protected trees vs the Phase 20.30 baseline: all 9 root source/config hashes identical; `dist\Phase20-28-Release`, `releases`, `backup`, `build`, `build-win7-test`, `vendor`, `win7`, `assets`, `.opencode` all identical. `webview_app` reflects only this phase's 2-file edit; `reports` gained this report only.

### 6.4 Key file hashes (post-phase)

| File | SHA-256 |
|---|---|
| `webview_app\frontend\index.html` | `4FA5B6ED50FC392BD71D3F04A59D2A10B4892887C3F0432C86E7CCD24ECD9CC0` |
| `webview_app\frontend\css\components.css` | `B68166946ECF717C039AEA417AB74B71426061A3972C4EA136BEF70089B671A2` |
| `webview_app\frontend\js\app.js` | `3ED308E7972B4B0811F85F2896C4E4C4B70BA793ED3886F2E51DBCC0DEAB77F1` |
| `main.py` | `6E998725B1E41D52B98B353D42E2B8CF0BCB675C95999E2EA1D1DD3CF7397AAB` |

---

## 7. Pre-Edit Backup

```
cleanup_backup_phase20_33/
├── index.html                 # 15,581 B (pre-edit)
├── css__components.css        # 18,749 B (pre-edit)
├── css__skins.css             # unchanged
├── css__theme.css             # unchanged
├── css__layout.css            # unchanged
├── js__app.js                 # unchanged
├── js__theme.js               # unchanged
├── _baseline_files.csv        # pre-edit hashes
├── _pycheck.py                # read-only ast.parse helper
└── _verify_whatsapp.js        # 39-check verification harness
```

Both edited files are recoverable verbatim.

---

## 8. Notes & Trade-offs

- **`<a>` instead of `<button>`**: the provided design styles a `<button>`, but a real hyperlink is strictly better here — it gives correct semantics, middle-click/new-tab behavior, and lets pywebview's own external-link handler do the opening. The design's appearance is fully preserved; only the element type differs.
- **External-link opening depends on the runtime, not on this phase**: `OPEN_EXTERNAL_LINKS_IN_BROWSER` defaults to `True` in pywebview (`webview\__init__.py:125`). If a deployment sets it `False`, the URL loads *inside* the window instead of the OS browser — still correct behavior, just in-app. Nothing in this phase depends on either outcome.
- **Dark-theme adaptation**: the resting fill uses `--surface` rather than the literal `#fff`. Light theme is pixel-identical to the provided design; dark theme avoids a white slab. The green brand color is untouched.
- **Mobile**: the sidebar footer is hidden below 820 px by pre-existing CSS (`layout.css:247`), so on narrow screens the button is not shown. This is the app's existing decision for footer content, not a new one.
- **No rebuild**: `dist\Phase20-28-Release` still contains the Phase 20.28 build and does not include this button or the 20.31/20.32 controls. Intentional — *"NO BUILD"*. A later build phase will pick all three up from source.
- **Reference provenance**: the Uiverse CSS and SVG were supplied directly in the session prompt (Uiverse.io by alshahwan; official WhatsApp glyph); neither is present in the repository.

---

## 9. Result

### **PASS**

- Exactly one WhatsApp button added, in the sidebar footer directly beneath the developer attribution — the most natural, balanced location; no existing control moved and no overcrowding.
- Click opens `https://wa.me/201010101182` via a plain hyperlink intercepted by pywebview's `NewWindowRequested` handler — **zero JS added**, zero risk of a runtime error.
- Provided Uiverse design preserved: shape, geometry, hover animation (label slide + icon fade + green fill), all `0.5s` transitions, and SVG behavior. Only the resting background was re-tokenized for the dark theme and offsets converted to logical properties for RTL.
- Official WhatsApp logo SVG, correctly marked decorative with an Arabic `aria-label` for the action.
- Scoped to `.uv-wa` only — verified that no bare `button` selectors leaked; all 14 existing buttons, the 20.31 checkboxes, and the 20.32 radios are byte-identical, and both prior harnesses still pass 26/26 and 31/31.
- Light/dark theming works through existing tokens; RTL mirroring intact; JS 2/2 and Python 5/5 syntax-clean; no caches regenerated.
- Zero impact outside `index.html` and `components.css`; source/release/backup/build trees byte-identical to the Phase 20.30 baseline.

**No code changes (JS/Python). No build performed. Stopping after report, as instructed.**
