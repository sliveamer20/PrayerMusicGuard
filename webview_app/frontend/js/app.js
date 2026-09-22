(function () {
  "use strict";

  var ORDER = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"];
var COUNTRIES = [
  {"name_en":"Afghanistan","name_ar":"أفغانستان","code":"AF"},
  {"name_en":"Albania","name_ar":"ألبانيا","code":"AL"},
  {"name_en":"Algeria","name_ar":"الجزائر","code":"DZ"},
  {"name_en":"Andorra","name_ar":"أندورا","code":"AD"},
  {"name_en":"Angola","name_ar":"أنغولا","code":"AO"},
  {"name_en":"Antigua and Barbuda","name_ar":"أنتيغوا وبربودا","code":"AG"},
  {"name_en":"Argentina","name_ar":"الأرجنتين","code":"AR"},
  {"name_en":"Armenia","name_ar":"أرمينيا","code":"AM"},
  {"name_en":"Australia","name_ar":"أستراليا","code":"AU"},
  {"name_en":"Austria","name_ar":"النمسا","code":"AT"},
  {"name_en":"Azerbaijan","name_ar":"أذربيجان","code":"AZ"},
  {"name_en":"Bahamas","name_ar":"الباهاماس","code":"BS"},
  {"name_en":"Bahrain","name_ar":"البحرين","code":"BH"},
  {"name_en":"Bangladesh","name_ar":"بنغلاديش","code":"BD"},
  {"name_en":"Barbados","name_ar":"بربادوس","code":"BB"},
  {"name_en":"Belarus","name_ar":"بيلاروسيا","code":"BY"},
  {"name_en":"Belgium","name_ar":"بلجيكا","code":"BE"},
  {"name_en":"Belize","name_ar":"بليز","code":"BZ"},
  {"name_en":"Benin","name_ar":"بنين","code":"BJ"},
  {"name_en":"Bhutan","name_ar":"بوتان","code":"BT"},
  {"name_en":"Bolivia","name_ar":"بوليفيا","code":"BO"},
  {"name_en":"Bosnia","name_ar":"البوسنة","code":"BA"},
  {"name_en":"Botswana","name_ar":"بوتسوانا","code":"BW"},
  {"name_en":"Brazil","name_ar":"البرازيل","code":"BR"},
  {"name_en":"Brunei","name_ar":"بروناي","code":"BN"},
  {"name_en":"Bulgaria","name_ar":"بلغاريا","code":"BG"},
  {"name_en":"Burkina Faso","name_ar":"بوركينا فاسو","code":"BF"},
  {"name_en":"Burundi","name_ar":"بوروندي","code":"BI"},
  {"name_en":"Cambodia","name_ar":"كمبوديا","code":"KH"},
  {"name_en":"Cameroon","name_ar":"الكاميرون","code":"CM"},
  {"name_en":"Canada","name_ar":"كندا","code":"CA"},
  {"name_en":"Cape Verde","name_ar":"الرأس الأخضر","code":"CV"},
  {"name_en":"Central African Republic","name_ar":"جمهورية أفريقيا الوسطى","code":"CF"},
  {"name_en":"Chad","name_ar":"تشاد","code":"TD"},
  {"name_en":"Chile","name_ar":"تشيلي","code":"CL"},
  {"name_en":"China","name_ar":"الصين","code":"CN"},
  {"name_en":"Colombia","name_ar":"كولومبيا","code":"CO"},
  {"name_en":"Comoros","name_ar":"جزر القمر","code":"KM"},
  {"name_en":"Congo","name_ar":"الكونغو","code":"CG"},
  {"name_en":"Democratic Republic of the Congo","name_ar":"جمهورية الكونغو الديمقراطية","code":"CD"},
  {"name_en":"Costa Rica","name_ar":"كوستاريكا","code":"CR"},
  {"name_en":"Côte d'Ivoire","name_ar":"ساحل العاج","code":"CI"},
  {"name_en":"Croatia","name_ar":"كرواتيا","code":"HR"},
  {"name_en":"Cuba","name_ar":"كوبا","code":"CU"},
  {"name_en":"Cyprus","name_ar":"قبرص","code":"CY"},
  {"name_en":"Czech Republic","name_ar":"الجمهورية التشيكية","code":"CZ"},
  {"name_en":"Denmark","name_ar":"الدنمارك","code":"DK"},
  {"name_en":"Djibouti","name_ar":"جيبوتي","code":"DJ"},
  {"name_en":"Dominica","name_ar":"دومينيكا","code":"DM"},
  {"name_en":"Dominican Republic","name_ar":"الجمهورية الدومينيكية","code":"DO"},
  {"name_en":"Ecuador","name_ar":"إكوادور","code":"EC"},
  {"name_en":"Egypt","name_ar":"مصر","code":"EG"},
  {"name_en":"El Salvador","name_ar":"السلفادور","code":"SV"},
  {"name_en":"Equatorial Guinea","name_ar":"غينيا الاستوائية","code":"GQ"},
  {"name_en":"Eritrea","name_ar":"إريتريا","code":"ER"},
  {"name_en":"Estonia","name_ar":"استونيا","code":"EE"},
  {"name_en":"Eswatini","name_ar":"إسواتيني","code":"SZ"},
  {"name_en":"Ethiopia","name_ar":"إثيوبيا","code":"ET"},
  {"name_en":"Fiji","name_ar":"فيجي","code":"FJ"},
  {"name_en":"Finland","name_ar":"فنلندا","code":"FI"},
  {"name_en":"France","name_ar":"فرنسا","code":"FR"},
  {"name_en":"Gabon","name_ar":"الغابون","code":"GA"},
  {"name_en":"Gambia","name_ar":"غامبيا","code":"GM"},
  {"name_en":"Georgia","name_ar":"جورجيا","code":"GE"},
  {"name_en":"Germany","name_ar":"ألمانيا","code":"DE"},
  {"name_en":"Ghana","name_ar":"غانا","code":"GH"},
  {"name_en":"Greece","name_ar":"اليونان","code":"GR"},
  {"name_en":"Grenada","name_ar":"غرينادا","code":"GD"},
  {"name_en":"Guatemala","name_ar":"غواتيمالا","code":"GT"},
  {"name_en":"Guinea","name_ar":"غينيا","code":"GN"},
  {"name_en":"Guinea-Bissau","name_ar":"غينيا بيساو","code":"GW"},
  {"name_en":"Guyana","name_ar":"غيانا","code":"GY"},
  {"name_en":"Haiti","name_ar":"هايتي","code":"HT"},
  {"name_en":"Honduras","name_ar":"هندوراس","code":"HN"},
  {"name_en":"Hungary","name_ar":"المجر","code":"HU"},
  {"name_en":"Iceland","name_ar":"أيسلندا","code":"IS"},
  {"name_en":"India","name_ar":"الهند","code":"IN"},
  {"name_en":"Indonesia","name_ar":"إندونيسيا","code":"ID"},
  {"name_en":"Iran","name_ar":"إيران","code":"IR"},
  {"name_en":"Iraq","name_ar":"العراق","code":"IQ"},
  {"name_en":"Ireland","name_ar":"أيرلندا","code":"IE"},
  {"name_en":"Israel","name_ar":"إسرائيل","code":"IL"},
  {"name_en":"Italy","name_ar":"إيطاليا","code":"IT"},
  {"name_en":"Jamaica","name_ar":"جامايكا","code":"JM"},
  {"name_en":"Japan","name_ar":"اليابان","code":"JP"},
  {"name_en":"Jordan","name_ar":"الأردن","code":"JO"},
  {"name_en":"Kazakhstan","name_ar":"كازاخستان","code":"KZ"},
  {"name_en":"Kenya","name_ar":"كينيا","code":"KE"},
  {"name_en":"Kiribati","name_ar":"كيريباتي","code":"KI"},
  {"name_en":"Kuwait","name_ar":"الكويت","code":"KW"},
  {"name_en":"Kyrgyzstan","name_ar":"قيرغيزستان","code":"KG"},
  {"name_en":"Laos","name_ar":"لاوس","code":"LA"},
  {"name_en":"Latvia","name_ar":"لاتفيا","code":"LV"},
  {"name_en":"Lebanon","name_ar":"لبنان","code":"LB"},
  {"name_en":"Lesotho","name_ar":"ليسوتو","code":"LS"},
  {"name_en":"Liberia","name_ar":"ليبيريا","code":"LR"},
  {"name_en":"Libya","name_ar":"ليبيا","code":"LY"},
  {"name_en":"Liechtenstein","name_ar":"ليختنشتاين","code":"LI"},
  {"name_en":"Lithuania","name_ar":"ليتوانيا","code":"LT"},
  {"name_en":"Luxembourg","name_ar":"لوكسمبورغ","code":"LU"},
  {"name_en":"Madagascar","name_ar":"مدغشقر","code":"MG"},
  {"name_en":"Malawi","name_ar":"ملاوي","code":"MW"},
  {"name_en":"Malaysia","name_ar":"ماليزيا","code":"MY"},
  {"name_en":"Maldives","name_ar":"جزر المالديف","code":"MV"},
  {"name_en":"Mali","name_ar":"مالي","code":"ML"},
  {"name_en":"Malta","name_ar":"مالطا","code":"MT"},
  {"name_en":"Marshall Islands","name_ar":"جزر مارشال","code":"MH"},
  {"name_en":"Mauritania","name_ar":"موريتانيا","code":"MR"},
  {"name_en":"Mauritius","name_ar":"موريشيوس","code":"MU"},
  {"name_en":"Mexico","name_ar":"المكسيك","code":"MX"},
  {"name_en":"Micronesia","name_ar":"ميكرونيسيا","code":"FM"},
  {"name_en":"Moldova","name_ar":"مولدوفا","code":"MD"},
  {"name_en":"Monaco","name_ar":"موناكو","code":"MC"},
  {"name_en":"Mongolia","name_ar":"منغوليا","code":"MN"},
  {"name_en":"Montenegro","name_ar":"الجبل الأسود","code":"ME"},
  {"name_en":"Morocco","name_ar":"المغرب","code":"MA"},
  {"name_en":"Mozambique","name_ar":"موزمبيق","code":"MZ"},
  {"name_en":"Myanmar","name_ar":"ميانمار","code":"MM"},
  {"name_en":"Namibia","name_ar":"ناميبيا","code":"NA"},
  {"name_en":"Nauru","name_ar":"ناورو","code":"NR"},
  {"name_en":"Nepal","name_ar":"النيبال","code":"NP"},
  {"name_en":"Netherlands","name_ar":"هولندا","code":"NL"},
  {"name_en":"New Zealand","name_ar":"نيوزيلندا","code":"NZ"},
  {"name_en":"Nicaragua","name_ar":"نيكاراغوا","code":"NI"},
  {"name_en":"Niger","name_ar":"النيجر","code":"NE"},
  {"name_en":"Nigeria","name_ar":"نيجيريا","code":"NG"},
  {"name_en":"North Korea","name_ar":"كوريا الشمالية","code":"KP"},
  {"name_en":"North Macedonia","name_ar":"مقدونيا الشمالية","code":"MK"},
  {"name_en":"Norway","name_ar":"النرويج","code":"NO"},
  {"name_en":"Oman","name_ar":"عمان","code":"OM"},
  {"name_en":"Pakistan","name_ar":"باكستان","code":"PK"},
  {"name_en":"Palau","name_ar":"بالاو","code":"PW"},
  {"name_en":"Palestine","name_ar":"فلسطين","code":"PS"},
  {"name_en":"Panama","name_ar":"بنما","code":"PA"},
  {"name_en":"Papua New Guinea","name_ar":"بابوا غينيا الجديدة","code":"PG"},
  {"name_en":"Paraguay","name_ar":"باراغواي","code":"PY"},
  {"name_en":"Peru","name_ar":"بيرو","code":"PE"},
  {"name_en":"Philippines","name_ar":"الفلبين","code":"PH"},
  {"name_en":"Poland","name_ar":"بولندا","code":"PL"},
  {"name_en":"Portugal","name_ar":"البرتغال","code":"PT"},
  {"name_en":"Qatar","name_ar":"قطر","code":"QA"},
  {"name_en":"Romania","name_ar":"رومانيا","code":"RO"},
  {"name_en":"Russia","name_ar":"روسيا","code":"RU"},
  {"name_en":"Rwanda","name_ar":"رواندا","code":"RW"},
  {"name_en":"Saint Kitts","name_ar":"سانت كيتس","code":"KN"},
  {"name_en":"Saint Lucia","name_ar":"سانت لوسيا","code":"LC"},
  {"name_en":"Saint Vincent","name_ar":"سانت فنسنت","code":"VC"},
  {"name_en":"Samoa","name_ar":"ساموا","code":"WS"},
  {"name_en":"San Marino","name_ar":"سان مارينو","code":"SM"},
  {"name_en":"São Tomé","name_ar":"سان تومي","code":"ST"},
  {"name_en":"Saudi Arabia","name_ar":"السعودية","code":"SA"},
  {"name_en":"Senegal","name_ar":"السنغال","code":"SN"},
  {"name_en":"Serbia","name_ar":"صربيا","code":"RS"},
  {"name_en":"Seychelles","name_ar":"سيشل","code":"SC"},
  {"name_en":"Sierra Leone","name_ar":"سيراليون","code":"SL"},
  {"name_en":"Singapore","name_ar":"سنغافورة","code":"SG"},
  {"name_en":"Slovakia","name_ar":"سلوفاكيا","code":"SK"},
  {"name_en":"Slovenia","name_ar":"سلوفينيا","code":"SI"},
  {"name_en":"Solomon Islands","name_ar":"جزر سليمان","code":"SB"},
  {"name_en":"Somalia","name_ar":"الصومال","code":"SO"},
  {"name_en":"South Africa","name_ar":"جنوب أفريقيا","code":"ZA"},
  {"name_en":"South Korea","name_ar":"كوريا الجنوبية","code":"KR"},
  {"name_en":"South Sudan","name_ar":"جنوب السودان","code":"SS"},
  {"name_en":"Spain","name_ar":"إسبانيا","code":"ES"},
  {"name_en":"Sri Lanka","name_ar":"سريلانكا","code":"LK"},
  {"name_en":"Sudan","name_ar":"السودان","code":"SD"},
  {"name_en":"Suriname","name_ar":"سورينام","code":"SR"},
  {"name_en":"Sweden","name_ar":"السويد","code":"SE"},
  {"name_en":"Switzerland","name_ar":"سويسرا","code":"CH"},
  {"name_en":"Syria","name_ar":"سوريا","code":"SY"},
  {"name_en":"Taiwan","name_ar":"تايوان","code":"TW"},
  {"name_en":"Tajikistan","name_ar":"طاجيكستان","code":"TJ"},
  {"name_en":"Tanzania","name_ar":"تنزانيا","code":"TZ"},
  {"name_en":"Thailand","name_ar":"تايلاند","code":"TH"},
  {"name_en":"Timor-Leste","name_ar":"تيمور الشرقية","code":"TL"},
  {"name_en":"Togo","name_ar":"توغو","code":"TG"},
  {"name_en":"Tonga","name_ar":"تونغا","code":"TO"},
  {"name_en":"Trinidad","name_ar":"ترينيداد","code":"TT"},
  {"name_en":"Tunisia","name_ar":"تونس","code":"TN"},
  {"name_en":"Turkey","name_ar":"تركيا","code":"TR"},
  {"name_en":"Turkmenistan","name_ar":"تركمانستان","code":"TM"},
  {"name_en":"Tuvalu","name_ar":"توفالو","code":"TV"},
  {"name_en":"Uganda","name_ar":"أوغندا","code":"UG"},
  {"name_en":"Ukraine","name_ar":"أوكرانيا","code":"UA"},
  {"name_en":"United Arab Emirates","name_ar":"الإمارات العربية المتحدة","code":"AE"},
  {"name_en":"United Kingdom","name_ar":"المملكة المتحدة","code":"GB"},
  {"name_en":"United States","name_ar":"الولايات المتحدة","code":"US"},
  {"name_en":"Uruguay","name_ar":"أوروغواي","code":"UY"},
  {"name_en":"Uzbekistan","name_ar":"أوزبكستان","code":"UZ"},
  {"name_en":"Vanuatu","name_ar":"فانواتو","code":"VU"},
  {"name_en":"Vatican City","name_ar":"الفاتيكان","code":"VA"},
  {"name_en":"Venezuela","name_ar":"فنزويلا","code":"VE"},
  {"name_en":"Vietnam","name_ar":"فيتنام","code":"VN"},
  {"name_en":"Yemen","name_ar":"اليمن","code":"YE"},
  {"name_en":"Zambia","name_ar":"زامبيا","code":"ZM"},
  {"name_en":"Zimbabwe","name_ar":"زيمبابوي","code":"ZW"}
];

  var NAMES = {
    Fajr: "الفجر",
    Dhuhr: "الظهر",
    Asr: "العصر",
    Maghrib: "المغرب",
    Isha: "العشاء"
  };
  var PAGE_META = {
    dashboard: ["لوحة القيادة", "نظرة سريعة على الصلاة القادمة وحالة المراقبة."],
    times: ["المواقيت", "مواقيت الصلاة وحساب الموقع."],
    music: ["المشغّل", "اختيار مشغّل الموسيقى وطريقة الإيقاف."],
    settings: ["الإعدادات", "المراقبة والتشغيل التلقائي والمظهر."]
  };
  var CITIES_DB = {};
  var citiesLoaded = false;
var RING_CIRCUMFERENCE = 2 * Math.PI * 88;

var countryCode = "";
var selectedCountry = "";
var state = null;
  var remaining = 0;
  var ringSpan = 24 * 60;
  var syncingTheme = false;
  var resumeTarget = null;
  var resumeRemaining = 0;

  function bridge() {
    return window.pywebview && window.pywebview.api ? window.pywebview.api : null;
  }

  function loadCitiesDB() {
    return call("get_cities").then(function (res) {
      if (res && res.ok && res.data) {
        CITIES_DB = res.data;
        citiesLoaded = true;
      }
    }).catch(function () {});
  }

  function preloadCitiesForCountry(code) {
    if (!code || citiesLoaded) return;
    call("get_cities", code).then(function (res) {
      if (res && res.ok && res.cities) {
        CITIES_DB[code] = res.cities;
      }
    }).catch(function () {});
  }


  function initLocationUI() {
    var locationModeRadios = document.querySelectorAll('input[name="location_mode"]');
    var countryCombobox = $("country-combobox");
    var cityCombobox = $("city-combobox");
    var countryInput = countryCombobox ? countryCombobox.querySelector(".combobox__input") : null;
    var countryArrow = countryCombobox ? countryCombobox.querySelector(".combobox__arrow") : null;
    var countryMenu = countryCombobox ? countryCombobox.querySelector(".combobox__menu") : null;
    var countryList = countryCombobox ? countryCombobox.querySelector(".combobox__list") : null;
    var cityInput = cityCombobox ? cityCombobox.querySelector(".combobox__input") : null;
    var cityArrow = cityCombobox ? cityCombobox.querySelector(".combobox__arrow") : null;
    var cityMenu = cityCombobox ? cityCombobox.querySelector(".combobox__menu") : null;
    var cityList = cityCombobox ? cityCombobox.querySelector(".combobox__list") : null;
    var manualFields = $("manual-fields");

    function debounce(fn, delay) {
      var timer;
      return function () {
        var args = arguments;
        var ctx = this;
        clearTimeout(timer);
        timer = setTimeout(function () { fn.apply(ctx, args); }, delay);
      };
    }

    function fetchJSON(url) {
      return fetch(url, { headers: { "User-Agent": "PrayerMusicGuard/1.2" } }).then(function (res) {
        if (!res.ok) throw new Error("HTTP " + res.status);
        return res.json();
      });
    }

    function closeAll() {
      if (countryMenu) countryMenu.classList.add("is-hidden");
      if (cityMenu) cityMenu.classList.add("is-hidden");
    }

    function renderList(ul, items) {
      if (!ul) return;
      ul.innerHTML = "";
      if (!items || items.length === 0) {
        var li = document.createElement("li");
        li.textContent = "لا توجد نتائج";
        li.style.opacity = "0.6";
        ul.appendChild(li);
        return;
      }
      items.forEach(function (item) {
        var li = document.createElement("li");
        li.textContent = item.label || item;
        li.addEventListener("mousedown", function (e) {
          e.preventDefault();
          item.__select && item.__select();
        });
        ul.appendChild(li);
      });
    }

    function updateResolved() {
      var resolved = $("location-resolved");
      var c = countryInput ? countryInput.value.trim() : "";
      var ci = cityInput ? cityInput.value.trim() : "";
      if (resolved) {
        if (c && ci) {
          resolved.textContent = "الموقع المحدد: " + ci + ", " + c;
          resolved.style.display = "block";
        } else {
          resolved.style.display = "none";
        }
      }
    }

    function showManualFields() {
      if (manualFields) manualFields.style.display = "block";
    }
    function hideManualFields() {
      if (manualFields) manualFields.style.display = "none";
      closeAll();
    }

    function renderCountryList(q) {
      var items = [];
      var query = q ? q.toLowerCase() : "";
      COUNTRIES.forEach(function (c) {
        var label = c.name_ar + " / " + c.name_en;
        if (!query || c.name_ar.toLowerCase().includes(query) || c.name_en.toLowerCase().includes(query) || c.code.toLowerCase().includes(query)) {
          items.push({ label: label, code: c.code, nameAr: c.name_ar, __select: function () {
            countryInput.value = c.name_ar + " / " + c.name_en;
            countryCode = c.code;
            selectedCountry = c.name_ar;
            if (cityInput) cityInput.value = "";
            if (cityArrow) cityArrow.disabled = false;
            if (cityInput) cityInput.disabled = false;
            cityInput.placeholder = "اختر المدينة";
            closeAll();
            updateResolved();
            preloadCitiesForCountry(c.code);
          }});
        }
      });
      renderList(countryList, items);
    }

    function getCitiesForCountry(code) {
      if (!code) return [];
      return CITIES_DB[code] || [];
    }

    function renderCityList(cities) {
      var items = [];
      if (cities && cities.length > 0) {
        cities.forEach(function (city) {
          items.push({ label: city, __select: function () {
            cityInput.value = city;
            closeAll();
            updateResolved();
          }});
        });
      } else {
        items.push({ label: "لا توجد مدن" });
      }
      renderList(cityList, items);
    }

    // Country combobox with static list
    if (countryCombobox && countryInput && countryArrow && countryMenu) {
      function openCountry() {
        closeAll();
        countryMenu.classList.remove("is-hidden");
        renderCountryList(countryInput.value.trim());
      }
      function closeCountry() {
        countryMenu.classList.add("is-hidden");
      }
      countryArrow.addEventListener("click", function (e) {
        e.stopPropagation();
        if (countryMenu.classList.contains("is-hidden")) openCountry(); else closeCountry();
      });
      countryInput.addEventListener("focus", openCountry);
      countryInput.addEventListener("input", debounce(function () {
        renderCountryList(countryInput.value.trim());
      }, 150));
    }

    // City combobox with dynamic city data from backend (cities.json)
    if (cityCombobox && cityInput && cityArrow && cityMenu) {
      function openCity() {
        if (!selectedCountry || !countryCode) return;
        closeAll();
        var cities = getCitiesForCountry(countryCode);
        if (cities.length > 0) {
          cityMenu.classList.remove("is-hidden");
          renderCityList(cities);
        } else {
          renderList(cityList, [{ label: "لا توجد مدن محلية — اكتب اسم المدينة للبحث", __select: function() {
            cityInput.focus();
            cityMenu.classList.add("is-hidden");
          }}]);
          cityMenu.classList.remove("is-hidden");
        }
      }
      function closeCity() {
        cityMenu.classList.add("is-hidden");
      }
      cityArrow.addEventListener("click", function (e) {
        e.stopPropagation();
        if (cityInput.disabled) return;
        if (cityMenu.classList.contains("is-hidden")) openCity(); else closeCity();
      });
      cityInput.addEventListener("focus", function () {
        if (!selectedCountry) return;
        openCity();
      });
      cityInput.addEventListener("input", debounce(function () {
        var q = cityInput.value.trim().toLowerCase();
        if (!q || !countryCode) {
          var cities = getCitiesForCountry(countryCode);
          renderCityList(cities);
          if (!cityMenu.classList.contains("is-hidden")) return;
          return;
        }
        var cities = getCitiesForCountry(countryCode);
        var filtered = cities.filter(function (c) { return c.toLowerCase().includes(q); });
        if (filtered.length > 0) {
          renderCityList(filtered);
          if (cityMenu.classList.contains("is-hidden")) {
            cityMenu.classList.remove("is-hidden");
          }
        } else {
          var url = "https://nominatim.openstreetmap.org/search?q=" + encodeURIComponent(q) + "&countrycodes=" + encodeURIComponent(countryCode) + "&format=json&limit=10&addressdetails=1";
          fetchJSON(url).then(function (results) {
            var items = results.map(function (r) {
              return { label: r.display_name.split(",")[0], __select: function () {
                cityInput.value = r.display_name.split(",")[0];
                closeAll();
                updateResolved();
              }};
            });
            renderList(cityList, items);
            if (cityMenu.classList.contains("is-hidden")) cityMenu.classList.remove("is-hidden");
          }).catch(function () { renderList(cityList, []); });
        }
      }, 300));
    }

    document.addEventListener("click", closeAll);

    Array.prototype.forEach.call(locationModeRadios, function (radio) {
      radio.addEventListener("change", function () {
        if (this.value === "manual") {
          showManualFields();
        } else {
          hideManualFields();
        }
        try { saveSettings("location-status"); } catch(e) {}
      });
    });

    var currentMode = document.querySelector('input[name="location_mode"]:checked');
    if (currentMode && currentMode.value === "manual") {
      showManualFields();
    } else {
      hideManualFields();
    }
    if (cityInput) cityInput.disabled = true;
    if (cityArrow) cityArrow.disabled = true;
  }




  // --- TEMPORARY DIAGNOSTICS (Phase 6): report bridge state to Python so the
  // frozen EXE can be verified externally. Does not change behavior. ---
  function diagWrite(obj) {
    try {
      var el = document.getElementById("bridge-diag");
      if (el) {
        el.textContent = JSON.stringify(obj);
      }
    } catch (e) { /* ignore */ }
    var api = bridge();
    if (api && typeof api.diag_report === "function") {
      try {
        api.diag_report(obj);
      } catch (e2) { /* ignore */ }
    }
  }

  function diagSnapshot(tag) {
    return {
      tag: tag,
      url: location.href,
      protocol: location.protocol,
      pywebview: typeof window.pywebview,
      api: typeof (window.pywebview && window.pywebview.api),
      apiKeys: window.pywebview && window.pywebview.api ? Object.keys(window.pywebview.api) : [],
      readyState: document.readyState
    };
  }
  // --- end diagnostics ---

  function call(name) {
    var args = Array.prototype.slice.call(arguments, 1);
    var api = bridge();
    if (!api || typeof api[name] !== "function") {
      diagWrite({ call: name, result: "bridge_unavailable", hasApi: !!api, apiKeys: api ? Object.keys(api) : [] });
      return Promise.resolve({ ok: false, error: "bridge unavailable" });
    }
    try {
      return Promise.resolve(api[name].apply(api, args));
    } catch (err) {
      diagWrite({ call: name, result: "throw", error: String(err) });
      return Promise.resolve({ ok: false, error: String(err) });
    }
  }

  function whenReady() {
    return new Promise(function (resolve) {
      if (bridge()) {
        resolve(true);
        return;
      }
      var done = false;
      function finish(value) {
        if (done) {
          return;
        }
        done = true;
        resolve(value);
      }
      window.addEventListener("pywebviewready", function () {
        finish(true);
      }, { once: true });
      setTimeout(function () {
        finish(!!bridge());
      }, 8000);
    });
  }

  function $(id) {
    return document.getElementById(id);
  }

  function setText(id, value) {
    var el = $(id);
    if (el) {
      el.textContent = value;
    }
  }

  // Visible, categorized status feedback. Types: success | warning | error | info.
  function setStatus(id, message, type) {
    var el = $(id);
    if (!el) {
      return;
    }
    el.textContent = message || "";
    el.classList.remove("is-success", "is-warning", "is-error", "is-info");
    if (type === "success" || type === "warning" || type === "error" || type === "info") {
      el.classList.add("is-" + type);
    }
  }

  // Classify pause/resume errors: a missing/not-running player is a warning,
  // everything else is an error.
  function playerError(res) {
    var msg = String((res && res.error) || "").trim();
    if (!msg) {
      return { type: "error", text: "خطأ غير معروف" };
    }
    if (
      msg.indexOf("نافذة المشغّل") !== -1 ||
      msg.indexOf("مشغّل موسيقى") !== -1 ||
      msg.indexOf("اختيار مشغّل") !== -1
    ) {
      return {
        type: "warning",
        text: "المشغّل غير مفتوح حاليًا أو لم يُحدَّد؛ شغّله ثم أعد المحاولة."
      };
    }
    return { type: "error", text: msg };
  }

  function pad(n) {
    return (n < 10 ? "0" : "") + n;
  }

  function shortenPath(path) {
    if (!path) return "";
    // Get the filename from the path
    var fileName = path.split('\\').pop();
    // Remove .exe extension (case-insensitive)
    fileName = fileName.replace(/\.exe$/i, "");
    // Replace dots, underscores, and hyphens with spaces
    var shortName = fileName.replace(/[._\-]/g, " ");
    // Collapse multiple spaces and trim
    shortName = shortName.replace(/\s+/g, " ").trim();
    // Truncate to 30 characters if too long
    if (shortName.length > 30) {
      shortName = shortName.substring(0, 30).trim();
    }
    return shortName;
  }

  function formatRemaining(seconds) {
    var s = Math.max(0, Math.floor(seconds));
    return pad(Math.floor(s / 3600)) + ":" + pad(Math.floor((s % 3600) / 60)) + ":" + pad(s % 60);
  }

  function formatTime12(time24) {
    if (!time24) return "";
    var parts = String(time24).split(":");
    if (parts.length !== 2) return time24;
    var h = parseInt(parts[0], 10);
    var m = parseInt(parts[1], 10);
    if (isNaN(h) || isNaN(m)) return time24;
    var period = h >= 12 ? "م" : "ص";
    var h12 = h % 12;
    if (h12 === 0) h12 = 12;
    return pad(h12) + ":" + pad(m) + " " + period;
  }

  function parseTime12(time12) {
    if (!time12) return null;
    var s = String(time12).trim().replace(/\s+/g, " ");
    // Accept "HH:MM ص" or "HH:MMص" or "H:M م"
    var m = s.match(/^(\d{1,2}):(\d{2})\s*([صم])$/);
    if (!m) {
      // Try without space
      m = s.match(/^(\d{1,2}):(\d{2})([صم])$/);
    }
    if (!m) return null;
    var h = parseInt(m[1], 10);
    var min = parseInt(m[2], 10);
    var period = m[3];
    if (isNaN(h) || isNaN(min)) return null;
    if (h < 1 || h > 12) return null;
    if (min < 0 || min > 59) return null;
    if (period === "ص") {
      if (h === 12) h = 0;
    } else if (period === "م") {
      if (h !== 12) h += 12;
    } else {
      return null;
    }
    return pad(h) + ":" + pad(min);
  }

  function formatResumeRemaining(seconds) {
    var s = Math.max(0, Math.floor(seconds));
    if (s >= 3600) {
      var h = Math.floor(s / 3600);
      var m = Math.floor((s % 3600) / 60);
      return "متبقي للاستئناف: " + h + " ساعة " + m + " دقيقة";
    } else if (s >= 60) {
      var m = Math.floor(s / 60);
      var sec = s % 60;
      return "متبقي للاستئناف: " + pad(m) + ":" + pad(sec);
    } else if (s > 0) {
      return "متبقي للاستئناف: " + s + " ثانية";
    }
    return "";
  }

  function updateResumeCountdown() {
    var el = $("resume-countdown");
    if (!el) return;
    var paused = state && state.paused;
    var noTarget = !resumeTarget || isNaN(resumeTarget.getTime());
    if (!paused || noTarget) {
      el.style.display = "none";
      el.textContent = "";
      resumeRemaining = 0;
      resumeTarget = null;
      return;
    }
    resumeRemaining = Math.max(0, Math.floor((resumeTarget.getTime() - Date.now()) / 1000));
    if (resumeRemaining <= 0) {
      el.style.display = "none";
      el.textContent = "";
      resumeTarget = null;
      return;
    }
    var text = "";
    if (resumeRemaining >= 3600) {
      var h = Math.floor(resumeRemaining / 3600);
      var m = Math.floor((resumeRemaining % 3600) / 60);
      text = "⏱ متبقي للاستئناف: " + h + " ساعة " + m + " د";
    } else if (resumeRemaining >= 60) {
      var m = Math.floor(resumeRemaining / 60);
      var s = resumeRemaining % 60;
      text = "⏱ متبقي للاستئناف: " + pad(m) + ":" + pad(s);
    } else {
      text = "⏱ متبقي للاستئناف: " + resumeRemaining + " ث";
    }
    el.textContent = text;
    el.style.display = "inline-block";
  }

  function minutesOf(text) {
    if (!text) {
      return null;
    }
    var parts = String(text).split(":");
    if (parts.length !== 2) {
      return null;
    }
    var h = parseInt(parts[0], 10);
    var m = parseInt(parts[1], 10);
    if (isNaN(h) || isNaN(m)) {
      return null;
    }
    return h * 60 + m;
  }

  function buildTimesEditor() {
    var host = $("times-editor");
    if (!host) {
      return;
    }
    host.innerHTML = "";
    ORDER.forEach(function (key) {
      var label = document.createElement("label");
      label.className = "field";
      var span = document.createElement("span");
      span.className = "field__label";
      span.textContent = NAMES[key];
      var input = document.createElement("input");
      input.className = "field__input";
      input.type = "text";
      input.id = "time-" + key;
      input.placeholder = "HH:MM ص/م";
      input.dir = "ltr";
      label.appendChild(span);
      label.appendChild(input);
      host.appendChild(label);
    });
  }

  function renderPrayers(data) {
    var grid = $("prayer-grid");
    if (!grid) {
      return;
    }
    var prayers = (data && data.prayers) || [];
    grid.innerHTML = "";
    prayers.forEach(function (prayer) {
      var card = document.createElement("div");
      card.className = "prayer-card";
      if (prayer.is_next) {
        card.className += " prayer-card--next";
      }
      if (prayer.is_current) {
        card.className += " prayer-card--current";
      }
      card.setAttribute("data-prayer", prayer.key);

      var name = document.createElement("span");
      name.className = "prayer-card__name";
      name.textContent = prayer.name;

      var time = document.createElement("span");
      time.className = "prayer-card__time";
      time.textContent = prayer.display || "--:--";

      var tag = document.createElement("span");
      tag.className = "prayer-card__tag";
      if (prayer.is_next) {
        tag.textContent = "القادمة";
      } else if (prayer.is_current) {
        tag.textContent = "الحالية";
      }

      card.appendChild(name);
      card.appendChild(time);
      card.appendChild(tag);
      grid.appendChild(card);
    });
  }

  function computeSpan(data) {
    var next = (data && data.next) || null;
    if (!next) {
      return 24 * 60;
    }
    var target = minutesOf(next.time);
    if (target === null) {
      return 24 * 60;
    }
    var values = [];
    ORDER.forEach(function (key) {
      var prayer = (data.prayers || []).filter(function (p) {
        return p.key === key;
      })[0];
      var m = prayer ? minutesOf(prayer.time) : null;
      if (m !== null) {
        values.push(m);
      }
    });
    if (!values.length) {
      return 24 * 60;
    }
    values.sort(function (a, b) {
      return a - b;
    });
    var now = new Date();
    var nowMin = now.getHours() * 60 + now.getMinutes();
    var earlier = values.filter(function (m) {
      return m < target;
    });
    var upcoming = values.filter(function (m) {
      return m > nowMin;
    });
    var span;
    if (earlier.length && upcoming.length) {
      span = target - earlier[earlier.length - 1];
    } else if (earlier.length) {
      span = 24 * 60 - earlier[earlier.length - 1] + target;
    } else {
      span = 24 * 60;
    }
    return span > 0 ? span : 24 * 60;
  }

  function drawRing() {
    var circle = $("ring-progress");
    if (!circle) {
      return;
    }
    var fraction = 1;
    if (ringSpan > 0) {
      fraction = (ringSpan - remaining / 60) / ringSpan;
    }
    fraction = Math.max(0, Math.min(1, fraction));
    circle.style.strokeDashoffset = String(RING_CIRCUMFERENCE * (1 - fraction));
  }

  function renderNext(data) {
    var next = (data && data.next) || null;
    if (!next) {
      setText("next-prayer-name", "—");
      setText("next-prayer-time", "--:--");
      setText("next-prayer-countdown", "00:00:00");
      remaining = 0;
      drawRing();
      return;
    }
    setText("next-prayer-name", next.tomorrow ? next.name + " (غدًا)" : next.name);
    setText("next-prayer-time", next.display || "--:--");
    remaining = Number(next.remaining_seconds) || 0;
    ringSpan = computeSpan(data);
    setText("next-prayer-countdown", formatRemaining(remaining));
    drawRing();
  }

  function renderStatus(data) {
    var chip = $("monitor-chip");
    if (chip) {
      var on = !!(data && data.enabled);
      var ICON_ON = '<span class="chip__icon" aria-hidden="true"><svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10" /><path d="m9 12 2 2 4-4" /></svg></span>';
      var ICON_OFF = '<span class="chip__icon" aria-hidden="true"><svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m2 2 20 20" /><path d="M8.35 2.69A10 10 0 0 1 21.3 15.65" /><path d="M19.08 19.08A10 10 0 1 1 4.92 4.92" /></svg></span>';
      chip.innerHTML = (on ? ICON_ON : ICON_OFF) + '<span class="chip__text">' + (on ? "المراقبة تعمل" : "المراقبة متوقفة") + "</span>";
      chip.className = "chip " + (on ? "chip--on" : "chip--off");
    }
    setText("app-version", data && data.version ? data.version : "—");
    var location = data && data.location ? data.location : "—";
    setText("location-line", data && data.location ? "الموقع: " + data.location : "");
    setText("times-location", location);

    // Set player-line with shortened display name and tooltip with full path
    var playerEl = $("player-line");
    if (playerEl) {
      var fullPath = data && data.music ? data.music : "";
      var shortName = shortenPath(fullPath);
      playerEl.textContent = shortName || "لم يتم الاختيار";
      if (fullPath) {
        playerEl.setAttribute("title", fullPath);
      } else {
        playerEl.removeAttribute("title");
      }
    }

    var statusText = "—";
    if (data && data.music) {
      if (data.player_running === true) {
        statusText = "قيد التشغيل الآن";
      } else if (data.player_running === false) {
        statusText = "غير مفتوح حاليًا";
      }
    }
    setText("player-status-line", statusText);
    setText("pause-state", data && data.paused ? "متوقفة مؤقتًا" : "تعمل");

    // Dashboard-level hints: Monitoring OFF and/or player not running.
    var hint = $("dashboard-status");
    if (hint) {
      var enabled = !!(data && data.enabled);
      if (!enabled) {
        setStatus("dashboard-status", "المراقبة متوقفة. فعّلها من صفحة الإعدادات لتفعيل الحماية عند الصلاة.", "warning");
      } else if (data && data.music && data.player_running === false) {
        setStatus("dashboard-status", "المشغّل المحدد (" + shortenPath(data.music) + ") غير مفتوح حاليًا؛ شغّله لتفعيل الإيقاف.", "warning");
      } else {
        setStatus("dashboard-status", "", null);
      }
    }
  }

  function fillSettings(data) {
    if (!data) {
      return;
    }
    var pairs = [
      ["set-music", data.music || ""],
      ["set-adhan", data.adhan || ""],
      ["set-minutes", data.minutes || 15],
      ["set-city", data.manual_city || ""],
      ["set-country", data.manual_country || ""],
      ["set-latitude", data.manual_latitude || ""],
      ["set-longitude", data.manual_longitude || ""]
    ];
    pairs.forEach(function (pair) {
      var el = $(pair[0]);
      if (el && document.activeElement !== el) {
        el.value = pair[1];
      }
    });
    var radios = document.querySelectorAll('input[name="method"]');
    Array.prototype.forEach.call(radios, function (radio) {
      radio.checked = radio.value === (data.method || "suspend");
    });
    var modeRadios = document.querySelectorAll('input[name="location_mode"]');
    Array.prototype.forEach.call(modeRadios, function (radio) {
      radio.checked = radio.value === (data.location_mode || "auto");
    });
    if (data.location_mode === "manual") {
      var mf = $("manual-fields");
      if (mf) mf.style.display = "block";
      var rawCountry = data.manual_country || "";
      var countryName = extractCountryName(rawCountry);
      var cityName = data.manual_city || "";
      var countryInput = $("set-country");
      var cityInput = $("set-city");
      if (countryInput && document.activeElement !== countryInput) countryInput.value = countryName ? (countryName + " / " + (COUNTRIES.find(function(c){return c.name_ar === countryName}) || {}).name_en || countryName) : rawCountry;
      if (cityInput && document.activeElement !== cityInput) cityInput.value = cityName;
      var foundCode = "";
      var foundArabic = "";
      for (var i = 0; i < COUNTRIES.length; i++) {
        if (COUNTRIES[i].name_ar === countryName || countryName.indexOf(COUNTRIES[i].name_ar) !== -1) {
          foundCode = COUNTRIES[i].code;
          foundArabic = COUNTRIES[i].name_ar;
          break;
        }
      }
      countryCode = foundCode;
      selectedCountry = foundArabic || countryName;
      if (cityInput) cityInput.disabled = !foundCode;
      var cityArrow = cityInput ? cityInput.parentElement.querySelector(".combobox__arrow") : null;
      if (cityArrow) cityArrow.disabled = !foundCode;
      if (foundCode) preloadCitiesForCountry(foundCode);
    } else {
      var mf = $("manual-fields");
      if (mf) mf.style.display = "none";
    }
    ["enabled", "announce", "autostart"].forEach(function (flag) {
      var box = $("set-" + flag);
      if (box) {
        box.checked = !!data[flag];
      }
    });
    ORDER.forEach(function (key) {
      var input = $("time-" + key);
      var prayer = (data.prayers || []).filter(function (p) {
        return p.key === key;
      })[0];
      if (input && prayer && document.activeElement !== input) {
        var display = formatTime12(prayer.time || "");
        input.value = display || "";
      }
    });
  }

  function syncTheme(data) {
    if (!data || (data.theme !== "dark" && data.theme !== "light")) {
      return;
    }
    if (window.pmgTheme && window.pmgTheme.get() !== data.theme) {
      syncingTheme = true;
      window.pmgTheme.set(data.theme);
      syncingTheme = false;
    }
  }

  function applyState(data) {
    state = data;
    // Update resume countdown target
    if (data && data.resume_at) {
      try {
        resumeTarget = new Date(data.resume_at);
      } catch (e) {
        resumeTarget = null;
      }
      resumeRemaining = Math.max(0, Math.floor((resumeTarget.getTime() - Date.now()) / 1000));
    } else {
      resumeTarget = null;
      resumeRemaining = 0;
    }
    updateResumeCountdown();
    renderPrayers(data);
    renderNext(data);
    renderStatus(data);
    fillSettings(data);
    syncTheme(data);
  }

  function refresh() {
    return call("get_state").then(function (res) {
      if (res && res.ok) {
        diagWrite({ call: "get_state", result: "ok", prayers: (res.prayers || []).length, next: res.next ? res.next.name : null, music: res.music, enabled: res.enabled });
        applyState(res);
      } else {
        diagWrite({ call: "get_state", result: "fail", error: (res && res.error) || "unknown" });
        setStatus("settings-status", "تعذر الاتصال بالخادم: " + ((res && res.error) || "غير متاح"), "error");
      }
      return res;
    });
  }

  function collectTimes() {
    var times = {};
    ORDER.forEach(function (key) {
      var input = $("time-" + key);
      if (input) {
        var raw = input.value.trim();
        if (raw) {
          var parsed = parseTime12(raw);
          // Fallback: if parse fails, try raw as HH:MM 24h
          if (!parsed) {
            var m = raw.match(/^(\d{1,2}):(\d{2})$/);
            if (m) {
              parsed = pad(parseInt(m[1],10)) + ":" + pad(parseInt(m[2],10));
            }
          }
          if (parsed) {
            times[key] = parsed;
          }
        }
      }
    });
    return times;
  }

function extractCountryName(comboboxValue) {
    if (!comboboxValue) return "";
    var parts = comboboxValue.split(" / ");
    return parts[0].trim();
  }

  function collectCommon() {
    var method = document.querySelector('input[name="method"]:checked');
    var mode = document.querySelector('input[name="location_mode"]:checked');
    return {
      music: $("set-music") ? $("set-music").value.trim() : "",
      adhan: $("set-adhan") ? $("set-adhan").value.trim() : "",
      minutes: $("set-minutes") ? Number($("set-minutes").value) : 15,
      method: method ? method.value : "suspend",
      enabled: $("set-enabled") ? $("set-enabled").checked : false,
      announce: $("set-announce") ? $("set-announce").checked : true,
      autostart: $("set-autostart") ? $("set-autostart").checked : false,
      location_mode: mode ? mode.value : "auto",
      manual_city: $("set-city") ? $("set-city").value.trim() : "",
      manual_country: extractCountryName($("set-country") ? $("set-country").value.trim() : ""),
      manual_latitude: $("set-latitude") ? $("set-latitude").value.trim() : "",
      manual_longitude: $("set-longitude") ? $("set-longitude").value.trim() : "",
      times: collectTimes()
    };
  }

  function collectLocation() {
    var mode = document.querySelector('input[name="location_mode"]:checked');
    return {
      location_mode: mode ? mode.value : "auto",
      manual_city: $("set-city") ? $("set-city").value.trim() : "",
      manual_country: extractCountryName($("set-country") ? $("set-country").value.trim() : ""),
      manual_latitude: $("set-latitude") ? $("set-latitude").value.trim() : "",
      manual_longitude: $("set-longitude") ? $("set-longitude").value.trim() : ""
    };
  }

function saveSettings(messageId, triggerBtn) {
    setStatus(messageId, "جارٍ الحفظ…", "info");
    return call("save_settings", collectCommon()).then(function (res) {
      if (res && res.ok) {
        setStatus(messageId, "تم حفظ الإعدادات.", "success");
        if (triggerBtn) {
          playSaveAnimation(triggerBtn);
        }
        if (res.state) {
          applyState(res.state);
        }
      } else {
        setStatus(messageId, "تعذر الحفظ: " + ((res && res.error) || "خطأ غير معروف"), "error");
      }
    });
  }

  /* Uiverse "Saved" success animation (ilkhoeri/chilly-sloth-36).
     Runs exactly once, only after a successful save, via the temporary
     .is-saving class (never :hover). Guards against double-triggering;
     restores the original Arabic label and normal button state after the
     animation completes. SVG geometry, keyframes, 1s duration,
     cubic-bezier(0.5, 0, 0.25, 1) easing and 1.75/0.75/1 zoom values are
     defined verbatim in skins.css. */
  var SAVE_ANIMATION_MS = 1000;

  function playSaveAnimation(btn) {
    if (!btn || btn.dataset.saveAnimating === "1") {
      return;
    }
    btn.dataset.saveAnimating = "1";
    btn.classList.add("is-saving");
    setTimeout(function () {
      btn.classList.remove("is-saving");
      delete btn.dataset.saveAnimating;
    }, SAVE_ANIMATION_MS);
  }

  function refreshTimes(messageId) {
    var statusId = messageId || "times-status";
    var mode = document.querySelector('input[name="location_mode"]:checked');
    var locMode = mode ? mode.value : "auto";
    if (locMode === "manual") {
      var country = $("set-country") ? $("set-country").value.trim() : "";
      var city = $("set-city") ? $("set-city").value.trim() : "";
      if (!country) {
        setStatus(statusId, "يرجى اختيار الدولة أولًا.", "error");
        return Promise.resolve({ ok: false });
      }
      if (!city) {
        setStatus(statusId, "يرجى اختيار المدينة أولًا.", "error");
        return Promise.resolve({ ok: false });
      }
    }
    setStatus(statusId, "جارٍ جلب المواقيت…", "info");
    return call("fetch_times", collectLocation()).then(function (res) {
      if (res && res.ok) {
        setStatus(statusId, "تم جلب المواقيت لـ " + (res.location || "") + ".", "success");
        var resolved = $("location-resolved");
        if (resolved && res.location) {
          resolved.textContent = "الموقع المستخدم: " + res.location;
          resolved.style.display = "block";
        }
        if (res.state) {
          applyState(res.state);
        }
      } else {
        setStatus(statusId, "تعذر الجلب: " + ((res && res.error) || "خطأ غير معروف"), "error");
      }
    });
  }

  function pauseMedia(messageId) {
    return call("pause_now").then(function (res) {
      if (res && res.ok) {
        setStatus(messageId, "تم إرسال أمر الإيقاف المؤقت.", "success");
      } else {
        var pe = playerError(res);
        setStatus(messageId, pe.type === "warning" ? pe.text : "تعذر الإيقاف: " + pe.text, pe.type);
      }
      return refresh();
    });
  }

  function browsePlayer() {
    setStatus("music-status", "جارٍ فتح محدد الملفات…", "info");
    return call("browse_player").then(function (res) {
      if (res && res.ok && res.path) {
        var input = $("set-music");
        if (input) {
          input.value = res.path;
        }
        setStatus("music-status", "تم اختيار المشغّل: " + res.path, "success");
        return refresh();
      }
      if (res && res.cancelled) {
        setStatus("music-status", res.error || "أُلغي اختيار المشغّل.", "info");
        return null;
      }
      setStatus("music-status", "تعذر فتح محدد الملفات: " + ((res && res.error) || "خطأ غير معروف"), "error");
      return null;
    });
  }

  function browseAdhan() {
    setStatus("music-status", "جارٍ فتح محدد الملفات…", "info");
    return call("browse_adhan").then(function (res) {
      if (res && res.ok && res.path) {
        var input = $("set-adhan");
        if (input) {
          input.value = res.path;
        }
        setStatus("music-status", "تم اختيار برنامج المؤذن: " + res.path, "success");
        return refresh();
      }
      if (res && res.cancelled) {
        setStatus("music-status", res.error || "أُلغي اختيار البرنامج.", "info");
        return null;
      }
      setStatus("music-status", "تعذر فتح محدد الملفات: " + ((res && res.error) || "خطأ غير معروف"), "error");
      return null;
    });
  }

  var appDropdownState = {};

  function closeAllAppDropdowns() {
    Object.keys(appDropdownState).forEach(function (key) {
      var s = appDropdownState[key];
      if (s && s.dropdown) {
        s.dropdown.classList.add("hidden");
        s.active = false;
      }
    });
  }

  function renderDropdownItems(state) {
    var dd = state.dropdown;
    if (!dd) return;
    dd.innerHTML = "";
    var items = state.filtered;
    if (!items || !items.length) {
      var empty = document.createElement("div");
      empty.className = "dropdown-empty";
      empty.textContent = "لا توجد تطبيقات مطابقة";
      dd.appendChild(empty);
      return;
    }
    items.forEach(function (app, idx) {
      var item = document.createElement("div");
      item.className = "dropdown-item";
      item.setAttribute("role", "option");
      item.dataset.path = app.path;
      var name = document.createElement("div");
      name.className = "dropdown-item__name";
      name.textContent = app.name || "";
      var path = document.createElement("div");
      path.className = "dropdown-item__path";
      path.textContent = app.path || "";
      item.appendChild(name);
      item.appendChild(path);
      if (idx === state.activeIndex) {
        item.classList.add("is-active");
      }
      item.addEventListener("mousedown", function (e) {
        e.preventDefault();
        selectApp(state, app);
      });
      dd.appendChild(item);
    });
  }

  function filterApps(state) {
    var q = (state.input.value || "").trim().toLowerCase();
    if (!q) {
      state.filtered = state.apps.slice();
    } else {
      state.filtered = state.apps.filter(function (app) {
        var name = (app.name || "").toLowerCase();
        var path = (app.path || "").toLowerCase();
        return name.indexOf(q) !== -1 || path.indexOf(q) !== -1;
      });
    }
    state.activeIndex = -1;
    renderDropdownItems(state);
  }

  function selectApp(state, app) {
    state.input.value = app.path || "";
    closeAllAppDropdowns();
    setStatus("music-status", "تم اختيار: " + (app.name || app.path), "success");
    saveSettings("music-status");
  }

  function openAppDropdown(inputId, dropdownId) {
    var input = $(inputId);
    var dropdown = document.getElementById(dropdownId);
    if (!input || !dropdown) return;
    var key = inputId;
    var state = appDropdownState[key];
    if (!state) {
      state = { input: input, dropdown: dropdown, apps: [], filtered: [], activeIndex: -1, active: false };
      appDropdownState[key] = state;
      input.addEventListener("input", function () { if (state.active) filterApps(state); });
      input.addEventListener("keydown", function (e) {
        if (!state.active) return;
        if (e.key === "ArrowDown") {
          e.preventDefault();
          state.activeIndex = Math.min(state.activeIndex + 1, state.filtered.length - 1);
          if (state.activeIndex < 0) state.activeIndex = 0;
          renderDropdownItems(state);
        } else if (e.key === "ArrowUp") {
          e.preventDefault();
          state.activeIndex = Math.max(state.activeIndex - 1, 0);
          renderDropdownItems(state);
        } else if (e.key === "Enter") {
          if (state.activeIndex >= 0 && state.filtered[state.activeIndex]) {
            e.preventDefault();
            selectApp(state, state.filtered[state.activeIndex]);
          }
        } else if (e.key === "Escape") {
          closeAllAppDropdowns();
        }
      });
      input.addEventListener("focus", function () { if (state.apps.length) { state.active = true; dropdown.classList.remove("hidden"); filterApps(state); } });
    }
    if (state.active) {
      closeAllAppDropdowns();
      return;
    }
    closeAllAppDropdowns();
    setStatus("music-status", "جارٍ تحميل التطبيقات الجارية…", "info");
    return call("list_running_apps").then(function (res) {
      if (res && res.ok && Array.isArray(res.apps)) {
        state.apps = res.apps;
        state.active = true;
        dropdown.classList.remove("hidden");
        filterApps(state);
        setStatus("music-status", "تم تحميل " + res.apps.length + " تطبيق جارٍ.", "success");
      } else {
        setStatus("music-status", "تعذر تحميل التطبيقات الجارية.", "warning");
      }
    });
  }

  // Close dropdowns on outside click
  document.addEventListener("click", function (e) {
    var inside = false;
    Object.keys(appDropdownState).forEach(function (key) {
      var s = appDropdownState[key];
      if (!s) return;
      if (s.input.contains(e.target) || s.dropdown.contains(e.target)) {
        inside = true;
      }
    });
    if (!inside) {
      closeAllAppDropdowns();
    }
  });

  function resumeMedia(messageId) {
    return call("resume_now").then(function (res) {
      if (res && res.ok) {
        setStatus(messageId, "تم إرسال أمر الاستئناف.", "success");
      } else {
        var pe = playerError(res);
        setStatus(messageId, pe.type === "warning" ? pe.text : "تعذر الاستئناف: " + pe.text, pe.type);
      }
      return refresh();
    });
  }

  function showPage(key) {
    var items = document.querySelectorAll(".nav__item");
    Array.prototype.forEach.call(items, function (item) {
      item.classList.toggle("is-active", item.getAttribute("data-page") === key);
    });
    var pages = document.querySelectorAll(".page");
    Array.prototype.forEach.call(pages, function (page) {
      page.classList.toggle("is-active", page.id === "page-" + key);
    });
    var meta = PAGE_META[key] || PAGE_META.dashboard;
    setText("page-title", meta[0]);
    setText("page-subtitle", meta[1]);
  }

  function tick() {
    if (remaining > 0) {
      remaining -= 1;
      setText("next-prayer-countdown", formatRemaining(remaining));
      drawRing();
      if (remaining === 0) {
        refresh();
      }
    }
    // Update resume countdown every second
    updateResumeCountdown();
  }

  function on(id, handler) {
    var el = $(id);
    if (el) {
      el.addEventListener("click", handler);
    }
  }

  function wire() {
    var items = document.querySelectorAll(".nav__item");
    Array.prototype.forEach.call(items, function (item) {
      item.addEventListener("click", function () {
        showPage(item.getAttribute("data-page"));
      });
    });
    on("btn-save", function () {
      saveSettings("settings-status", $("btn-save"));
    });
    on("btn-save-times", function () {
      saveSettings("times-status", $("btn-save-times"));
    });
    on("btn-save-music", function () {
      saveSettings("music-status", $("btn-save-music"));
    });
    on("btn-refresh-state", refresh);
    on("btn-fetch-times", function() { return refreshTimes("times-status"); });
    on("btn-fetch-location", function() { return refreshTimes("location-status"); });
    on("btn-pause", function () {
      pauseMedia("settings-status");
    });
    on("btn-resume", function () {
      resumeMedia("settings-status");
    });
    on("btn-pause-2", function () {
      pauseMedia("music-status");
    });
    on("btn-resume-2", function () {
      resumeMedia("music-status");
    });
    on("btn-browse-music", browsePlayer);
    on("btn-browse-adhan", browseAdhan);
    on("btn-dropdown-music", function () {
      openAppDropdown("set-music", "dropdown-music");
    });
    on("btn-dropdown-adhan", function () {
      openAppDropdown("set-adhan", "dropdown-adhan");
    });
    document.addEventListener("themechange", function (event) {
      if (syncingTheme) {
        return;
      }
      call("set_theme", event.detail.theme);
    });
  }

  function init() {
    buildTimesEditor();
    wire();
    initLocationUI();
    loadCitiesDB();
    diagWrite(diagSnapshot("init"));
    window.addEventListener("pywebviewready", function () {
      diagWrite(diagSnapshot("pywebviewready"));
      refresh();
    });
    whenReady().then(function (available) {
      if (available) {
        diagWrite(diagSnapshot("whenReady-available"));
        refresh();
      } else {
        diagWrite(diagSnapshot("whenReady-timeout"));
        setStatus("settings-status", "واجهة الجسر غير متاحة؛ يتم عرض البيانات الفارغة فقط.", "error");
        renderPrayers(null);
        renderNext(null);
        renderStatus(null);
      }
    });
    setInterval(tick, 1000);
    setInterval(refresh, 30000);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();