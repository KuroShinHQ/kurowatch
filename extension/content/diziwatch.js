// KuroWatch — Diziwatch content script
(function () {
  function extract() {
    const url = window.location.href;
    const path = window.location.pathname;

    const animeMatch = path.match(/\/anime\/([^/]+)/);
    if (!animeMatch) return null;

    const slug = animeMatch[1];
    const epMatch = path.match(/\/bolum-(\d+)/);
    const episode = epMatch ? parseInt(epMatch[1], 10) : null;

    const h1 = document.querySelector('h1.entry-title, h1.title, article h1, h1');
    let title = h1?.textContent?.trim() || KW.slugToTitle(slug);
    // "Bölüm N" / "Episode N" suffix'ini temizle
    title = title.replace(/\s*(Bölüm|Episode)\s*\d+.*/i, '').trim();

    return { url, title, episode, chapter: null, site: 'diziwatch', type: 'anime' };
  }

  chrome.runtime.onMessage.addListener((msg, _sender, reply) => {
    if (msg.type === 'GET_PAGE_INFO') reply({ ok: true, data: extract() });
  });
})();
