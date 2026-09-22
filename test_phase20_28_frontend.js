// Phase 20.28 — frontend regression tests.
// Loads the REAL app.js IIFE against a minimal DOM shim built from the REAL
// index.html id list, then drives the real event handlers:
//   - country/city typing + filtering (user test 7)
//   - fillSettings activeElement guard, i.e. refresh must not clobber typing (fix D)
//   - removed lat/long elements must not crash fillSettings (fix C)
const fs = require("fs");
const path = require("path");

const APP_JS = fs.readFileSync(path.join(__dirname, "webview_app", "frontend", "js", "app.js"), "utf8");
const INDEX = fs.readFileSync(path.join(__dirname, "webview_app", "frontend", "index.html"), "utf8");

const results = [];
function check(name, cond, detail) {
  results.push([name, !!cond, detail || ""]);
  console.log((cond ? "PASS " : "FAIL ") + name + (detail ? " | " + detail : ""));
}
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// ---------- DOM shim ----------
function makeEl(tag, id) {
  const el = {
    tag: tag, id: id || "", _text: "", _children: [], _listeners: {},
    _classes: new Set(), _attrs: {}, style: {}, value: "", disabled: false,
    checked: false, placeholder: "", dir: "", type: "", name: "", parentElement: null,
    _qmap: {},
  };
  el.className = "";
  Object.defineProperty(el, "textContent", {
    get() { return el._text; },
    set(v) { el._text = String(v); },
  });
  Object.defineProperty(el, "innerHTML", {
    get() { return el._children.map((c) => c._text).join(""); },
    set() { el._children = []; },
  });
  el.classList = {
    add: (c) => el._classes.add(c),
    remove: (c) => el._classes.delete(c),
    contains: (c) => el._classes.has(c),
  };
  el.setAttribute = (k, v) => { el._attrs[k] = v; };
  el.removeAttribute = (k) => { delete el._attrs[k]; };
  el.getAttribute = (k) => el._attrs[k];
  el.appendChild = (child) => { el._children.push(child); child.parentElement = el; return child; };
  el.addEventListener = (type, fn) => {
    (el._listeners[type] = el._listeners[type] || []).push(fn);
  };
  el.querySelector = (sel) => el._qmap[sel] || null;
  el.contains = (t) => t === el || el._children.includes(t);
  return el;
}
function dispatch(el, type, ev) {
  (el._listeners[type] || []).forEach((fn) => fn.call(el, ev || {}));
}

const byId = {};
const ids = [...INDEX.matchAll(/id="([^"]+)"/g)].map((m) => m[1]);
ids.forEach((id) => { byId[id] = makeEl("div", id); });
// removed lat/long inputs must be genuinely absent
check("F-C: index.html has no latitude label", !/خط العرض/.test(INDEX));
check("F-C: index.html has no longitude label", !/خط الطول/.test(INDEX));
check("F-C: index.html has no set-latitude input", !/set-latitude/.test(INDEX));
check("F-C: index.html has no set-longitude input", !/set-longitude/.test(INDEX));

// location-mode radios (parsed from the real markup)
const radios = [];
const radioRe = /<input[^>]*name="location_mode"[^>]*value="(\w+)"/g;
let rm;
while ((rm = radioRe.exec(INDEX))) {
  const r = makeEl("input");
  r.name = "location_mode";
  r.value = rm[1];
  r.checked = false;
  radios.push(r);
}
check("F-setup: two location_mode radios parsed", radios.length === 2, "count=" + radios.length);

// nav items
const navItems = [];
for (let i = 0; i < 4; i++) navItems.push(makeEl("button"));

// combobox wiring (country + city), mirroring index.html structure
function wireCombobox(rootId, inputId) {
  const root = byId[rootId];
  const input = byId[inputId];
  const arrow = makeEl("button");
  const menu = makeEl("div");
  const list = makeEl("ul");
  root._qmap[".combobox__input"] = input;
  root._qmap[".combobox__arrow"] = arrow;
  root._qmap[".combobox__menu"] = menu;
  root._qmap[".combobox__list"] = list;
  menu._qmap[".combobox__list"] = list;
  input.parentElement = root;
  return { root, input, arrow, menu, list };
}
const cb = wireCombobox("country-combobox", "set-country");
const cbCity = wireCombobox("city-combobox", "set-city");

const documentEl = makeEl("document");
const activeElOwner = { active: null };
const documentObj = {
  readyState: "loading",
  getElementById: (id) => byId[id] || null,
  createElement: (tag) => makeEl(tag),
  addEventListener: (type, fn) => dispatch(documentEl, type) || documentEl.addEventListener(type, fn),
  querySelectorAll: (sel) => {
    if (sel === 'input[name="location_mode"]') return radios;
    if (sel === ".nav__item") return navItems;
    return [];
  },
  querySelector: (sel) => {
    if (sel === 'input[name="location_mode"]:checked') return radios.find((r) => r.checked) || null;
    return null;
  },
  get activeElement() { return activeElOwner.active; },
  set activeElement(v) { activeElOwner.active = v; },
};

const windowEl = makeEl("window");
windowEl.pywebview = {
  api: {
    get_state: () => stateOverride,
    get_cities: () => ({ ok: true, data: CITY_DB }),
    diag_report: () => ({ ok: true }),
  },
};
globalThis.window = windowEl;

globalThis.document = documentObj;
globalThis.location = { href: "file:///index.html", protocol: "file:" };
globalThis.navigator = { userAgent: "node" };
globalThis.fetch = () => Promise.reject(new Error("no network in tests"));

// offline bridge data
const CITY_DB = {
  EG: ["Cairo", "Alexandria", "Giza", "Asyut", "Luxor"],
  SA: ["Riyadh", "Jeddah", "Mecca", "Medina"],
};
let stateOverride = null;

// ---------- run the real app.js IIFE ----------
try {
  new Function(APP_JS)(); // executes the IIFE; init() fires on DOMContentLoaded
  check("F-load: app.js IIFE executed without error", true);
} catch (e) {
  check("F-load: app.js IIFE executed without error", false, e.message);
  process.exit(1);
}
// fire DOMContentLoaded -> init()
dispatch(documentEl, "DOMContentLoaded");
check("F-init: init() ran without error", byId["times-editor"] && byId["times-editor"]._children.length === 5,
  "time fields=" + (byId["times-editor"] ? byId["times-editor"]._children.length : 0));

(async () => {
  // ===== User test 7: country filtering =====
  dispatch(cb.input, "focus");
  check("F-7a: country list opens with all 196 countries",
    cb.list._children.length === 196, "count=" + cb.list._children.length);

  cb.input.value = "مصر";
  dispatch(cb.input, "input");
  await sleep(250);
  check("F-7b: typing Arabic 'مصر' filters to 1 country",
    cb.list._children.length === 1 && cb.list._children[0]._text.includes("مصر"),
    "items=" + cb.list._children.map((c) => c._text).join("|"));

  cb.input.value = "united";
  dispatch(cb.input, "input");
  await sleep(250);
  const united = cb.list._children.map((c) => c._text);
  check("F-7c: typing latin letters filters (United...)",
    united.length > 0 && united.every((t) => t.toLowerCase().includes("united")),
    "items=" + united.length);

  cb.input.value = "zzzz";
  dispatch(cb.input, "input");
  await sleep(250);
  check("F-7d: no-match shows empty state",
    cb.list._children.length === 1 && cb.list._children[0]._text === "لا توجد نتائج",
    cb.list._children[0]._text);

  // select Egypt from the list
  cb.input.value = "مصر";
  dispatch(cb.input, "input");
  await sleep(250);
  dispatch(cb.list._children[0], "mousedown", { preventDefault() {} });
  check("F-7e: selecting a country sets combobox value",
    cb.input.value === "مصر / Egypt", JSON.stringify(cb.input.value));
  check("F-7f: city input enabled after country choice", cbCity.input.disabled === false);

  // ===== User test 7: city filtering =====
  dispatch(cbCity.input, "focus");
  check("F-7g: city list opens with Egypt cities",
    cbCity.list._children.length === 5,
    "items=" + cbCity.list._children.map((c) => c._text).join("|"));
  cbCity.input.value = "alex";
  dispatch(cbCity.input, "input");
  await sleep(450);
  check("F-7h: typing letters filters cities",
    cbCity.list._children.length === 1 && cbCity.list._children[0]._text === "Alexandria",
    "items=" + cbCity.list._children.map((c) => c._text).join("|"));

  // ===== Fix C: fillSettings tolerates removed lat/long elements =====
  stateOverride = {
    ok: true, version: "1.2.7", prayers: [], next: null, enabled: false,
    announce: true, autostart: false, music: "", adhan: "", minutes: 15,
    method: "suspend", theme: "", location: "", location_mode: "manual",
    manual_city: "جدة", manual_country: "السعودية",
    manual_latitude: "", manual_longitude: "", paused: false, player_running: null,
  };
  activeElOwner.active = null;
  dispatch(globalThis.window, "pywebviewready"); // triggers refresh() -> applyState -> fillSettings
  await sleep(50);
  check("F-C: fillSettings ran with lat/long elements absent (no crash)",
    cb.input.value.includes("السعودية"), JSON.stringify(cb.input.value));

  // ===== Fix D: refresh must not clobber a field the user is typing in =====
  cb.input.value = "ال";
  activeElOwner.active = cb.input; // user is typing in the country field
  dispatch(globalThis.window, "pywebviewready"); // a later refresh tick
  await sleep(50);
  check("F-D1: typing in country NOT overwritten by refresh (guard active)",
    cb.input.value === "ال", JSON.stringify(cb.input.value));

  activeElOwner.active = null; // field blurred
  dispatch(globalThis.window, "pywebviewready");
  await sleep(50);
  check("F-D2: same refresh DOES update the field when not focused",
    cb.input.value.includes("السعودية"), JSON.stringify(cb.input.value));

  const failed = results.filter((r) => !r[1]).map((r) => r[0]);
  console.log("\n==== " + (results.length - failed.length) + "/" + results.length + " frontend checks passed ====");
  if (failed.length) { console.log("FAILED: " + failed.join(", ")); process.exit(1); }
  console.log("ALL FRONTEND CHECKS PASSED");
  process.exit(0);
})();
