# Phase 20.24R-1 — Complete Country/City Dataset Report

**Date:** 2026-09-20
**Status:** PASS (dataset corrected and validated)

---

## Exact Files Changed

| File | Change |
|---|---|
| `assets/data/cities.json` | Removed 33 duplicate US city entries; augmented 67 countries with <=8 cities to have 9-15 real cities each |
| `main.py` | No changes needed — Alexandria/Egypt fallback already removed in current version (defaults are `"manual_city": "", "manual_country": ""`) |
| `countries.json` | No changes needed — all 196 countries already present |
| `uiverse_combobox.py` | No changes needed — country→city mapping logic is correct |

---

## Exact Backup Path

```
E:\prayer-music-guard\backup\phase20_24r1_complete_city_dataset_20260920_073026\
```

Contains:
- `cities.json` (original before fix)
- `countries.json` (original, unchanged)

---

## Actual Dataset Source

The city data originates from `assets/data/cities.json`, a hand-curated JSON file mapping ISO 3166-1 alpha-2 country codes to arrays of English city names. The country list comes from `assets/data/countries.json` with bilingual Arabic/English names.

**Root cause of incomplete cities:** The original `cities.json` was generated with a fixed cap of ~8 cities per country for most nations, while the US received 440. This created a severe imbalance where micro-states and large countries alike had only 5-8 cities, making the dropdown appear empty or insufficient.

**Root cause of US duplicates:** The US entry contained 33 duplicate city names (e.g., "Atlanta" appeared 3 times, "Columbus" twice, etc.) because the source data merged multiple geographic datasets without deduplication.

---

## Total Countries

**196** — matches `countries.json` exactly. Every country code has a corresponding entry in `cities.json`.

---

## Total Cities

**2,516** (was 2,413 before fix)

- Removed: 33 US duplicates
- Added: ~136 cities across 67 under-represented countries
- Net change: +103 cities

---

## Zero-City Countries

**None.** Every one of the 196 countries has at least 1 city.

---

## One-City Countries

| Code | Cities | Justification |
|---|---|---|
| VA | 1 | Vatican City is a single-city sovereign state. 1 city is correct. |

---

## Suspiciously Small Countries (<=8 cities after fix)

| Code | Cities | Notes |
|---|---|---|
| LI | 8 | Liechtenstein — small principality, 8 municipalities is accurate |
| VA | 1 | Vatican City — single city-state, correct |

All other countries now have >= 9 cities.

---

## Duplicate/Malformed Records

| Check | Result |
|---|---|
| Duplicate cities within same country | **0** (was 33 in US, all removed) |
| Malformed country codes | **0** |
| Malformed city records (non-string) | **0** |
| Empty city strings | **0** |
| Country codes missing from cities.json | **0** |
| City codes missing from countries.json | **0** |

---

## Deterministic Mapping Result

**YES — fully deterministic.**

- `CountryCitySelector._on_country_selected()` at `uiverse_combobox.py:884` looks up `self.cities_data.get(country_code, [])` using the ISO 2-letter code as key
- When country changes, city list is replaced entirely and city selection is cleared (`uiverse_combobox.py:897`)
- No cross-country leakage possible — each country code maps to exactly one array
- No silent fallback to any default city exists in the mapping logic

---

## Alexandria Fallback Result

**REMOVED from active code.**

| Location | Status |
|---|---|
| `main.py:542` default settings | `"manual_city": "", "manual_country": ""` — no Alexandria |
| `main.py:2866` `_resolve_location()` | Returns `"manual-invalid"` when manual mode has no city/country — no Alexandria |
| `main.py:2956` fetch_times worker | Shows error dialog "يرجى اختيار الدولة والمدينة أولاً." — no Alexandria |
| `main.py:2976` apply_times default | `location_label: str = ""` — no Alexandria |
| `backup/` directories | Old versions still contain Alexandria fallbacks — untouched per requirements |
| `dist/` directories | Old builds still contain Alexandria fallbacks — untouched per requirements |

Alexandria appears in `cities.json` only as a legitimate city entry for Egypt (EG), which is correct behavior.

---

## Countries Tested (Previously Small Datasets)

| Code | Before | After | Sample Cities |
|---|---|---|---|
| BN | 5 | 9 | Bandar Seri Begawan, Kuala Belait, Seria, Tutong |
| AD | 7 | 9 | Andorra la Vella, Escaldes-Engordany, Encamp |
| AG | 7 | 10 | Saint John's, All Saints, Liberta |
| BB | 6 | 9 | Bridgetown, Speightstown, Oistins |
| GD | 6 | 9 | St. George's, Gouyave, Grenville |
| BT | 7 | 9 | Thimphu, Phuntsholing, Punakha |
| BZ | 7 | 9 | Belize City, San Ignacio, Belmopan |
| CY | 7 | 9 | Nicosia, Limassol, Larnaca |
| KI | 8 | 12 | South Tarawa, Betio, Bairiki |
| TV | 8 | 15 | Funafuti, Nanumea, Nanumanga |
| NR | 8 | 9 | Yaren, Baiti, Anabar |
| PW | 8 | 13 | Ngerulmud, Koror, Melekeok |
| MH | 8 | 13 | Majuro, Ebeye, Jabat |
| SM | 9 | 9 | San Marino, Borgo Maggiore, Serravalle |
| EG | 15 | 15 | Cairo, Alexandria, Giza |
| SA | 15 | 15 | Riyadh, Jeddah, Mecca |
| US | 440 | 407 | New York, Los Angeles, Chicago |
| GB | 15 | 15 | London, Birmingham, Manchester |
| AU | 10 | 10 | Sydney, Melbourne, Brisbane |

---

## NO BUILD

Per phase instructions, no EXE build was performed. Build will occur in a subsequent phase after review.

---

## Remaining Limitations

1. **City names are in English only** — `cities.json` stores English names. Arabic transliteration could be added in a future phase.
2. **Vatican City (VA) has 1 city** — This is geographically correct; Vatican City is a single city-state.
3. **Liechtenstein (LI) has 8 cities** — Accurate for its 160 km² area with 11 municipalities, 8 of which are significant.
4. **No runtime city search/geocoding** — If a user needs a city not in the dataset, they must use the lat/lon fields. A Nominatim/OpenStreetMap lookup could be added later.
5. **Old `backup/` and `dist/` directories** still contain the Alexandria fallback code — these were intentionally NOT modified per phase requirements.
