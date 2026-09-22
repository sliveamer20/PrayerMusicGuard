# صلاة وسكون — PrayerMusicGuard

**صلاة وسكون** (PrayerMusicGuard) هو تطبيق ويندوز يوقف مشغّل الموسيقى المختار
أوقات الصلاة تلقائياً، ثم يعيده بعد انتهائها. واجهة عربية (RTL) بتقنية WebView2
مع لوحة أوقات العودة والصلاة القادمة، وأيقونة بجوار الساعة، ووضعَي فاتح/داكن.

الإصدار الحالي: **1.2.7** (انظر ملف `VERSION`). منصّة الهدف: **Windows 7 SP1 x64**
فأحدث.

---

## Overview (English)

PrayerMusicGuard is a Windows utility that automatically suspends your selected
music player at prayer times and resumes it when the prayer window ends.

- Arabic, right-to-left WebView2 frontend with a live next-prayer countdown.
- System-tray icon for opening the window, pausing monitoring, or safe exit.
- Light / dark theme (persisted, independent of the Windows system theme).
- Country/city selection from bundled offline datasets (`assets/data`).
- Optional launch-at-logon (per-user HKCU entry, no administrator required).
- No telemetry, no auto-updater, no runtime downloads.

The UI layer is HTML/CSS/JS driven through `pywebview` + WebView2; the Windows
side (player detection, media-key/window handling, tray) is Python.

## Install (end users)

1. Get `PrayerMusicGuard-Setup.exe` for the latest release.
2. Run it — a per-user install needs no administrator rights.
3. Launch **صلاة وسكون**, pick your music player, set the athan program as an
   exception, fetch the prayer times, then press **حفظ وتشغيل** (Save & Run).

Closing the window does not stop monitoring: the app moves to the tray icon.
Right-click the tray icon to reopen the window, pause monitoring, or exit.

Verify the installer before installing — see [SECURITY.md](SECURITY.md).

## Build from source

Requires the pinned Windows 7 toolchain (Python 3.8.10 x64 + PyInstaller
5.13.2), kept locally in `win7\` and pinned by `requirements-win7.txt`.
See `release.ps1` for the exact preflight checks the build enforces.

```bat
:: Build the EXE bundle (one-dir) -> dist\PrayerMusicGuard\PrayerMusicGuard.exe
build_exe.bat

:: Full release: EXE + Inno Setup installer, archived under releases\vX.Y.Z\
powershell -File release.ps1 -Release
```

`release.ps1` builds with the pinned toolchain, produces
`dist\PrayerMusicGuard-Setup.exe`, and archives the signed artifacts under
`releases\vX.Y.Z\` with `SHA256SUMS.txt` and a release manifest. Without
`-Release` it only validates the environment and changes nothing.

To run from source (development only), a local Python toolchain is required —
see `requirements.txt`. The launcher `تشغيل-صلاة-وسكون.bat` runs `main.py`
with the local `vendor\` toolchain on the path.

## Icons

Files are organized under `assets/`:

- `images/prayer-music-guard.png`: the original logo with a real transparent
  background.
- `icons/prayer_music_guard.ico`: Windows icon at 16, 20, 24, 32, 40, 48, 64,
  128 and 256 px, bound to the window title, taskbar, and the EXE file.

## Repository layout

| Path | Contents |
|---|---|
| `main.py`, `uiverse_combobox.py`, `webview_app/` | Application source (entry point: `webview_app/app_entry.py`) |
| `assets/` | Icons, images, and the prayer-time datasets |
| `PrayerMusicGuard.spec`, `PrayerMusicGuard.iss` | PyInstaller and Inno Setup build definitions |
| `build_exe.bat`, `release.ps1` | Build and release scripts |
| `VERSION` | Single source of truth for the version (MAJOR.MINOR.PATCH) |
| `reports/` | Phase-by-phase development and QA history |
| `win7/`, `vendor/`, `build/`, `dist/`, `releases/`, `backup/` | Local only — not committed (toolchains, build output, release binaries, backups) |

The `releases/` folder is the **local release archive**: official binaries stay
on this machine (and on the GitHub Releases page), not in the git tree. Its
layout and policy are documented in `releases/RELEASES.md`.

## Safety

The default mode **suspends** only the selected music player process; it does
not terminate it. Do not choose the athan program as the music player. The
media-key mode is generic, and therefore less precise.

## Security

See [SECURITY.md](SECURITY.md) for how to report a vulnerability, how build-time
secrets (PYZ encryption key, signing certificate) are kept out of the
repository, and how to verify signed release binaries.

## License

No license has been declared yet. Until one is added, standard copyright terms
apply and the source is published for reference. Contact the repository owner
before redistributing or building derivative releases.
