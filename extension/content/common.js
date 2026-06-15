// KuroWatch content script — paylaşılan yardımcılar
window.KW = window.KW || {};

KW.slugToTitle = function(slug) {
  return slug.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
};

KW.getMetaContent = function(prop) {
  return document.querySelector(`meta[property="${prop}"]`)?.content
      || document.querySelector(`meta[name="${prop}"]`)?.content
      || null;
};
