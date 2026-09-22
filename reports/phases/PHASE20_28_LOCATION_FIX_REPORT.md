# PHASE 20.28 — LOCATION STATE FIX

**Date:** 2026-09-20
**Scope:** Implement the four isolated fixes (A–D) diagnosed in the Phase 20.27 root-cause analysis for the Prayer Times location screen, plus the one-time stale-location migration. No UI redesign, no Music Player / Settings / Dashboard changes, no EXE build.
**Release baseline:** Phase 20.27 PASS build left **byte-identical** (verified by SHA256, §6).

---

## Result: **PASS**

- 35/35 backend state-layer checks passed (`test_phase20_28.py`, release toolchain Python 3.8.10).
- 18/18 frontend DOM-level checks passed (`test_phase20_28_frontend.js`, Node 24 against the **real** `app.js` IIFE and `index.html`).
- The real user profile's stale Jeddah state was migrated once; unrelated settings preserved.
- Zero JS runtime errors in the frontend harness; zero Python exceptions; syntax clean on both Python 3.8.10 and 3.14.

---

## 1. Files Changed (5 edits in 4 files)

| File | Lines | Change |
|------|-------|--------|
| `webview_app/backend_api.py` | 551–555 (`save_settings`) | **Fix A** — removed the manual→auto rejection block; persists the requested `location_mode` |
| `webview_app/backend_api.py` | 1047–1070 (`fetch_times`) | **Fix B** — persists the location actually used (manual city/country + clear stale coords; auto resolved city/country + mode=auto) |
| `webview_app/frontend/index.html` | 187–194 (removed) | **Fix C** — deleted both visible Latitude/Longitude field blocks |
| `webview_app/frontend/js/app.js` | 952–953 (`fillSettings`) | **Fix D** — `document.activeElement` guard so refresh never clobbers a field being typed in |
| `main.py` | 545, 567–582 (`load_settings`) | **Migration** — one-time clear of the stale manual location + marker `location_migrated_20_28` |

Backup (pre-edit source + profile): `backup\phase20_28_location_fix_20260920_142303\` (backend_api.py, app.js, index.html, main.py, `settings.json.profile-backup`).

### Fix A — `webview_app/backend_api.py:551-555`
```python
        if "location_mode" in payload:
            if payload["location_mode"] not in ("auto", "manual"):
                return {"ok": False, "error": "وضع الموقع غير صالح."}
            # Phase 20.28: allow switching freely between manual and auto.
            merged["location_mode"] = payload["location_mode"]
```
The rejected switch (`current_mode == "manual" and payload["location_mode"] == "auto"` → error "لا يمكن التبديل…") was the literal source of **"تعذر الحفظ"** (`app.js:1107`).

### Fix B — `webview_app/backend_api.py:1047-1070`
```python
        saved["times"] = values
        # Phase 20.28: persist the location actually used, otherwise get_state()
        # keeps reporting a stale saved location (e.g. a previously stored
        # Jeddah/Saudi Arabia) and the UI reverts to it after every fetch.
        if loc_mode == "manual":
            saved["location_mode"] = "manual"
            saved["manual_city"] = str(manual_city or "").strip()
            saved["manual_country"] = str(manual_country or "").strip()
            saved["manual_latitude"] = ""
            saved["manual_longitude"] = ""
            saved["manual_timezone"] = ""
        else:
            saved["location_mode"] = "auto"
            saved["manual_city"] = str((info or {}).get("city") or "").strip()
            saved["manual_country"] = str((info or {}).get("country") or "").strip()
            saved["manual_latitude"] = ""
            saved["manual_longitude"] = ""
            saved["manual_timezone"] = str((info or {}).get("timezone") or "").strip()
        _MAIN.save_settings(saved)
```
Previously `fetch_times` wrote **only** `times`, so `get_state()` re-reported the old saved location and `applyState → fillSettings` reset the comboboxes when the network call landed (~2–3 s) — the visible revert.

### Fix C — `webview_app/frontend/index.html`
Removed the two `<div class="field">` blocks carrying the visible labels "خط العرض" / "خط الطول" and the hidden `#set-latitude` / `#set-longitude` inputs. The IDs are still referenced by `app.js` (`fillSettings`, `collectCommon`, `collectLocation`) but every access is null-guarded (`$(…) ? … : ""`), so removal is safe — proven by check F-C. HTML `<div>` balance verified: 57/57 before and after.

### Fix D — `webview_app/frontend/js/app.js:952-953`
```js
      if (countryInput && document.activeElement !== countryInput) countryInput.value = …;
      if (cityInput && document.activeElement !== cityInput) cityInput.value = cityName;
```
Mirrors the guard already used by the `pairs` loop at `app.js:932`. A periodic `refresh()` (30 s, `app.js:1450`) or a post-save `applyState` can no longer wipe in-progress typing.

### Migration — `main.py:545, 567-582` (`load_settings`)
One-time, marker-guarded (`location_migrated_20_28`): clears `manual_city/manual_country/manual_latitude/manual_longitude/manual_timezone`, resets `location_mode` to `"auto"`, and persists once. The marker prevents a later migration from wiping a location the user deliberately chose. `main.py` defaults were already empty (`main.py:542-543`) — this only heals profiles that carry the stale state.

**Applied to the live profile** (backed up first): `manual_city "جدة"` / `manual_country "السعودية"` / coords `24.7136, 46.6753` → cleared, mode → `auto`, marker set. `music`, `enabled`, `theme`, `minutes`, `times` all preserved.

---

## 2. Test Evidence

### Backend (`test_phase20_28.py`) — 35/35 PASS
Offline harness: `ipapi.co` and `api.aladhan.com` stubbed; isolated temp profile. Covers user tests 1–5 at the state layer where the bug lived.

| Group | Checks | Meaning |
|-------|--------|---------|
| T0a–T0g | 7 | Migration clears Jeddah, writes marker, preserves unrelated settings, runs **once** (file stable on 2nd load) |
| T1a–T1e | 5 | **User test 5** — manual→auto switch returns `ok:true`, no "تعذر الحفظ" |
| T2a–T2h | 8 | **User test 1** — Egypt→Alexandria fetch persists; `get_state()` stays "Alexandria، Egypt" across a later refresh tick (no revert) |
| T3a–T3c | 3 | **User test 2** — Saudi→Riyadh persists; no Jeddah revert |
| T4a–T4b | 2 | **User test 3** — change to Giza/Egypt; no revert to Riyadh/Jeddah |
| T5a–T5f | 6 | **User test 4** — auto fetch stays auto, resolved city persisted, no revert |
| T6 | 1 | **User test 5b** — manual↔auto↔manual↔auto round trip never rejected |
| T7a–T7c | 3 | `get_state` coherent after all churn (prayers/next intact) |

### Frontend (`test_phase20_28_frontend.js`) — 18/18 PASS
Executes the **real** `app.js` IIFE against a DOM shim built from the **real** `index.html`; drives the actual event handlers and the real `refresh → applyState → fillSettings` path.

| Group | Checks | Meaning |
|-------|--------|---------|
| F-C ×4 | 4 | **User test 6** — no "خط العرض"/"خط الطول"/`set-latitude`/`set-longitude` in `index.html` |
| F-load / F-init | 2 | IIFE + `init()` run with zero errors (proves removal didn't break init) |
| F-7a–F-7h | 8 | **User test 7** — 196 countries on open; Arabic "مصر" → 1; latin "united" → 3; no-match → empty state; country select enables city; city list opens; typing filters cities |
| F-C (fill) | 1 | `fillSettings` runs with lat/long elements absent (no crash), still seeds country correctly |
| F-D1 / F-D2 | 2 | **Fix D** — typing in country NOT overwritten while focused; the same refresh DOES update it once blurred (guard, not a broken setter) |

### Startup state (live migrated profile, real `get_state()`)
```json
{"ok": true, "location_mode": "auto", "manual_city": "",
 "manual_country": "", "manual_latitude": "", "manual_longitude": "", "location": ""}
```
→ **Manual fields start empty when no location is saved.**

---

## 3. User Test Matrix (1–8)

| # | Required behavior | Result | Evidence |
|---|-------------------|--------|----------|
| 1 | Manual: Egypt → Alexandria → fetch → remains Alexandria | **PASS** | T2a–T2h (persisted + stays across later refresh) |
| 2 | Manual: Saudi → Riyadh → fetch → remains Riyadh | **PASS** | T3a–T3c |
| 3 | Change country/city → fetch → no revert | **PASS** | T4a–T4b (Giza/Egypt after Riyadh) |
| 4 | Auto Location → fetch → remains auto/resolved | **PASS** | T5a–T5f |
| 5 | Switch Manual ↔ Auto → no "تعذر الحفظ" | **PASS** | T1a–T1e, T6 (round trip never rejected) |
| 6 | Latitude/Longitude labels no longer visible | **PASS** | F-C ×4 + HTML balance 57/57 |
| 7 | Type letters in Country/City → filtering works | **PASS** | F-7a–F-7h (196/1/3/0 filtering + city filter) |
| 8 | No JS/runtime errors | **PASS** | `node --check` clean; IIFE + `init()` error-free; py compile on 3.8.10 and 3.14; 35+18 checks, zero exceptions |

---

## 4. Constraints Compliance

| Rule | Status |
|------|--------|
| Backup first | `backup\phase20_28_location_fix_20260920_142303\` created before any edit (source + profile) |
| Only fixes A–D (+ required migration) | No other logic touched; no UI redesign |
| Music Player / Settings / Dashboard untouched | Confirmed — all changes scoped to location paths + `load_settings` |
| Do not build EXE | No build performed; no `dist\` writes |
| Manual must not default to Saudi/Jeddah | `main.py` defaults already empty; stale profile migrated; T0a–T0d |
| Stale Jeddah migrated safely once | Marker-guarded; T0g proves idempotence; unrelated settings preserved (T0f) |
| Windows 7 compatibility | Edits use only Python 3.8-compatible syntax (verified with the pinned `win7\venv` 3.8.10 toolchain) and ES5/ES6 JS already used by the file |

---

## 5. Regression Notes

- The removed `manual_latitude/manual_longitude` inputs were dead in the WebView UI path: the frontend always sent empty strings, and `fetch_times` now explicitly clears stored coordinates. The legacy Tkinter UI in `main.py` keeps its own coordinate entries and is unaffected (it does not read the hidden HTML inputs).
- `_location_label` (`backend_api.py:445-450`) still derives the on-screen location from `manual_city`/`manual_country`; Fix B keeps those populated with the location actually used, so the label is now correct in both modes.
- Manual city/country are deliberately stored for auto mode too (as the "last resolved location") purely so `_location_label` reports correctly; `location_mode` remains `"auto"` and the manual fields stay hidden.

---

## 6. Release Baseline Integrity

SHA256 of `webview_app/frontend/js/app.js` in `dist\Phase20-27-Release-UAT\PrayerMusicGuard\`:
`F5ED5515DA161AC222F250B5212B07841DE243ADD5F91A7A64AC14E426206EFD`
— **identical** to the pre-fix source and to the value recorded in the Phase 20.27 report.
`index.html` (`F23D1B17…`), `backend_api.py` (`45C56869…`) and `main.py` (`37862BAA…`) in the release bundle are also byte-identical to the pre-fix source. **The 20.27 release was not modified.**

---

## 7. Overall Status

**PASS** — All four diagnosed root causes are fixed with minimal isolated edits, the stale profile state is migrated, and all 8 required user tests pass (53 automated checks, zero errors). No build produced; ready for a review build when requested.
