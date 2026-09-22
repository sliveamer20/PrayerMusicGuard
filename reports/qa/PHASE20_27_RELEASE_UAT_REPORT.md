# PHASE 20.27 — RELEASE BUILD & FINAL UAT REPORT

**Date:** 2026-09-20
**Scope:** Build the release EXE from the current PASSING source (Phase 20.24R-1 / 20.25 / 20.26R / 20.26R-QA all PASS) and run the final User Acceptance Test on the built artifact.
**Rules honored:** Backup first; no UI/logic changes; no previous build overwritten; Windows 7 compatibility; OneDir build; new isolated dist folder.

---

## Result: **PASS**

- Build completed with the pinned Windows 7 toolchain (exit 0).
- The real EXE boots end-to-end: splash → selector → WebView2 child → frontend load → bridge attached → scheduler started → ready flag written → clean shutdown.
- Functional UAT on the bundled (frozen) frontend: **38/38 test steps PASS**, **0 JavaScript / runtime errors** (error hook injected *before* `app.js` executed).
- Source tree is byte-for-byte unchanged from the verified PASS state.

---

## 1. Build Artifact

| Item | Value |
|------|-------|
| **Build path** | `E:\prayer-music-guard\dist\Phase20-27-Release-UAT\PrayerMusicGuard\PrayerMusicGuard.exe` |
| **EXE SHA256** | `3B49918FB8261B2C62D7EBDDC8AD652B660CBF03F7BD9E1C0655E1ED20B550CF` |
| EXE size | 4,253,030 bytes |
| OneDir bundle | 1,028 files / 31.2 MB (folder `PrayerMusicGuard\`) |
| Build mode | OneDir (`COLLECT` in `PrayerMusicGuard.spec`) |
| Toolchain | `win7\venv` — Python **3.8.10 x64** + **PyInstaller 5.13.2** (Windows 7 compatible) |
| Build command | `pyinstaller --noconfirm --clean --distpath dist\Phase20-27-Release-UAT PrayerMusicGuard.spec` |
| Build exit code | 0 |
| Built | 2026-09-20 13:19 (local) |
| Source version | `VERSION` = 1.2.7 (unchanged) |

**Dist isolation:** the release went into the **new** folder `dist\Phase20-27-Release-UAT\`. All previous builds are untouched — `dist\Phase20-24-Location-Data-Fix`, `dist\Phase20-23-UI-Regression-Fix`, `dist\Phase20-22-Location-Combobox-Uiverse` EXEs are intact with their original timestamps, and the 7 standalone EXEs in `dist\` root still carry their 9/18–9/19 timestamps. Nothing was overwritten.

**Backup:** full source mirror created *before* any build work at `backup\phase20_27_release_uat_20260920_131804\` (all key source files verified present).

---

## 2. Bundle Integrity — PASS

All data files shipped inside the EXE are **byte-identical (SHA256)** to the verified PASS source:

| Check | Result |
|-------|--------|
| `webview_app/frontend/js/app.js` (196-country list) | MATCH — `F5ED5515…206EFD` |
| `webview_app/frontend/index.html` | MATCH — `F23D1B17…44B2D7` |
| `assets/data/countries.json` (196) | MATCH — `17ECDBB5…61FE01` |
| `assets/data/cities.json` (2,516 cities) | MATCH — `D45B6BFD…F1B22E` |
| `webview_app/backend_api.py`, `launcher.py`, `platform_check.py`, `webview_main.py`, `splash.html` | MATCH (4/4) |
| `webview_app/frontend/js/theme.js` + 4 CSS files | MATCH (5/5) |
| `main.py`, `uiverse_combobox.py` | MATCH (2/2) |
| `webview/js` bridge files (`api.js`, `customize.js`, `finish.js`, `state.js`) | **Present** — the frozen `window.pywebview` bridge is correctly bundled (the known OneDir bridge gap) |
| `app_entry.py` | Compiled entry script (in the EXE scripts layer, not a data file) — proven at runtime by the probe |

**16/16 bundled data files match the verified source exactly.**

---

## 3. Real-EXE Verification — PASS

### 3a. WebView2 probe (`PrayerMusicGuard.exe --webview-child --probe`)

Exit code **0**. `webview.log` trace from the real frozen EXE:

```
probe started, INDEX=...\Phase20-27-Release-UAT\PrayerMusicGuard\webview_app\frontend\index.html
frozen=True _MEIPASS=...\Phase20-27-Release-UAT\PrayerMusicGuard
INDEX exists
WebView2 runtime path set from registry to: 153.0.4234.48
window created (visible, off-screen)
shown event fired
webview gui returned, loaded=True
probe SUCCESS
```

(The `[pywebview] Failed to delete user data folder` / `E_ABORT` lines printed on stdout appear **after** `probe SUCCESS` — they are benign teardown noise from window destruction, identical to the earlier source-level QA run.)

### 3b. Normal launch (full selector pipeline)

Launched `PrayerMusicGuard.exe` with no arguments. The complete frozen pipeline executed:

```
[launcher] Splash file exists: ...Phase20-27-Release-UAT\PrayerMusicGuard\webview_app\splash.html
[launcher] Splash page loaded → Closing splash window → HTML splash completed successfully
[launcher] starting HTML frontend (WebView2)
[launcher] HTML frontend ready; waiting for window to close → HTML frontend closed cleanly
[webview] Changed cwd to ...\Phase20-27-Release-UAT\PrayerMusicGuard
[webview] BackendAPI instance created → js_api attached to window
[webview] Single-instance guard: acquired (first instance)
[webview] Window created successfully → Scheduler started → Ready flag written
```

The real frontend window was detected: **900×760** (exactly as configured), process **Responding=True**, title "صلاة وسكون". A screenshot of the live window contained **346 distinct colors** dominated by the app's dark-theme palette (`#1c1f28`, `#1b1e27`, `#14161d`) — real rendered UI content, not a blank/white screen.

---

## 4. Functional UAT — 38/38 PASS

Driven through the **bundled frozen frontend** (the exact files shipped in the EXE) in a live WebView2 window with the **real `BackendAPI`** bridge attached. An error hook was injected **before** `js/app.js` loaded, so any init-time `ReferenceError` would have been caught. **Zero errors were captured at every poll.**

### Area results

| # | UAT Area | Result | Evidence |
|---|----------|--------|----------|
| 1 | Modern HTML UI | **PASS** | app shell + sidebar + topbar + main; 4 nav items; 4 pages; `dir=rtl lang=ar`; bridge `window.pywebview.api` available |
| 2 | Dashboard + countdown | **PASS** | 5 prayer cards; next prayer العصر 03:14 م; countdown `01:39:37` → `01:39:35` (ticking) |
| 3 | Manual/Automatic location | **PASS** | auto radio selectable; manual radio → `manual-fields display=block` |
| 4 | 196 countries | **PASS** | `country li count=196`; 4 added countries present (`missing=` none) |
| 5 | Egypt/Alexandria | **PASS** | Egypt → 15 cities (Cairo\|Alexandria\|Giza…); Alexandria selected; resolved "Alexandria, مصر / Egypt"; country change clears city; Saudi Arabia → Riyadh |
| 6 | Music Player | **PASS** | all controls present; 2 method radios; pause/resume commands delivered; running-apps dropdown loaded **39 apps** |
| 7 | Settings | **PASS** | all controls present; checkboxes populated (`enabled=true announce=true autostart=false`); save round-trip |
| 8 | Dark/Light theme | **PASS** | `data-theme` dark → light on switch; persisted to `localStorage pmg-theme=light` |
| 9 | Navigation | **PASS** | all 4 pages activate with correct titles (المواقيت / المشغّل / الإعدادات / لوحة القيادة) |

### Two steps re-verified (harness artifacts, not app defects)

| Step | First read | Root cause | Re-verification |
|------|-----------|------------|-----------------|
| 6b Egypt cities load | `cities=0` | The city `<li>` list renders only when the city combobox is **opened/focused**; the step counted it without opening it. | **6b-R2 PASS** — after focusing the city input: `cities=15 disabled=false firstItems=Cairo\|Alexandria\|Giza`, `hasAlexandria=true` |
| 7e running-apps dropdown | `visible=false` | `openAppDropdown()` is **async** — it calls the `list_running_apps` backend API and only removes `hidden` inside the promise callback; 1.0s settle was too short. | **7e-R3 PASS** — poll try 2: `visible=true status=تم تحميل 39 تطبيق جارٍ.` (loaded 39 running apps) |

Both are timing/sequencing artifacts of the test harness. With correct sequencing and wait, both pass. **No source change was made or needed.**

### Console / runtime errors

**None.** `window.__pmgErrors` was empty at every poll (init, post-load, and after all interactions) in both the main run and the follow-up run.

---

## 5. Constraints Compliance

| Rule | Status |
|------|--------|
| Backup first | `backup\phase20_27_release_uat_20260920_131804\` created before build (full source mirror, all key files verified) |
| No UI/logic changes | All source files **byte-identical** to pre-build state (SHA256 verified for 14 key files + spec/VERSION/CSS) |
| Do not overwrite previous builds | New isolated folder only; all prior `dist\Phase20-*` builds and root EXEs intact |
| Windows 7 compatibility | Built with pinned `win7\venv` Python 3.8.10 x64 + PyInstaller 5.13.2 (never the modern vendor Python) |
| OneDir build | `COLLECT` mode in `PrayerMusicGuard.spec`; output is a `PrayerMusicGuard\` folder (not a single file) |
| New isolated dist folder | `dist\Phase20-27-Release-UAT\` |

**User settings:** backed up before UAT and **fully restored** after (SHA256-identical to pre-test profile).

---

## 6. Overall Status

**PASS** — The release build was produced from the verified PASSING source with the pinned Windows 7 toolchain. The real EXE boots through the complete frozen pipeline (splash → WebView2 → bridge → scheduler), the bundled content is byte-identical to the verified source, and the final UAT passes all 9 required areas with 38/38 steps and zero runtime errors.

No further action is required. This concludes Phase 20.27.
