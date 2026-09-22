"""Phase 20.28 Release UAT — functional test of the BUILT EXE's bundled content.

Runs the frozen frontend shipped inside dist\\Phase20-28-Release (byte-identical
to source, verified separately) in a live WebView2 window, with the real
BackendAPI bridge loaded from the BUNDLE (so main.py/backend_api.py are the
frozen copies too). Real network for the location fetch.

Covers: UI shell, Dashboard+countdown, Manual/Auto location, 196 countries,
Egypt/Alexandria, Auto Location, Music Player, Settings (save round-trip),
Dark/Light theme, Navigation, removed lat/long fields.

No source file is modified; the user profile is snapshotted and restored.
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
BUNDLE = ROOT / "dist" / "Phase20-28-Release" / "PrayerMusicGuard"
FROZEN_FRONTEND = BUNDLE / "webview_app" / "frontend"
PROFILE = Path(os.environ.get("APPDATA", "")) / "PrayerMusicGuard" / "settings.json"

# load the frozen backend copies (bundle root has main.py; bundle webview_app has backend_api.py)
sys.path.insert(0, str(BUNDLE / "webview_app"))
sys.path.insert(0, str(BUNDLE))

import webview  # noqa: E402
import webview_main  # noqa: E402  (module-level helper reuse)

RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond), detail))
    print(("PASS " if cond else "FAIL ") + name + (" | " + str(detail) if detail != "" else ""), flush=True)


def u(text):
    return "".join("\\u%04x" % ord(ch) for ch in text)


class JS:
    def __init__(self, window):
        self.win = window

    def __call__(self, expr, timeout=45.0):
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


# ------------------------------------------------------------------ setup
QA_DIR = Path(tempfile.mkdtemp(prefix="pmg_rel2028_"))
FRONT = QA_DIR / "frontend"
shutil.copytree(FROZEN_FRONTEND, FRONT)
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

# frozen frontend must be byte-identical to the shipped bundle
same = {}
for rel in ("js/app.js", "js/theme.js", "css/components.css", "css/layout.css", "css/skins.css", "css/theme.css"):
    same[rel] = (FRONT / rel).read_bytes() == (FROZEN_FRONTEND / rel).read_bytes()
check("UAT setup: frozen frontend copied byte-identically", all(same.values()), json.dumps(same))
check("UAT setup: error hook runs before app.js",
      index2.index(HOOK) < index2.index("js/app.js"))

api = webview_main._build_api()
check("UAT setup: real BackendAPI bridge built (from bundle)", api is not None)
storage_path, _runtime = webview_main._configure_webview()
check("UAT setup: WebView2 configured", storage_path is not None)
if api is not None:
    api.start_scheduler()

win = webview.create_window(
    "PMG Release UAT 20.28",
    str(FRONT / "index.html"),
    width=900, height=760, x=40, y=40,
    js_api=api,
)


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
    check("1. UI shell: bridge attached, first refresh rendered",
          st.get("cards", 0) > 0 and st.get("bridge") is True, json.dumps(st, ensure_ascii=False))
    check("1. UI shell: zero JS errors at startup", st.get("errs", 99) == 0, json.dumps(st.get("errs")))

    shell = js("JSON.stringify({html: document.documentElement.lang + '/' + document.documentElement.dir,"
               " rtl: document.documentElement.dir === 'rtl',"
               " nav: document.querySelectorAll('.nav__item').length,"
               " pages: document.querySelectorAll('.page').length,"
               " version:(document.getElementById('app-version')||{}).textContent})")
    check("1. UI shell: dir=rtl lang=ar, 4 nav items, 4 pages",
          shell.get("rtl") is True and shell.get("nav") == 4 and shell.get("pages") == 4,
          json.dumps(shell, ensure_ascii=False))

    # ---------- 2. Dashboard + countdown ----------
    dash = js("(function(){document.querySelector('.nav__item[data-page=\\\"dashboard\\\"]').click();"
              " return JSON.stringify({active: document.getElementById('page-dashboard').classList.contains('is-active'),"
              " cards: document.querySelectorAll('#prayer-grid .prayer-card').length,"
              " nextName:(document.getElementById('next-prayer-name')||{}).textContent,"
              " countdown:(document.getElementById('next-prayer-countdown')||{}).textContent});})()")
    check("2. Dashboard: active, 5 prayer cards, next prayer named",
          dash.get("active") is True and dash.get("cards") == 5 and bool(dash.get("nextName")),
          json.dumps(dash, ensure_ascii=False))
    c1 = js("JSON.stringify({c:(document.getElementById('next-prayer-countdown')||{}).textContent})")
    time.sleep(2.2)
    c2 = js("JSON.stringify({c:(document.getElementById('next-prayer-countdown')||{}).textContent})")
    check("2. Dashboard: countdown is ticking", c1.get("c") != c2.get("c"),
          json.dumps({"t0": c1.get("c"), "t2s": c2.get("c")}, ensure_ascii=False))

    # ---------- 3. Manual/Auto location modes ----------
    js("(function(){document.querySelector('.nav__item[data-page=\\\"times\\\"]').click(); return 1;})()")
    time.sleep(0.5)
    m = js("(function(){var r=document.querySelector('input[name=\\\"location_mode\\\"][value=\\\"manual\\\"]');"
           " r.checked=true; r.dispatchEvent(new Event('change'));"
           " return JSON.stringify({fields: document.getElementById('manual-fields').style.display});})()")
    time.sleep(1.0)
    check("3. Location: Manual radio shows the manual fields", m.get("fields") == "block", json.dumps(m, ensure_ascii=False))
    m = js("(function(){var r=document.querySelector('input[name=\\\"location_mode\\\"][value=\\\"auto\\\"]');"
           " r.checked=true; r.dispatchEvent(new Event('change'));"
           " return JSON.stringify({fields: document.getElementById('manual-fields').style.display});})()")
    time.sleep(1.0)
    check("3. Location: Auto radio hides the manual fields (no 'تعذر الحفظ')",
          m.get("fields") == "none", json.dumps(m, ensure_ascii=False))
    s3 = read_profile()
    check("3. Location: Auto mode persisted, switch produced no save error",
          s3.get("location_mode") == "auto", json.dumps({"location_mode": s3.get("location_mode")}, ensure_ascii=False))

    # ---------- 4. 196 countries ----------
    js("(function(){var r=document.querySelector('input[name=\\\"location_mode\\\"][value=\\\"manual\\\"]');"
       " r.checked=true; r.dispatchEvent(new Event('change')); return 1;})()")
    time.sleep(1.0)
    js("(function(){var ci=document.getElementById('set-country'); ci.value=''; ci.dispatchEvent(new Event('input'));"
       " ci.dispatchEvent(new Event('focus')); return 1;})()")
    time.sleep(0.5)
    cc = js("JSON.stringify({count: document.querySelectorAll('#country-combobox .combobox__list li').length})")
    check("4. Countries: full list renders 196 entries", cc.get("count") == 196, json.dumps(cc))

    # ---------- 5. Egypt/Alexandria (real network fetch) ----------
    js("(function(){var ci=document.getElementById('set-country'); ci.value='" + u("مصر") + "';"
       " ci.dispatchEvent(new Event('input')); return 1;})()")
    time.sleep(0.45)
    pk = js("(function(){var lis=document.querySelectorAll('#country-combobox .combobox__list li');"
            " if(!lis.length) return JSON.stringify({items:0});"
            " lis[0].dispatchEvent(new MouseEvent('mousedown',{bubbles:true,cancelable:true}));"
            " return JSON.stringify({items:lis.length, picked:(document.getElementById('set-country')||{}).value});})()")
    check("5a. Egypt filters to 1 country and selects it",
          pk.get("items") == 1 and "مصر" in str(pk.get("picked")), json.dumps(pk, ensure_ascii=False))
    # city data loads asynchronously (get_cities); poll until it settles
    cities = {"count": 0}
    for _ in range(16):
        js("(function(){var ci=document.getElementById('set-city'); if(ci.disabled) return 0;"
           " ci.value=''; if(!ci.classList.contains('x')){ci.dispatchEvent(new Event('focus'));} return 1;})()")
        time.sleep(0.4)
        cities = js("JSON.stringify({count: document.querySelectorAll('#city-combobox .combobox__list li').length,"
                    " first: (document.querySelector('#city-combobox .combobox__list li')||{}).textContent})")
        if cities.get("count", 0) > 1:
            break
    check("5b. Egypt loads its city list", cities.get("count", 0) > 1, json.dumps(cities, ensure_ascii=False))
    js("(function(){var ci=document.getElementById('set-city'); ci.value='Alexandria';"
       " ci.dispatchEvent(new Event('input')); return 1;})()")
    time.sleep(0.5)
    pk = js("(function(){var lis=document.querySelectorAll('#city-combobox .combobox__list li');"
            " if(!lis.length) return JSON.stringify({items:0});"
            " lis[0].dispatchEvent(new MouseEvent('mousedown',{bubbles:true,cancelable:true}));"
            " return JSON.stringify({items:lis.length, picked:(document.getElementById('set-city')||{}).value});})()")
    check("5c. Alexandria filters and selects", pk.get("items") == 1 and pk.get("picked") == "Alexandria",
          json.dumps(pk, ensure_ascii=False))
    js("(function(){document.getElementById('btn-fetch-location').click(); return 1;})()")
    time.sleep(7.0)
    res = js("JSON.stringify({resolved:(document.getElementById('location-resolved')||{}).textContent,"
             " status:(document.getElementById('location-status')||{}).textContent,"
             " timesLoc:(document.getElementById('times-location')||{}).textContent})")
    check("5d. Egypt/Alexandria fetch succeeds via the real API",
          "Alexandria" in str(res.get("resolved")) or "Alexandria" in str(res.get("timesLoc")),
          json.dumps(res, ensure_ascii=False))
    p5 = read_profile()
    check("5e. location persisted (city=Alexandria)",
          p5.get("manual_city") == "Alexandria", json.dumps({k: p5.get(k) for k in ("manual_city", "manual_country")}, ensure_ascii=False))

    # ---------- 6. Auto Location (real network) ----------
    js("(function(){var r=document.querySelector('input[name=\\\"location_mode\\\"][value=\\\"auto\\\"]');"
       " r.checked=true; r.dispatchEvent(new Event('change')); return 1;})()")
    time.sleep(1.0)
    js("(function(){document.getElementById('btn-fetch-location').click(); return 1;})()")
    time.sleep(7.0)
    res = js("JSON.stringify({mode:(document.querySelector('input[name=\\\"location_mode\\\"]:checked')||{}).value,"
             " resolved:(document.getElementById('location-resolved')||{}).textContent})")
    p6 = read_profile()
    check("6. Auto Location: resolves a real location, mode stays auto",
          res.get("mode") == "auto" and p6.get("location_mode") == "auto" and bool(res.get("resolved")),
          json.dumps({"ui": res, "profile_mode": p6.get("location_mode")}, ensure_ascii=False))

    # ---------- 7. Music Player ----------
    mus = js("(function(){document.querySelector('.nav__item[data-page=\\\"music\\\"]').click();"
             " return JSON.stringify({active: document.getElementById('page-music').classList.contains('is-active'),"
             " music:(document.getElementById('set-music')||{}).value,"
             " radios: document.querySelectorAll('input[name=\\\"method\\\"]').length,"
             " hasPause: !!document.getElementById('btn-pause-2'),"
             " hasBrowse: !!document.getElementById('btn-browse-music')});})()")
    check("7a. Music Player page unchanged (inputs, method radios, pause/browse buttons)",
          mus.get("active") is True and mus.get("radios") == 2 and mus.get("hasPause") is True and mus.get("hasBrowse") is True,
          json.dumps(mus, ensure_ascii=False))
    js("(function(){document.getElementById('btn-dropdown-music').click(); return 1;})()")
    time.sleep(5.0)
    dd = js("JSON.stringify({visible: !document.getElementById('dropdown-music').classList.contains('hidden'),"
            " items: document.querySelectorAll('#dropdown-music .dropdown-item').length,"
            " status:(document.getElementById('music-status')||{}).textContent})")
    check("7b. Running-apps dropdown loads (real process enumeration)",
          dd.get("visible") is True and dd.get("items", 0) > 0, json.dumps(dd, ensure_ascii=False))

    # ---------- 8. Settings (save round-trip) ----------
    setb = api.get_state()
    set_st = js("(function(){document.querySelector('.nav__item[data-page=\\\"settings\\\"]').click();"
                " return JSON.stringify({active: document.getElementById('page-settings').classList.contains('is-active'),"
                " minutes:(document.getElementById('set-minutes')||{}).value,"
                " enabled: document.getElementById('set-enabled').checked});})()")
    check("8a. Settings page unchanged and populated",
          set_st.get("active") is True and set_st.get("minutes") == str(setb.get("minutes")),
          json.dumps({"ui": set_st, "backend_minutes": setb.get("minutes")}, ensure_ascii=False))
    js("(function(){var m=document.getElementById('set-minutes'); m.value='7';"
       " document.getElementById('btn-save').click(); return 1;})()")
    time.sleep(1.5)
    after = api.get_state()
    check("8b. Settings save round-trip persists to the backend",
          after.get("minutes") == 7 and after.get("ok") is not False,
          json.dumps({"backend_after": after.get("minutes")}, ensure_ascii=False))
    # restore the original minutes value through the same path
    js("(function(){var m=document.getElementById('set-minutes'); m.value='" + str(setb.get("minutes")) + "';"
       " document.getElementById('btn-save').click(); return 1;})()")
    time.sleep(1.2)

    # ---------- 9. Dark/Light theme ----------
    t0 = js("JSON.stringify({theme: document.documentElement.dataset.theme,"
            " stored: localStorage.getItem('pmg-theme')})")
    js("(function(){var cb=document.getElementById('theme-checkbox'); cb.checked=!cb.checked;"
       " cb.dispatchEvent(new Event('change')); return 1;})()")
    time.sleep(1.2)
    t1 = js("JSON.stringify({theme: document.documentElement.dataset.theme,"
            " stored: localStorage.getItem('pmg-theme')})")
    check("9a. Dark/Light toggle flips data-theme and persists to localStorage",
          t0.get("theme") != t1.get("theme") and bool(t1.get("stored")),
          json.dumps({"before": t0, "after": t1}, ensure_ascii=False))
    time.sleep(1.0)
    tback = api.get_state().get("theme")
    check("9b. theme persisted to the backend settings",
          bool(tback) and tback == t1.get("theme"),
          json.dumps({"backend_theme": tback, "ui_theme": t1.get("theme")}))
    # restore original theme
    if t0.get("theme"):
        js("(function(){var cb=document.getElementById('theme-checkbox');"
           " if((cb.checked) !== (" + ("true" if t0.get("theme") == "dark" else "false") + ")){ cb.checked=!cb.checked;"
           " cb.dispatchEvent(new Event('change')); } return 1;})()")
        time.sleep(1.0)

    # ---------- 10. Navigation ----------
    titles = []
    for pg in ("dashboard", "times", "music", "settings"):
        t = js("(function(){document.querySelector('.nav__item[data-page=\\\"" + pg + "\\\"]').click();"
               " return JSON.stringify({title:(document.getElementById('page-title')||{}).textContent,"
               " active: document.getElementById('page-" + pg + "').classList.contains('is-active')});})()")
        titles.append(t)
    check("10. Navigation: all 4 pages activate with titles",
          all(t.get("active") is True and bool(t.get("title")) for t in titles) and len(set(t.get("title") for t in titles)) == 4,
          json.dumps(titles, ensure_ascii=False))

    # ---------- 11. Latitude/Longitude gone (20.28 carry-over) ----------
    g = js("JSON.stringify({lat: !!document.getElementById('set-latitude'),"
           " lon: !!document.getElementById('set-longitude'),"
           " latLabel: Array.prototype.some.call(document.querySelectorAll('.field__label'),"
           " function(l){return l.textContent.indexOf('" + u("خط العرض") + "')!==-1;}),"
           " lonLabel: Array.prototype.some.call(document.querySelectorAll('.field__label'),"
           " function(l){return l.textContent.indexOf('" + u("خط الطول") + "')!==-1;})})")
    check("11. Latitude/Longitude inputs and labels are gone",
          g.get("lat") is False and g.get("lon") is False and g.get("latLabel") is False and g.get("lonLabel") is False,
          json.dumps(g))

    # ---------- final error sweep ----------
    fin = js("JSON.stringify({errs:(window.__pmgErrors||[]).slice(),"
             " bridge: !!(window.pywebview && window.pywebview.api),"
             " ready: document.readyState})")
    check("12. Zero JS/runtime errors across the whole UAT",
          len(fin.get("errs", [])) == 0 and fin.get("bridge") is True and fin.get("ready") == "complete",
          json.dumps(fin, ensure_ascii=False))

    time.sleep(0.5)
    try:
        win.destroy()
    except Exception:  # noqa: BLE001
        pass


# ------------------------------------------------------------------ run
_snap = PROFILE.read_text(encoding="utf-8") if PROFILE.is_file() else None
try:
    webview.start(gui=webview_main._gui_name(), storage_path=storage_path, func=driver)
except TypeError:
    webview.start(gui="edgechromium", func=driver)
except Exception as e:  # noqa: BLE001
    print("FAIL UAT driver crashed: " + repr(e))

try:
    api.stop_scheduler()
except Exception:  # noqa: BLE001
    pass
if _snap is not None:
    PROFILE.write_text(_snap, encoding="utf-8")

_failed = [n for n, ok_, _d in RESULTS if not ok_]
print("\n==== " + str(len(RESULTS) - len(_failed)) + "/" + str(len(RESULTS)) + " UAT checks passed ====")
if _failed:
    print("FAILED: " + ", ".join(_failed))
    print("OVERALL: FAIL")
else:
    print("OVERALL: PASS")
shutil.rmtree(QA_DIR, ignore_errors=True)
