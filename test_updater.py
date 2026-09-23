"""Phase 20.57: unit tests for webview_app/updater.py (Auto Update core).

Self-contained: NO network access, NO GitHub contact, NO destructive action.
Run with the pinned Win7 toolchain or any Python 3.8+ interpreter:

    win7\\venv\\Scripts\\python.exe test_updater.py

Covers:
  - version comparison (valid / equal rejected / downgrade rejected)
  - digest parsing (valid / invalid rejected)
  - asset selection (exact / missing / duplicate / unexpected / malformed)
  - size mismatch
  - SHA256 success / mismatch
  - SHA256SUMS parsing / mismatch / missing entry
  - interrupted download cleanup
  - malformed API response
  - network failure handling (URLError, HTTP 403, HTTP 404)
  - installer launch validation
"""
from __future__ import annotations

import hashlib
import os
import shutil
import sys
import tempfile
import urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
WEBVIEW_APP = os.path.join(HERE, "webview_app")
if WEBVIEW_APP not in sys.path:
    sys.path.insert(0, WEBVIEW_APP)

import updater  # noqa: E402

_RESULTS = []


def check(name, condition, detail=""):
    _RESULTS.append((name, bool(condition), detail))
    status = "PASS" if condition else "FAIL"
    line = "[{0}] {1}".format(status, name)
    if detail:
        line += "  -- {0}".format(detail)
    print(line)


# ---------------------------------------------------------------------------
# Version comparison
# ---------------------------------------------------------------------------

def test_version_comparison():
    check("valid version comparison (1.2.8 -> 1.2.9 available)",
          updater.is_update_available("1.2.8", "1.2.9"))
    check("equal version rejected",
          not updater.is_update_available("1.2.8", "1.2.8"))
    check("downgrade rejected (current 1.2.9, latest 1.2.8)",
          not updater.is_update_available("1.2.9", "1.2.8"))
    check("leading v stripped in tag comparison",
          updater.is_update_available("1.2.8", "v1.2.9") and
          updater.is_update_available("v1.2.8", "1.2.9"))
    check("equal tag with v prefix rejected",
          not updater.is_update_available("1.2.8", "v1.2.8"))
    check("invalid latest version rejected",
          not updater.is_update_available("1.2.8", "not-a-version"))
    check("invalid current version rejected",
          not updater.is_update_available("garbage", "1.2.9"))
    check("major bump detected (1.2.9 -> 2.0.0)",
          updater.is_update_available("1.2.9", "2.0.0"))


# ---------------------------------------------------------------------------
# Current version mechanism
# ---------------------------------------------------------------------------

def test_current_version():
    fake = type("FakeMain", (), {"APP_VERSION": "9.9.9"})()
    saved = sys.modules.get("main")
    sys.modules["main"] = fake
    try:
        check("get_current_version reads main.APP_VERSION",
              updater.get_current_version() == "9.9.9")
    finally:
        if saved is not None:
            sys.modules["main"] = saved
        else:
            sys.modules.pop("main", None)

    noattr = type("FakeMain", (), {})()
    sys.modules["main"] = noattr
    try:
        check("get_current_version handles missing APP_VERSION",
              updater.get_current_version() == "")
    finally:
        if saved is not None:
            sys.modules["main"] = saved
        else:
            sys.modules.pop("main", None)

    # The real running version must match the bumped VERSION (Phase 20.60: 1.2.9).
    if saved is not None:
        check("current version is 1.2.9 (real main.py)",
              updater.get_current_version() == "1.2.9",
              "got {0!r}".format(updater.get_current_version()))


# ---------------------------------------------------------------------------
# Digest parsing
# ---------------------------------------------------------------------------

_VALID_DIGEST = "sha256:" + ("a" * 64)
_VALID_HEX = "a" * 64


def test_digest_parsing():
    check("valid digest parsed", updater.parse_digest(_VALID_DIGEST) == _VALID_HEX)
    check("valid uppercase digest normalized",
          updater.parse_digest("sha256:" + ("A" * 64)) == _VALID_HEX)
    check("base64-style digest rejected (not 64 hex)",
          updater.parse_digest("sha256:bc941805efbce81580badc0bb5839eeca6fdd62bf9197b99f4c25d4fbf4d0079x==") is None)
    check("wrong prefix rejected", updater.parse_digest("md5:" + _VALID_HEX) is None)
    check("short digest rejected", updater.parse_digest("sha256:abc") is None)
    check("non-hex digest rejected", updater.parse_digest("sha256:" + "g" * 64) is None)
    check("empty digest rejected", updater.parse_digest("") is None)
    check("non-string digest rejected", updater.parse_digest(None) is None)
    check("bare 64-hex accepted", updater.parse_digest(_VALID_HEX) == _VALID_HEX)


# ---------------------------------------------------------------------------
# SHA256SUMS parsing
# ---------------------------------------------------------------------------

def test_sha256sums_parsing():
    content = "{0}  PrayerMusicGuard.exe\n{1}  PrayerMusicGuard-Setup.exe\n".format("B" * 64, "C" * 64)
    check("SHA256SUMS parses Setup line",
          updater.parse_sha256sums(content) == "c" * 64)
    check("SHA256SUMS handles single-space separator",
          updater.parse_sha256sums("{0} PrayerMusicGuard-Setup.exe".format("C" * 64)) == "c" * 64)
    check("SHA256SUMS missing entry returns None",
          updater.parse_sha256sums("{0}  PrayerMusicGuard.exe".format("B" * 64)) is None)
    check("SHA256SUMS malformed hash returns None",
          updater.parse_sha256sums("short  PrayerMusicGuard-Setup.exe") is None)
    check("SHA256SUMS empty content returns None", updater.parse_sha256sums("") is None)
    check("SHA256SUMS none content returns None", updater.parse_sha256sums(None) is None)
    check("SHA256SUMS mismatch detected",
          updater.parse_sha256sums("{0}  PrayerMusicGuard-Setup.exe".format("D" * 64)) == "d" * 64)


# ---------------------------------------------------------------------------
# Asset selection (pure: operates on fake API payloads)
# ---------------------------------------------------------------------------

def _good_payload(digest_hex=None, sums_hex=None):
    return {
        "tag_name": "v1.2.9",
        "html_url": "https://github.com/sliveamer20/PrayerMusicGuard/releases/tag/v1.2.9",
        "assets": [
            {"name": "PrayerMusicGuard-Setup.exe", "size": 14650176,
             "browser_download_url": "https://github.com/sliveamer20/PrayerMusicGuard/releases/download/v1.2.9/PrayerMusicGuard-Setup.exe",
             "digest": "sha256:{0}".format(digest_hex or ("a" * 64))},
            {"name": "SHA256SUMS.txt", "size": 182,
             "browser_download_url": "https://github.com/sliveamer20/PrayerMusicGuard/releases/download/v1.2.9/SHA256SUMS.txt"},
            {"name": "RELEASE_MANIFEST.txt", "size": 1212,
             "browser_download_url": "https://github.com/sliveamer20/PrayerMusicGuard/releases/download/v1.2.9/RELEASE_MANIFEST.txt"},
        ],
    }


def test_asset_selection():
    r = updater.parse_release_response(_good_payload())
    check("exact asset selected", r.get("ok") and r["asset"]["name"] == "PrayerMusicGuard-Setup.exe")
    check("release version parsed", r.get("ok") and r.get("version") == "1.2.9")
    check("release URL captured", r.get("ok") and r.get("html_url", "").startswith("https://"))
    check("asset size captured", r.get("ok") and r["asset"]["size"] == 14650176)
    check("asset download URL captured", r.get("ok") and r["asset"]["url"].startswith("https://"))
    check("asset digest captured", r.get("ok") and r["asset"]["digest_hex"] == "a" * 64)
    check("sha256sums URL from same release",
          r.get("ok") and r.get("sha256sums_url", "").endswith("/v1.2.9/SHA256SUMS.txt"))

    # missing setup asset
    p = _good_payload()
    p["assets"] = [a for a in p["assets"] if a["name"] != "PrayerMusicGuard-Setup.exe"]
    check("missing Setup.exe rejected", not updater.parse_release_response(p).get("ok"))

    # duplicate setup asset
    p = _good_payload()
    p["assets"].append(dict(p["assets"][0]))
    check("duplicate Setup.exe rejected", not updater.parse_release_response(p).get("ok"))

    # unexpected asset
    p = _good_payload()
    p["assets"].append({"name": "PrayerMusicGuard.exe", "size": 100, "digest": "sha256:" + "a" * 64})
    check("unexpected asset rejected", not updater.parse_release_response(p).get("ok"))

    # malformed asset (no size)
    p = _good_payload()
    p["assets"][0]["size"] = None
    check("malformed asset (no size) rejected", not updater.parse_release_response(p).get("ok"))

    # malformed asset (http url)
    p = _good_payload()
    p["assets"][0]["browser_download_url"] = "http://evil.example/x.exe"
    check("non-HTTPS asset URL rejected", not updater.parse_release_response(p).get("ok"))

    # malformed asset (bad digest)
    p = _good_payload()
    p["assets"][0]["digest"] = "not-a-digest"
    check("invalid asset digest rejected", not updater.parse_release_response(p).get("ok"))

    # missing SHA256SUMS asset
    p = _good_payload()
    p["assets"] = [a for a in p["assets"] if a["name"] != "SHA256SUMS.txt"]
    check("missing SHA256SUMS asset rejected", not updater.parse_release_response(p).get("ok"))

    # malformed API responses
    check("malformed API response (not dict) rejected",
          not updater.parse_release_response(["nope"]).get("ok"))
    p = _good_payload()
    del p["tag_name"]
    check("missing tag_name rejected", not updater.parse_release_response(p).get("ok"))
    p = _good_payload()
    p["tag_name"] = "vnot-a-version"
    check("unparseable tag rejected", not updater.parse_release_response(p).get("ok"))
    p = _good_payload()
    del p["assets"]
    check("missing assets list rejected", not updater.parse_release_response(p).get("ok"))


# ---------------------------------------------------------------------------
# Network failure handling (fake urlopen)
# ---------------------------------------------------------------------------

class _FakeHTTPError(urllib.error.HTTPError):
    def __init__(self, code, reason):
        urllib.error.HTTPError.__init__(self, "https://example", code, reason, {}, None)


def test_network_failures():
    real_urlopen = updater.urllib.request.urlopen

    def fail_urlerror(*a, **k):
        raise urllib.error.URLError("name resolution failed")

    def fail_timeout(*a, **k):
        raise OSError("timed out")

    def fail_403(*a, **k):
        raise _FakeHTTPError(403, "rate limit exceeded")

    def fail_404(*a, **k):
        raise _FakeHTTPError(404, "Not Found")

    def fail_json(*a, **k):
        class _Resp:
            headers = {}

            def read(self, *a, **k):
                return b"this is not json"

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        return _Resp()

    for label, fn in (("URLError", fail_urlerror), ("timeout", fail_timeout),
                      ("HTTP 403", fail_403), ("HTTP 404", fail_404),
                      ("malformed JSON", fail_json)):
        updater.urllib.request.urlopen = fn
        try:
            result = updater.fetch_latest_release()
            check("network failure handled: {0}".format(label),
                  not result.get("ok") and isinstance(result.get("error"), str),
                  result.get("error", "")[:60])
        finally:
            updater.urllib.request.urlopen = real_urlopen

    updater.urllib.request.urlopen = fail_urlerror
    try:
        check("check_for_update fails closed on network error",
              not updater.check_for_update().get("ok"))
    finally:
        updater.urllib.request.urlopen = real_urlopen


# ---------------------------------------------------------------------------
# Download + verification (fake urlopen, local temp files)
# ---------------------------------------------------------------------------

class _FakeBinaryResponse:
    def __init__(self, data, fail_after=None):
        self._data = data
        self._sent = 0
        self._fail_after = fail_after
        self.headers = {"Content-Length": str(len(data))}

    def read(self, n=-1):
        if self._fail_after is not None and self._sent >= self._fail_after:
            raise OSError("connection reset by peer")
        chunk = self._data[self._sent:self._sent + n]
        self._sent += len(chunk)
        return chunk

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _url_of(request_or_url):
    """urllib accepts a URL string OR a Request object; normalize to a string."""
    if hasattr(request_or_url, "get_full_url"):
        return request_or_url.get_full_url()
    return str(request_or_url)


def _make_interrupting_urlopen(data, fail_after):
    """A response that dies mid-stream to simulate an interrupted download."""
    def fake(url, timeout=None, *a, **k):
        return _FakeBinaryResponse(data, fail_after=fail_after)
    return fake


def _make_urlopen(asset_bytes, sums_text, sums_fail=False):
    def fake(url, timeout=None, *a, **k):
        target = _url_of(url)
        if target.endswith("SHA256SUMS.txt"):
            if sums_fail:
                raise urllib.error.URLError("checksums unavailable")
            return _FakeBinaryResponse(sums_text.encode("utf-8"))
        if target.endswith("PrayerMusicGuard-Setup.exe"):
            return _FakeBinaryResponse(asset_bytes)
        raise urllib.error.URLError("unexpected URL: {0}".format(target))
    return fake


def _write_tmp(dirpath, name, data):
    path = os.path.join(dirpath, name)
    with open(path, "wb") as handle:
        handle.write(data)
    return path


def test_download_and_verify():
    real_urlopen = updater.urllib.request.urlopen
    tmpdir = tempfile.mkdtemp(prefix="pmg-test-")
    try:
        installer = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + os.urandom(200000)
        installer_hex = hashlib.sha256(installer).hexdigest()
        sums_ok = "{0}  PrayerMusicGuard-Setup.exe\n{1}  PrayerMusicGuard.exe\n".format(
            installer_hex, "b" * 64)

        # --- real local streaming via file:// (uses the REAL urlopen) ---
        local_file = _write_tmp(tmpdir, "payload.bin", installer)
        file_url = "file:///" + local_file.replace(os.sep, "/")
        part_path = os.path.join(tmpdir, "fileio.exe.part")
        stream = updater._download_part(file_url, part_path, expected_size=len(installer))
        check("file:// streamed download + hash",
              stream.get("ok") and stream.get("sha256") == installer_hex,
              str(stream.get("error", ""))[:80])
        stream2 = updater._download_part(file_url, part_path, expected_size=len(installer) + 1)
        check("file:// size mismatch cleanup",
              not stream2.get("ok") and not os.path.exists(part_path))

        # --- GitHub-simulated flows (fake urlopen, fully offline) ---
        updater.urllib.request.urlopen = _make_urlopen(installer, sums_ok)
        try:
            # --- full success ---
            result = updater.download_update(
                "https://github.com/x/PrayerMusicGuard-Setup.exe",
                len(installer), installer_hex,
                "https://github.com/x/SHA256SUMS.txt", "1.2.9", dest_dir=tmpdir)
            check("download success path", result.get("ok"), str(result.get("error", ""))[:80])
            check("final .exe produced (renamed from .part)",
                  result.get("ok") and os.path.isfile(result["path"]) and
                  result["path"].endswith("pmg-update-1.2.9.exe"))
            check("no leftover .part on success",
                  not os.path.exists(os.path.join(tmpdir, "pmg-update-1.2.9.exe.part")))
            check("downloaded content hash matches",
                  result.get("sha256") == installer_hex)

            # --- interrupted download: cleaned up, never executed ---
            updater.urllib.request.urlopen = _make_interrupting_urlopen(installer, 50000)
            broken = updater._download_part(
                "https://github.com/x/PrayerMusicGuard-Setup.exe",
                os.path.join(tmpdir, "interrupted.exe.part"),
                expected_size=len(installer))
            check("interrupted download returns failure",
                  not broken.get("ok"), str(broken.get("error", ""))[:60])
            check("interrupted download .part removed",
                  not os.path.exists(os.path.join(tmpdir, "interrupted.exe.part")))

            # --- expected size mismatch (server sends fewer bytes) ---
            mismatch = updater.download_update(
                "https://github.com/x/PrayerMusicGuard-Setup.exe",
                len(installer) + 9999, installer_hex,
                "https://github.com/x/SHA256SUMS.txt", "1.2.9b", dest_dir=tmpdir)
            check("expected size mismatch rejected", not mismatch.get("ok"), str(mismatch.get("error", ""))[:60])
            check("size-mismatch .part removed",
                  not os.path.exists(os.path.join(tmpdir, "pmg-update-1.2.9b.exe.part")))

            # --- SHA256 mismatch vs API digest ---
            bad_digest = updater.download_update(
                "https://github.com/x/PrayerMusicGuard-Setup.exe",
                len(installer), "d" * 64,
                "https://github.com/x/SHA256SUMS.txt", "1.2.9c", dest_dir=tmpdir)
            check("API digest mismatch rejected", not bad_digest.get("ok"), str(bad_digest.get("error", ""))[:60])

            # --- SHA256SUMS mismatch ---
            updater.urllib.request.urlopen = _make_urlopen(installer, "e" * 64 + "  PrayerMusicGuard-Setup.exe\n")
            bad_sums = updater.download_update(
                "https://github.com/x/PrayerMusicGuard-Setup.exe",
                len(installer), installer_hex,
                "https://github.com/x/SHA256SUMS.txt", "1.2.9d", dest_dir=tmpdir)
            check("SHA256SUMS mismatch rejected", not bad_sums.get("ok"), str(bad_sums.get("error", ""))[:60])

            # --- SHA256SUMS entry missing ---
            updater.urllib.request.urlopen = _make_urlopen(
                installer, "f" * 64 + "  PrayerMusicGuard.exe\n")
            missing_sums = updater.download_update(
                "https://github.com/x/PrayerMusicGuard-Setup.exe",
                len(installer), installer_hex,
                "https://github.com/x/SHA256SUMS.txt", "1.2.9e", dest_dir=tmpdir)
            check("missing SHA256SUMS entry rejected", not missing_sums.get("ok"))

            # --- SHA256SUMS unreachable ---
            updater.urllib.request.urlopen = _make_urlopen(installer, sums_ok, sums_fail=True)
            unreachable = updater.download_update(
                "https://github.com/x/PrayerMusicGuard-Setup.exe",
                len(installer), installer_hex,
                "https://github.com/x/SHA256SUMS.txt", "1.2.9f", dest_dir=tmpdir)
            check("unreachable SHA256SUMS rejected", not unreachable.get("ok"))
        finally:
            updater.urllib.request.urlopen = real_urlopen

        # --- non-HTTPS URL refused ---
        check("non-HTTPS download URL refused",
              not updater.download_update("http://evil/x.exe", 1, "a" * 64,
                                          "https://github.com/x/SHA256SUMS.txt", "1.2.9", dest_dir=tmpdir).get("ok"))

        # --- verify_file standalone (offline: content supplied directly) ---
        good_path = _write_tmp(tmpdir, "installer-good.exe", installer)
        check("verify_file success",
              updater.verify_file(good_path, installer_hex, sha256sums_content=sums_ok).get("ok"))
        check("verify_file API-digest mismatch",
              not updater.verify_file(good_path, "d" * 64, sha256sums_content=sums_ok).get("ok"))
        check("verify_file SHA256SUMS mismatch",
              not updater.verify_file(good_path, installer_hex, sha256sums_content="z" * 64 + "  PrayerMusicGuard-Setup.exe\n").get("ok"))
        check("verify_file missing SHA256SUMS entry",
              not updater.verify_file(good_path, installer_hex, sha256sums_content="empty\n").get("ok"))
        check("verify_file missing file",
              not updater.verify_file(os.path.join(tmpdir, "nope.exe"), installer_hex,
                                      sha256sums_content=sums_ok).get("ok"))
        check("verify_file invalid expected digest",
              not updater.verify_file(good_path, "garbage", sha256sums_content=sums_ok).get("ok"))
    finally:
        updater.urllib.request.urlopen = real_urlopen
        shutil.rmtree(tmpdir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Installer launch validation (no real installer is executed)
# ---------------------------------------------------------------------------

def test_launch_installer():
    tmpdir = tempfile.mkdtemp(prefix="pmg-launch-")
    real_spawn = updater._spawn_detached
    launched = []

    def fake_spawn(argv):
        launched.append(argv)
        return {"ok": True, "pid": 4242}

    def fail_spawn(argv):
        # _spawn_detached itself catches OSError and returns a controlled error;
        # launch_installer must propagate it, never raise.
        return {"ok": False, "error": "permission denied"}

    installer = os.path.join(tmpdir, "pmg-update-1.2.9.exe")
    with open(installer, "wb") as handle:
        handle.write(b"fake-installer")
    readme = os.path.join(tmpdir, "readme.txt")
    with open(readme, "wb") as handle:
        handle.write(b"x")
    evil = os.path.join(tmpdir, "evil.exe")
    with open(evil, "wb") as handle:
        handle.write(b"x")

    updater._spawn_detached = fake_spawn
    try:
        check("launch refuses missing file",
              not updater.launch_installer(os.path.join(tmpdir, "nope.exe")).get("ok"))
        check("launch refuses non-.exe file",
              not updater.launch_installer(readme).get("ok"))
        check("launch refuses unexpected .exe name",
              not updater.launch_installer(evil).get("ok"))
        check("launch accepts verified pmg-update installer",
              updater.launch_installer(installer).get("ok"))
        check("launch invoked detached spawn once", len(launched) == 1)

        updater._spawn_detached = fail_spawn
        check("launch reports spawn failure safely",
              not updater.launch_installer(installer).get("ok"))
    finally:
        updater._spawn_detached = real_spawn
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_spawn_error_handling():
    """The REAL _spawn_detached catches OSError from Popen and never raises."""
    real_popen = updater.subprocess.Popen

    def raising_popen(argv, **kwargs):
        raise OSError("access denied")

    updater.subprocess.Popen = raising_popen
    try:
        result = updater._spawn_detached(["c:\\does-not-exist\\pmg-update-1.2.9.exe"])
        check("_spawn_detached catches OSError",
              not result.get("ok") and isinstance(result.get("error"), str),
              str(result.get("error", ""))[:60])
    finally:
        updater.subprocess.Popen = real_popen


# ---------------------------------------------------------------------------
# Detached spawn flags (no process is actually started)
# ---------------------------------------------------------------------------

def test_spawn_flags():
    real_popen = updater.subprocess.Popen
    captured = {}

    class FakeProc:
        pid = 999

    def fake_popen(argv, **kwargs):
        captured["argv"] = argv
        captured["kwargs"] = kwargs
        return FakeProc()

    updater.subprocess.Popen = fake_popen
    try:
        result = updater._spawn_detached([os.path.join("c:\\tmp", "pmg-update-1.2.9.exe")])
        check("spawn returns ok with pid", result.get("ok") and result.get("pid") == 999)
        check("spawn is detached (creationflags set)",
              "creationflags" in captured.get("kwargs", {}))
        check("spawn closes stdio fds",
              captured.get("kwargs", {}).get("close_fds") is True)
    finally:
        updater.subprocess.Popen = real_popen


# ---------------------------------------------------------------------------

def main():
    print("=" * 70)
    print("Phase 20.57 — updater.py unit tests (offline, no GitHub contact)")
    print("=" * 70)
    test_version_comparison()
    test_current_version()
    test_digest_parsing()
    test_sha256sums_parsing()
    test_asset_selection()
    test_network_failures()
    test_download_and_verify()
    test_launch_installer()
    test_spawn_flags()
    test_spawn_error_handling()

    passed = sum(1 for _, ok, _ in _RESULTS if ok)
    failed = sum(1 for _, ok, _ in _RESULTS if not ok)
    print("-" * 70)
    print("TOTAL: {0} checks | PASS: {1} | FAIL: {2}".format(len(_RESULTS), passed, failed))
    if failed:
        print("\nFAILURES:")
        for name, ok, detail in _RESULTS:
            if not ok:
                print("  [FAIL] {0} -- {1}".format(name, detail))
    print("-" * 70)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
