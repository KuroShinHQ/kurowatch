// KuroWatch — MangaDex content script
(function () {
  function extract() {
    const url = window.location.href;
    const path = window.location.pathname;

    const isChapter = path.startsWith('/chapter/');
    const isTitle   = path.startsWith('/title/');
    if (!isChapter && !isTitle) return null;

    const ogTitle = KW.getMetaContent('og:title') || document.title || '';
    let title   = '';
    let chapter = null;

    if (isChapter) {
      const chMatch = ogTitle.match(/Chapter\s+([\d.]+)/i);
      if (chMatch) chapter = parseInt(chMatch[1], 10);
      const breadcrumb = document.querySelector('nav a[href*="/title/"]');
      title = breadcrumb?.textContent?.trim()
           || ogTitle.replace(/Chapter.*$/i, '').replace(/\s*\|.*$/, '').trim();
    } else {
      title = document.querySelector('h1')?.textContent?.trim()
           || ogTitle.replace(/\s*\|.*$/, '').trim();
    }

    if (!title) return null;

    return { url, title, episode: null, chapter, site: 'mangadex', type: 'manga' };
  }

  chrome.runtime.onMessage.addListener((msg, _sender, reply) => {
    if (msg.type === 'GET_PAGE_INFO') reply({ ok: true, data: extract() });
  });
})();
