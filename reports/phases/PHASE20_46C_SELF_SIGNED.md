# Phase 20.46.C — Self-Signed Developer Code Signing

**Status:** COMPLETE — PrayerMusicGuard.exe signed with a self-signed developer
certificate identifying **Ayman Alaa Abu Leila**.

> ## IMPORTANT: THIS IS A SELF-SIGNED CERTIFICATE — NOT PUBLICLY TRUSTED
>
> The certificate used here is **self-signed**. It was issued by the developer to the
> developer and is **not chained to any publicly trusted Certificate Authority**.
> Windows will display the signer name "Ayman Alaa Abu Leila", but signature
> verification reports an **untrusted root** condition on every machine that has not
> explicitly trusted this certificate. This is expected and inherent to self-signed
> certificates.
>
> This is **developer identification only**. It is *not* equivalent to a certificate
> from a public CA (Sectigo, DigiCert, SSL.com, GlobalSign, …) and must never be
> presented as such. It does **not** clear SmartScreen reputation, does **not** satisfy
> the Phase 20.46.C-audit prerequisites for a public release, and will still trigger
> Windows "Unknown publisher" / SmartScreen warnings for end users who do not have the
> certificate installed. A public release still requires a CA-issued certificate.

**Date:** 2026-09-22
**Source build:** `dist\Phase20-46B-Verification\PrayerMusicGuard` (the latest verified
20.46.B build — Python 3.8.10 x64, PyInstaller 5.13.2, PYZ-encrypted, source-stripped).

---

## 1. Certificate — Public Metadata

Created with PowerShell `New-SelfSignedCertificate -Type CodeSigningCert`. Only public
metadata is listed below. **No private key was exported, printed, or logged anywhere in
this phase.**

| Field | Value |
|---|---|
| **Subject (CN)** | **Ayman Alaa Abu Leila** |
| **Issuer** | Ayman Alaa Abu Leila (self-signed: subject == issuer) |
| **SHA-1 thumbprint (store key)** | **E62474D0BE183AA95876BC5464B319D54B248E1F** |
| Serial number | `7AABC066259598B24706E04A57825CF6` |
| Subject Key Identifier (SHA-1) | `E9F9B29DFE58A8125DCB807C41035B89B16EC86E` |
| Public key algorithm | **RSA** |
| Public key size | **3072 bits** |
| Signature algorithm | **sha256RSA** (SHA-256 with RSA) |
| Valid from | 2026-09-22 18:04:26 (local) |
| **Valid to (expires)** | **2028-09-22 18:14:26 (local)** — 2 years |
| Key usage | Digital Signature (critical) |
| **EKU** | **Code Signing — OID 1.3.6.1.5.5.7.3.3** |
| Store | **`Cert:\CurrentUser\My`** |
| Private key | Present in the CNG key container, **non-exportable** |
| Trust status | **SELF-SIGNED / NOT publicly trusted** |

### Private key non-exportability (verified, not assumed)

The key is held in a Windows CNG (KSP) key container. An actual export attempt was made
programmatically to prove the key cannot leave the container:

```
CNG key algorithm: RSA
CNG key size     : 3072
IsMachineKey     : False
Export attempt   -> "The requested operation is not supported."  (REFUSED)
```

The private key material was **never** read into memory as a blob and **no** `.pfx`,
`.pvk`, or `.p12` file was created anywhere on disk. A recursive search of the whole
project tree for `*.pfx` / `*.pvk` returned **zero** files.

> The certificate and private key exist **only** in the local Windows certificate store
> of this build machine. They were **not** uploaded to GitHub or any remote location
> (the project repository is local, and no `git add`/`git push` was performed in this
> phase).

---

## 2. Signed Build

A **new isolated copy** was created so the original 20.46.B verification build was not
modified:

- **Signed EXE path:**
  `E:\prayer-music-guard\dist\Phase20-46C-SelfSigned\PrayerMusicGuard\PrayerMusicGuard.exe`
- **Copy provenance:** `dist\Phase20-46B-Verification\PrayerMusicGuard` →
  `dist\Phase20-46C-SelfSigned\PrayerMusicGuard` — 1023 files copied, verified
  **byte-for-byte identical** to the source (all 1023 SHA-256 hashes matched) *before*
  signing.
- **Signing tool:** `C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64\signtool.exe`
  (version 10.0.26100.8249)
- **Command used:**
  ```
  signtool sign /fd sha256 /sha1 E62474D0BE183AA95876BC5464B319D54B248E1F ^
                /tr http://ts.ssl.com /td sha256 PrayerMusicGuard.exe
  ```
  - `/fd sha256` — SHA-256 file digest
  - `/tr http://ts.ssl.com` + `/td sha256` — RFC 3161 timestamp, SHA-256 timestamp digest
- **Result:** `Successfully signed` (exit code 0). Signature appended to the EXE; size
  grew from `4,264,707` → `4,270,384` bytes (+5,677 bytes of signature + countersignature).

### SHA-256 of the signed EXE

```
4BA1D9DBAC881FA499584571111602CA692AA6105C20702EFAE4AEC169BFC4C2
```

For reference, the **unsigned** 20.46.B source EXE hash was
`5984502F83847C0C4D343AE28FC29650EB5FD4DCAB996C601ED8A496870CF48F` — the difference is
entirely the embedded Authenticode signature, not a content change.

### Why signing is safe for this PyInstaller onedir EXE

PyInstaller 5.13.2's `CArchiveReader` locates the embedded package by scanning the whole
file for the `MEI\014\013\012\013\016` cookie magic (`win7\venv\Lib\site-packages\
PyInstaller\archive\readers.py:113-137`), not by reading a fixed offset from end-of-file.
Authenticode **appends** the signature after that cookie, so the archive remains fully
readable. This was proven empirically: the signed EXE boots, decrypts its PYZ, and runs
(see §4 and §5).

---

## 3. Signature Verification

### 3a. `Get-AuthenticodeSignature` (PowerShell)

| Property | Value |
|---|---|
| Status | `UnknownError` |
| StatusMessage | *"A certificate chain processed, but terminated in a root certificate which is not trusted by the trust provider."* |
| **SignerCertificate.Subject** | **`CN=Ayman Alaa Abu Leila`** ✓ |
| SignerCertificate.Issuer | `CN=Ayman Alaa Abu Leila` |
| SignerCertificate.Thumbprint | `E62474D0BE183AA95876BC5464B319D54B248E1F` |
| TimeStamperCertificate.Subject | `CN=SSL.com Timestamping Unit 2025 E1, O=SSL Corp, L=Houston, S=Texas, C=US` |
| Timestamp | present (RFC 3161, SHA-256) |

The `UnknownError` status is **solely** the untrusted-root condition. It is the expected
and correct outcome for a self-signed certificate and is **not** a defect in the
signature. The signer name displays correctly as **Ayman Alaa Abu Leila**.

### 3b. `signtool verify /pa /v`

```
Verifying: ...\Phase20-46C-SelfSigned\PrayerMusicGuard\PrayerMusicGuard.exe

Signature Index: 0 (Primary Signature)
Hash of file (sha256): 057998EE451925BCE62B362C1134C68D0B47BAB45F0DC579FE694E55FDCFA367

Signing Certificate Chain:
    Issued to: Ayman Alaa Abu Leila
    Issued by: Ayman Alaa Abu Leila
    Expires:   Fri Sep 22 18:14:26 2028
    SHA1 hash: E62474D0BE183AA95876BC5464B319D54B248E1F

The signature is timestamped: Tue Sep 22 18:17:38 2026
Timestamp Verified by: SSL.com Root Certification Authority RSA  (public trusted root)
        Issued to: SSL.com Timestamping Issuing RSA CA R1
            Issued to: SSL.com Timestamping Unit 2025 E1

Number of files successfully Verified: 0
Number of errors: 1
SignTool Error: A certificate chain processed, but terminated in a root
    certificate which is not trusted by the trust provider.
```

**Interpretation:**
- The signature **structure** is valid: `signtool` parsed the primary signature,
  recomputed the SHA-256 file hash, and resolved the full signing chain to the
  self-signed root.
- The **timestamp counter-signature is valid and chains to the public, trusted
  SSL.com root** — so the signature remains verifiable after the certificate expires.
- The single error is the expected **untrusted root** for a self-signed certificate. On
  a machine where this certificate is explicitly trusted (e.g. installed in
  `CurrentUser\Root` for testing), the same command reports
  `Number of files successfully Verified: 1`.

### 3c. Displayed signer identity

Confirmed by **both** verification tools:

```
Ayman Alaa Abu Leila
```

This is the exact string that appears in the Windows file-properties "Digital
Signatures" tab and in the UAC / SmartScreen publisher field.

---

## 4. Runtime Verification of the Signed EXE

The signed EXE was launched live and driven over the Chrome DevTools Protocol against its
WebView2 frontend (`reports\phases\phase20_46c_evidence\_runtime.js`). Evidence:
`runtime_result.json`, `signed_light.png`, `signed_dark.png`.

**Result: 23 / 23 checks PASSED, 0 failed, 0 CDP exceptions, 0 console errors.**

| # | Check | Result |
|---|---|---|
| 1a | WebView2 page target reachable (frontend index.html) | PASS |
| 1b | Window title is صلاة وسكون | PASS |
| 1c | Document finished loading | PASS |
| 1d | Rendered content present, not blank (553 chars) | PASS |
| 2a | `window.pywebview` object present | PASS |
| 2b | `pywebview.api` present with 16 real methods | PASS |
| 2c | Required bridge methods present (`get_state`, `save_settings`, `pause_now`, `resume_now`, `browse_player`) | PASS |
| 3a | `get_state()` round-trip returns `ok: true` | PASS (4 ms) |
| 3b | Response time reasonable (< 5000 ms) | PASS |
| 3c | State carries version (1.2.7) / prayers / next | PASS |
| 3d | All 5 prayers with names + real computed times | PASS |
| 3e | Exactly one next prayer flagged (Maghrib) | PASS |
| 4a | 5 prayer cards rendered in the grid | PASS |
| 4b | Cards keyed Fajr, Dhuhr, Asr, Maghrib, Isha | PASS |
| 4c | Arabic names + 12h times rendered | PASS |
| 4d | Next-prayer ring populated (المغرب / 06:57 م / countdown 00:35:06) | PASS |
| 5a | Light theme applied | PASS |
| 5b | Dark theme applied | PASS |
| 6a | Settings page reachable | PASS |
| 6b | Save button shows its Arabic label | PASS |
| 7a | Document is RTL + Arabic (`dir=rtl`, `lang=ar`) | PASS |
| 8a | Zero CDP page exceptions | PASS |
| 8b | Zero `console.error` calls | PASS |

**Conclusion:** the signature did not disturb the PyInstaller bootloader, the embedded
CArchive, the PYZ decryption path, the .NET/WebView2 runtime, or any application
behavior. The signed build operates identically to the unsigned 20.46.B build.

---

## 5. PYZ Encryption and 20.46.A Source-Removal — Intact

### 5a. Phase 20.46.B PYZ encryption (re-verified on the *signed* copy)

Ran the Phase 20.46.B PYZ proof (`_verify_pyz_signed.py`) with the pinned Win7 toolchain
against `dist\Phase20-46C-SelfSigned\PrayerMusicGuard\PrayerMusicGuard.exe`. Evidence:
`reports\phases\phase20_46c_evidence\pyz_encryption_result.json`.

**Result: 26 / 26 checks PASSED.**

- Embedded CArchive TOC still contains `PYZ-00.pyz` (typecode `z`).
- **Embedded PYZ encryption flag byte == 1** (header offset 12) — encryption is genuinely
  present after signing.
- **Without the key:** extracting `backend_api` / `main` bytecode FAILS
  (`incorrect header check`).
- **With a wrong key:** extraction still FAILS.
- **With the real key:** all **7 application modules** extract and are provably the real
  modules by their code-object names (`BackendAPI`/`get_state`/`save_settings`,
  `acquire_single_instance`, `CountryCitySelector`, `can_use_html_frontend`, …).
- `tinyaes.cp38-win_amd64.pyd` (runtime decryption backend) still bundled.
- `pyimod00_crypto_key` is in the EXE's CArchive (as the bootloader requires) and **no
  readable crypto-key file is shipped** in the bundle folder.

### 5b. Phase 20.46.A source-removal

Scanned **both** the original 20.46.B bundle and the new signed bundle for the eight
application/source files that must never ship as readable data (`main.py`,
`uiverse_combobox.py`, `backend_api.py`, `launcher.py`, `platform_check.py`,
`webview_main.py`, `app_entry.py`, `pyz_crypto_key.txt`):

| Bundle | Violations |
|---|---|
| `dist\Phase20-46B-Verification\PrayerMusicGuard` | **0** |
| `dist\Phase20-46C-SelfSigned\PrayerMusicGuard` | **0** |

Both bundles hold 1023 files with identical file counts. Source-removal and the 20.46.B
encryption key isolation are fully preserved.

---

## 6. Previous Builds and Releases — Untouched

A full SHA-256 manifest of **7,204 files** across all pre-existing `dist\` builds and the
entire `releases\` tree was recorded **before** this phase began and re-computed after it
ended:

```
Baseline files: 7204   Current files: 7204
IMMUTABLE: every previously existing build + release file hash is UNCHANGED (0 differences).
```

- `dist\Phase20-46B-Verification\PrayerMusicGuard\PrayerMusicGuard.exe` SHA-256 is still
  `5984502F…70CF48F` — **identical** to its pre-phase value. The 20.46.B build was not
  signed, re-signed, or modified in any way.
- `dist\Phase20-46A-Verification` — unchanged.
- `dist\Phase20-28-Release`, `Phase20-36/38/42/44-Visual-Review` — unchanged.
- `releases\v1.2.5`, `releases\v1.2.6`, `releases\v1.2.7` and their
  `SHA256SUMS.txt` / `RELEASE_MANIFEST.txt` — unchanged.
- No new release folder was created. No version bump. No archive written.
- No application source, UI, behavior, updater, spec, or build script was modified.

The only artifact added to `dist\` is the new isolated folder
`dist\Phase20-46C-SelfSigned\`.

---

## 7. Files Created or Modified by This Phase

**Created (new, isolated):**
- `dist\Phase20-46C-SelfSigned\` — the signed copy (1023 files; only `PrayerMusicGuard.exe`
  differs from its 20.46.B source, by exactly the embedded signature).
- `reports\phases\PHASE20_46C_SELF_SIGNED.md` — this report.
- `reports\phases\phase20_46c_evidence\` — verification evidence:
  - `_runtime.js` — CDP runtime harness (adapted from the 20.46.B harness)
  - `runtime_result.json` — 23/23 runtime results
  - `_verify_pyz_signed.py` — PYZ proof adapted to the signed copy
  - `pyz_encryption_result.json` — 26/26 PYZ results
  - `signed_light.png`, `signed_dark.png` — live screenshots of the signed app

**Modified:** none. Zero existing project files were changed.

**Certificate store:** one new certificate added to `Cert:\CurrentUser\My`
(thumbprint `E62474D0BE183AA95876BC5464B319D54B248E1F`). This is a local machine store
change, not a repository change.

---

## 8. Summary Table

| Item | Value |
|---|---|
| Signer / developer identity | **Ayman Alaa Abu Leila** |
| Certificate type | **SELF-SIGNED** — Code Signing |
| EKU | Code Signing (`1.3.6.1.5.5.7.3.3`) |
| Key | RSA 3072, SHA-256, private key **non-exportable** |
| Thumbprint (SHA-1) | `E62474D0BE183AA95876BC5464B319D54B248E1F` |
| Validity | 2026-09-22 → 2028-09-22 |
| Store | `Cert:\CurrentUser\My` |
| Signed EXE | `dist\Phase20-46C-SelfSigned\PrayerMusicGuard\PrayerMusicGuard.exe` |
| Signed EXE SHA-256 | `4BA1D9DBAC881FA499584571111602CA692AA6105C20702EFAE4AEC169BFC4C2` |
| Signature | Embedded, SHA-256, RFC 3161 timestamped (SSL.com TSA) |
| `Get-AuthenticodeSignature` | Signer = **Ayman Alaa Abu Leila** ✓ (status: untrusted root — expected) |
| `signtool verify /pa /v` | Signature parsed OK, timestamp valid, 1 error = untrusted root (expected) |
| Runtime | **23 / 23 PASS**, app fully functional, 0 errors |
| PYZ encryption | **26 / 26 PASS** — intact after signing |
| Source-removal (20.46.A) | **0 violations** in both bundles |
| Prior builds / releases | **7,204 / 7,204 hashes unchanged** |
| Private key exposure | **None** — never exported, printed, or written to disk |
| PFX/PVK on disk | **None** (recursive search returned zero) |
| Uploaded to GitHub | **No** |
| Publicly trusted | **NO — self-signed, developer identification only** |

---

## 9. Limitations and Next Steps

1. **Not for public distribution as-is.** End users will still see "Unknown publisher" /
   SmartScreen prompts because the root is untrusted. This signature proves the pipeline
   works and attributes the binary to the developer; it does not confer public trust.
2. **Expires 2028-09-22.** Although the signature is timestamped (so it remains valid
   after expiry on machines that trust it), the certificate itself is only usable for
   signing until that date.
3. **Only the EXE is signed.** The 41 native payloads (DLLs/PYDs) and the Inno Setup
   installer remain unsigned, per the scope of this phase.
4. **To make this publicly trusted**, a CA-issued code-signing certificate is still
   required (OV or EV), per the Phase 20.46.C signing-preparation audit. The private key
   of *that* certificate should likewise be kept non-exportable and never committed.

**Phase 20.46.C is complete. Signing was performed on an isolated copy only; the original
20.46.B build and all prior releases are provably unmodified.**
