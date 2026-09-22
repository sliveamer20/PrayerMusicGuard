# PHASE 20.28-QA — RUNTIME LOCATION TEST REPORT

**Date:** 2026-09-20
**Scope:** Run the **real application from current source** (no EXE, no code changes) and exercise the Prayer Times location screen end to end in a live WebView2 window against the real backend and the real network.
**Baseline tested:** Phase 20.28 source (fixes A–D + migration), immediately after the automated 53/53 PASS.

---

## Result: **PASS**

**52/52 runtime checks passed** in a live window driving the real UI handlers, the real `BackendAPI` bridge, the real scheduler, and the real `ipapi.co` + `api.aladhan.com` endpoints.

Key real-world proof points:

| Evidence | Result |
|----------|--------|
| Real prayer times fetched per city (Fajr) | Alexandria **05:19 ص** → Riyadh **04:18 ص** → Amman **04:54 ص** — genuinely different Aladhan data, proving each fetch truly used the selected location |
| The app's own **30 s background refresh fired 3×** during the session | **No revert** — UI and persisted state stayed on the selected location every time |
| Manual ↔ Auto switched 5× | **Never** "تعذر الحفظ"; every switch returned "تم حفظ الإعدادات." |
| JS / runtime errors (hook installed **before** `app.js` ran) | **Zero** for the entire run, including startup |
| Manual Country/City at startup | **Empty** (profile and DOM inputs), no Saudi/Jeddah |

---

## 1. How the real app was run

`qa_phase20_28_runtime.py` launches the genuine application stack:

- **Frontend:** a byte-identical copy of `webview_app/frontend` (SHA-verified per file) in a real WebView2 window; the only difference is a 6-line error hook prepended to the *copy* of `index.html` so `window.__pmgErrors` is installed **before** `js/app.js` executes. No shipped file was modified.
- **Bridge:** the real `BackendAPI` (`webview_main._build_api`), with its real scheduler started and stopped around the session.
- **Network:** real `https://ipapi.co/json/` and `https://api.aladhan.com/v1/timingsByCity/…` — nothing stubbed.
- **Interaction:** real DOM events dispatched through the app's own handlers (`change` on the mode radios, `input` on the comboboxes with the app's real 150/300 ms debounces, `mousedown` on real list items, `click` on the real "جلب المواقيت" button), then a genuine **10 s wait** after each fetch before asserting.
- **Hygiene:** the user profile was reset to the clean post-20.28 baseline before the run and restored verbatim after it; no app processes were left running.

Toolchain: `win7\venv` Python 3.8.10 (the release toolchain) + pywebview 6.2.1 + WebView2 runtime 153.0.4234.48.

---

## 2. Test Results (9/9 user scenarios)

### 1. Manual → Egypt → Alexandria → Fetch → wait 10s — **PASS**
Selected `مصر / Egypt` + `Alexandria` through the real comboboxes (filtering to exactly 1 item each), fetched, waited 10 s.
- Status: `تم جلب المواقيت لـ Alexandria، مصر.` — Resolved: `الموقع المستخدم: Alexandria، مصر`
- After 10 s: UI still `مصر / Egypt` + `Alexandria` (**no revert**)
- Persisted: `manual_country=مصر`, `manual_city=Alexandria`, coordinates cleared
- Real times fetched (05:19 / 12:54 / 16:23 / 19:00 / 20:18)

### 2. Saudi → Riyadh → Fetch → wait 10s — **PASS**
- After 10 s: UI still `السعودية / Saudi Arabia` + `Riyadh` (**no revert to Jeddah**)
- Persisted: `السعودية` / `Riyadh`
- Times genuinely changed for Riyadh (04:18 / 11:47 / 15:14 / 17:52 / 19:06) — different from Alexandria, proving the fetch used the new location

### 3. Change to another country/city → Fetch → wait 10s — **PASS**
Switched to `الأردن / Jordan` + `Amman`.
- After 10 s: UI still Jordan/Amman (**no revert to Riyadh or Jeddah**)
- Persisted: `الأردن` / `Amman`; times changed again (04:54 Fajr)

### 4. Auto Location → Fetch → wait 10s — **PASS**
- Switch to Auto persisted (`location_mode=auto`), status = success message, **no "تعذر الحفظ"**
- Auto stayed `auto` after fetch + 10 s
- Real IP geolocation resolved (Alexandria, Egypt) and was persisted as the resolved location
- Dashboard location line agrees with the fetch — **not stale Jeddah**

### 5. Manual ↔ Auto several times — **PASS**
Switched manual → auto → manual → auto → manual (5 switches). Every switch returned `تم حفظ الإعدادات.`; **"تعذر الحفظ" never appeared**, and the mode persisted correctly each time.

### 6. Type/filter Country and City — **PASS**
- `united` → 3 country matches (United Arab Emirates / United Kingdom / United States)
- `zzzz` → the "لا توجد نتائج" empty state
- Arabic partial `مصر` → 1 match; city `Cai` → `Cairo`
- City combobox enabled only after a country is chosen (unchanged behavior)

### 7. Latitude/Longitude gone — **PASS**
`#set-latitude` and `#set-longitude` are absent from the DOM, and no `خط العرض` / `خط الطول` label remains anywhere.

### 8. Dashboard / Music Player / Settings unchanged — **PASS**
Navigated all four pages (each became active) and cross-checked against the live backend state:
- Dashboard: 5 prayer cards, live countdown (not `00:00:00`), player line matches the backend's music
- Music Player: all controls present; music path + method in sync with backend
- Settings: minutes/enabled/announce/autostart/version in sync with backend
- Times page: 5 time inputs + 2 mode radios intact

### 9. JS / runtime errors — **PASS**
The error hook captured **zero** errors at startup, after every interaction, and at the final sweep. Bridge stayed attached throughout (`window.pywebview.api` present, `document.readyState === "complete"`).

---

## 3. Check inventory (52/52)

| Group | Checks | Covers |
|-------|--------|--------|
| Setup & startup | 6 | byte-identical frontend copy, hook precedence, real bridge built, WebView2 configured, first refresh rendered, zero startup errors |
| T1 (Egypt→Alexandria) | 10 | mode switch, empty start, country/city filtering, fetch success, no revert after 10 s, persistence, coords cleared, real times, no errors |
| T2 (Saudi→Riyadh) | 7 | filtering, no Jeddah revert, persistence, times changed for the new city, no errors |
| T3 (Jordan→Amman) | 7 | filtering, no revert, persistence, times changed again, no errors |
| T4 (Auto) | 8 | mode persists, no "تعذر الحفظ", stays auto, resolved location persisted/shown, dashboard agrees, no errors |
| T5 (Manual↔Auto ×5) | 1 | never rejected, never "تعذر الحفظ" |
| T6 (type/filter) | 4 | partial-letter filtering, empty state, city filtering, no errors |
| T7 (lat/long gone) | 1 | inputs and labels absent |
| T8 (unchanged pages) | 9 | dashboard/music/settings/times pages present, active, and in sync with backend; no errors |
| T9 (error sweep) | 1 | zero errors, bridge intact |
| Background refresh | 1 | the app's own 30 s `get_state` refresh fired 3× during the session (the original revert vector) with no revert |

---

## 4. Two QA-driver defects found and fixed (not application defects)

Honest disclosure — the first run failed 8 checks, all traced to the test harness, not the app:

1. **Fetch click never executed.** The driver dispatched the button click as `document.getElementById('btn-fetch-location').click(); return 1;`. `ExecuteScriptAsync` requires a single expression, so the top-level `return` made the whole script a syntax error — silently. The fetch never ran (status stayed at the earlier radio-save message, times never changed). Fixed by wrapping in an IIFE. This also explains why the first run's "revert" checks looked empty: the app's 30 s refresh correctly re-seeded the comboboxes from the *saved* (still-empty) location.
2. **Country-name expectation.** The real UI persists the Arabic segment (`extractCountryName("مصر / Egypt") → "مصر"`); the driver wrongly asserted the English name. Corrected to the value the app actually stores.
3. **Window placement.** An off-screen window let Chromium throttle timers; moving it on-screen let the real 30 s background refresh run (3 ticks), which is the strongest end-to-end evidence that the original revert bug is gone.
4. **Baseline profile.** An earlier direct diagnostic call had left a location in the user profile; the driver now resets a clean post-20.28 baseline before the run and restores it after.

After these harness fixes, all 52 checks pass on the unmodified Phase 20.28 source.

---

## 5. Post-run hygiene

| Item | Status |
|------|--------|
| User profile | Restored to the clean baseline (auto / empty manual fields / migration marker), `music`, `times`, `theme`, `minutes`, `enabled`, `announce`, `autostart` all preserved |
| Leftover processes | None — no `PrayerMusicGuard` or QA-spawned WebView2 processes remain (the remaining `msedgewebview2` processes belong to Windows `SearchHost.exe`, pre-existing) |
| Source files | Unmodified — no code was changed during QA |
| Release 20.27 bundle | Untouched — `dist\Phase20-27-Release-UAT\…\js\app.js` SHA256 still `F5ED5515…206EFD`, byte-identical to the pre-fix source |
| Temp QA artifacts | Removed (the QA frontend copy; the driver scripts remain as regression tests) |

---

## 6. Overall Status

**PASS** — The real application, run from the current Phase 20.28 source with the real bridge and real network, passes all 9 required scenarios with 52/52 runtime checks and zero JavaScript/runtime errors. Manual country/city starts empty and stays put after fetching (across three different countries plus automatic mode), manual ↔ auto switching never produces "تعذر الحفظ", the visible latitude/longitude fields are gone, typing/filtering works, the rest of the UI is unchanged, and the app's own 30-second background refresh no longer reverts anything.

No fixes were made and no build was produced. Stopped after diagnosis-by-execution and this report.
