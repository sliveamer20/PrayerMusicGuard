(function () {
  const STORAGE_KEY = "pmg-theme";
  const root = document.documentElement;
  const checkbox = document.getElementById("theme-checkbox");
  const statusEl = document.getElementById("theme-status");

  function applyTheme(theme) {
    root.setAttribute("data-theme", theme);
    if (checkbox) {
      checkbox.checked = theme === "dark";
    }
    if (statusEl) {
      statusEl.textContent = theme === "dark" ? "الوضع الحالي: داكن" : "الوضع الحالي: فاتح";
    }
    document.dispatchEvent(new CustomEvent("themechange", { detail: { theme } }));
  }

  function readStoredTheme() {
    try {
      return localStorage.getItem(STORAGE_KEY);
    } catch (e) {
      return null;
    }
  }

  function storeTheme(theme) {
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch (e) {
      /* storage unavailable */
    }
  }

  function preferredTheme() {
    const stored = readStoredTheme();
    if (stored === "dark" || stored === "light") {
      return stored;
    }
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  }

  function toggleTheme() {
    const next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
    storeTheme(next);
    applyTheme(next);
  }

  function init() {
    applyTheme(preferredTheme());

    if (checkbox) {
      checkbox.addEventListener("change", toggleTheme);
    }

    window.pmgTheme = {
      get: function () {
        return root.getAttribute("data-theme");
      },
      set: function (theme) {
        storeTheme(theme);
        applyTheme(theme);
      },
      toggle: toggleTheme,
    };
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();