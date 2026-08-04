/* ============================================================
   FTMS Theme Toggle
   Dark is the default theme. A `.light-mode` class on <body>
   flips the CSS variables to the light palette.
   Choice is persisted in localStorage across page loads.
   ============================================================ */
(function () {
  'use strict';

  var STORAGE_KEY = 'ftms-theme';
  var LIGHT = 'light';

  function getSavedTheme() {
    try {
      return localStorage.getItem(STORAGE_KEY);
    } catch (e) {
      return null;
    }
  }

  function setSavedTheme(value) {
    try {
      if (value === LIGHT) {
        localStorage.setItem(STORAGE_KEY, LIGHT);
      } else {
        localStorage.removeItem(STORAGE_KEY);
      }
    } catch (e) {
      /* ignore storage errors */
    }
  }

  function applyTheme(theme) {
    var isLight = theme === LIGHT;
    var html = document.documentElement;
    var body = document.body;
    if (isLight) {
      html.classList.add('light-mode');
      body.classList.add('light-mode');
    } else {
      html.classList.remove('light-mode');
      body.classList.remove('light-mode');
    }
    syncToggle(isLight);
  }

  function syncToggle(isLight) {
    var toggle = document.querySelector('.theme-toggle');
    if (!toggle) return;
    toggle.classList.toggle('active', isLight);
    var label = toggle.querySelector('.theme-toggle-label');
    if (label) {
      label.textContent = isLight ? '☀️' : '🌙';
    }
  }

  function init() {
    var toggle = document.querySelector('.theme-toggle');
    if (!toggle) return;

    // Reflect saved theme on the toggle's visual state
    applyTheme(getSavedTheme() === LIGHT ? LIGHT : 'dark');

    toggle.addEventListener('click', function (e) {
      e.preventDefault();
      var isLight = !document.body.classList.contains('light-mode');
      applyTheme(isLight ? LIGHT : 'dark');
      setSavedTheme(isLight ? LIGHT : 'dark');
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
