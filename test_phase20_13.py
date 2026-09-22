"""Automated verification tests for Phase 20.13."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ast

results = []
def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))

print("=== Phase 20.13 Verification ===\n")

# Syntax
try:
    ast.parse(open(os.path.join(os.path.dirname(__file__), "main.py"), encoding="utf-8").read())
    check("main.py syntax", True)
except Exception as e:
    check("main.py syntax", False, str(e))

try:
    ast.parse(open(os.path.join(os.path.dirname(__file__), "webview_app", "backend_api.py"), encoding="utf-8").read())
    check("backend_api.py syntax", True)
except Exception as e:
    check("backend_api.py syntax", False, str(e))

# Resume countdown UI element
try:
    html = open(os.path.join(os.path.dirname(__file__), "webview_app", "frontend", "index.html"), encoding="utf-8").read()
    has = 'id="resume-countdown"' in html
    check("Resume countdown element present", has)
except Exception as e:
    check("Resume countdown element", False, str(e))

# 12-hour hint updated
try:
    html = open(os.path.join(os.path.dirname(__file__), "webview_app", "frontend", "index.html"), encoding="utf-8").read()
    has = "الوقت يُعرض ويُعدّل بنظام 12 ساعة" in html
    check("Hint updated for 12h editing", has)
except Exception as e:
    check("Hint updated", False, str(e))

# JS has formatTime12 / parseTime12
try:
    js = open(os.path.join(os.path.dirname(__file__), "webview_app", "frontend", "js", "app.js"), encoding="utf-8").read()
    has_fmt = "function formatTime12" in js
    has_parse = "function parseTime12" in js
    check("JS formatTime12 present", has_fmt)
    check("JS parseTime12 present", has_parse)
except Exception as e:
    check("JS time functions", False, str(e))

# JS fillSettings uses formatTime12
try:
    js = open(os.path.join(os.path.dirname(__file__), "webview_app", "frontend", "js", "app.js"), encoding="utf-8").read()
    has = "formatTime12(prayer.time" in js
    check("fillSettings uses formatTime12", has)
except Exception as e:
    check("fillSettings", False, str(e))

# Build exists
exe = os.path.join(os.path.dirname(__file__), "dist", "Phase20-13-UI-Countdown-12H-Location", "PrayerMusicGuard", "PrayerMusicGuard.exe")
check("Phase20-13 build exists", os.path.exists(exe), exe)
if os.path.exists(exe):
    check("Build size reasonable", os.path.getsize(exe) > 1_000_000)

# Previous builds untouched
check("Phase20-12 build still exists", os.path.exists(os.path.join(os.path.dirname(__file__), "dist", "Phase20-12-Music-Control-UI-12H", "PrayerMusicGuard", "PrayerMusicGuard.exe")))
check("Phase20-11 build still exists", os.path.exists(os.path.join(os.path.dirname(__file__), "dist", "Phase20-11-Music-Control-Fix", "PrayerMusicGuard", "PrayerMusicGuard.exe")))

passed = sum(1 for _, ok, _ in results if ok)
total = len(results)
print(f"\n=== {passed}/{total} tests passed ===")
sys.exit(0 if passed == total else 1)
