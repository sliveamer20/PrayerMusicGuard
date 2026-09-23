# PrayerMusicGuard — Stable Releases

This folder holds the official stable releases of صلاة وسكون (PrayerMusicGuard).
Each release folder is immutable: it must never be modified, renamed, or mixed.

## Stable releases

### v1.2.8 (current stable)
Location: `releases\v1.2.8\`
Built: 2026-09-23, Phase 20.51 final release — rebuilt from the current source
(commit `fd5e580`, identical to the verified Phase 20.47 Final Stable state plus
the 1.2.7 → 1.2.8 version bump) with the pinned Windows 7 toolchain.
Files:
- `PrayerMusicGuard.exe` — signed EXE (one-dir bootloader; run from its installed
  folder, SHA-256 `3C1B50B1…E43E0E`)
- `PrayerMusicGuard-Setup.exe` — signed Windows installer
  (SHA-256 `BC941805…D0079`), per-user, no administrator required
- `SHA256SUMS.txt` — integrity hashes of both artifacts
- `RELEASE_MANIFEST.txt` — build metadata, toolchain, QA results

Verification: app reports v1.2.8 at runtime; 14/14 build + PYZ-encryption +
version checks; 28/28 standalone runtime QA; 28/28 installed runtime QA; install
exit 0 (1,024 files, installed EXE hash-identical, signature preserved);
uninstall exit 0 with a clean removal and no residual registry entries.
Published as the GitHub Release `v1.2.8`, assets byte-matching this folder.

### v1.2.7 (historical; superseded by v1.2.8)
Location: `releases\v1.2.7\`
The Phase 20.47 Final Stable build, published as the GitHub Release `v1.2.7`
(source-stripped, PYZ-encrypted, Authenticode-signed; the GitHub release assets
were built from `dist\Phase20-47-Final-Stable\`, which is byte-equivalent to this
source state). Kept as an immutable historical record; not modified.
Note: this local folder also retains the earlier 2026-09-18 one-file build
artifacts from the pre-20.47 release process.

### v1.2.5 (historical)
Location: `releases\v1.2.5\`
Files:
- `PrayerMusicGuard.exe` — standalone EXE (Win7-compatible toolchain)
- `PrayerMusicGuard-Setup.exe` — Windows installer (Inno Setup 6.7.3)
- `SHA256SUMS.txt` — integrity hashes of the two artifacts above
- `RELEASE_MANIFEST.txt` — build metadata (version, date, source hash)

SHA256 verification status: **VERIFIED** (Phase 59 release; hashes of both
artifacts match SHA256SUMS.txt, and dist\ copies are byte-identical).
Re-verified 2026-09-13 after the release cleanup.

Highlights: reliable prayer trigger (5s monitoring cadence +
5-minute catch-up window + day-bucketed duplicate prevention, midnight-safe);
exception-armored monitoring/countdown/dashboard chains with full tracebacks
and per-tick DEBUG diagnostics (PMG_LOG_LEVEL); per-window APPCOMMAND
pause/resume proof-logging with PID/window detail; reliable next-prayer
HH:MM:SS countdown with tomorrow fallback; scrollable responsive dashboard at
all window sizes; manual Dark/Light theme toggle (persisted, independent of
the Windows system theme); optional per-user launch-at-logon (HKCU Run entry,
no admin needed) with single-instance mutex guard; clean timer cancellation
and bounded worker shutdown; internal WAV announcements with completion
logging and hardened MP3 fallback validation.
Built with the Windows 7 toolchain (Python 3.8.10 x64 / PyInstaller 5.13.2),
cp38 PIL bundled, Win7-era bootloader, python38.dll, no api-ms-win-core-path
dependency. Frozen-build integration tests passed on the real EXE: monitoring
starts once, real VLC playing→paused→playing via APPCOMMAND only, internal
WAV from _MEIPASS ~2s after pause, no external player, single-instance guard,
close-to-tray, per-user installer verified (installed EXE hash-identical to
release). Full hardware verification still requires running this exact build
on the real Windows 7 SP1 x64 machine.

Older stable releases (v1.1.0, v1.2.0, v1.2.1, v1.2.2, v1.2.3, v1.2.4) and
the former `releases\archive\` (test-only/obsolete artifacts) were removed
from this folder during the 2026-09-13 release cleanup. Retained historical
releases: v1.2.5, v1.2.7, v1.2.8.

Future stable versions are added as new `vX.Y.Z\` folders, one immutable folder
per version, after bumping the `VERSION` file and completing the build + QA.

## Important: what is NOT a stable release

- The project-root `dist\` folder is TEST/EXPERIMENTAL BUILD OUTPUT ONLY — it is
  not a stable release and not an archive. It holds many phase-by-phase builds
  (`Phase20-XX-*` folders) whose contents are recreated by each build, and it
  must never be cleaned, deleted, or reorganized. The installer's `[Files]`
  source is a staged bundle under `dist\`. The authoritative release copies live
  HERE, under `releases\vX.Y.Z\`, and GitHub Releases are published from these
  folders only.

- The Windows 7 toolchain is maintained separately under `win7\`
  (`win7\python\` — Python 3.8.10 x64 runtime, and `win7\venv\` — PyInstaller
  5.13.2 + cp38 build dependencies, pinned by the root
  `requirements-win7.txt`). It is intentionally kept apart from the modern
  cp314 toolchain in `vendor\` to avoid mixing Python 3.8 and Python 3.14
  files. Win7 test builds must use `win7\venv` and must NOT pass
  `--paths vendor`.
