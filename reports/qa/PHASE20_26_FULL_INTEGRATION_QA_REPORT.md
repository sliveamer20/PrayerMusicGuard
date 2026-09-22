# Phase 20.26 — Full Integration & Regression QA Report

**Date:** 2026-09-20
**Overall Status: FAIL**

Phases 20.24R-1 (dataset) and 20.25 (Music/Settings UI) are individually intact and their fixes are present, but their **integration is broken by three pre-existing defects in `webview_app/frontend/js/app.js`**, two of which are `ReferenceError`s that abort page initialization. These were found by driving the real application (live WebView2 + real `BackendAPI` bridge + real Aladhan API), not by source inspection alone.

---

## Executive Summary

| # | Test Area | Result |
|---|---|---|
| 1 | HTML structure (Phase 20.25 fix) | **PASS** |
| 2 | Navigation / no disappearing pages | **PASS** |
| 3 | Prayer fetch (Egypt/Saudi/US) | **PASS** (real API, correct locations) |
| 4 | No-fallback validation | **PASS** (errors, no request, no substitution) |
| 5 | Prayer editor save/persist | **PASS** |
| 6 | Music player page + pause/resume | **PASS** (commands actually delivered) |
| 7 | Settings page | **PASS** (layout; some fields mis-populated — see Bug 2) |
| 8 | Theme dark/light | **PASS** |
| 9 | Country/city dropdown mechanics | **PASS** (192 of 196 countries — see Bug 3) |
| 10 | **Dashboard startup population** | **FAIL — Bug 1** |
| 11 | **Manual Location radio toggle** | **FAIL — Bug 1** |
| 12 | **Times editor / checkbox population after refresh** | **FAIL — Bug 2** |
| 13 | **Country count 196** | **FAIL — Bug 3 (192)** |

**Critical failures: 3. Overall: FAIL.**

---

## 1. Read-Only Inspection — PASS

| Check | Result |
|---|---|
| Phase 20.25 fix present | `index.html` 289 lines, `<div>` balance 59/59, `main` 1/1, `section` 4/4 |
| DOM tree (live WebView2) | `body > .app > [aside.sidebar, main.main > [topbar, page-dashboard, page-times, page-music, page-settings]]` — exactly as required |
| No stray/duplicate closing tags | Confirmed: `#page-music` ×1, `#page-settings` ×1, `#page-times` ×1, `#page-dashboard` ×1; `#page-music` parent chain → `main.main → div.app → body` |
| countries.json intact | 196 countries, SHA256 `17ECDBB5…FE01` (unchanged) |
| cities.json intact | 2,516 cities, 0 zero-city countries, SHA256 `D45B6BFD…B22E` (unchanged) |
| Alexandria fallback | Zero matches for `Alexandria` / `الإسكندرية` / `اسكندرية` in `main.py`, `backend_api.py`, `app.js` |
| Unexpected changes | None. No project source file modified during this QA. |

---

## 2. Country / City — PARTIAL FAIL (192/196)

**Working (verified at runtime):**

| Test | Result |
|---|---|
| Manual Location radio selected | mode = `manual` |
| Country dropdown opens, searchable | 192 items listed |
| Egypt → cities list | 15 cities incl. **Alexandria** ✓ |
| Saudi Arabia → cities list | 15 cities incl. **Riyadh** ✓ |
| United States → cities list | 407 cities incl. **New York** ✓ |
| Changing country clears city | **cleared = true** ✓ |
| City input enabled after country | ✓ |
| Manual stays selected after navigation | mode `manual` retained |
| Previously-small country coverage | Tuvalu: 15 cities (Funafuti, Nanumea, …) — Phase 20.24R-1 augmentation visible in UI ✓ |

**FAIL — Bug 3: dropdown offers 192 countries, not 196.**

`app.js` embeds its own copy of the country list (`var COUNTRIES = […]`, app.js:5-198) with **192 entries**, while `assets/data/countries.json` has 196. The four countries present in the dataset but missing from the dropdown:

| Code | Country | Searchable in dropdown? |
|---|---|---|
| AG | Antigua and Barbuda | **No** |
| CD | Democratic Republic of the Congo | **No** |
| MK | North Macedonia | **No** |
| VA | Vatican City | **No** |

(Tested by opening the full list and searching the Arabic names — all four return `searchable: false` against a 192-item list.)

Note: AG was one of the countries augmented in Phase 20.24R-1 (7→10 cities); its cities exist in `cities.json` but the country cannot be selected.

---

## 3. Prayer Times Fetch — PASS (real network)

Real requests were issued to `api.aladhan.com` using the exact payload the frontend produces (English city name + Arabic country name, `method=5`). All three succeeded and returned **location labels matching the selection exactly**:

| Selection | Status | Location label shown | Dashboard prayer cards |
|---|---|---|---|
| مصر / Alexandria | `is-success` "تم جلب المواقيت لـ Alexandria، مصر." | `Alexandria، مصر` | 5 |
| السعودية / Riyadh | `is-success` "تم جلب المواقيت لـ Riyadh، السعودية." | `Riyadh، السعودية` | 5 |
| الولايات المتحدة / New York | `is-success` "تم جلب المواقيت لـ New York، الولايات المتحدة." | `New York، الولايات المتحدة` | 5 |

- Request uses the exact selected location: **yes** (verified payload + returned label).
- No Alexandria fallback: **confirmed** — Saudi/US fetches returned Riyadh/New York, never Alexandria.
- No automatic-location substitution: **confirmed** — in manual mode `fetch_times()` uses only `manual_city`/`manual_country` (the auto-location lookup result is computed but never used outside the `auto` branch).
- No fake success: **confirmed** — success class only when the API returned real timings.

---

## 4. No-Fallback Validation — PASS

| Input | Result |
|---|---|
| Manual + no Country → fetch | `is-error` validation message; **times unchanged**; no request issued |
| Manual + Country but no City → fetch | `is-error` validation message; **times unchanged**; no request issued |

`backend_api.fetch_times()` returns `"يرجى اختيار الدولة والمدينة يدويًا."` before any HTTP call. No Alexandria, no computer location, no previously-stored location was ever substituted.

---

## 5. Prayer Editor — PASS (with caveat)

Fetched Alexandria → edited Fajr to `06:00 ص` → clicked حفظ المواقيت → `is-success` "تم حفظ الإعدادات." → navigated Dashboard → Music → back to Times → **Fajr still `06:00 ص`** (persisted), and the Dashboard next-prayer updated to `الفجر (غدًا)` at `06:00 ص` with a live countdown of `19:01:32`.

Caveat: only the edited field is re-populated after save (other four inputs render empty) — that is **Bug 2** below, a population defect, not a save/persistence defect. Saving and persistence themselves work.

---

## 6. Music Player — PASS

| Check | Result |
|---|---|
| Layout / no giant empty space | first card `top=168, left=26` — identical to Dashboard ✓ |
| Selector, dropdown, browse buttons | all visible ✓ |
| Selected player visible | `player-line` = "samsunginternet", input populated with full path ✓ |
| Interruption method | `suspend` (APPCOMMAND) + `media` (Play/Pause) radios present, `suspend` checked ✓ |
| Pause control | `is-success` "تم إرسال أمر الإيقاف المؤقت." ✓ |
| Resume control | `is-success` "تم إرسال أمر الاستئناف." ✓ |
| Resume countdown chip | appeared after pause: "⏱ متبقي للاستئناف: 59 ث" (matches `minutes=1`) ✓ |
| Save button | visible ✓ |
| RTL / Dark / Light | `dir="rtl"`; page renders correctly in both themes ✓ |

Pause/resume were exercised against the configured player and both commands were delivered successfully (not the "player not open" warning).

---

## 7. Settings — PASS (layout), PARTIAL FAIL (population)

| Check | Result |
|---|---|
| Layout / no giant empty space | first card `top=168`, 2 cards (settings + appearance) ✓ |
| Duration field | present, value `1` ✓ |
| Monitoring / Adhan / autostart toggles | present ✓ |
| Save / Refresh state buttons | present, clickable, refresh returned clean ✓ |
| Appearance card | present with title ✓ |
| Navigation Dashboard→Settings→Dashboard→Music→Settings | all pages appear correctly, exactly one visible at a time ✓ |

**FAIL (Bug 2):** checkbox states were NOT populated from the backend — `enabled` and `announce` both read `false` while the persisted settings have `true`. See Bug 2.

---

## 8. Dashboard — FAIL (Bug 1)

| Check | Result |
|---|---|
| Layout unchanged | first card `top=168`, 2 cards ✓ |
| Pause/resume buttons present & visible | ✓ |
| **Next prayer / countdown / prayer grid / location / version at startup** | **all placeholders** — `next-prayer-name` = "—", countdown `00:00:00`, prayer grid empty, location empty, version "—" for 20+ seconds with the bridge available |

The dashboard only populates **after** the user clicks an action that calls `refresh()` (pause/resume/fetch/save). At cold startup it stays blank. Root cause: **Bug 1**.

**Countdown ticker: PENDING** — could not be verified because the ticker's `setInterval` is never registered (Bug 1 aborts `init()` before it). This is not an independent defect, but it cannot be signed off until Bug 1 is fixed.

---

## 9. Prayer Times Page — PASS (structure), PARTIAL FAIL (population)

| Check | Result |
|---|---|
| 5 prayer inputs exist | all present ✓ |
| 12-hour format | input placeholder `HH:MM ص/م`; fetched values render as e.g. `12:54 م` ✓ |
| Manual + Automatic radios | both present ✓ |
| Country/city comboboxes | both present and functional ✓ |
| Fetch buttons | both present ✓ |
| **Editable fields populated from state** | **FAIL (Bug 2)** — all five inputs empty after a successful fetch |

---

## 10. Theme — PASS

Captured with transitions disabled (to avoid measuring mid-fade values):

| Element | Dark | Light |
|---|---|---|
| body bg | `rgb(20,22,29)` | `rgb(238,241,248)` |
| body fg | `rgb(242,244,249)` | `rgb(19,26,43)` |
| card bg | `rgb(28,31,40)` | `rgb(255,255,255)` |
| combobox menu bg | `rgb(28,31,40)` | `rgb(255,255,255)` |
| menu item fg | `rgb(242,244,249)` | `rgb(19,26,43)` |

- Both themes switch correctly (`data-theme` attribute + checkbox state).
- Dropdown menus readable in both themes (dark-on-dark and dark-on-light; no transparent/unreadable items).
- No layout movement when switching (all page/card geometry identical: `top=168, left=26`).

---

## 11. Navigation — PASS

4 laps of Dashboard → Times → Music → Settings → Dashboard:

| Check | Result (every lap) |
|---|---|
| Exactly one page visible | `visiblePages = 1` ✓ |
| No disappearing pages / duplicates | each `#page-*` count = 1 ✓ |
| Card counts stable | dashboard 2, times 2, music 1, settings 2 ✓ |
| No layout shifts | active card `top` 171-173 across all laps ✓ |
| No state corruption | selected mode/country retained ✓ |
| Runtime/JS errors | only Bug 1 & Bug 2 ReferenceErrors (see below); nothing else |

---

## 12. HTML Structure — PASS

Verified against the required tree, live in the browser:

```
body
└── div.app
    ├── aside.sidebar
    └── main.main
        ├── header.topbar
        ├── section#page-dashboard
        ├── section#page-times
        ├── section#page-music
        └── section#page-settings
```

`body` children are only `div.app`, two `script`s, and `div#bridge-diag`. No stray closing tags; `<div>` balance 59/59.

---

## 13. Data Integrity — PASS

| File | Value | Modified during QA? |
|---|---|---|
| `assets/data/countries.json` | 196 countries, SHA256 `17ECDBB5…FE01` | No |
| `assets/data/cities.json` | 2,516 cities, 0 zero-city, SHA256 `D45B6BFD…B22E` | No |

---

## 14. Alexandria Fallback — PASS

Zero occurrences of `Alexandria`, `الإسكندرية`, or `اسكندرية` in any active code file (`main.py`, `webview_app/backend_api.py`, `webview_app/frontend/js/app.js`). No fallback path observed at runtime. Defaults remain `"manual_city": "", "manual_country": ""`.

---

## THE THREE DEFECTS (all in `webview_app/frontend/js/app.js`)

### Bug 1 — CRITICAL: `manualFields is not defined` (aborts page initialization)

- **Location:** `app.js:311` and `app.js:314` — `showManualFields()` / `hideManualFields()` reference a variable that is **never declared**.
- **Called from:** `initLocationUI()` at `app.js:467`/`app.js:469` — executed unconditionally at the end of `init()` (neither location-mode radio is `checked` in the HTML, so `hideManualFields()` always runs).
- **Impact:** the `ReferenceError` propagates out of `initLocationUI()` and **aborts `init()`**. Everything after it never runs:
  - `loadCitiesDB()` — city dataset not preloaded
  - `diagWrite(diagSnapshot("init"))` — proven: `#bridge-diag` stays empty for 20+ s
  - the `pywebviewready` listener and `whenReady().then(refresh)` — **no initial state load**, so the Dashboard shows placeholders until the user manually triggers an action
  - `setInterval(tick, 1000)` — countdown never ticks
  - `setInterval(refresh, 30000)` — no periodic refresh
- **Also breaks:** clicking "إدخال الموقع يدويًا" or "تحديد الموقع تلقائيًا" throws (the manual panel neither shows nor hides, and the mode change is not persisted on click).
- **Evidence:** `timeFajrExists: true` and nav wired (init started) but `bridgeDiag: ""`, countdown `00:00:00`, grid 0, version "-", plus the captured `Uncaught ReferenceError: manualFields is not defined`.
- **Regression history:** backups show `var manualFields = $("manual-fields");` was declared (inside `initLocationUI`) in every version through 09/19 09:03 and **was deleted** by the 09/19 10:10 edit; it has been missing since. This silently broke startup during the location-dropdown rebuild work.

### Bug 2 — CRITICAL: `preloadCitiesForCountry is not defined` (breaks state population)

- **Location:** `app.js:963` — `fillSettings()` (module scope) calls `preloadCitiesForCountry(foundCode)`, but that function is declared at `app.js:341` **inside** `initLocationUI()`, so it is out of scope.
- **Triggered:** on every `applyState()` where a manual location with a recognized country is saved — i.e. on every fetch/save/refresh once the user acts.
- **Impact:** the `ReferenceError` aborts `fillSettings()` and `applyState()` mid-run:
  - the prayer-times editor inputs (`app.js:974-983`) are never populated → all five inputs render empty even after a successful fetch
  - the `enabled`/`announce`/`autostart` checkboxes (`app.js:968-973`) are never populated → read `false` while persisted values are `true`
  - `syncTheme()` (`app.js:1016`) never runs → backend theme not applied on refresh
  - (values set *before* line 963 — music/adhan/minutes/country/city inputs — do populate)
- **Evidence:** after a successful Alexandria fetch, `times: {Fajr:"", Dhuhr:"", Asr:"", Maghrib:"", Isha:"}` and `enabledCheckbox: false, announceCheckbox: false` despite persisted `true`; plus 3 captured unhandled rejections.

### Bug 3 — HIGH: country dropdown shows 192 of 196 countries

- **Location:** `app.js:5-198` — the inline `COUNTRIES` array has 192 entries.
- **Missing:** `AG` Antigua and Barbuda, `CD` Democratic Republic of the Congo, `MK` North Macedonia, `VA` Vatican City — all present in `assets/data/countries.json` (196).
- **Impact:** these four countries cannot be selected in the UI; their cities (added/augmented in Phase 20.24R-1) are unreachable.

---

## 15. Build Status — NO BUILD (PASS)

No build tooling was executed: no PyInstaller, `build_exe.bat`, Inno Setup, `release.ps1`, or `npm dist`. No `dist/` output created, modified, or deleted.

---

## 16. Files Modified — ZERO

| Item | Status |
|---|---|
| Project source files | **Not modified** — the only write today was Phase 20.25's `index.html` fix (09/20 10:35, pre-existing). A `.pyc` cache file was auto-generated by Python imports; no source changed. |
| Runtime `settings.json` | Backed up before testing, **restored byte-for-byte** afterward (SHA256-verified identical to pre-QA state) |

All testing was performed against unmodified source, served over a local HTTP server, with the real `BackendAPI` attached as the `js_api` bridge.

---

## 17. Verification Methodology

Every functional claim above comes from a live run: `index.html` served over local HTTP into a 900×760 pywebview/WebView2 window with the real `BackendAPI` (same bridge the production EXE uses), driving the actual combobox/dropdown/button event handlers via synthetic DOM events, reading `getBoundingClientRect` / `getComputedStyle` for layout, and capturing `window.onerror` + `unhandledrejection` for runtime errors. Real HTTPS requests to `api.aladhan.com` confirmed the prayer-fetch path end to end. Backend behavior was additionally verified in-process (`BackendAPI.get_state()`).

---

## Required Follow-up (for a future fix phase — NOT performed here)

Per QA-only scope, **no fixes were applied**. To reach PASS, a future phase must:

1. Restore the `var manualFields = $("manual-fields");` declaration in `initLocationUI()` (Bug 1) — then re-verify dashboard startup population, countdown ticking, and the Manual/Auto radio toggling.
2. Move `preloadCitiesForCountry` to module scope (or call it only from within `initLocationUI`) so `fillSettings()` no longer throws (Bug 2) — then re-verify times editor and checkbox population.
3. Add the 4 missing countries (AG, CD, MK, VA) to the `COUNTRIES` array in `app.js` (Bug 3) — then re-verify the dropdown lists 196.

All three are contained in `webview_app/frontend/js/app.js`; no other file needs changes for these items.
