// KuroWatch — Background Service Worker (Manifest V3)
const BACKEND = 'http://localhost:8099';

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === 'GET_STATUS') {
    fetch(`${BACKEND}/api/extension/status`, { signal: AbortSignal.timeout(3000) })
      .then(r => r.json())
      .then(d => sendResponse({ ok: true, data: d }))
      .catch(() => sendResponse({ ok: false }));
    return true;
  }

  if (msg.type === 'GET_ACTIVE_TAB_INFO') {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const tab = tabs[0];
      if (!tab?.id) { sendResponse({ ok: false }); return; }
      chrome.tabs.sendMessage(tab.id, { type: 'GET_PAGE_INFO' }, (resp) => {
        if (chrome.runtime.lastError || !resp?.ok) {
          sendResponse({ ok: false });
        } else {
          sendResponse({ ok: true, data: resp.data });
        }
      });
    });
    return true;
  }

  if (msg.type === 'CAPTURE') {
    fetch(`${BACKEND}/api/extension/capture`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(msg.payload),
      signal: AbortSignal.timeout(10000),
    })
      .then(r => r.json())
      .then(d => sendResponse({ ok: true, data: d }))
      .catch(e => sendResponse({ ok: false, error: e.message }));
    return true;
  }
});
