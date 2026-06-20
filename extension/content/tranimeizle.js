// KuroWatch — tranimeizle.co / tranimeizle.io content script
(function () {
  function extract() {
    const og = document.querySelector('meta[property="og:title"]');
    const text = (og ? og.getAttribute('content') : document.title) || '';
    const siteDomain = location.hostname.replace(/^www\./, '');

    // Desen 1: "Anime Adı 12. Bölüm" veya "Anime Adı - 12. Bölüm"
    let m = text.match(/^(.+?)\s*[-–]?\s*(\d+)\.\s*(?:bölüm|episode|kisim)/i);
    // Desen 2: "Anime Adı – Bölüm 12"
    if (!m) m = text.match(/^(.+?)\s*[-–]\s*(?:bölüm|episode)\s*(\d+)/i);

    let title = null, episode = null;

    if (m) {
      title   = m[1].replace(/\s*[-–]\s*$/, '').trim();
      episode = parseInt(m[2], 10);
    } else {
      // URL'den parse: /anime-adi-12-bolum-izle
      const slug = location.pathname.split('/').pop() || '';
      const urlM = slug.match(/^(.+?)-(\d+)-bolum/i);
      if (urlM) {
        title   = urlM[1].replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
        episode = parseInt(urlM[2], 10);
      }
    }

    if (!title || !episode) return null;
    return { url: location.href, title, episode, chapter: null, site: siteDomain, type: 'anime' };
  }

  chrome.runtime.onMessage.addListener(function (msg, _sender, reply) {
    if (msg.type === 'GET_PAGE_INFO') {
      const data = extract();
      reply(data ? { ok: true, data: data } : { ok: false });
    }
  });
})();
