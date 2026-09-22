# PrayerMusicGuard — Stable Releases

This folder holds the official stable releases of صلاة وسكون (PrayerMusicGuard).
Each release folder is immutable: it must never be modified, renamed, or mixed.

## Stable releases

### v1.2.5 (current stable, only retained release)
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
from this folder during the 2026-09-13 release cleanup; v1.2.5 is the only
retained release.

Future stable versions are added as new `vX.Y.Z\` folders (created only by
`release.ps1 -Release` after bumping the `VERSION` file).

## Important: what is NOT a stable release

- The project-root `dist\` folder is CURRENT BUILD OUTPUT ONLY — it is not a
  stable release and not an archive. `release.ps1` and `PrayerMusicGuard.iss`
  operate on it (the installer packages `dist\PrayerMusicGuard.exe`), and its
  contents are recreated by each build. As of this writing its contents are
  byte-identical duplicates of `releases\v1.2.5` (leftovers of the v1.2.5
  build), but the authoritative v1.2.5 copies live here, under
  `releases\v1.2.5\`.

- The Windows 7 toolchain is maintained separately under `win7\`
  (`win7\python\` — Python 3.8.10 x64 runtime, and `win7\venv\` — PyInstaller
  5.13.2 + cp38 build dependencies, pinned by the root
  `requirements-win7.txt`). It is intentionally kept apart from the modern
  cp314 toolchain in `vendor\` to avoid mixing Python 3.8 and Python 3.14
  files. Win7 test builds must use `win7\venv` and must NOT pass
  `--paths vendor`.
