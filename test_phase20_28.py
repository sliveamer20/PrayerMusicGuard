"""Phase 20.28 location-state fix — automated regression tests.

Exercises the exact user-visible scenarios (tests 1-5) at the state layer,
which is where the revert bug lived, plus the one-time stale-location
migration. Runs fully offline: ipapi.co and api.aladhan.com are stubbed.
"""
import io
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WEBVIEW = ROOT / "webview_app"

# --- isolate the profile BEFORE importing main.py (it reads APPDATA at import)
_tmp = tempfile.mkdtemp(prefix="pmg2028_")
os.makedirs(os.path.join(_tmp, "PrayerMusicGuard"))
os.environ["APPDATA"] = _tmp
os.environ["LOCALAPPDATA"] = _tmp
PROFILE = Path(_tmp) / "PrayerMusicGuard" / "settings.json"

sys.path.insert(0, str(WEBVIEW))
sys.path.insert(0, str(ROOT))

import urllib.request  # noqa: E402

import backend_api  # noqa: E402

MAIN = backend_api._MAIN
if MAIN is None:
    print("FATAL: main.py did not load:", backend_api._LOAD_ERROR)
    sys.exit(1)

# ---------------- network stubs (offline, deterministic) ----------------
ALADHAN_TIMINGS = {"Fajr": "05:00", "Dhuhr": "12:00", "Asr": "15:30",
                   "Maghrib": "18:00", "Isha": "19:30"}
AUTO_LOC = {"city": "Cairo", "country": "Egypt", "country_name": "Egypt",
            "latitude": 30.04, "longitude": 31.24, "timezone": "Africa/Cairo"}


class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()
        return False


def _fake_urlopen(request, timeout=None):
    url = getattr(request, "full_url", str(request))
    if "ipapi.co" in url:
        body = json.dumps(AUTO_LOC).encode()
    elif "aladhan.com" in url:
        body = json.dumps({"data": {"timings": dict(ALADHAN_TIMINGS)}}).encode()
    else:
        raise IOError("unexpected url " + url)
    return _Resp(body)


urllib.request.urlopen = _fake_urlopen

# ---------------- helpers ----------------
RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond), detail))
    print(("PASS " if cond else "FAIL ") + name + (" | " + detail if detail else ""))


def write_profile(obj):
    PROFILE.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def read_profile():
    return json.loads(PROFILE.read_text(encoding="utf-8"))


STALE_JEDDAH = {
    "music": "C:\\player.exe", "adhan": "", "minutes": 15, "method": "suspend",
    "times": {"Fajr": "05:19", "Dhuhr": "12:54"}, "enabled": True,
    "announce": True, "theme": "dark", "autostart": False,
    "location_mode": "manual",
    "manual_city": "\u062c\u062f\u0629",            # جدة
    "manual_country": "\u0627\u0644\u0633\u0639\u0648\u062f\u064a\u0629",  # السعودية
    "manual_latitude": "24.7136", "manual_longitude": "46.6753",
    "manual_timezone": "",
}

api = backend_api.BackendAPI()

# ================= T0: one-time stale Jeddah migration =================
write_profile(dict(STALE_JEDDAH))
s = MAIN.load_settings()
check("T0a migration: mode back to auto", s.get("location_mode") == "auto", str(s.get("location_mode")))
check("T0b migration: manual_city cleared", s.get("manual_city") == "", repr(s.get("manual_city")))
check("T0c migration: manual_country cleared", s.get("manual_country") == "", repr(s.get("manual_country")))
check("T0d migration: stale coords cleared",
      s.get("manual_latitude") == "" and s.get("manual_longitude") == "")
check("T0e migration: marker written", s.get("location_migrated_20_28") is True)
check("T0f migration: unrelated settings preserved",
      s.get("music") == "C:\\player.exe" and s.get("enabled") is True and s.get("theme") == "dark")
after_first = read_profile()
MAIN.load_settings()  # second load must NOT rewrite (idempotent, marker set)
check("T0g migration: runs only once (file stable)", read_profile() == after_first)

# ================= T1 (User test 5): manual -> auto switch allowed =================
r = api.save_settings({"location_mode": "manual", "manual_city": "Alexandria",
                       "manual_country": "Egypt", "manual_latitude": "",
                       "manual_longitude": ""})
check("T1a save manual mode ok", r.get("ok") is True, str(r.get("error")))
check("T1b saved mode is manual", read_profile().get("location_mode") == "manual")
r = api.save_settings({"location_mode": "auto"})
check("T1c switch manual->auto ok (no 'تعذر الحفظ')", r.get("ok") is True, str(r.get("error")))
check("T1d saved mode is now auto", read_profile().get("location_mode") == "auto")
check("T1e get_state reports auto", api.get_state().get("location_mode") == "auto")

# ================= T2 (User test 1): Egypt -> Alexandria persists =================
r = api.fetch_times({"location_mode": "manual", "manual_city": "Alexandria",
                     "manual_country": "Egypt", "manual_latitude": "",
                     "manual_longitude": ""})
check("T2a fetch ok", r.get("ok") is True, str(r.get("error")))
check("T2b fetch location label", r.get("location") == "Alexandria\u060c Egypt", str(r.get("location")))
p = read_profile()
check("T2c persisted manual_city", p.get("manual_city") == "Alexandria", repr(p.get("manual_city")))
check("T2d persisted manual_country", p.get("manual_country") == "Egypt", repr(p.get("manual_country")))
check("T2e persisted mode manual", p.get("location_mode") == "manual")
check("T2f coords cleared on manual save", p.get("manual_latitude") == "" and p.get("manual_longitude") == "")
loc = api.get_state().get("location")
check("T2g get_state location = Alexandria (no revert)", loc == "Alexandria\u060c Egypt", repr(loc))
loc2 = api.get_state().get("location")  # simulate the 30s refresh tick
check("T2h later refresh still Alexandria", loc2 == "Alexandria\u060c Egypt", repr(loc2))

# ================= T3 (User test 2): Saudi -> Riyadh persists =================
r = api.fetch_times({"location_mode": "manual", "manual_city": "Riyadh",
                     "manual_country": "Saudi Arabia", "manual_latitude": "",
                     "manual_longitude": ""})
check("T3a fetch ok", r.get("ok") is True, str(r.get("error")))
p = read_profile()
check("T3b persisted Riyadh", p.get("manual_city") == "Riyadh" and p.get("manual_country") == "Saudi Arabia")
loc = api.get_state().get("location")
check("T3c get_state location = Riyadh (no Jeddah revert)", loc == "Riyadh\u060c Saudi Arabia", repr(loc))

# ================= T4 (User test 3): change country/city, no revert =================
r = api.fetch_times({"location_mode": "manual", "manual_city": "Giza",
                     "manual_country": "Egypt", "manual_latitude": "",
                     "manual_longitude": ""})
loc = api.get_state().get("location")
check("T4a changed to Giza/Egypt (no revert to Riyadh/Jeddah)",
      loc == "Giza\u060c Egypt", repr(loc))
check("T4b fetch ok", r.get("ok") is True, str(r.get("error")))

# ================= T5 (User test 4): auto fetch stays auto/resolved =================
r = api.fetch_times({"location_mode": "auto", "manual_city": "", "manual_country": "",
                     "manual_latitude": "", "manual_longitude": ""})
check("T5a auto fetch ok", r.get("ok") is True, str(r.get("error")))
check("T5b auto resolved label", r.get("location") == "Cairo\u060c Egypt", str(r.get("location")))
p = read_profile()
check("T5c persisted mode auto", p.get("location_mode") == "auto")
check("T5d persisted resolved city", p.get("manual_city") == "Cairo", repr(p.get("manual_city")))
loc = api.get_state().get("location")
check("T5e get_state location = Cairo (no Jeddah revert)", loc == "Cairo\u060c Egypt", repr(loc))
loc2 = api.get_state().get("location")
check("T5f later refresh still Cairo", loc2 == "Cairo\u060c Egypt", repr(loc2))

# ================= T6 (User test 5b): full manual<->auto round trip =================
ok = True
errs = []
for mode, city, country in (("manual", "Alexandria", "Egypt"), ("auto", "", ""),
                            ("manual", "Dubai", "United Arab Emirates"), ("auto", "", "")):
    r = api.save_settings({"location_mode": mode, "manual_city": city, "manual_country": country})
    ok = ok and r.get("ok") is True
    if r.get("ok") is not True:
        errs.append(mode + ": " + str(r.get("error")))
check("T6 manual<->auto round trip, never rejected", ok, "; ".join(errs))

# ================= T7: get_state fields coherent after all churn =================
st = api.get_state()
check("T7a get_state ok", st.get("ok") is True)
check("T7b times were fetched", len(st.get("prayers", [])) == 5)
check("T7c next prayer present", st.get("next") is not None)

failed = [n for n, ok_, _ in RESULTS if not ok_]
print("\n==== {0}/{1} checks passed ====".format(len(RESULTS) - len(failed), len(RESULTS)))
if failed:
    print("FAILED: " + ", ".join(failed))
    sys.exit(1)
print("ALL BACKEND CHECKS PASSED")
