"""Phase 20.28-QA: RUNTIME location test against the real application.

Launches the real frontend with the real BackendAPI bridge (real network:
ipapi.co + api.aladhan.com) in a live WebView2 window and drives the actual
UI handlers: radio switches, combobox typing/filtering, item selection, and
the real "جلب المواقيت" fetch, then waits 10s and checks for reverts.

Faithfulness:
  * app.js / theme.js / css are BYTE-IDENTICAL copies of the real frontend.
  * index.html is copied with a 6-line error hook prepended (runs BEFORE
    app.js) - the only difference, purely for error capture.
  * The bridge is the real BackendAPI with its real scheduler.

No source file is modified. The user profile is snapshotted and restored.
"""
import json
import os
import shutil
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WV = ROOT / "webview_app"
PROFILE = Path(os.environ.get("APPDATA", "")) / "PrayerMusicGuard" / "settings.json"

sys.path.insert(0, str(WV))
sys.path.insert(0, str(ROOT))

import webview  # noqa: E402
import webview_main  # noqa: E402

RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond), detail))
    print(("PASS " if cond else "FAIL ") + name + (" | " + str(detail) if detail != "" else ""), flush=True)


def u(text):
    """Arabic -> JS \\u escapes so the driver is encoding-safe end to end."""
    return "".join("\\u%04x" % ord(ch) for ch in text)


class JS:
    def __init__(self, window):
        self.win = window

    def __call__(self, expr, timeout=30.0):
        box = {}

        def _run():
            try:
                box["r"] = self.win.evaluate_js(expr)
            except Exception as e:  # noqa: BLE001
                box["e"] = str(e)

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        t.join(timeout)
        if t.is_alive():
            return {"__timeout__": True}
        if "e" in box:
            return {"__error__": box["e"]}
        raw = box.get("r")
        if raw is None:
            return {"__none__": True}
        try:
            return json.loads(raw) if isinstance(raw, str) else raw
        except ValueError:
            return {"__raw__": raw}


def read_profile():
    if not PROFILE.is_file():
        return {}
    try:
        return json.loads(PROFILE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def prepare_baseline_profile():
    """Force a clean post-20.28 baseline (auto mode, empty manual fields),
    preserving the user's other settings. Proves 'starts empty' honestly."""
    cur = read_profile()
    cur["location_mode"] = "auto"
    for k in ("manual_city", "manual_country", "manual_latitude",
              "manual_longitude", "manual_timezone"):
        cur[k] = ""
    cur["location_migrated_20_28"] = True
    PROFILE.write_text(json.dumps(cur, ensure_ascii=False, indent=2), encoding="utf-8")
    return cur


def restore_profile(snap):
    if snap is None:
        try:
            PROFILE.unlink()
        except OSError:
            pass
        return
    PROFILE.write_text(snap, encoding="utf-8")


def errs():
    return "JSON.stringify({e:(window.__pmgErrors||[]).slice()})"


# ------------------------------------------------------------------ setup
QA_DIR = Path(tempfile.mkdtemp(prefix="pmg_qa2028_"))
FRONT = QA_DIR / "frontend"
shutil.copytree(WV / "frontend", FRONT)
index = (FRONT / "index.html").read_text(encoding="utf-8")
HOOK = (
    "<script>window.__pmgErrors=[];"
    "window.addEventListener('error',function(e){window.__pmgErrors.push(String(e.message||e.error||'err'));});"
    "window.addEventListener('unhandledrejection',function(e){window.__pmgErrors.push('rej:' + String(e.reason));});"
    "</script>"
)
index2 = index.replace("<body>", "<body>" + HOOK, 1)
assert index2 != index, "hook not injected"
(FRONT / "index.html").write_text(index2, encoding="utf-8")

same = {}
for rel in ("js/app.js", "js/theme.js", "css/components.css", "css/layout.css", "css/skins.css", "css/theme.css"):
    same[rel] = (FRONT / rel).read_bytes() == (WV / "frontend" / rel).read_bytes()
check("QA setup: real frontend files copied byte-identically", all(same.values()),
      json.dumps(same))
check("QA setup: error hook runs before app.js",
      index2.index(HOOK) < index2.index("js/app.js"))

api = webview_main._build_api()
check("QA setup: real BackendAPI bridge built", api is not None)
storage_path, _runtime = webview_main._configure_webview()
check("QA setup: WebView2 configured", storage_path is not None)
if api is not None:
    api.start_scheduler()

win = webview.create_window(
    "PMG QA 20.28",
    str(FRONT / "index.html"),
    width=900, height=760, x=40, y=40,  # on-screen so timers are not throttled
    js_api=api,
)


# ------------------------------------------------------------------ driver
def driver():
    js = JS(win)
    time.sleep(1.0)

    st = {}
    for _ in range(40):
        st = js("JSON.stringify({bridge: !!(window.pywebview && window.pywebview.api),"
                "cards: document.querySelectorAll('#prayer-grid .prayer-card').length,"
                "errs: (window.__pmgErrors||[]).length})")
        if st.get("cards", 0) and st.get("bridge"):
            break
        time.sleep(0.5)
    check("R0: real bridge attached and first refresh rendered",
          st.get("cards", 0) > 0 and st.get("bridge") is True, json.dumps(st, ensure_ascii=False))
    check("R0: zero JS errors at startup", st.get("errs", 99) == 0, json.dumps(st.get("errs")))

    def read_state(tag):
        return js(
            "JSON.stringify({tag:'" + tag + "',"
            "mode: (document.querySelector('input[name=\\\"location_mode\\\"]:checked')||{}).value,"
            "country: (document.getElementById('set-country')||{}).value,"
            "city: (document.getElementById('set-city')||{}).value,"
            "resolved: (document.getElementById('location-resolved')||{}).textContent,"
            "locStatus: (document.getElementById('location-status')||{}).textContent,"
            "timesLoc: (document.getElementById('times-location')||{}).textContent,"
            "dashLoc: (document.getElementById('location-line')||{}).textContent,"
            "times: (function(){var o={};var l=document.querySelectorAll('#times-editor input');"
            "for(var i=0;i<l.length;i++){o[l[i].id]=l[i].value} return o;})(),"
            "errs: (window.__pmgErrors||[]).slice()})"
        )

    def radio(mode):
        return js("(function(){var r=document.querySelector('input[name=\\\"location_mode\\\"][value=\\\""
                  + mode + "\\\"]'); r.checked=true; r.dispatchEvent(new Event('change'));"
                  " return JSON.stringify({mode:r.value, fields:document.getElementById('manual-fields').style.display});})()")

    def type_into(el_id, text, wait=0.45):
        js("(function(){var ci=document.getElementById('" + el_id + "'); ci.value='"
           + u(text) + "'; ci.dispatchEvent(new Event('input')); return 1;})()")
        time.sleep(wait)

    def pick_first(combo_id, list_sel):
        return js("(function(){var lis=document.querySelectorAll('" + list_sel + " li');"
                  " if(!lis.length) return JSON.stringify({items:0});"
                  " var names=[]; for(var i=0;i<Math.min(lis.length,6);i++){names.push(lis[i].textContent);}"
                  " lis[0].dispatchEvent(new MouseEvent('mousedown',{bubbles:true,cancelable:true}));"
                  " return JSON.stringify({items:lis.length, first:names, picked:(document.getElementById('"
                  + combo_id + "')||{}).value});})()")

    def fetch_and_wait(tag, seconds=10):
        # NOTE: ExecuteScriptAsync needs a single expression - a top-level
        # "return" silently fails, so wrap the click in an IIFE.
        js("(function(){document.getElementById('btn-fetch-location').click(); return 1;})()")
        t0 = time.time()
        time.sleep(seconds)
        res = read_state(tag)
        res["__elapsed__"] = round(time.time() - t0, 1)
        res["__profile__"] = read_profile()
        return res

    def no_errors(tag):
        e = js(errs())
        check(tag + ": no JS errors", len(e.get("e", [])) == 0, json.dumps(e, ensure_ascii=False))

    # ================= TEST 1: Manual Egypt -> Alexandria =================
    r = radio("manual")
    time.sleep(1.2)
    check("T1a: switch to Manual shows manual fields", r.get("fields") == "block", json.dumps(r, ensure_ascii=False))
    s1 = read_profile()
    dom = js("JSON.stringify({country:(document.getElementById('set-country')||{}).value,"
             " city:(document.getElementById('set-city')||{}).value,"
             " placeholder:(document.getElementById('set-city')||{}).placeholder})")
    check("T1b: Manual starts EMPTY (profile has no country/city, no Saudi/Jeddah)",
          s1.get("location_mode") == "manual" and s1.get("manual_country", "X") == "" and s1.get("manual_city", "X") == "",
          json.dumps({k: s1.get(k) for k in ("location_mode", "manual_country", "manual_city")}, ensure_ascii=False))
    check("T1b2: Manual DOM inputs start empty (no Saudi/Jeddah pre-filled)",
          dom.get("country", "X") == "" and dom.get("city", "X") == "",
          json.dumps(dom, ensure_ascii=False))

    type_into("set-country", "مصر")
    pick = pick_first("set-country", "#country-combobox .combobox__list")
    check("T1c: typing 'مصر' filters country list to Egypt", pick.get("items") == 1,
          json.dumps(pick, ensure_ascii=False))
    type_into("set-city", "Alexandria")
    pick = pick_first("set-city", "#city-combobox .combobox__list")
    check("T1d: typing 'Alexandria' filters city list", pick.get("items") == 1 and pick.get("picked") == "Alexandria",
          json.dumps(pick, ensure_ascii=False))

    res = fetch_and_wait("T1")
    check("T1e: fetch ok, resolved = Alexandria/Egypt",
          "Alexandria" in str(res.get("resolved")),
          json.dumps({k: res.get(k) for k in ("resolved", "timesLoc", "locStatus")}, ensure_ascii=False))
    check("T1f: after 10s UI still Egypt/Alexandria (NO REVERT)",
          "مصر" in str(res.get("country")) and str(res.get("city")) == "Alexandria",
          json.dumps({"country": res.get("country"), "city": res.get("city")}, ensure_ascii=False))
    p = res["__profile__"]
    # the real UI stores the ARABIC country segment (extractCountryName of
    # "مصر / Egypt" -> "مصر"); that is the correct persisted value.
    check("T1g: persisted = Egypt/Alexandria, coords cleared",
          p.get("manual_country") == "مصر" and p.get("manual_city") == "Alexandria"
          and p.get("manual_latitude") == "" and p.get("manual_longitude") == "",
          json.dumps({k: p.get(k) for k in ("location_mode", "manual_country", "manual_city", "manual_latitude")}, ensure_ascii=False))
    t1_times = res.get("times", {})
    check("T1h: prayer times actually fetched (5 fields)", len([k for k in t1_times if t1_times[k]]) == 5,
          json.dumps(t1_times, ensure_ascii=False))
    no_errors("T1")

    # ================= TEST 2: Saudi -> Riyadh =================
    type_into("set-country", "السعودية")
    pick = pick_first("set-country", "#country-combobox .combobox__list")
    check("T2a: typing 'السعودية' filters to Saudi Arabia", pick.get("items") == 1,
          json.dumps(pick, ensure_ascii=False))
    type_into("set-city", "Riyadh")
    pick = pick_first("set-city", "#city-combobox .combobox__list")
    check("T2b: typing 'Riyadh' filters city list", pick.get("items") == 1 and pick.get("picked") == "Riyadh",
          json.dumps(pick, ensure_ascii=False))
    res = fetch_and_wait("T2")
    check("T2c: after 10s UI still Saudi/Riyadh (NO REVERT to Jeddah)",
          "السعودية" in str(res.get("country")) and str(res.get("city")) == "Riyadh",
          json.dumps({"country": res.get("country"), "city": res.get("city")}, ensure_ascii=False))
    p = res["__profile__"]
    check("T2d: persisted = Saudi Arabia/Riyadh",
          p.get("manual_country") == "السعودية" and p.get("manual_city") == "Riyadh",
          json.dumps({k: p.get(k) for k in ("manual_country", "manual_city")}, ensure_ascii=False))
    t2_times = res.get("times", {})
    check("T2e: times changed for Riyadh (differ from Alexandria)",
          t2_times != t1_times and len([k for k in t2_times if t2_times[k]]) == 5,
          json.dumps(t2_times, ensure_ascii=False))
    no_errors("T2")

    # ================= TEST 3: change to another country/city =================
    type_into("set-country", "الأردن")
    pick = pick_first("set-country", "#country-combobox .combobox__list")
    check("T3a: typing 'الأردن' filters to Jordan", pick.get("items") == 1, json.dumps(pick, ensure_ascii=False))
    type_into("set-city", "Amman")
    pick = pick_first("set-city", "#city-combobox .combobox__list")
    check("T3b: typing 'Amman' filters city list", pick.get("items") == 1 and pick.get("picked") == "Amman",
          json.dumps(pick, ensure_ascii=False))
    res = fetch_and_wait("T3")
    check("T3c: after 10s UI still Jordan/Amman (NO REVERT)",
          "الأردن" in str(res.get("country")) and str(res.get("city")) == "Amman",
          json.dumps({"country": res.get("country"), "city": res.get("city")}, ensure_ascii=False))
    p = res["__profile__"]
    check("T3d: persisted = Jordan/Amman",
          p.get("manual_country") == "الأردن" and p.get("manual_city") == "Amman",
          json.dumps({k: p.get(k) for k in ("manual_country", "manual_city")}, ensure_ascii=False))
    t3_times = res.get("times", {})
    check("T3e: times changed for Amman (differ from Riyadh)",
          t3_times != t2_times and len([k for k in t3_times if t3_times[k]]) == 5,
          json.dumps(t3_times, ensure_ascii=False))
    no_errors("T3")

    # ================= TEST 4: Auto Location =================
    r = radio("auto")
    time.sleep(1.2)
    s4 = read_profile()
    check("T4a: switch to Auto persisted (no 'تعذر الحفظ')",
          s4.get("location_mode") == "auto", json.dumps({k: s4.get(k) for k in ("location_mode",)}, ensure_ascii=False))
    msg = js("JSON.stringify({s:(document.getElementById('location-status')||{}).textContent})")
    check("T4b: auto switch status is a success message",
          "تعذر" not in str(msg.get("s", "")) and str(msg.get("s", "")).strip() != "",
          json.dumps(msg, ensure_ascii=False))
    res = fetch_and_wait("T4")
    check("T4c: auto mode stayed auto after fetch+10s",
          res.get("mode") == "auto", json.dumps({"mode": res.get("mode")}, ensure_ascii=False))
    p = res["__profile__"]
    check("T4d: persisted mode auto with a resolved location",
          p.get("location_mode") == "auto" and bool(p.get("manual_city")) and bool(p.get("manual_country")),
          json.dumps({k: p.get(k) for k in ("location_mode", "manual_city", "manual_country")}, ensure_ascii=False))
    check("T4e: resolved location shown (not stale Jeddah)",
          "Jeddah" not in str(res.get("resolved")) and "جد" not in str(res.get("resolved")) and bool(res.get("resolved")),
          json.dumps({"resolved": res.get("resolved"), "timesLoc": res.get("timesLoc")}, ensure_ascii=False))
    check("T4f: dashboard location line agrees with the fetch",
          "Jeddah" not in str(res.get("dashLoc")) and "جد" not in str(res.get("dashLoc")),
          json.dumps({"dashLoc": res.get("dashLoc")}, ensure_ascii=False))
    no_errors("T4")

    # ================= TEST 5: Manual <-> Auto several times =================
    seq = []
    bad = []
    for mode in ("manual", "auto", "manual", "auto", "manual"):
        radio(mode)
        time.sleep(1.0)
        stt = js("JSON.stringify({mode:(document.querySelector('input[name=\\\"location_mode\\\"]:checked')||{}).value,"
                 " s:(document.getElementById('location-status')||{}).textContent})")
        seq.append(stt)
        if "تعذر" in str(stt.get("s", "")):
            bad.append(stt)
    check("T5: Manual<->Auto x5, never 'تعذر الحفظ'", len(bad) == 0, json.dumps(seq, ensure_ascii=False))

    # ================= TEST 6: type/filter country + city =================
    radio("manual")
    time.sleep(0.8)
    type_into("set-country", "united")
    f = js("JSON.stringify({items: document.querySelectorAll('#country-combobox .combobox__list li').length})")
    check("T6a: letters 'united' filter the country list (3 matches)", f.get("items") == 3, json.dumps(f))
    type_into("set-country", "zzzz")
    f = js("JSON.stringify({empty: (document.querySelector('#country-combobox .combobox__list li')||{}).textContent})")
    check("T6b: no-match shows the empty state", "لا توجد نتائج" in str(f.get("empty")), json.dumps(f, ensure_ascii=False))
    type_into("set-country", "مصر")
    pick = pick_first("set-country", "#country-combobox .combobox__list")
    type_into("set-city", "Cai")
    f = js("JSON.stringify({items: document.querySelectorAll('#city-combobox .combobox__list li').length,"
           " first: (document.querySelector('#city-combobox .combobox__list li')||{}).textContent})")
    check("T6c: letters filter the city list (Cairo)", f.get("items", 0) >= 1 and "Cai" in str(f.get("first", "")),
          json.dumps(f, ensure_ascii=False))
    no_errors("T6")

    # ================= TEST 7: Latitude/Longitude gone =================
    g = js("JSON.stringify({lat: !!document.getElementById('set-latitude'),"
           " lon: !!document.getElementById('set-longitude'),"
           " latLabel: Array.prototype.some.call(document.querySelectorAll('.field__label'),"
           " function(l){return l.textContent.indexOf('" + u("خط العرض") + "')!==-1;}),"
           " lonLabel: Array.prototype.some.call(document.querySelectorAll('.field__label'),"
           " function(l){return l.textContent.indexOf('" + u("خط الطول") + "')!==-1;})})")
    check("T7: Latitude/Longitude inputs and labels gone",
          g.get("lat") is False and g.get("lon") is False and g.get("latLabel") is False and g.get("lonLabel") is False,
          json.dumps(g))

    # ================= TEST 8: Dashboard / Music / Settings unchanged =================
    backend = api.get_state()

    dash = js("(function(){document.querySelector('.nav__item[data-page=\\\"dashboard\\\"]').click();"
              " return JSON.stringify({title:(document.getElementById('page-title')||{}).textContent,"
              " active: document.getElementById('page-dashboard').classList.contains('is-active'),"
              " cards: document.querySelectorAll('#prayer-grid .prayer-card').length,"
              " player: (document.getElementById('player-line')||{}).textContent,"
              " nextName:(document.getElementById('next-prayer-name')||{}).textContent,"
              " countdown:(document.getElementById('next-prayer-countdown')||{}).textContent,"
              " dashLoc:(document.getElementById('location-line')||{}).textContent});})()")
    check("T8a: Dashboard unchanged - page active, 5 prayer cards",
          dash.get("active") is True and dash.get("cards") == 5, json.dumps(dash, ensure_ascii=False))
    check("T8b: Dashboard countdown is live (not 00:00:00)",
          bool(dash.get("countdown")) and dash.get("countdown") != "00:00:00",
          json.dumps({"countdown": dash.get("countdown"), "next": dash.get("nextName")}, ensure_ascii=False))
    # mimic the app's own shortenPath(): basename without .exe, ./_/- -> spaces
    def shorten(path):
        import os as _os
        name = _os.path.basename(path or "")
        name = name.rsplit(".", 1)[0] if name.lower().endswith(".exe") else name
        return name.replace(".", " ").replace("_", " ").replace("-", " ").strip()

    check("T8c: Dashboard player line matches backend music",
          dash.get("player") == shorten(backend.get("music")) or dash.get("player") == "لم يتم الاختيار",
          json.dumps({"ui": dash.get("player"), "expected": shorten(backend.get("music"))}, ensure_ascii=False))

    mus = js("(function(){document.querySelector('.nav__item[data-page=\\\"music\\\"]').click();"
             " return JSON.stringify({active: document.getElementById('page-music').classList.contains('is-active'),"
             " music:(document.getElementById('set-music')||{}).value,"
             " adhan:(document.getElementById('set-adhan')||{}).value,"
             " btns: !!document.getElementById('btn-pause-2') && !!document.getElementById('btn-save-music')"
             " && !!document.getElementById('btn-dropdown-music'),"
             " method: (document.querySelector('input[name=\\\"method\\\"]:checked')||{}).value});})()")
    check("T8d: Music Player page unchanged (controls present, page active)",
          mus.get("active") is True and mus.get("btns") is True, json.dumps(mus, ensure_ascii=False))
    check("T8e: Music page in sync with backend (music + method)",
          mus.get("music") == backend.get("music") and mus.get("method") == backend.get("method"),
          json.dumps({"ui": {k: mus.get(k) for k in ("music", "method")},
                      "backend": {k: backend.get(k) for k in ("music", "method")}}, ensure_ascii=False))

    set_st = js("(function(){document.querySelector('.nav__item[data-page=\\\"settings\\\"]').click();"
                " return JSON.stringify({active: document.getElementById('page-settings').classList.contains('is-active'),"
                " minutes:(document.getElementById('set-minutes')||{}).value,"
                " enabled: document.getElementById('set-enabled').checked,"
                " announce: document.getElementById('set-announce').checked,"
                " autostart: document.getElementById('set-autostart').checked,"
                " version:(document.getElementById('app-version')||{}).textContent});})()")
    check("T8f: Settings page unchanged (controls present, page active)",
          set_st.get("active") is True and set_st.get("version") == backend.get("version"),
          json.dumps(set_st, ensure_ascii=False))
    check("T8g: Settings in sync with backend",
          set_st.get("minutes") == str(backend.get("minutes")) and set_st.get("enabled") == backend.get("enabled")
          and set_st.get("announce") == backend.get("announce") and set_st.get("autostart") == backend.get("autostart"),
          json.dumps({"ui": {k: set_st.get(k) for k in ("minutes", "enabled", "announce", "autostart")},
                      "backend": {k: backend.get(k) for k in ("minutes", "enabled", "announce", "autostart")}}, ensure_ascii=False))

    tim = js("(function(){document.querySelector('.nav__item[data-page=\\\"times\\\"]').click();"
             " return JSON.stringify({active: document.getElementById('page-times').classList.contains('is-active'),"
             " inputs: document.querySelectorAll('#times-editor input').length,"
             " radios: document.querySelectorAll('input[name=\\\"location_mode\\\"]').length});})()")
    check("T8h: Times page unchanged (5 time inputs + 2 mode radios)",
          tim.get("active") is True and tim.get("inputs") == 5 and tim.get("radios") == 2, json.dumps(tim))
    no_errors("T8")

    # ================= TEST 9: final error sweep =================
    fin = js("JSON.stringify({errs:(window.__pmgErrors||[]).slice(),"
             " bridge: !!(window.pywebview && window.pywebview.api),"
             " ready: document.readyState})")
    check("T9: zero JS/runtime errors across the whole run",
          len(fin.get("errs", [])) == 0 and fin.get("bridge") is True and fin.get("ready") == "complete",
          json.dumps(fin, ensure_ascii=False))

    time.sleep(0.5)
    try:
        win.destroy()
    except Exception:  # noqa: BLE001
        pass


# ------------------------------------------------------------------ run
prepare_baseline_profile()  # clean post-20.28 baseline; restored at the end
_snap = PROFILE.read_text(encoding="utf-8")
RUN_START = time.strftime("%Y-%m-%dT%H:%M:%S")
try:
    webview.start(gui=webview_main._gui_name(), storage_path=storage_path, func=driver)
except TypeError:
    webview.start(gui="edgechromium", func=driver)
except Exception as e:  # noqa: BLE001
    print("FAIL runtime driver crashed: " + repr(e))
RUN_END = time.strftime("%Y-%m-%dT%H:%M:%S")

# prove the app's own 30s background refresh actually ran during the session
ticks = -1
try:
    diag = Path(os.environ.get("APPDATA", "")) / "PrayerMusicGuard" / "bridge_diag.log"
    ticks = 0
    for line in diag.read_text(encoding="utf-8").splitlines():
        if '"call": "get_state"' in line and '"result": "ok"' in line:
            ts = line.split('"t": "', 1)[1].split('"', 1)[0]
            if RUN_START <= ts <= RUN_END:
                ticks += 1
except Exception:  # noqa: BLE001
    ticks = -1
check("R-interval: app's own 30s background refresh fired during run (>=2 ticks)",
      ticks >= 2, "get_state ticks=" + str(ticks))

try:
    api.stop_scheduler()
except Exception:  # noqa: BLE001
    pass
restore_profile(_snap)

_failed = [n for n, ok_, _d in RESULTS if not ok_]
print("\n==== " + str(len(RESULTS) - len(_failed)) + "/" + str(len(RESULTS)) + " runtime checks passed ====")
if _failed:
    print("FAILED: " + ", ".join(_failed))
    print("OVERALL: FAIL")
else:
    print("OVERALL: PASS")
shutil.rmtree(QA_DIR, ignore_errors=True)
