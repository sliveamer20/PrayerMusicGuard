# PrayerMusicGuard — Stable Releases

This folder holds the official stable releases of صلاة وسكون (PrayerMusicGuard).
Each release folder is immutable: it must never be modified, renamed, or mixed.

## Stable releases

### v1.2.9 (current final release)
Location: `releases\v1.2.9\`
Built: 2026-09-23, Phase 20.61 final stable release — promoted byte-for-byte
from the fully tested Phase 20.60 build (`dist\Phase20-60-v1.2.9-Test\`); the
source was **not** rebuilt for this release. Version bumped 1.2.8 → 1.2.9
(Phase 20.60) and built with the pinned Windows 7 toolchain.
**v1.2.9 is the FIRST stable release containing Auto Update support.**
Files:
- `PrayerMusicGuard.exe` — signed EXE (one-dir bootloader; run from its installed
  folder, SHA-256 `7C8AF804…0D6302`)
- `PrayerMusicGuard-Setup.exe` — signed Windows installer
  (SHA-256 `95B890FE…092958`), per-user, no administrator required
- `SHA256SUMS.txt` — integrity hashes of both artifacts
- `RELEASE_MANIFEST.txt` — build metadata, toolchain, QA results

Verification (Phase 20.60, run on the exact artifacts promoted here): the app
reports v1.2.9 at runtime; 159/159 updater + update-UI regression checks;
35/35 application regression; 24/24 live + offline Auto Update QA; the real EXE
runs on both the WebView2 and Tkinter fallback paths with the system tray live;
isolated install exit 0 (1,024 files, installed EXE hash-identical, signature
preserved); uninstall exit 0 with a clean removal. Authenticode-signed by
`CN=Ayman Alaa Abu Leila` (self-signed, RFC 3161 timestamped); the SHA-256
hashes above remain the authoritative integrity check.
Not yet published to GitHub: this phase performed local finalization only
(GitHub publication is a separate step), so the live update channel still
resolves to v1.2.8 until v1.2.9 is published.

### v1.2.8 (historical; superseded by v1.2.9)
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

### Older releases (removed; not active)

The previous release folders (`v1.2.5\`, `v1.2.6\`, `v1.2.7\`) were removed from
this folder during the 2026-09-23 Phase 20.52 final release cleanup. **v1.2.8 was
the only final release at that time** (it has since been superseded by v1.2.9,
the current final release, in Phase 20.61); no older release folders remain in
`releases\`. v1.2.8 itself is preserved here as an immutable historical record.
The GitHub Release `v1.2.7` and its tag were deleted in the same cleanup, so
v1.2.8 is also the only published GitHub release. A one-time safety backup of the
removed artifacts was taken outside the project before deletion.

Older stable releases (v1.1.0, v1.2.0, v1.2.1, v1.2.2, v1.2.3, v1.2.4, and the
former `releases\archive\`) had already been removed during the 2026-09-13
release cleanup.

Future stable versions are added as new `vX.Y.Z\` folders, one immutable folder
per version, after bumping the `VERSION` file and completing the build + QA.

## Important: what is NOT a stable release

- The project-root `dist\` folder is TEST/EXPERIMENTAL BUILD OUTPUT ONLY — it is
  not a stable release and not an archive. It previously held many
  phase-by-phase builds (`Phase20-XX-*` folders) whose contents were recreated by
  each build; all obsolete build folders were removed during the 2026-09-23
  Phase 20.52 final release cleanup, and it now retains only the current final
  build, `dist\Phase20-51-Final-v1.2.8\`, which is the build the v1.2.8 release
  was produced from. The installer's `[Files]` source is a staged bundle under
  `dist\`. The authoritative release copies live HERE, under
  `releases\vX.Y.Z\`, and GitHub Releases are published from these folders only.

- The Windows 7 toolchain is maintained separately under `win7\`
  (`win7\python\` — Python 3.8.10 x64 runtime, and `win7\venv\` — PyInstaller
  5.13.2 + cp38 build dependencies, pinned by the root
  `requirements-win7.txt`). It is intentionally kept apart from the modern
  cp314 toolchain in `vendor\` to avoid mixing Python 3.8 and Python 3.14
  files. Win7 test builds must use `win7\venv` and must NOT pass
  `--paths vendor`.
