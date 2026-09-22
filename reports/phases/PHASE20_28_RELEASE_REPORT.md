# PHASE 20.28 — RELEASE BUILD & UAT REPORT

**Date:** 2026-09-20
**Scope:** Build the release EXE from the current PASSING Phase 20.28 source (automated 53/53 PASS + runtime QA 52/52 PASS, zero JS/runtime errors) and run the final User Acceptance Test on the built artifact.
**Rules honored:** Backup first; no source/UI/logic changes; no previous build overwritten; Windows 7 compatibility; OneDir build; new isolated dist folder.

---

## Result: **PASS**

- Build completed with the pinned Windows 7 toolchain (exit 0).
- The real EXE boots end-to-end: launcher → splash → WebView2 child → bridge attached → single-instance acquired → scheduler started → ready flag → live window.
- Functional UAT on the **bundled (frozen) frontend** with the **real `BackendAPI` bridge**: **28/28 checks PASS**, **zero JavaScript / runtime errors** (error hook injected *before* `app.js` executed).
- Source tree is byte-for-byte unchanged from the pre-build state (19/19 key files verified).

---

## 1. Build Artifact

| Item | Value |
|------|-------|
| **Build path** | `E:\prayer-music-guard\dist\Phase20-28-Release\PrayerMusicGuard\PrayerMusicGuard.exe` |
| **EXE SHA256** | `6D2E434F673948C684C66D91FE6249D998074825D2B31E3C7A1DADB7D64ACB18` |
| EXE size | 4,253,142 bytes |
| OneDir bundle | 1,028 files / 31.2 MB (folder `PrayerMusicGuard\`) |
| Build mode | OneDir (`COLLECT` in `PrayerMusicGuard.spec`) |
| Toolchain | `win7\venv` — Python **3.8.10 x64** + **PyInstaller 5.13.2** (Windows 7 compatible) |
| Build command | `pyinstaller --noconfirm --clean --distpath dist\Phase20-28-Release PrayerMusicGuard.spec` |
| Build exit code | 0 |
| Built | 2026-09-20 15:13 (local) |
| Source version | `VERSION` = 1.2.7 (unchanged) |

**Dist isolation:** the release went into the **new** folder `dist\Phase20-28-Release\`. All previous builds are untouched — every other `dist\Phase20-*` folder retains its original timestamp, and the Phase 20.27 EXE still hashes to `3B49918F…B550CF`, byte-identical to the value recorded in the 20.27 report. Nothing was overwritten.

**Backup:** full source mirror created *before* any build work at `backup\phase20_28_release_20260920_151204\` (19 key files verified present).

---

## 2. Bundle Integrity — PASS

All data files shipped inside the EXE are **byte-identical (SHA256)** to the Phase 20.28 source:

| Check | Result |
|-------|--------|
| `webview_app/frontend/js/app.js` | MATCH |
| `webview_app/frontend/index.html` | MATCH |
| `webview_app/frontend/js/theme.js` + 4 CSS files | MATCH |
| `webview_app/backend_api.py`, `launcher.py`, `platform_check.py`, `webview_main.py`, `splash.html` | MATCH |
| `main.py`, `uiverse_combobox.py` | MATCH |
| `assets/data/countries.json` (196), `assets/data/cities.json` (2,516 cities) | MATCH |

**13/13 bundled data files match the Phase 20.28 source exactly.** The pywebview `webview/js` bridge resources (`api.js`, `customize.js`, `finish.js`, `state.js`) are bundled via the spec's explicit `collect_data_files('webview', subdir='js')`, so the frozen `window.pywebview` bridge is present — proven at runtime by the attached-bridge checks below.

---

## 3. Real-EXE Verification — PASS

Launched `PrayerMusicGuard.exe` with no arguments. The complete frozen pipeline executed:

```
[webview] BackendAPI instance created → js_api attached to window
[webview] Single-instance guard: acquired (first instance)
[webview] Using relative frontend URL: webview_app/frontend/index.html
[webview] Window created successfully → Scheduler started → Ready flag written
[webview] Starting webview gui=edgechromium, storage_path=…\webview2_data
```

The live frontend window was detected with title "صلاة وسكون", process **Responding=True**, and the WebView2 runtime was resolved from the registry (153.0.4234.48). A clean shutdown followed (window closed, no leftover processes).

---

## 4. Functional UAT — 28/28 PASS

Driven through the **bundled frozen frontend** (the exact files shipped in the EXE) in a live WebView2 window with the **real `BackendAPI`** bridge loaded from the bundle, and the **real network** for location fetches. An error hook was injected **before** `js/app.js` loaded, so any init-time error would have been caught. **Zero errors were captured at every poll.**

### Area results

| # | UAT Area | Result | Evidence |
|---|----------|--------|----------|
| 1 | Modern HTML UI | **PASS** | `dir=rtl lang=ar`; 4 nav items; 4 pages; version 1.2.7; bridge `window.pywebview.api` available |
| 2 | Dashboard + countdown | **PASS** | 5 prayer cards; next prayer العصر; countdown `01:00:34` → `01:00:32` (ticking) |
| 3 | Manual/Automatic location | **PASS** | Manual radio → fields `display=block`; Auto radio → `none`; Auto persisted; **no "تعذر الحفظ"** on either switch |
| 4 | 196 countries | **PASS** | full country list renders `count=196` |
| 5 | Egypt/Alexandria | **PASS** | Egypt → 1 filter match → 15 cities (Cairo first); Alexandria selected; real fetch → "تم جلب المواقيت لـ Alexandria، مصر."; persisted `manual_city=Alexandria` |
| 6 | Auto Location | **PASS** | real IP geolocation resolved (Alexandria, Egypt); mode stayed `auto` in UI and profile |
| 7 | Music Player | **PASS** | inputs + 2 method radios + pause/browse buttons present; running-apps dropdown loaded **40 apps** (`visible=true`) |
| 8 | Settings | **PASS** | page populated from backend (`minutes=1, enabled=true`); save round-trip `1 → 7 → backend=7`, then restored |
| 9 | Dark/Light theme | **PASS** | toggle flipped `data-theme` dark → light, persisted to `localStorage pmg-theme=light` **and** backend `theme=light` |
| 10 | Navigation | **PASS** | all 4 pages activate with correct distinct titles (لوحة القيادة / المواقيت / المشغّل / الإعدادات) |
| 11 | Latitude/Longitude gone | **PASS** | no `#set-latitude`/`#set-longitude`, no خط العرض/خط الطول labels (Phase 20.28 fix verified in the frozen build) |
| 12 | Console / runtime errors | **PASS** | `window.__pmgErrors` empty at every poll; bridge intact; `readyState=complete` |

### One step re-verified (harness artifact, not an app defect)

| Step | First read | Root cause | Re-verification |
|------|-----------|------------|-----------------|
| 5b Egypt cities | `cities=0` + fallback message | The city `<li>` list renders from the **async** `get_cities` payload, which had not landed at the instant of the focus probe; the data arrived <1 s later (Alexandria was found in the immediately following step). Identical timing artifact to Phase 20.27 step 6b. | **5b-R2 PASS** — after a short settle poll: `cities=15`, first item `Cairo` |

This is a timing artifact of the test harness, not an application defect. **No source change was made or needed.**

### User settings

Backed up before UAT and **fully restored** after (profile verified identical to the pre-test baseline: `theme=dark`, `minutes=1`, `location_mode=auto`, empty manual fields, migration marker present). No app processes were left running.

---

## 5. Constraints Compliance

| Rule | Status |
|------|--------|
| Backup first | `backup\phase20_28_release_20260920_151204\` created before build (19 key files) |
| No source/UI/logic changes | All 19 key source files **byte-identical** to the pre-build backup (SHA256 verified) |
| Do not overwrite previous builds | New isolated folder only; all prior `dist\Phase20-*` builds intact with original timestamps; 20.27 EXE hash still matches its report |
| Windows 7 compatibility | Built with pinned `win7\venv` Python 3.8.10 x64 + PyInstaller 5.13.2 (never the modern vendor Python) |
| OneDir build | `COLLECT` mode in `PrayerMusicGuard.spec`; output is a `PrayerMusicGuard\` folder (not a single file) |
| New isolated dist folder | `dist\Phase20-28-Release\` |

---

## 6. Overall Status

**PASS** — The release build was produced from the verified PASSING Phase 20.28 source with the pinned Windows 7 toolchain. The real EXE boots through the complete frozen pipeline (launcher → WebView2 → bridge → scheduler), the bundled content is byte-identical to the source, and the final UAT passes all required areas with **28/28 steps and zero runtime errors**.

| Deliverable | Value |
|-------------|-------|
| Build | `dist\Phase20-28-Release\PrayerMusicGuard\PrayerMusicGuard.exe` — exit 0 |
| EXE SHA256 | `6D2E434F673948C684C66D91FE6249D998074825D2B31E3C7A1DADB7D64ACB18` |
| Bundle | 1,028 files / 31.2 MB OneDir, 13/13 data files byte-identical to source |
| UAT | **28/28 PASS**, 0 JS/runtime errors |
| Source integrity | Unchanged (19/19 files byte-identical to pre-build backup) |
| Prior builds | Untouched (20.27 EXE still `3B49918F…B550CF`) |

This concludes Phase 20.28. **Final verdict: PASS.**
