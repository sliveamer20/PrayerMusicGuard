# Phase 20.50 — GitHub Release v1.2.7

**Status:** COMPLETE — **PASS**
**Date:** 2026-09-22
**Version:** 1.2.7

Published the verified Phase 20.47 Final Stable as GitHub Release **v1.2.7**.
No application source, UI, behavior, encryption, signing, build, or toolchain was
modified; nothing was rebuilt. The only writes were one annotated git tag, the
GitHub Release + its assets, and two release-manifest text files created in the
git-ignored `dist\Phase20-47-Final-Stable\` folder.

---

## 1. Result summary

| Field | Value |
|---|---|
| **Release URL** | <https://github.com/sliveamer20/PrayerMusicGuard/releases/tag/v1.2.7> |
| **Release API id** | `394166336` |
| **Tag** | `v1.2.7` (annotated, `tag` object) |
| **Tag target commit** | `9b11e0901b4873bdc9edfc544299d28d7e7cf46b` — **exact match** |
| **Tag message** | `PrayerMusicGuard v1.2.7 — Phase 20.47 Final Stable` |
| **Release name** | `v1.2.7` |
| **State** | published (`draft: false`, `prerelease: false`) |
| **Uploaded assets** | 3 (`PrayerMusicGuard-Setup.exe`, `SHA256SUMS.txt`, `RELEASE_MANIFEST.txt`) |
| **No source binaries / dist tree uploaded** | confirmed — only the 3 intended assets |

---

## 2. Artifact verification (pre-publish)

Two v1.2.7 artifact sets exist locally; the task designates
`dist\Phase20-47-Final-Stable\` as authoritative, and it is the one that matches
the Phase 20.47 report:

| Set | EXE | Setup |
|---|---|---|
| `dist\Phase20-47-Final-Stable\` (**authoritative, published**) | 4,270,360 B — `E3B0D69D…3E3DB9` | 14,648,840 B — `FF589DCC…6C65F` |
| `releases\v1.2.7\` (historical 2026-09-18 archive, untouched) | 16,416,372 B — `A966A99C…7529F` | 18,239,729 B — `70574567…636BC` |

The published hashes **match the Phase 20.47 report exactly**. The older
`releases\v1.2.7\` folder predates the 20.46/20.47 hardening (one-file build,
different toolchain output) and was **not** used; it remains untouched as the
local historical archive.

### Signature status

| Check | PrayerMusicGuard.exe | PrayerMusicGuard-Setup.exe |
|---|---|---|
| Signer | `CN=Ayman Alaa Abu Leila` | `CN=Ayman Alaa Abu Leila` |
| Thumbprint | `E62474D0BE183AA95876BC5464B319D54B248E1F` | same |
| Signature algorithm | **sha256RSA** | **sha256RSA** |
| Timestamp | RFC 3161, `SSL.com Timestamping Unit 2025 E1` | same |
| `Get-AuthenticodeSignature` | `UnknownError` (untrusted root — expected, self-signed) | same |
| `signtool verify /pa /v` | 1 error only: *"certificate chain … terminated in a root certificate which is not trusted"* | same |

Both resolve a full chain to the self-signed root with **only** the expected
untrusted-root condition (Phase 20.47 §9). The certificate is present in
`Cert:\CurrentUser\My`, Code Signing, valid to 2028-09-22.

`VERSION` = `1.2.7`; `PrayerMusicGuard.iss` `MyAppVersion` = `1.2.7` (consistent).

### Release manifest files

`SHA256SUMS.txt` and `RELEASE_MANIFEST.txt` were **created** for this release in
`dist\Phase20-47-Final-Stable\` (git-ignored). The pre-existing
`releases\v1.2.7\{SHA256SUMS,RELEASE_MANIFEST}.txt` describe the older build and
were deliberately **not** reused, since their hashes do not match the published
artifacts.

- `SHA256SUMS.txt` (94 B) — the downloadable installer hash:
  `FF589DCC…6C65F  PrayerMusicGuard-Setup.exe`
- `RELEASE_MANIFEST.txt` (885 B) — version, toolchain, hardening, signing, and
  both artifact hashes (Setup as the downloadable asset; EXE as the in-bundle
  executable the Setup installs).

---

## 3. Tag

```
git tag -a v1.2.7 9b11e0901b4873bdc9edfc544299d28d7e7cf46b \
       -m "PrayerMusicGuard v1.2.7 — Phase 20.47 Final Stable"
git push origin v1.2.7        ->  * [new tag]  v1.2.7 -> v1.2.7
```

Verified after push (API `GET /repos/.../tags`): `v1.2.7 -> 9b11e0901b…f46b`.

---

## 4. Assets uploaded

| Asset | Size | GitHub asset id | Purpose |
|---|---|---|---|
| `PrayerMusicGuard-Setup.exe` | 14,648,840 B | 582389748 | Signed installer (the only binary published) |
| `SHA256SUMS.txt` | 94 B | 582390408 | Integrity hash of the installer |
| `RELEASE_MANIFEST.txt` | 885 B | 582390426 | Build provenance |

Uploaded via `POST /releases/{id}/assets` (multipart body, `name` query). The
full `dist\` tree, the bundle folder, and all source/DLL/PYD binaries were **not**
uploaded — only the three intended files.

### Post-upload verification (downloaded back from GitHub)

| Asset | Published size | Downloaded size | Remote SHA-256 | Local SHA-256 | Match |
|---|---|---|---|---|---|
| `PrayerMusicGuard-Setup.exe` | 14,648,840 B | 14,648,840 B | `FF589DCC0628D99BDE297E43492F5E185E3C8A0B41AD5854EDE1F21A7ED6C65F` | `FF589DCC…6C65F` | **byte-identical** |
| `SHA256SUMS.txt` | 94 B | 94 B | `CAAAA80F…6543A3` | `CAAAA80F…6543A3` | **byte-identical** |
| `RELEASE_MANIFEST.txt` | 885 B | 885 B | `8B58C1AC…46428B` | `8B58C1AC…46428B` | **byte-identical** |

Every published asset was re-downloaded from GitHub and hashes/sizes compared
against the local authoritative copies: **all match**.

---

## 5. Secret verification

| Check | Result |
|---|---|
| Token pattern scan of release notes, release name, tag name, and all asset names/labels | **PASS** — no `ghp_`/`github_pat_`/`sk-`/PEM/`AKIA`/`xox` patterns |
| Token pattern scan of the public release HTML page (unauthenticated fetch) | **PASS** |
| Secret scan of all 145 repository files | **PASS** — 0 hits |
| Remote URL / `.git/config` free of embedded credentials | **PASS** — clean URL, no `ghp_`/`github_pat_` |
| Token persisted to credential store by this phase | **PASS** — not persisted (ephemeral `-c credential.helper` only; pre-existing store entry is an unrelated secret, confirmed by hash in 20.49) |
| Token ever printed or logged | **No** — used only via `$env:GH_TOKEN` in `Authorization` headers; all command output scanned for `ghp_`/`github_pat_` before display |

Release notes contain only 64-hex SHA-256 hashes; the token is a distinct format
and cannot collide.

---

## 6. Release notes content

Concise notes describing v1.2.7 as the verified stable release: download
instructions, the expected SHA-256 for the installer, what the build is (pinned
Win7 toolchain — Python 3.8.10 x64 + PyInstaller 5.13.2, Inno Setup 6; encrypted
PYZ with no readable application `.py` shipped; Authenticode SHA-256 signed by
`CN=Ayman Alaa Abu Leila` with the self-signed caveat), runtime QA results
(25/25 on standalone and installed copies; clean install/uninstall), and install
steps. Links to the repository and `SECURITY.md` guidance.

---

## 7. Previous repository / release integrity

| Item | Status |
|---|---|
| `main` local == remote | `2276463…6ed140` — **unchanged** (no new commit this phase) |
| Source files (main.py, webview_app/*, spec, .iss, build_exe.bat, release.ps1, VERSION) | **untouched** — read-only this phase |
| Encryption / signing design and material | **untouched** — no rebuild, no re-sign |
| `pyz_crypto_key.txt` | hash `83DA49E5…CE433B9C` — **unchanged**, still git-ignored, never bundled |
| `releases\v1.2.5` / `v1.2.6` / `v1.2.7` local archives | counts 4 / 5 / 4 files — **untouched** |
| 20.47 Final Stable EXE/Setup in `dist\` | hashes unchanged — byte-identical to published assets |
| Repository files (145) | no modifications, no new commits |

---

## 8. FINAL STATUS

| Gate | Result |
|---|---|
| Authoritative artifacts verified (hashes match Phase 20.47) | **PASS** |
| Signatures valid (SHA-256, correct signer, only expected untrusted-root) | **PASS** |
| VERSION = 1.2.7 | **PASS** |
| `SHA256SUMS.txt` created and consistent | **PASS** |
| Tag `v1.2.7` → exactly `9b11e0901b…f46b`, pushed | **PASS** |
| GitHub Release created, published (not draft/prerelease) | **PASS** |
| Only intended assets uploaded (Setup + 2 manifests); no dist tree / source binaries | **PASS** |
| Published assets byte-match local verified artifacts | **PASS** |
| No secret anywhere in output, repo, notes, or asset names | **PASS** |
| No rebuild, no UI/source/encryption/signing change | **PASS** |
| Prior repo, tags, local archives, and key material unchanged | **PASS** |

# **FINAL: PASS**

Release: <https://github.com/sliveamer20/PrayerMusicGuard/releases/tag/v1.2.7>
(tag `v1.2.7`, commit `9b11e0901b4873bdc9edfc544299d28d7e7cf46b`, 3 assets).

No GitHub Actions or auto-update code was created. Phase 20.51 not started.

**STOP — Phase 20.50 complete.**
