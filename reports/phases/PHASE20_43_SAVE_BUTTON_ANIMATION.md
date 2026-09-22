# PHASE 20.43 — SAVE BUTTON SUCCESS ANIMATION

**Uiverse.io "Saved" by ilkhoeri** → applied to the app's SAVE buttons, triggered on successful save instead of `:hover`.

- Source of truth: https://uiverse.io/ilkhoeri/chilly-sloth-36 (element slug confirmed by fetching the author profile and the element page; HTML + CSS extracted verbatim from the page's embedded JSON-LD `SoftwareSourceCode.text`).
- The supplied CSS block matches the published element **byte-for-byte**.
- Per requirement, the **only** behavioral change from the original is the trigger: `:hover` → temporary `.is-saving` success class.

---

## 1. TARGET BUTTONS

| Requested label | Actual button | ID | Page |
|---|---|---|---|
| حفظ المواقع | **حفظ المواقيت** | `btn-save-times` | Times |
| حفظ الإعدادات | حفظ الإعدادات | `btn-save` | Settings |
| (same save-success flow) | حفظ إعدادات المشغّل | `btn-save-music` | Music |

> Note: the request's "حفظ المواقع" corresponds to the existing **`حفظ المواقيت`** button (`btn-save-times`) — there is no "حفظ المواقع" label in the app. The third save button (`btn-save-music`) shares the exact `saveSettings()` success flow, so it was included per requirement *"Any other existing SAVE button only if it uses the same save-success flow."*

All three buttons were already wired through one shared handler:

```js
on("btn-save-times", function () { saveSettings("times-status"); });
on("btn-save",       function () { saveSettings("settings-status"); });
on("btn-save-music", function () { saveSettings("music-status"); });
```

---

## 2. CHANGES MADE

### 2.1 `frontend/index.html` — SVG injected, IDs preserved
Each save button's Arabic text is wrapped in `<span class="btn__label">` and the **exact Uiverse SVG** is appended. Button IDs, classes, `type`, and onclick wiring are unchanged.

```html
<button class="btn btn--accent" id="btn-save-times" type="button">
  <span class="btn__label">حفظ المواقيت</span>
  <svg class="save-anim" aria-hidden="true" xmlns="http://www.w3.org/2000/svg"
       width="20" height="20" stroke-linejoin="round" stroke-linecap="round"
       stroke-width="2" viewBox="0 0 24 24" stroke="currentColor" fill="none">
    <path d="m19,21H5c-1.1,0-2-.9-2-2V5c0-1.1.9-2,2-2h11l5,5v11c0,1.1-.9,2-2,2Z"
          stroke-linejoin="round" stroke-linecap="round" data-path="box"></path>
    <path d="M7 3L7 8L15 8" stroke-linejoin="round" stroke-linecap="round"
          data-path="line-top"></path>
    <path d="M17 20L17 13L7 13L7 20" stroke-linejoin="round" stroke-linecap="round"
          data-path="line-bottom"></path>
  </svg>
</button>
```

SVG geometry is the **published Uiverse markup, unmodified** (box path, line-top, line-bottom).

### 2.2 `frontend/css/skins.css` — Uiverse CSS (verbatim, re-triggered)
The full Uiverse block was appended to **skins.css** (the last-loaded sheet), so the container overrides win specificity ties against `.btn`, `.btn--accent`, the responsive `.button-row .btn` flex rule, and the 640px `.btn` min-height rule in **both themes**.

The **only** edits vs. the published Uiverse CSS:
1. Trigger selector `.has_saved:hover …` → `.btn.is-saving …` (the required change).
2. The container class `.action_has` → `.btn.is-saving` plus the three rules that swap label ↔ icon:

```css
.btn .save-anim              { display: none; }     /* icon hidden by default */
.btn.is-saving .btn__label   { display: none; }     /* text hidden during anim */
.btn.is-saving .save-anim    { display: block; }    /* icon shown during anim */
```

**Unchanged (verbatim):** all four `@keyframes` (`has-saved`, `has-saved-line-top`, `has-saved-line-bottom`, `has-saved-line-bottom-2`), every `d: path(...)` geometry string, `--ease: cubic-bezier(0.5, 0, 0.25, 1)`, `--zoom-from: 1.75`, `--zoom-via: 0.75`, `--zoom-to: 1`, `--duration: 1s`, the `0.75 × duration` staggered delay on `has-saved-line-bottom-2`, `fill: hsl(var(--color-has) / 0.35)`, and the `fill: white` finish.

Theme adaptation uses the Uiverse `--color` / `--color-has` custom properties (gray border + blue accent) which read correctly on both light and dark surfaces — no theme-specific override needed.

### 2.3 `frontend/js/app.js` — success-only trigger
`saveSettings()` gained an optional `triggerBtn` parameter. The animation fires **only inside the `res.ok` branch**; the failure branch is untouched.

```js
function saveSettings(messageId, triggerBtn) {
  setStatus(messageId, "جارٍ الحفظ…", "info");
  return call("save_settings", collectCommon()).then(function (res) {
    if (res && res.ok) {
      setStatus(messageId, "تم حفظ الإعدادات.", "success");
      if (triggerBtn) { playSaveAnimation(triggerBtn); }   // <-- success only
      if (res.state) { applyState(res.state); }
    } else {
      setStatus(messageId, "تعذر الحفظ: " + ..., "error");  // untouched
    }
  });
}
```

```js
var SAVE_ANIMATION_MS = 1000;

function playSaveAnimation(btn) {
  if (!btn || btn.dataset.saveAnimating === "1") return;   // double-trigger guard
  btn.dataset.saveAnimating = "1";
  btn.classList.add("is-saving");                            // runs animation once
  setTimeout(function () {
    btn.classList.remove("is-saving");                       // restore text + state
    delete btn.dataset.saveAnimating;                        // re-arm button
  }, SAVE_ANIMATION_MS);
}
```

The three click handlers now pass the button element. The two auto-save callers (`location_mode` radio change, `selectApp`) omit the argument and behave exactly as before.

---

## 3. FILES TOUCHED

| File | Change |
|---|---|
| `webview_app/frontend/index.html` | `btn__label` span + Uiverse SVG in 3 save buttons |
| `webview_app/frontend/css/skins.css` | Uiverse animation CSS (verbatim keyframes), re-triggered |
| `webview_app/frontend/js/app.js` | `saveSettings(msg, btn)`, `playSaveAnimation()`, handlers pass button |
| `webview_app/frontend/css/components.css` | **unchanged** (hash-verified vs backup) |
| `webview_app/frontend/css/theme.css`, `layout.css`, `theme.js` | **unchanged** |

**Backup:** `backup/phase20_43_save_animation_20260921_143000/frontend/{index.html, css/components.css, js/app.js}` (SHA-256 hash-verified).

**NOT modified (per requirement 9):** WhatsApp button, alerts, checkboxes, radios, Lucide icons, Park UI button styling, theme switch, navigation, Python/backend, save API.

---

## 4. VERIFICATION

### 4.1 Method
A live browser suite (`test_phase20_43.js`, Playwright + headless Chromium) loads the **real frontend over `file://`**, stubs the pywebview bridge so `save_settings` can be resolved success/failure on demand, **clicks the actual buttons**, and reads computed styles, CSS custom properties, `getComputedStyle`, and `getAnimations()`.

### 4.2 Live scenario matrix

| Scenario | Result |
|---|---|
| حفظ المواقيت → success → animation → text restored | ✅ pass |
| حفظ الإعدادات → success → animation → text restored | ✅ pass |
| حفظ إعدادات المشغّل → success → animation → text restored | ✅ pass |
| Failed save → **no animation**, error status shown | ✅ pass |
| Repeat save after animation → works again | ✅ pass |
| Light theme | ✅ pass |
| Dark theme | ✅ pass |
| RTL (`dir="rtl"`, `lang="ar"`) | ✅ pass |
| Zero JS/runtime errors | ✅ pass (no `pageerror`, no `console.error`) |

### 4.3 Numeric verification (all measured live in-browser)

| Property | Expected | Measured | Status |
|---|---|---|---|
| Animation duration | `1s` | `1s` (computed) · `1000ms` (`getAnimations`) · **1005/1019/1023/1022/1011/1020 ms** wall-clock | ✅ |
| Easing | `cubic-bezier(0.5, 0, 0.25, 1)` | `cubic-bezier(0.5, 0, 0.25, 1)` (computed `animation-timing-function` + per-keyframe) | ✅ |
| Zoom-from | `1.75` | `1.75` | ✅ |
| Zoom-via | `0.75` | `0.75` | ✅ |
| Zoom-to | `1` | `1` | ✅ |
| Runs exactly once | iteration count `1` | `1` (computed + `getComputedTiming().iterations`) | ✅ |
| SVG/path structure | 3 paths present | `3` on every button | ✅ |
| `data-path` attributes | box / line-top / line-bottom | exact order on every button | ✅ |
| Box path geometry | Uiverse `d` verbatim | byte-identical | ✅ |
| Line-top / line-bottom geometry | Uiverse `d` verbatim | verbatim in `@keyframes` | ✅ |
| All 4 keyframes registered | has-saved* | confirmed running via `getAnimations()` (raw-text check too — CSSOM `cssRules` is blocked on `file://` by Chromium CORS, so keyframes were verified via live animation instances + verbatim stylesheet text) | ✅ |
| Original text returns | label `display` restored | restored in all cases | ✅ |

### 4.4 Behavioral checks
- Normal state: Arabic label visible, **not** animating, SVG `display: none`, button is full-width text button (not icon-only). ✅
- On success: label hidden, SVG shown, button becomes the exact 40×40 Uiverse square icon, guard flag set. ✅
- Mid-animation second click is ignored (single run). ✅
- After ~1s: class removed, label visible, SVG hidden, guard cleared, button clickable again. ✅
- During animation: container `direction` stays `rtl`. ✅

### 4.5 Visual confirmation
Screenshots captured at normal / mid-animation (~350 ms, zoom+rotate phase) / restored states for light + dark: `reports/phases/phase20_43_shots/`. Region hashes confirm the button area **changes** during the animation and **returns** to the text state afterward (normal≠anim, anim≠restored). The icon clips differ from both text states.

### 4.6 Untouched-component regression checks
Theme switch, navigation (4 items), radios (4), checkboxes (4), Lucide icons (10), and pause/resume buttons all remain present and intact. `components.css` hash-identical to backup.

### 4.7 Syntax
`node --check` clean on `app.js` and `theme.js`.

---

## 5. RESULT

**196/196 automated checks passed**, 0 failures, 0 JS runtime errors.

The Uiverse "Saved" animation by ilkhoeri is now active on **حفظ المواقيت**, **حفظ الإعدادات**, and **حفظ إعدادات المشغّل**, firing exactly once on each **successful** save, with the original Arabic label and normal button state restored after exactly 1 second. Keyframes, timing, easing, zoom values, and SVG geometry are the published Uiverse values — unmodified. Failed saves keep the existing error behavior with no animation.

**No build performed** (per instruction). Verification only.
