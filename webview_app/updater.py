"""Phase 20.57: Auto Update core for Prayer Music Guard (صلاة وسكون).

An isolated, testable updater **backend**. Deliberately NO UI, NO scheduling,
NO background timers, and NO silent installation in this phase.

Security model (designed in Phase 20.56 — see
reports/auto-update/PHASE20_56_AUTO_UPDATE_ARCHITECTURE_AUDIT.md):

  * HTTPS only. The GitHub owner/repo are COMPILED-IN CONSTANTS — never read
    from user settings and never taken from an API response.
  * Only the exact asset "PrayerMusicGuard-Setup.exe" is accepted.
  * Strict semantic version comparison (packaging.version): an update is offered
    only when latest > current. Equal or lower never triggers an update, so a
    downgrade "offer" is impossible by construction.
  * Expected-size validation against the API-declared asset size.
  * DUAL mandatory SHA256 verification before anything is executed:
        A) SHA256 computed locally over the downloaded bytes
        B) the GitHub asset API ``digest``  ("sha256:<64 hex>")
        C) the line for PrayerMusicGuard-Setup.exe in the SAME release's
           SHA256SUMS.txt
    All three must agree exactly.
  * The download lands in a ".part" temp file and is renamed to the final
    ".exe" ONLY after every verification passes. A failed/interrupted download
    is deleted and is NEVER executed.
  * No HTTP fallback, no certificate-validation disabling, no arbitrary URLs.

The installer (never the app itself) replaces the OneDir bundle: the app exits
cleanly only AFTER launch_installer() has started the detached installer, and
the existing App.exit_app() cleanup path is the safe exit sequence the caller
should use (wired up in the UI phase, not here).

Python 3.8.10 (the pinned Windows 7 toolchain) compatible: stdlib plus the
already-pinned packaging==24.2 only. No new dependency.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

# ---------------------------------------------------------------------------
# Compiled-in update source. NEVER derive these from settings or responses.
# ---------------------------------------------------------------------------
GITHUB_OWNER = "sliveamer20"
GITHUB_REPO = "PrayerMusicGuard"
LATEST_RELEASE_URL = "https://api.github.com/repos/{0}/{1}/releases/latest".format(
    GITHUB_OWNER, GITHUB_REPO
)

# The exact assets a legitimate release is expected to carry. An asset outside
# this allowlist rejects the whole release (see parse_release_response).
SETUP_ASSET_NAME = "PrayerMusicGuard-Setup.exe"
SHA256SUMS_NAME = "SHA256SUMS.txt"
MANIFEST_NAME = "RELEASE_MANIFEST.txt"
KNOWN_ASSET_NAMES = frozenset({SETUP_ASSET_NAME, SHA256SUMS_NAME, MANIFEST_NAME})

API_TIMEOUT = 10           # seconds — short, non-blocking version check
DOWNLOAD_TIMEOUT = 60      # socket inactivity timeout while streaming
DOWNLOAD_CHUNK = 64 * 1024
_DIGEST_HEX_LEN = 64
_HEX_CHARS = frozenset("0123456789abcdefABCDEF")


class UpdaterError(Exception):
    """A controlled, reportable updater failure. Never crashes the app."""


# ---------------------------------------------------------------------------
# Current version
# ---------------------------------------------------------------------------

def get_current_version() -> str:
    """The running application version, from the existing APP_VERSION mechanism.

    Reads ``main.APP_VERSION`` exactly the way webview_app/backend_api.py exposes
    it to the UI (getattr(_MAIN, 'APP_VERSION', '')). In frozen builds ``main``
    is a hiddenimport compiled into the PYZ, so this works frozen and from
    source. Returns "" if the version cannot be determined.
    """
    module = sys.modules.get("main")
    if module is None:
        try:
            module = __import__("main")
        except Exception:
            return ""
    try:
        return str(getattr(module, "APP_VERSION", "") or "").strip()
    except Exception:
        return ""


def _user_agent() -> str:
    return "PrayerMusicGuard/{0} (auto-update)".format(get_current_version() or "unknown")


# ---------------------------------------------------------------------------
# Version comparison
# ---------------------------------------------------------------------------

def parse_version(text):
    """Parse "v1.2.9" / "1.2.9" into a packaging Version.

    Strips a single leading "v"/"V" (GitHub tag style). Raises
    packaging.version.InvalidVersion for anything invalid.
    """
    from packaging.version import InvalidVersion, Version

    raw = str(text or "").strip()
    if raw[:1] in ("v", "V"):
        raw = raw[1:].strip()
    if not raw:
        raise InvalidVersion("empty version string")
    return Version(raw)


def is_update_available(current_version, latest_version) -> bool:
    """True ONLY when latest > current (strict semantic comparison).

    Equal, lower, or unparseable versions never report an update.
    """
    try:
        return parse_version(latest_version) > parse_version(current_version)
    except Exception:
        # InvalidVersion or any malformed input: fail closed (no update).
        return False


# ---------------------------------------------------------------------------
# Digest / checksum helpers
# ---------------------------------------------------------------------------

def _is_hex(text: str) -> bool:
    return all(ch in _HEX_CHARS for ch in text)


def _normalize_hex(value):
    """Accept "sha256:<hex>" or a bare 64-char hex; return lowercase hex or None."""
    if not isinstance(value, str):
        return None
    value = value.strip()
    marker = "sha256:"
    if value[:len(marker)].lower() == marker:
        value = value[len(marker):].strip()
    if len(value) == _DIGEST_HEX_LEN and _is_hex(value):
        return value.lower()
    return None


def parse_digest(digest):
    """GitHub asset digest "sha256:<64 hex>" -> lowercase hex, or None.

    The value after "sha256:" is HEXADECIMAL SHA256 (NOT Base64). It must be
    exactly 64 hex characters; anything else is rejected.
    """
    return _normalize_hex(digest)


def parse_sha256sums(content, target_name=SETUP_ASSET_NAME):
    """Parse SHA256SUMS.txt content; return the hex checksum for target_name.

    Accepts the release format "<UPPERCASE_SHA256>  <name>" (any whitespace
    separator). Hash comparison is case-insensitive after normalization.
    Returns None when the entry is missing or malformed.
    """
    if not content or not isinstance(content, str):
        return None
    for line in content.splitlines():
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 2:
            continue
        hash_part, name = parts
        if name != target_name:
            continue
        if len(hash_part) != _DIGEST_HEX_LEN or not _is_hex(hash_part):
            continue
        return hash_part.lower()
    return None


def _sha256_of_file(path, chunk=DOWNLOAD_CHUNK):
    """Streaming SHA256 of a file, or None on any I/O error."""
    hasher = hashlib.sha256()
    try:
        with open(path, "rb") as handle:
            while True:
                block = handle.read(chunk)
                if not block:
                    break
                hasher.update(block)
    except OSError:
        return None
    return hasher.hexdigest()


# ---------------------------------------------------------------------------
# GitHub API: latest release
# ---------------------------------------------------------------------------

def _http_reason(exc) -> str:
    try:
        return str(exc.reason)
    except Exception:
        return "error"


def _github_get_json(url, timeout=API_TIMEOUT):
    """HTTPS GET to the GitHub API, returning parsed JSON.

    Raises UpdaterError with a human-readable message for network/HTTP/JSON
    failures. Never returns partial data.
    """
    request = urllib.request.Request(
        url,
        headers={"User-Agent": _user_agent(), "Accept": "application/vnd.github+json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        raise UpdaterError("GitHub API HTTP {0}: {1}".format(exc.code, _http_reason(exc)))
    except urllib.error.URLError as exc:
        raise UpdaterError("GitHub API unreachable: {0}".format(_http_reason(exc)))
    except Exception as exc:  # socket timeout, SSL error, etc.
        raise UpdaterError("GitHub API request failed: {0}".format(exc))
    if not raw:
        raise UpdaterError("GitHub API returned an empty response")
    try:
        return json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise UpdaterError("malformed GitHub API response: {0}".format(exc))


def parse_release_response(payload):
    """Validate a parsed GitHub releases/latest JSON payload (PURE: no network).

    Returns:
      {"ok": True, "tag": ..., "version": ..., "html_url": ...,
       "asset": {"name", "size", "url", "digest_hex"},
       "sha256sums_url": "https://..."}
    or {"ok": False, "error": "..."} for missing/duplicate/unexpected/malformed
    assets or an unparseable version.
    """
    from packaging.version import InvalidVersion

    if not isinstance(payload, dict):
        return {"ok": False, "error": "malformed API response: not an object"}

    tag = payload.get("tag_name")
    if not isinstance(tag, str) or not tag.strip():
        return {"ok": False, "error": "missing or invalid release tag_name"}
    tag = tag.strip()
    try:
        version = str(parse_version(tag))
    except InvalidVersion:
        return {"ok": False, "error": "unparseable release version: {0!r}".format(tag)}

    html_url = payload.get("html_url")
    if not isinstance(html_url, str) or not html_url.startswith("https://"):
        html_url = ""

    assets = payload.get("assets")
    if not isinstance(assets, list):
        return {"ok": False, "error": "missing or invalid assets list"}

    setup_assets = []
    sha256sums_url = ""
    for asset in assets:
        if not isinstance(asset, dict):
            return {"ok": False, "error": "malformed asset entry in release"}
        name = asset.get("name")
        if not isinstance(name, str) or not name:
            return {"ok": False, "error": "malformed asset entry: missing name"}
        if name not in KNOWN_ASSET_NAMES:
            return {"ok": False, "error": "unexpected asset in release: {0!r}".format(name)}
        if name == SETUP_ASSET_NAME:
            setup_assets.append(asset)
        elif name == SHA256SUMS_NAME:
            url = asset.get("browser_download_url")
            if isinstance(url, str) and url.startswith("https://"):
                sha256sums_url = url

    if not setup_assets:
        return {"ok": False, "error": "missing required asset: {0}".format(SETUP_ASSET_NAME)}
    if len(setup_assets) > 1:
        return {"ok": False, "error": "duplicate asset: {0} appears {1} times".format(
            SETUP_ASSET_NAME, len(setup_assets))}

    asset = setup_assets[0]
    size = asset.get("size")
    if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
        return {"ok": False, "error": "invalid or missing expected size for {0}".format(SETUP_ASSET_NAME)}
    url = asset.get("browser_download_url")
    if not isinstance(url, str) or not url.startswith("https://"):
        return {"ok": False, "error": "invalid or non-HTTPS download URL for {0}".format(SETUP_ASSET_NAME)}
    digest_hex = parse_digest(asset.get("digest"))
    if digest_hex is None:
        return {"ok": False, "error": "invalid asset digest (expected sha256:<64 hex>)"}
    if not sha256sums_url:
        return {"ok": False, "error": "missing {0} asset in release".format(SHA256SUMS_NAME)}

    return {
        "ok": True,
        "tag": tag,
        "version": version,
        "html_url": html_url,
        "asset": {
            "name": SETUP_ASSET_NAME,
            "size": size,
            "url": url,
            "digest_hex": digest_hex,
        },
        "sha256sums_url": sha256sums_url,
    }


def fetch_latest_release():
    """Query GitHub for the latest release (HTTPS, hardcoded owner/repo).

    Returns the parse_release_response() result dict. Never raises: every
    failure (offline, HTTP 403/404, malformed JSON, bad assets) comes back as
    {"ok": False, "error": "..."} so a failed check can never crash the app.
    """
    try:
        payload = _github_get_json(LATEST_RELEASE_URL)
    except UpdaterError as exc:
        return {"ok": False, "error": str(exc)}
    return parse_release_response(payload)


def check_for_update(current_version=None):
    """Fetch the latest release and compare it against the running version.

    Returns {"ok": True, "update_available": bool, "current_version": ...,
    "latest": {...}} on a successful check, or {"ok": False, "error": "..."}
    when the check itself failed. Never raises.
    """
    release = fetch_latest_release()
    if not release.get("ok"):
        return release
    current = current_version if current_version is not None else get_current_version()
    if not current:
        return {"ok": False, "error": "current application version unavailable"}
    return {
        "ok": True,
        "update_available": is_update_available(current, release["version"]),
        "current_version": current,
        "latest": release,
    }


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------

def _fail(path, message):
    """Delete a partial download and wrap the failure. Never executes anything."""
    if path:
        try:
            if os.path.isfile(path):
                os.remove(path)
        except OSError:
            pass
    return {"ok": False, "error": message}


def _download_part(url, dest_part_path, expected_size=None, progress_callback=None,
                   timeout=DOWNLOAD_TIMEOUT):
    """Stream ``url`` into ``dest_part_path``, hashing as the bytes flow.

    Returns {"ok": True, "sha256": hex, "size": n} or {"ok": False, "error": ...}
    and ALWAYS removes dest_part_path on failure. Never executes anything.
    """
    request = urllib.request.Request(url, headers={"User-Agent": _user_agent()})
    hasher = hashlib.sha256()
    total = 0
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            declared = response.headers.get("Content-Length")
            if expected_size is not None and declared is not None:
                try:
                    if int(declared) != int(expected_size):
                        return _fail(dest_part_path,
                                     "server Content-Length {0} != expected {1}".format(
                                         int(declared), int(expected_size)))
                except ValueError:
                    pass
            with open(dest_part_path, "wb") as out:
                while True:
                    chunk = response.read(DOWNLOAD_CHUNK)
                    if not chunk:
                        break
                    out.write(chunk)
                    hasher.update(chunk)
                    total += len(chunk)
                    if progress_callback is not None:
                        try:
                            progress_callback(total)
                        except Exception:
                            pass
    except urllib.error.HTTPError as exc:
        return _fail(dest_part_path, "download HTTP {0}: {1}".format(exc.code, _http_reason(exc)))
    except urllib.error.URLError as exc:
        return _fail(dest_part_path, "download failed: {0}".format(_http_reason(exc)))
    except Exception as exc:
        return _fail(dest_part_path, "download interrupted: {0}".format(exc))

    if expected_size is not None and total != int(expected_size):
        return _fail(dest_part_path, "downloaded size {0} != expected {1}".format(
            total, int(expected_size)))
    return {"ok": True, "sha256": hasher.hexdigest(), "size": total}


def _fetch_text(url, timeout=API_TIMEOUT):
    """HTTPS GET returning decoded text, or None on any failure."""
    if not isinstance(url, str) or not url.startswith("https://"):
        return None
    request = urllib.request.Request(url, headers={"User-Agent": _user_agent()})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read().decode("utf-8", errors="replace")
    except Exception:
        return None


def fetch_sha256sums(sha256sums_url, timeout=API_TIMEOUT):
    """Download and parse the release's SHA256SUMS.txt.

    Returns the hex checksum for SETUP_ASSET_NAME, or None on any failure
    (unreachable URL, missing entry, malformed content).
    """
    return parse_sha256sums(_fetch_text(sha256sums_url, timeout))


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

def verify_file(path, expected_sha256_hex, sha256sums_url=None, sha256sums_content=None,
                target_name=SETUP_ASSET_NAME):
    """Dual SHA256 verification of a downloaded installer.

    All three values must agree:
      A) SHA256 computed locally over the file bytes
      B) expected_sha256_hex  (the GitHub API asset digest)
      C) the checksum line in the SAME release's SHA256SUMS.txt

    ``sha256sums_url`` is downloaded from the exact release (never
    /releases/latest again); ``sha256sums_content`` overrides it for tests.

    Returns {"ok": True, "sha256": hex} or {"ok": False, "error": "..."}.
    Never executes anything and never deletes the file (the caller decides).
    """
    if not isinstance(path, str) or not path:
        return {"ok": False, "error": "no file path provided"}
    if not os.path.isfile(path):
        return {"ok": False, "error": "file not found: {0}".format(path)}

    local = _sha256_of_file(path)
    if local is None:
        return {"ok": False, "error": "could not compute SHA256 of {0}".format(path)}

    expected = _normalize_hex(expected_sha256_hex)
    if expected is None:
        return {"ok": False, "error": "invalid expected digest (API)"}
    if local != expected:
        return {"ok": False, "error": "local SHA256 {0} != API digest {1}".format(local, expected)}

    if sha256sums_content is None:
        if not sha256sums_url:
            return {"ok": False, "error": "no SHA256SUMS.txt source provided"}
        sha256sums_content = _fetch_text(sha256sums_url)
        if sha256sums_content is None:
            return {"ok": False, "error": "could not download SHA256SUMS.txt"}
    sums = parse_sha256sums(sha256sums_content, target_name)
    if sums is None:
        return {"ok": False, "error": "SHA256SUMS.txt entry missing or malformed for {0}".format(target_name)}
    if local != sums:
        return {"ok": False, "error": "local SHA256 {0} != SHA256SUMS.txt {1}".format(local, sums)}

    return {"ok": True, "sha256": local}


def download_update(asset_url, expected_size, expected_sha256_hex, sha256sums_url, version,
                    dest_dir=None, progress_callback=None):
    """Download and fully verify the exact Setup.exe asset.

    Streams into ``<TEMP>\pmg-update-<version>.exe.part``, validates the size
    and BOTH SHA256 sources (API digest + the same release's SHA256SUMS.txt),
    and only then renames it to ``pmg-update-<version>.exe``.

    Returns {"ok": True, "path": <final .exe path>, "sha256": hex} or
    {"ok": False, "error": "..."} — in which case the .part file is deleted and
    nothing is executed.
    """
    if not isinstance(asset_url, str) or not asset_url.startswith("https://"):
        return {"ok": False, "error": "refused non-HTTPS download URL"}
    if not isinstance(expected_size, int) or isinstance(expected_size, bool) or expected_size <= 0:
        return {"ok": False, "error": "invalid expected asset size"}
    if _normalize_hex(expected_sha256_hex) is None:
        return {"ok": False, "error": "invalid expected digest"}
    if not isinstance(sha256sums_url, str) or not sha256sums_url.startswith("https://"):
        return {"ok": False, "error": "missing HTTPS SHA256SUMS.txt URL for the release"}

    safe_version = "".join(ch for ch in str(version or "") if ch.isalnum() or ch in (".", "-", "_"))
    if not safe_version:
        safe_version = "unknown"
    directory = dest_dir or tempfile.gettempdir()
    part_path = os.path.join(directory, "pmg-update-{0}.exe.part".format(safe_version))
    final_path = os.path.join(directory, "pmg-update-{0}.exe".format(safe_version))

    download = _download_part(asset_url, part_path, expected_size, progress_callback)
    if not download.get("ok"):
        return download  # .part already deleted by _download_part

    # Fetch the release checksums ONCE, from the exact release (never /releases/latest).
    sums_content = _fetch_text(sha256sums_url)
    if sums_content is None:
        return _fail(part_path, "SHA256SUMS.txt unavailable: {0}".format(sha256sums_url))

    # Reuse verify_file so the three-way check has a single implementation.
    verification = verify_file(part_path, expected_sha256_hex, sha256sums_content=sums_content)
    if not verification.get("ok"):
        return _fail(part_path, verification.get("error", "verification failed"))

    # Every check passed — expose the installer under its final name.
    try:
        if os.path.exists(final_path):
            os.remove(final_path)
        os.rename(part_path, final_path)
    except OSError as exc:
        return _fail(part_path, "could not finalize {0}: {1}".format(final_path, exc))

    return {"ok": True, "path": final_path, "sha256": verification["sha256"]}


def download_and_verify(release, progress_callback=None):
    """Run the full safe download for a release dict from fetch_latest_release()."""
    if not isinstance(release, dict) or not release.get("ok"):
        return {"ok": False, "error": "no verified release to download"}
    asset = release.get("asset") or {}
    return download_update(
        asset_url=asset.get("url"),
        expected_size=asset.get("size"),
        expected_sha256_hex=asset.get("digest_hex"),
        sha256sums_url=release.get("sha256sums_url"),
        version=release.get("version"),
        progress_callback=progress_callback,
    )


# ---------------------------------------------------------------------------
# Installer launch
# ---------------------------------------------------------------------------

def _spawn_detached(argv):
    """Start argv as a detached process that outlives this application."""
    kwargs = {
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "close_fds": True,
    }
    if sys.platform.startswith("win"):
        flags = getattr(subprocess, "DETACHED_PROCESS", 0x00000008) | \
            getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)
        kwargs["creationflags"] = flags
    try:
        proc = subprocess.Popen(argv, **kwargs)
    except OSError as exc:
        return {"ok": False, "error": "could not start {0}: {1}".format(argv[0], exc)}
    return {"ok": True, "pid": proc.pid}


def launch_installer(setup_path):
    """Launch the VERIFIED installer as a detached process.

    Only safe to call AFTER every check in download_update() passed. Does NOT
    replace the running OneDir files (the installer owns that), and does NOT
    install silently — user confirmation is enforced by the UI layer.

    On success the caller should exit the application through the existing
    App.exit_app() cleanup path so the installer can replace the bundle.

    Returns {"ok": True, "pid": n} or {"ok": False, "error": "..."}.
    """
    if not isinstance(setup_path, str) or not setup_path:
        return {"ok": False, "error": "no installer path provided"}
    if not os.path.isfile(setup_path):
        return {"ok": False, "error": "installer not found: {0}".format(setup_path)}

    name = os.path.basename(setup_path)
    lowered = name.lower()
    if not lowered.endswith(".exe"):
        return {"ok": False, "error": "refused to launch a non-.exe file: {0!r}".format(name)}
    if not (lowered.startswith("pmg-update-") or name == SETUP_ASSET_NAME):
        return {"ok": False, "error": "refused to launch unexpected installer name: {0!r}".format(name)}

    return _spawn_detached([setup_path])
