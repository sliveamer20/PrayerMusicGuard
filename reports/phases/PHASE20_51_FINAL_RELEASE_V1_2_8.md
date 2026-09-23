# Phase 20.51 — FINAL RELEASE v1.2.8

**Status:** COMPLETE — **PASS**
**Date:** 2026-09-23
**Version:** 1.2.8

Created the final **v1.2.8** release in `releases\` (the project's release
archive), rebuilt from the current source with the pinned Windows 7 toolchain and
the version bumped from 1.2.7 → 1.2.8, then published to GitHub **from
`releases\v1.2.8\`**. `dist\` was treated as test/experimental build output: not
cleaned, not deleted, not reorganized — one new isolated build folder was added
and nothing pre-existing was modified. `releases\v1.2.7\` and the GitHub v1.2.7
release were preserved untouched as historical record.

---

## 1. Result summary

| Field | Value |
|---|---|
| **GitHub Release URL** | <https://github.com/sliveamer20/PrayerMusicGuard/releases/tag/v1.2.8> |
| Release API id | `394201527` |
| Tag | `v1.2.8` (annotated) → commit `01ae3e9cd8c9edd0ccbf44a6c9522ef41cad1ac9` |
| Source commit | `01ae3e9` — parent `fd5e580` + the 1.2.8 version-bump commit |
| Release state | published (`draft: false`, `prerelease: false`) |
| Assets | 3, uploaded from `releases\v1.2.8\` only |
| GitHub assets == release folder | **byte-identical** (all 3, re-downloaded and hashed) |

---

## 2. Exact source state used

- Working tree at build time: `main` = `fd5e580` (the commit that proved source
  equivalence to the 20.47 Final Stable), clean, 0 uncommitted.
- Source-equivalence re-confirmed before building: the harness in
  `reports\phases\phase20_51_evidence\_source_equivalence.py` extracted all 7
  application modules from the *existing* 20.47 EXE's encrypted PYZ and compared
  them to current source — **37/37 checks: bytecode, names, and consts
  byte-for-byte identical** (Python 3.8.10).
- `main.py @ A46CF2E1C2B8` at build time; `main.py @ 6E998725B1E4` before the
  1.2.8 bump (single-line `APP_VERSION` change).

**Reference test build:** `dist\Phase20-47-Final-Stable\` was inspected
(read-only) to identify the latest completed and tested project state (1,022-file
bundle, EXE `E3B0D69D…3E3DB9`, Setup `FF589DCC…6C65F`). It was used only as a
*reference* — v1.2.8 was rebuilt from source, not copied from it.

### Version-bump changes (6 files, metadata only)

| File | Change |
|---|---|
| `VERSION` | `1.2.7` → `1.2.8` |
| `main.py` | `APP_VERSION = "1.2.7"` → `"1.2.8"` (single line; the app's only version source) |
| `PrayerMusicGuard.iss` | `#define MyAppVersion "1.2.7"` → `"1.2.8"` |
| `README.md` | current-version reference 1.2.7 → 1.2.8 |
| `releases\RELEASES.md` | documented v1.2.8 as current stable; v1.2.7/v1.2.5 as historical; corrected the `dist\` description to "test/experimental build output" |
| (new) `reports\phases\PHASE20_51_FINAL_RELEASE_V1_2_8.md` | this report |

`release.ps1` validation confirmed `VERSION == .iss MyAppVersion` consistency and
all preflight checks before building. No UI, behavior, security, or architecture
change was made.

### Backup created before any change

`backup\phase20_51_final_v1_2_8_20260923\` — `VERSION`, `main.py`,
`PrayerMusicGuard.iss`, `README.md`, `releases\RELEASES.md`, plus the two
transient `dist\` staging byproducts the installer build would otherwise touch.

---

## 3. Build result (pinned Win7 toolchain)

| Component | Version |
|---|---|
| Python | 3.8.10 x64 (`win7\venv`) |
| PyInstaller | 5.13.2 |
| tinyaes | bundled (PYZ crypto backend) |
| Inno Setup | 6 |
| signtool | 10.0.26100.0 x64 |

```
win7\venv\Scripts\python.exe -m PyInstaller --noconfirm --clean \
    --distpath dist\Phase20-51-Final-v1.2.8 PrayerMusicGuard.spec
  -> exit 0, COLLECT completed
```

Bundle: **1,022 files / 31 MB**, all required runtime resources present (icon,
both prayer datasets, splash, frontend index/app.js/CSS, WebView2 Core DLL,
tinyaes, python38.dll). **0** readable application `.py` files and no key file
shipped (only the 13 pystray third-party `.py` files, matching 20.47).

Signing: 11 first-party binaries + the installer, signed with
`signtool sign /fd sha256 /sha1 E62474D0…48E1F /tr http://ts.ssl.com /td sha256`
— all verified signed by `CN=Ayman Alaa Abu Leila`, thumbprint
`E62474D0BE183AA95876BC5464B319D54B248E1F`, SHA-256, RFC 3161 timestamped. The
only `Get-AuthenticodeSignature` status is `UnknownError` — the expected
untrusted-root condition for the self-signed certificate (documented in 20.47 §9).

The installer was built from a **temporary** `.iss` variant in the project root
(differs only in two path lines; identical metadata/config, including
`MyAppVersion 1.2.8`), so the canonical `dist\PrayerMusicGuard\` staging folder
and `dist\PrayerMusicGuard-Setup.exe` were never overwritten.

---

## 4. Release artifacts — `releases\v1.2.8\`

| File | Size | SHA-256 |
|---|---|---|
| `PrayerMusicGuard.exe` | 4,270,368 B | `3C1B50B1BC6724E6851E7D536E057B0331ABF981ACFA6C603D9066D2FFE43E0E` |
| `PrayerMusicGuard-Setup.exe` | 14,650,176 B | `BC941805EFBCE81580BADC0BB5839EECA6FDD62BF9197B99F4C25D4FBF4D0079` |
| `SHA256SUMS.txt` | 182 B | (contains both artifact hashes above) |
| `RELEASE_MANIFEST.txt` | 1,212 B | full build/QA provenance |

Uploaded to GitHub (3 assets, from this folder only):
`PrayerMusicGuard-Setup.exe`, `SHA256SUMS.txt`, `RELEASE_MANIFEST.txt`.

---

## 5. Complete QA results

| Suite | Result |
|---|---|
| Build / PYZ encryption / shipped version (`_verify_v128.py`) | **14/14 PASS** |
| Standalone signed-EXE runtime QA (CDP) | **28/28 PASS** |
| Installed-app runtime QA (CDP) | **28/28 PASS** |
| Install (silent, per-user) | **exit 0** — 1,024 files; installed EXE SHA-256 `3C1B50B1…E43E0E` = bundled EXE; signature preserved |
| Uninstall | **exit 0** — install dir removed, 0 residual uninstall registry entries |
| Source-removal in installed app | **0 violations** (no application `.py`, no key file) |
| Signing | **12/12** signed by `CN=Ayman Alaa Abu Leila`, timestamped |
| GitHub asset verification | **3/3 byte-identical** to `releases\v1.2.8\` |

Runtime-QA coverage: clean startup, WebView2 frontend (title/load/rendered
content), bridge with **16** API methods, prayer-data round-trip (5 prayers with
real times, exactly one next flagged), 5 prayer cards keyed Fajr..Isha,
next-prayer ring countdown, **Lucide icon SVGs** (Lucide signature: viewBox
24×24, `fill=none stroke=currentColor stroke-width=2`, round caps/joins),
**Park-UI** button/nav classes, **save animation** (`.is-saving` applied ~60 ms
after a real click, removed ~970–1000 ms later), **light/dark** themes, **RTL**
(`dir=rtl lang=ar`), zero CDP exceptions, zero console errors.

### v1.2.8 (not v1.2.7) shipped — three independent proofs

1. The decrypted `main` module inside the built EXE carries `APP_VERSION
   = "1.2.8"` and **not** `"1.2.7"` (`_verify_v128.py`, 2 dedicated checks).
2. The running application reports `get_state().version === "1.2.8"` (runtime
   check 3d, both standalone and installed).
3. Built EXE SHA-256 `3C1B50B1…E43E0E` ≠ v1.2.7's `E3B0D69D…3E3DB9`; Setup
   `BC941805…D0079` ≠ `FF589DCC…6C65F`. The v1.2.7 build was never used as build
   source — v1.2.8 was rebuilt from current source.

---

## 6. Preservation confirmations

| Item | Status |
|---|---|
| `dist\` not cleaned/deleted/reorganized | **CONFIRMED** — only `dist\Phase20-51-Final-v1.2.8\` added; `dist\PrayerMusicGuard\` (hash `E3B0D69D…`, unchanged), `dist\PrayerMusicGuard-Setup.exe`, and all `Phase20-*` folders byte-identical to pre-phase |
| `releases\v1.2.7\` preserved | **CONFIRMED** — 4 files, EXE `A966A99C…7529F`, Setup `70574567…636BC` (unchanged) |
| GitHub v1.2.7 release preserved | **CONFIRMED** — 3 assets intact, Setup hash `FF589DCC…6C65F` after re-download |
| Git history | **CONFIRMED** — no rewrite, no force-push; `v1.2.7` tag still points at `9b11e0901b…f46b` |
| `pyz_crypto_key.txt` | hash `83DA49E5…CE433B9C` — unchanged, git-ignored, never bundled |
| No secret exposed | **CONFIRMED** — scans clean on changed files, release notes, asset names; token never printed/logged/persisted |
| Auto Update (v1.2.9) | **NOT STARTED** — no auto-update or updater code written this phase |

---

## 7. FINAL STATUS

| Gate | Result |
|---|---|
| Latest completed source/build identified with confidence | **PASS** — 37/37 source-equivalence proof vs 20.47 |
| Version bump 1.2.7 → 1.2.8 (metadata only) | **PASS** — 4 files + RELEASES.md |
| Build with pinned Win7 toolchain | **PASS** — exit 0, 1,022 files |
| PYZ encryption + source-strip + shipped version | **PASS** — 14/14, 0 violations |
| Signing (EXE + 10 payloads + installer) | **PASS** — 12/12 |
| Runtime QA (standalone + installed) | **PASS** — 28/28 + 28/28 |
| Install / uninstall | **PASS** — exit 0 / exit 0, clean |
| `releases\v1.2.8\` created, final artifacts only | **PASS** — 4 files |
| `dist\` untouched; v1.2.7 preserved (local + GitHub) | **PASS** |
| GitHub Release v1.2.8 published from `releases\v1.2.8\` | **PASS** — assets byte-match |
| No secret exposed; no Auto Update; no unrelated changes | **PASS** |

# **FINAL: PASS**

Release: <https://github.com/sliveamer20/PrayerMusicGuard/releases/tag/v1.2.8>
(tag `v1.2.8`, commit `01ae3e9cd8c9edd0ccbf44a6c9522ef41cad1ac9`).

Evidence: `reports\phases\phase20_51_v128_evidence\`
(`_verify_v128.py` + `v128_build_result.json`, `_runtime.js`,
`_runtime_installed.js` + `runtime_result.json` ×2, `v128_light.png`,
`v128_dark.png`, `installed_light.png`, `installed_dark.png`), and
`reports\phases\phase20_51_evidence\` (`_source_equivalence.py`,
`source_equivalence_result.json`).

No GitHub Release was overwritten; v1.2.7 stands as historical record. Auto
Update was not implemented (deferred to the next phase / v1.2.9). Phase 20.52 not
started.

**STOP — Phase 20.51 complete.**
