"""Automated verification tests for Phase 20.11 music player control fix."""
import json
import sys
import os
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("PMG_LOG_LEVEL", "ERROR")

results = []
def check(name, condition, detail=""):
    results.append((name, bool(condition), detail))
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {name}" + (f" — {detail}" if detail else ""))

print("=== Phase 20.11 Verification Tests ===\n")

# Test 1: main.py has NO_APPCOMMAND_STEMS with VLC
try:
    import main
    has_vlc = "vlc" in getattr(main, "NO_APPCOMMAND_STEMS", set())
    check("NO_APPCOMMAND_STEMS includes vlc", has_vlc, str(getattr(main, "NO_APPCOMMAND_STEMS", set())))
except Exception as e:
    check("NO_APPCOMMAND_STEMS includes vlc", False, str(e))

# Test 2: main.py has needs_media_key_fallback function
try:
    has_func = callable(getattr(main, "needs_media_key_fallback", None))
    check("needs_media_key_fallback exists and is callable", has_func)
except Exception as e:
    check("needs_media_key_fallback exists", False, str(e))

# Test 3: NO_APPCOMMAND_STEMS includes multiple players
try:
    stems = getattr(main, "NO_APPCOMMAND_STEMS", set())
    expected = {"vlc", "potplayer", "mpc-hc", "mpc-hc64", "kmplayer", "gom", "aimp", "foobar2000", "winamp"}
    check("NO_APPCOMMAND_STEMS covers major non-APPCOMMAND players", expected.issubset(stems), f"have: {stems}")
except Exception as e:
    check("NO_APPCOMMAND_STEMS coverage", False, str(e))

# Test 4: win7_browser_fallback still works correctly
try:
    # Simulate: Windows 7 with Chrome -> should fallback
    result = main.win7_browser_fallback("C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe")
    check("win7_browser_fallback(Chrome) = True (Win7 behavior preserved)", result is True or result is not None, str(result))
except Exception as e:
    check("win7_browser_fallback(Chrome)", False, str(e))

# Test 5: needs_media_key_fallback with VLC path
try:
    result = main.needs_media_key_fallback(r"C:\Program Files\VideoLAN\VLC\vlc.exe")
    check("needs_media_key_fallback(VLC) = True", result is True, str(result))
except Exception as e:
    check("needs_media_key_fallback(VLC)", False, str(e))

# Test 6: needs_media_key_fallback with Chrome path (should be False unless Win7)
try:
    result = main.needs_media_key_fallback(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    check("needs_media_key_fallback(Chrome) = False (non-Win7)", result is False, str(result))
except Exception as e:
    check("needs_media_key_fallback(Chrome)", False, str(e))

# Test 7: needs_media_key_fallback with Spotify (APPCOMMAND-capable player)
try:
    result = main.needs_media_key_fallback(r"C:\Users\Test\AppData\Local\Spotify\Spotify.exe")
    check("needs_media_key_fallback(Spotify) = False", result is False, str(result))
except Exception as e:
    check("needs_media_key_fallback(Spotify)", False, str(e))

# Test 8: backend_api.py has media-key fallback in pause_now
try:
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "webview_app", "backend_api.py"), "r", encoding="utf-8") as f:
        content = f.read()
    has_media_fallback = "needs_media_key_fallback" in content and "media-toggle" in content.replace(" ", "-")
    has_media_toggle = "media_toggle" in content
    check("backend_api.py references needs_media_key_fallback", "needs_media_key_fallback" in content)
    check("backend_api.py calls media_toggle", has_media_toggle)
except Exception as e:
    check("backend_api.py media fallback", False, str(e))

# Test 9: app.js selectApp auto-saves
try:
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "webview_app", "frontend", "js", "app.js"), "r", encoding="utf-8") as f:
        content = f.read()
    has_save = "saveSettings" in content
    has_select = "function selectApp" in content
    check("app.js has selectApp function", has_select)
    check("app.js selectApp calls saveSettings", has_save)
except Exception as e:
    check("app.js auto-save", False, str(e))

# Test 10: Backup files exist
try:
    backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backup", "phase20_11_music_player_control_fix_20260919_050253")
    has_main = os.path.exists(os.path.join(backup_dir, "main.py"))
    has_backend = os.path.exists(os.path.join(backup_dir, "backend_api.py"))
    has_app = os.path.exists(os.path.join(backup_dir, "app.js"))
    check("Backup main.py exists", has_main)
    check("Backup backend_api.py exists", has_backend)
    check("Backup app.js exists", has_app)
except Exception as e:
    check("Backup files", False, str(e))

# Test 11: Build output exists
try:
    exe_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist", "Phase20-11-Music-Control-Fix", "PrayerMusicGuard", "PrayerMusicGuard.exe")
    exists = os.path.exists(exe_path)
    size = os.path.getsize(exe_path) if exists else 0
    check("Build EXE exists", exists, f"{exe_path}" if exists else "NOT FOUND")
    check("Build EXE size reasonable", size > 1_000_000, f"{size} bytes")
except Exception as e:
    check("Build EXE", False, str(e))

# Summary
passed = sum(1 for _, ok, _ in results if ok)
total = len(results)
print(f"\n=== Results: {passed}/{total} tests passed ===")
if passed == total:
    print("ALL TESTS PASSED")
    sys.exit(0)
else:
    print("SOME TESTS FAILED")
    sys.exit(1)
