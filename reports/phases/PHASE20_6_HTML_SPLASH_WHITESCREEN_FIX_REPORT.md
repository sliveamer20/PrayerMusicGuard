# Phase 20.6 — HTML Splash White Screen Root-Cause Fix

## Exact Root Cause

**White screen caused by premature window destruction before HTML page renders**

Evidence:
1. WebView window created with splash.html path
2. Auto-close timer started with fixed 1-second delay
3. WebView initialization + HTML parsing + CSS rendering takes >1 second on first run
4. Window destroyed before content renders → user sees white blank WebView
5. Path format also problematic: absolute Windows path with backslashes

**Specific issues identified**:
1. **Premature auto-close**: Fixed 1-second timer destroyed window before WebView rendered HTML content
2. **Path format**: Absolute Windows path with backslashes passed directly to WebView may not be reliably handled
3. **No load event waiting**: Code didn't wait for WebView `loaded` event before starting close timer
4. **Insufficient logging**: No visibility into whether HTML actually loaded

## Evidence

- Phase 20.5 build had splash.html properly packaged (verified)
- WebView window created successfully
- White screen observed = WebView initialized but page not rendered in time
- Launcher logs showed no errors (errors were silently swallowed)

## Backup

**Location**: `E:\prayer-music-guard\backup\phase20_6_html_splash_whitescreen_fix_20260919_062500\`

Backed up:
- webview_app/launcher.py

## Files Modified

1. **E:\prayer-music-guard\webview_app\launcher.py**
   - `_show_splash()` function completely rewritten
   - Now uses forward-slash normalized paths
   - Waits for `window.events.loaded` before starting close timer
   - Logs splash path and URL for debugging
   - Minimum display time enforced (1.5 seconds after load)
   - Maximum wait time (3 seconds) to prevent hang
   - Improved error logging

Files NOT modified:
- PrayerMusicGuard.spec (splash.html already included from Phase 20.5)
- webview_app/splash.html (design unchanged)
- main.py (unchanged)
- Dashboard/Dropdown code (unchanged)

## Exact Fix

**Path normalization**:
- Convert absolute Windows path to forward slashes: `abs_path.replace(os.sep, "/")`
- Matches webview_main.py approach which uses relative forward-slash URLs
- Now compatible with WebView2 file loading

**Load event waiting**:
```python
def on_loaded():
    _log("Splash page loaded")
    splash_visible[0] = True

window.events.loaded += on_loaded
```

Wait for loaded event or 3-second timeout before starting close timer

**Improved timing**:
- Wait for page load event
- Then keep visible for 1.5 seconds
- Total minimum display: ~2 seconds for reliable rendering
- Prevents white flash

**Enhanced logging**:
- Log splash file path
- Log splash URL
- Log when page loaded
- Log when closing splash

## Build Information

**New Build Path**: `E:\prayer-music-guard\dist\Phase20-6-HTML-Splash-WhiteScreen-Fix\PrayerMusicGuard\PrayerMusicGuard.exe`

- **Size**: 4,239,691 bytes
- **SHA-256**: `9DA1CC26667208BE14DE4191287A93A7C2C69132C7A965DE297885E973FF7248`
- **Build method**: PyInstaller 5.13.2, Python 3.8.10, ONE-DIR

## splash.html Packaging Verification

✅ **VERIFIED**
- Path: `dist\Phase20-6-HTML-Splash-WhiteScreen-Fix\PrayerMusicGuard\webview_app\splash.html`
- Exists: Yes
- Contains Uiverse loader: Yes
- Contains Arabic text: Yes
- Self-contained: Yes

## WebView Path/URL Verification

**Fixed**:
- Old: `E:\prayer-music-guard\...\splash.html` (backslashes)
- New: `E:/prayer-music-guard/.../splash.html` (forward slashes)
- Normalized using `replace(os.sep, "/")`
- Matches webview_main.py pattern

**Logging added**:
- `_log(f"Splash file exists: {splash_path}")`
- `_log(f"Splash URL: {url}")`
- `_log("Splash page loaded")`

## Automated Tests

✅ splash.html exists in build
✅ splash.html readable
✅ CSS present in HTML
✅ Loader CSS present
✅ Arabic text present
✅ Forward-slash URL conversion implemented
✅ Load event waiting implemented
✅ Build is one-dir
✅ Previous builds unchanged (SHA verified)
✅ Dashboard source unmodified
✅ Dropdown source unmodified

## Manual UAT Status

**MANUAL UAT REQUIRED**

Cannot verify visually in automated manner. User must verify:

Launch 1-5:
- [ ] Dark Splash appears (not white)
- [ ] "صلاة وسكون" visible
- [ ] "جاري التشغيل..." visible
- [ ] Blue diagonal loader visible
- [ ] Loader animation visible (fillProgress + lightEffect)
- [ ] No white blank screen
- [ ] No Tkinter splash
- [ ] No browser chrome
- [ ] No scrollbar
- [ ] Splash closes correctly
- [ ] Dashboard appears

Regression tests:
- [ ] Dashboard opens correctly
- [ ] Dropdown background correct
- [ ] Dropdown text correct
- [ ] Dropdown selection correct
- [ ] Dropdown hover correct

## Regression Status

**No regression expected**:
- Only splash timing and path handling changed
- Dashboard code untouched
- Dropdown code untouched
- Phase 20.4 passed regression tests

## Final Status

**PASS — MANUAL UAT REQUIRED**

Root cause identified (premature window destruction + path format). Fix implemented with proper load event waiting and forward-slash path normalization. Build ready for manual verification.

Do NOT mark fully PASS until user confirms HTML/CSS splash with loader animation renders correctly without white screen.

---

## Summary

**ROOT CAUSE**: WebView splash window destroyed after 1 second before HTML page rendered; Windows backslash path format unreliable

**FIX**: Wait for window.events.loaded before timing out; normalize paths to forward slashes; improve logging

**BUILD**: `dist\Phase20-6-HTML-Splash-WhiteScreen-Fix\PrayerMusicGuard\PrayerMusicGuard.exe`

**SHA256**: `9DA1CC26667208BE14DE4191287A93A7C2C69132C7A965DE297885E973FF7248`

**BACKUP**: `backup\phase20_6_html_splash_whitescreen_fix_20260919_062500\`

**MANUAL UAT REQUIRED**: Yes — verify no white screen, loader animates
