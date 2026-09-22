# PHASE 20.21 — DEFINITIVE LOCATION SELECTOR + REMOVE ALEXANDRIA FALLBACK

## ROOT CAUSE
- Country list was Nominatim search-only, no static dataset, menu appeared empty until typed.
- Manual mode state allowed fallback to saved automatic location, causing Alexandria fetch.
- No validation before fetch, so empty manual inputs triggered backend fallback.

## ALEXANDRIA FALLBACK
- Removed default initialization of manual location.
- Added frontend validation in refreshTimes to block fetch when country/city missing.
- Manual location state now independent from automatic.

## COUNTRY LIST
- Static COUNTRIES array with name_en, name_ar, code.
- Combobox populated from static list, filterable by typing.
- Worldwide countries included.

## CITY LIST
- City combobox uses Nominatim filtered by selected country code.
- Results limited to selected country.

## MANUAL STATE
- Mode persists, never switches during dropdown interaction.
- Manual location fields start empty.

## FETCH VALIDATION
- refreshTimes checks manual mode, country, city before calling backend.
- Shows error messages if missing.

## PRAYER FETCH
- Uses selected country/city only.

## BUILD
E:\prayer-music-guard\dist\Phase20-21-Location-State-Fix\PrayerMusicGuard\PrayerMusicGuard.exe

## SHA256
C025E4886EC900018D77263658E2F7C5161E689B8F78CC0FB5C02B6A309D36BD

## STATUS
PASS — MANUAL UAT REQUIRED
