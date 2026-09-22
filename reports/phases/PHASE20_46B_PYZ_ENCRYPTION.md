# Phase 20.46.B — PYZ Encryption ONLY

**Status: PASS** (static validation; no release build performed, per scope)

**Date:** 2026-09-22
**Scope:** Enable PyInstaller PYZ (embedded bytecode) block-cipher encryption. Source-change phase only.
**Backups:** `backup\phase20_46b_pyz_encryption_20260922_124929\`

---

## 1. Exact files changed

| File | Change | Notes |
|---|---|---|
| `PrayerMusicGuard.spec` | Modified | `block_cipher = None` → real cipher (20 lines added, 1 removed). Nothing else in the file changed — verified by full line-diff against the backup (§5). |
| `.gitignore` | Modified | Added `pyz_crypto_key.txt` (2 lines) so the local build secret is never committed. |
| `pyz_crypto_key.txt` | Created | Local build-secret file holding the encryption key. **Not** in `datas`/`hiddenimports`, so it is never bundled. Content withheld from this report. |
| `reports\phases\phase20_46b_evidence\` | Created | Validation harness + results (see §4). |

**Environment change (required by the mechanism, not a source change):**
the pinned Win7 build venv (`win7\venv`, Python 3.8.10 x64) gained its only missing
build-time dependency: `tinyaes==1.1.2` (prebuilt `tinyaes.cp38-win_amd64.pyd`, 54 KB,
plus `tinyaes-1.1.2.dist-info`). `pip freeze` confirms `pyinstaller==5.13.2` is
unchanged and `tinyaes` is the sole addition.

## 2. Exact PyInstaller encryption mechanism/API used

Confirmed from the **installed** environment (not guessed — an initial probe of the
guessed path `PyInstaller.loader.pyimod01_crypto` did **not** exist in 5.13.2):

- **Class:** `PyInstaller.archive.pyz_crypto.PyiBlockCipher`
  (file `win7\venv\lib\site-packages\PyInstaller\archive\pyz_crypto.py`)
- **Constructor:** `PyiBlockCipher(key=<str>)` — asserts `type(key) is str`, truncates
  or zero-fills the key to `BLOCK_SIZE = 16` bytes, and imports `tinyaes` as the
  AES-CTR backend.
- **Import used in the spec:** `from PyInstaller.archive import pyz_crypto` — this is
  exactly how PyInstaller's own `building/build_main.py` imports it (line 27), and the
  class is the one the spec template emits (`templates.py:114`:
  `block_cipher = pyi_crypto.PyiBlockCipher(key=...)`, where `pyi_crypto` is the
  spec-namespace alias for this same module, `build_main.py:934`).
- **Wiring (both pre-existing spec lines, now fed a real cipher):**
  - `Analysis(..., cipher=block_cipher)` — `build_main.py:382-389`: logs
    "Will encrypt Python bytecode with provided cipher key", writes the derived runtime
    decryption-key module `pyimod00_crypto_key.py` into the workpath, and **appends
    `tinyaes` to `hiddenimports`** automatically (so the frozen app can decrypt at runtime).
  - `PYZ(a.pure, a.zipped_data, cipher=block_cipher)` — `building/api.py:73,83,159`:
    `cipher = kwargs.get('cipher', None)` → `self.cipher` → passed to
    `ZlibArchiveWriter(..., cipher=self.cipher)`, which encrypts each module's bytecode.
    (`PYZ.__init__` signature is `(self, *tocs, **kwargs)`; `cipher=` is accepted via
    `**kwargs` — this is why the existing spec line is valid.)

**Known limitation (documented, inherent to PyInstaller's design):** the runtime
decryption key is embedded in the frozen app (it must be, for the bootloader to decrypt
the PYZ). This raises the bar — the PYZ is no longer a plain archive of extractable
bytecode — but it is not protection against a determined reverse-engineer. PyInstaller
also logs a non-fatal `DEPRECATION` ("Bytecode encryption will be removed in
PyInstaller v6") on cipher construction; harmless on the pinned 5.13.2 toolchain, which
this phase does not change.

## 3. Key-handling approach

- The key is a 43-char `secrets.token_urlsafe(32)` secret (the cipher uses its first 16
  bytes) generated once and stored **only** in the local file `pyz_crypto_key.txt` at the
  project root.
- The spec reads that file at **build time** by absolute path
  (`os.path.join(PROJECT_ROOT, "pyz_crypto_key.txt")`) — never imported as a module, so
  there is no import-graph path by which it could be collected into the bundle.
- **Guards are enforced, not decorative:** a missing key file or an empty key file
  aborts the build with a loud `SystemExit` naming Phase 20.46.B and the expected path
  (both negative tests executed — §4).
- **Never in application source or UI:** verified by scanning every `.py`, `.js`,
  `.html`, `.css`, `.json`, `.spec`, `.ps1`, `.bat`, `.md` in the project (excluding the
  venvs, `build/`, `dist/`, `backup/`, `vendor/`, and the key file itself) for the exact
  key string — **0 matches**.
- **Never bundled:** not present in `datas` or `hiddenimports` (validated), and nothing
  in the application imports it.
- **Never committed:** `pyz_crypto_key.txt` is now matched by `.gitignore`.
- **Reproducible for authorized local builds:** the key file persists locally and is the
  only build input besides the committed sources; any builder holding the same key file
  reproduces an identical encrypted bundle. A fresh checkout without the key file fails
  loudly rather than silently producing an unencrypted build.

## 4. Validation result

Harness: `reports\phases\phase20_46b_evidence\_validate_pyz.py`
(raw output + `validate_result.json` in the same folder).

Method — the spec is syntactically compiled, then **executed** with the **real**
`pyz_crypto` module and the **real** `collect_all`/`collect_data_files` helpers, but with
recorder stand-ins for `Analysis`/`PYZ`/`EXE`/`COLLECT` so no build output is produced.
(The spec imports `COLLECT` itself, so the four target names are locked against
re-binding in the exec globals to keep the recorders authoritative.) This proves
encryption is genuinely *configured and wired*, not merely commented.

**18/18 checks PASS (exit 0):**

- Syntax: spec compiles (`compile(..., "exec")`, in-memory — no `__pycache__` artifact).
- `tinyaes` importable (build-time crypto backend).
- Spec **loads end-to-end** (all top-level statements execute, including both `collect_*`
  calls and the key-file read).
- `block_cipher` is **not `None`**; is a **real** `pyz_crypto.PyiBlockCipher`;
  `.key` is 16 bytes (`BLOCK_SIZE`).
- `Analysis` receives `cipher=block_cipher` (**identical object**); `PYZ` receives
  `cipher=block_cipher` (**identical object**); the Analysis key-module + `tinyaes`
  side-effect path is confirmed armed.
- Unchanged: all 11 declared `hiddenimports` present (24 after `collect_all("pystray")`,
  as before); application entry point still `webview_app\app_entry.py`; `datas` contains
  **no** application `.py` and **no** key file; `tinyaes` is *not* declared by the spec
  (Analysis appends it at build time).
- Key isolation: key string absent from all application/UI/build sources;
  `.gitignore` excludes `pyz_crypto_key.txt`.
- Negative tests: missing key → `SystemExit "Phase 20.46.B: PYZ encryption key file not
  found: …"`; empty key → `SystemExit "… key file is empty: …"`.

Note on one initially-failing check: an over-strict assertion flagged `collect_all("pystray")`
adding pystray's own dependency `.py` files to `datas`. That is the **pre-existing**
20.44/20.46.A situation (the bundle's `pystray\` `.py`/`.pyc` files), whose cleanup is
**Phase 20.46.D** scope; the check was corrected to exclude the six *application*
modules + the key file, which is what 20.46.A guarantees. No product defect.

## 5. Confirmation: UI / behavior / source entry points untouched

- Full line-diff of `PrayerMusicGuard.spec` (backup → current) shows **only** the crypto
  import, the explanatory comment block, the key-file read, and the
  `block_cipher = pyz_crypto.PyiBlockCipher(key=_PYZ_KEY)` assignment; the removed line is
  exactly `block_cipher = None`. Every `hiddenimports`, `datas`, `binaries`, `pathex`,
  `excludes`, `hookspath`, `runtime_hooks`, `EXE` (name/icon/console/window flags) and
  `COLLECT` entry is byte-identical, as is the `webview_app\app_entry.py` entry script.
- No file under `webview_app\` or the frontend tree was modified — an mtime sweep of the
  whole project confirms the only 20.46.B writes are `PrayerMusicGuard.spec`,
  `.gitignore`, `pyz_crypto_key.txt`, and `reports\phases\phase20_46b_evidence\`
  (the 10:33–10:48 `__pycache__`/`.py` mtimes are 20.46.A leftovers, untouched here).
- Encryption is transparent to the runtime: the bootloader decrypts the PYZ before
  importing, so `backend_api`/`launcher`/`webview_main` and the frontend behave
  identically. No application logic, UI, theme, animation, prayer-time, music-guard, or
  updater/signing code was touched.
- No release was built and no prior build/release was modified or deleted
  (`dist\`, `releases\` untouched).

## 6. Confirmation: 20.46.C / 20.46.D / 20.46.E NOT implemented

- **20.46.C (code signing):** not implemented. `EXE(codesign_identity=None, ...)`
  remains exactly as before; no certificate, `signtool`, or Authenticode step added.
- **20.46.D (hygiene purge):** not implemented. The pre-existing `pystray\` dependency
  `.py`/`.pyc` files and `.bak` handling are untouched; the `collect_all("pystray")`
  call is unchanged.
- **20.46.E (Cython/Nuitka):** not implemented. No compilation of application sources to
  C/native modules; the entry point and module set are unchanged.
- **No packers:** no UPX, PyArmor, VMProtect, or other third-party packer introduced
  (`upx=False` throughout, `strip=False`).

## 7. PASS/FAIL

**PASS.** PYZ block-cipher encryption is enabled via the confirmed PyInstaller 5.13.2
mechanism (`PyInstaller.archive.pyz_crypto.PyiBlockCipher` wired into `Analysis` and
`PYZ`), the key is isolated in a local git-ignored build-secret file with enforced
guards, and 18/18 static validation checks pass with UI/behavior/entry points provably
untouched and 20.46.C/D/E not started. No release build was run.

**Known follow-ups (out of this phase's scope):** a verification build (like Phase
20.46.A's) to exercise the encrypted bundle end-to-end at runtime; the v6 deprecation of
this mechanism; and phases 20.46.C/D/E.
