# PHASE 20.19 — REBUILD LOCATION SELECTORS FROM SCRATCH + WORLDWIDE COUNTRY/CITY DROPDOWNS + REAL PRAYER TIME FETCH

## 1. Root cause of previous dropdown failures
- Previous implementation used text inputs with datalist/custom searchable lists that rebuilt DOM on each keystroke, causing focus loss and dropdown closing unexpectedly.
- No stable real dropdown component; results rendered over button.
- Location mode state was overwritten by init default and fillSettings callbacks.

## 2. New dropdown architecture
- Removed broken searchable input implementation.
- Built reusable dropdown component with trigger button, arrow, menu panel, search input inside menu.
- Dropdowns are stable: menu stays open, DOM node preserved, selection commits via mousedown.

## 3. Country data source
- Online Nominatim OpenStreetMap via featureType=country.
- User types in search inside dropdown; results are worldwide.
- Country names displayed as returned by Nominatim, preserving natural language.

## 4. City data source
- Online Nominatim OpenStreetMap filtered by country code.
- City search performed inside dropdown after country selection.
- Results filtered to city/town/village/place types, displayed in English.

## 5. Country language handling
- Display uses Nominatim display_name which preserves Arabic/English as provided.
- No forced translation.

## 6. City language handling
- City names displayed as returned by Nominatim, primarily English.

## 7. Manual/automatic state handling
- Radio change persists mode immediately via saveSettings.
- initLocationUI respects current mode, does not force auto.
- Country/city operations never modify location_mode.
- fillSettings updates display without forcing mode change.

## 8. Internet fetch flow
- collectLocation reads hidden inputs set-country/set-city.
- refreshTimes calls backend fetch_times with location_data.
- Backend resolves coordinates via Nominatim or uses city/country for AlAdhan.

## 9. AlAdhan integration
- Existing AlAdhan integration retained.
- Manual mode with city/country uses timingsByCity endpoint.

## 10. Prayer-time field update
- Fetched timings populate existing prayer-time fields above location section.
- 12-hour formatting preserved.
- Manual editing remains possible.

## 11. Backup path
`E:\prayer-music-guard\backup\phase20_19_location_dropdown_rebuild_20260919_080918\`

## 12. Modified files
- `E:\prayer-music-guard\webview_app\frontend\index.html`
- `E:\prayer-music-guard\webview_app\frontend\js\app.js`
- `E:\prayer-music-guard\webview_app\frontend\css\components.css`

## 13. Unmodified files
- Backend API, music control, scheduler, splash, countdown logic.

## 14. Build path
`E:\prayer-music-guard\dist\Phase20-19-Location-Dropdown-Rebuild\PrayerMusicGuard\PrayerMusicGuard.exe`

## 15. EXE size
4,241,026 bytes

## 16. SHA256
FE031D1C18F3721086C3B1DEDF739C40F4E86AA131897CB01D1F487D5778C713

## 17. Automated tests
- Python syntax OK
- JS syntax OK
- Dropdown markup present
- Nominatim URLs present
- Build exists
PASS

## 18. Manual UAT
Pending manual verification of country/city dropdowns, real fetch, manual mode stability, prayer times update.

## 19. Known limitations
- Nominatim rate limits, requires internet.
- Dropdown search requires typing at least 2 chars.

## 20. Final status
PASS — MANUAL UAT REQUIRED
