// KuroWatch — tranimeizle.co content script
(function () {
  function extract() {
    const og = document.querySelector('meta[property="og:title"]');
    const text = og ? og.getAttribute('content') : document.title;
    // "Anime Adı - Bölüm N" ya da "Anime Adı – Episode N"
    const match = text && text.match(/^(.+?)\s*[-–]\s*(?:bölüm|episode)\s*(\d+)/i);
    if (!match) return null;
    return {
      url: location.href,
      title: match[1].trim(),
      episode: parseInt(match[2], 10),
      chapter: null,
      site: 'tranimeizle.co',
      type: 'anime',
    };
  }

  chrome.runtime.onMessage.addListener(function (msg, _sender, reply) {
    if (msg.type === 'GET_PAGE_INFO') {
      const data = extract();
      reply(data ? { ok: true, data: data } : { ok: false });
    }
  });
})();
