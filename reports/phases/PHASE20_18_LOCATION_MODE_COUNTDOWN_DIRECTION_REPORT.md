# PHASE 20.18 — FINAL MANUAL LOCATION MODE STABILITY + COUNTDOWN BLOCK DIRECTION FIX

## 1. Root cause of manual → automatic switch
- `initLocationUI` forced `location_mode` to auto on every initialization by selecting the auto radio by default and unconditionally hiding manual fields.
- `fillSettings` overwrote the radio checked state on every state update from backend, causing a race where a late settings callback reset manual to auto during interaction.
- No immediate persistence of mode change: selecting manual did not save mode until later, so backend state remained auto.

## 2. Exact functions/events responsible
- `initLocationUI` default mode selection: `defaultMode.checked = true`
- `initLocationUI` unconditional `hideManualFields()` and city disable
- `fillSettings` at line 683-685 resetting `input[name="location_mode"]` from `data.location_mode`
- `saveSettings` not triggered on radio change

## 3. Fix applied
- Removed forced auto default selection in `initLocationUI`.
- Made `initLocationUI` initialize manual fields visibility based on current radio state, preserving user selection.
- Added immediate `saveSettings("location-status")` on `location_mode` radio change to persist mode to backend and prevent state revert.
- Kept country/city dropdowns stable with custom searchable lists; no DOM rebuild of location mode radios.
- Ensured `onCountrySelect` enables city only after country selected; no mode mutation.

## 4. Country dropdown behavior
- Custom searchable dropdown with in-place `<ul>` updates.
- Search via Nominatim `featureType=country`.
- Selection commits value, stores country code, clears city, does not modify `location_mode`.
- No duplicate result item left over button.

## 5. City dropdown behavior
- Disabled until country selected.
- Search via Nominatim filtered by `countrycodes`.
- Selection commits value, updates resolved location, does not modify `location_mode`.
- No entire section rebuild.

## 6. Countdown layout root cause
- Previous topbar changed to `flex-direction: column` which altered internal layout and perceived order.
- Countdown was forced into column flow changing control block direction.

## 7. Original control direction
- Topbar originally `display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap`.
- `.topbar__actions` is row flex with RTL visual order: Light/Dark toggle left, Monitoring status right in RTL.
- Controls order in DOM: monitor-chip then theme-switch, which in RTL renders as desired.

## 8. Final control direction
- Reverted topbar to original row wrap layout.
- `.topbar__actions { order:1 }`, `.topbar__countdown { width:100%; margin-top:8px; order:2 }`
- Countdown wraps below controls on next line, controls remain in original row and visual direction unchanged.

## 9. Backup
`E:\prayer-music-guard\backup\phase20_18_location_mode_countdown_direction_20260919_075735\`

## 10. Modified files
- `E:\prayer-music-guard\webview_app\frontend\index.html`
- `E:\prayer-music-guard\webview_app\frontend\js\app.js`
- `E:\prayer-music-guard\webview_app\frontend\css\components.css`

## 11. Build path
`E:\prayer-music-guard\dist\Phase20-18-Location-Mode-Countdown-Direction\PrayerMusicGuard\PrayerMusicGuard.exe`

## 12. EXE size
4,241,025 bytes

## 13. SHA256
CA9FCEE59D7069DBA0AE99348F6EB229291DE1C027CF590254B20D5C4C98E7DC

## 14. Automated tests
- Python syntax OK
- JS contains manual mode persistence
- HTML has searchable dropdowns, no coordinates
- CSS has topbar row wrap, countdown order
- Build exists
PASS

## 15. Manual UAT
- TEST A MANUAL MODE STABILITY: Pending
- TEST B REPEAT SAUDI ARABIA: Pending
- TEST C FETCH: Pending
- TEST D COUNTDOWN VISUAL: Pending
- TEST E APPEAR/DISAPPEAR: Pending

## 16. Regression
No changes to music control, scheduler, prayer calculation, splash. PASS

## 17. Known limitations
- Nominatim rate limits.
- Custom dropdown uses mousedown selection to preserve focus.

## 18. Final status
PASS — MANUAL UAT REQUIRED
