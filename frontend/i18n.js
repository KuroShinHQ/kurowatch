// ═══════════════════════════════════════════════════════════════════
// KuroWatch i18n — TR/EN çeviri sistemi
// data-i18n HTML attribute ile çalışır. localStorage.kw_lang
// ═══════════════════════════════════════════════════════════════════

(function() {
  'use strict';

  let currentLang = localStorage.getItem('kw_lang') || 'tr';
  let translations = {};

  async function loadLocale(lang) {
    try {
      const r = await fetch('locales/' + lang + '.json');
      if (!r.ok) throw new Error('locale fetch ' + r.status);
      translations = await r.json();
      currentLang = lang;
      localStorage.setItem('kw_lang', lang);
      applyTranslations();
      return true;
    } catch (err) {
      console.warn('i18n load fail:', err);
      return false;
    }
  }

  function t(key, fallback) {
    return translations[key] || fallback || key;
  }

  function applyTranslations() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.dataset.i18n;
      const val = translations[key];
      if (val) el.textContent = val;
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
      const key = el.dataset.i18nPlaceholder;
      const val = translations[key];
      if (val) el.setAttribute('placeholder', val);
    });
  }

  window.kuroI18n = {
    t: t,
    load: loadLocale,
    apply: applyTranslations,
    getLang: () => currentLang,
    setLang: (lang) => loadLocale(lang)
  };

  // İlk yüklemede locale yükle
  document.addEventListener('DOMContentLoaded', () => loadLocale(currentLang));
})();
