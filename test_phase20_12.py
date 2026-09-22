"""Automated verification tests for Phase 20.12."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("PMG_LOG_LEVEL", "ERROR")

results = []
def check(name, condition, detail=""):
    results.append((name, bool(condition), detail))
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {name}" + (f" — {detail}" if detail else ""))

print("=== Phase 20.12 Verification Tests ===\n")

# 1. Syntax check
try:
    import ast
    ast.parse(open(os.path.join(os.path.dirname(__file__), "main.py"), encoding="utf-8").read())
    check("main.py syntax OK", True)
except Exception as e:
    check("main.py syntax OK", False, str(e))

try:
    import ast
    ast.parse(open(os.path.join(os.path.dirname(__file__), "webview_app", "backend_api.py"), encoding="utf-8").read())
    check("backend_api.py syntax OK", True)
except Exception as e:
    check("backend_api.py syntax OK", False, str(e))

# 2. UI label changed
try:
    with open(os.path.join(os.path.dirname(__file__), "webview_app", "frontend", "index.html"), encoding="utf-8") as f:
        html = f.read()
    has_old = "المشغّل المحمي" in html
    has_new = '<span class="stat__label">المشغّل</span>' in html
    check("UI label changed to المشغل", has_new and not has_old, "old present" if has_old else "")
except Exception as e:
    check("UI label changed", False, str(e))

# 3. send_appcommand lParam includes 0xC000
try:
    with open(os.path.join(os.path.dirname(__file__), "main.py"), encoding="utf-8") as f:
        src = f.read()
    has_flag = "0xC000" in src and "lparam = (command << 16) | 0xC000" in src
    check("send_appcommand uses correct lParam with 0xC000", has_flag)
except Exception as e:
    check("send_appcommand lParam", False, str(e))

# 4. NO_APPCOMMAND_STEMS removed / VLC not in media key fallback
try:
    import main
    # needs_media_key_fallback should NOT force VLC
    result = main.needs_media_key_fallback(r"C:\Program Files\VideoLAN\VLC\vlc.exe")
    check("needs_media_key_fallback(VLC) = False", result is False, str(result))
except Exception as e:
    check("needs_media_key_fallback(VLC)", False, str(e))

# 5. format_time_12 exists and works
try:
    import main
    t1 = main.format_time_12("05:18")
    t2 = main.format_time_12("12:54")
    t3 = main.format_time_12("16:24")
    t4 = main.format_time_12("19:01")
    t5 = main.format_time_12("20:20")
    ok = (t1 == "05:18 ص" and t2 == "12:54 م" and t3 == "04:24 م" and t4 == "07:01 م" and t5 == "08:20 م")
    check("format_time_12 produces correct Arabic 12-hour output", ok, f"{t1},{t2},{t3},{t4},{t5}")
except Exception as e:
    check("format_time_12", False, str(e))

# 6. Backend uses format_time_12
try:
    with open(os.path.join(os.path.dirname(__file__), "webview_app", "backend_api.py"), encoding="utf-8") as f:
        src = f.read()
    check("backend_api uses format_time_12 via _display", "format_time_12" in src)
except Exception as e:
    check("backend_api format_time_12", False, str(e))

# 7. Build exists
try:
    exe_path = os.path.join(os.path.dirname(__file__), "dist", "Phase20-12-Music-Control-UI-12H", "PrayerMusicGuard", "PrayerMusicGuard.exe")
    exists = os.path.exists(exe_path)
    size = os.path.getsize(exe_path) if exists else 0
    check("Phase20-12 build EXE exists", exists, exe_path if exists else "missing")
    check("Build EXE size reasonable", size > 1_000_000, f"{size} bytes")
except Exception as e:
    check("Build EXE", False, str(e))

# 8. Previous builds untouched
try:
    p11 = os.path.join(os.path.dirname(__file__), "dist", "Phase20-11-Music-Control-Fix", "PrayerMusicGuard", "PrayerMusicGuard.exe")
    p8 = os.path.join(os.path.dirname(__file__), "dist", "Phase20-8-Splash-Timing", "PrayerMusicGuard", "PrayerMusicGuard.exe")
    check("Phase20-11 build still exists", os.path.exists(p11))
    check("Phase20-8 build still exists", os.path.exists(p8))
except Exception as e:
    check("Previous builds intact", False, str(e))

passed = sum(1 for _, ok, _ in results if ok)
total = len(results)
print(f"\n=== Results: {passed}/{total} tests passed ===")
sys.exit(0 if passed == total else 1)
