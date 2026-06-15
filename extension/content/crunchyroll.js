// KuroWatch — Crunchyroll content script
(function () {
  function extract() {
    const url = window.location.href;
    if (!url.includes('/watch/') && !url.includes('/series/')) return null;

    // og:title → "Başlık · Episode N – Bölüm Adı"
    const ogTitle = KW.getMetaContent('og:title') || document.title || '';
    let title = '';
    let episode = null;

    if (ogTitle.includes(' · ')) {
      const parts = ogTitle.split(' · ');
      title = parts[0].trim();
      const epMatch = (parts[1] || '').match(/[Ee]pisode\s+(\d+)/);
      if (epMatch) episode = parseInt(epMatch[1], 10);
    } else {
      title = ogTitle.replace(/\s*[-|]?\s*Crunchyroll$/i, '').trim();
    }

    if (!title) title = document.querySelector('h1')?.textContent?.trim() || '';
    if (!title) return null;

    return { url, title, episode, chapter: null, site: 'crunchyroll', type: 'anime' };
  }

  chrome.runtime.onMessage.addListener((msg, _sender, reply) => {
    if (msg.type === 'GET_PAGE_INFO') reply({ ok: true, data: extract() });
  });
})();
