// KuroWatch Popup
const $ = id => document.getElementById(id);

function send(type, payload) {
  return new Promise(resolve => chrome.runtime.sendMessage({ type, payload }, resolve));
}

async function init() {
  // Backend ping
  const statusResp = await send('GET_STATUS');
  const dot = $('status-dot');
  if (statusResp?.ok) {
    dot.className = 'dot dot-green';
    dot.title = 'KuroWatch bağlı (localhost:8099)';
  } else {
    dot.className = 'dot dot-red';
    dot.title = 'KuroWatch bağlanamadı';
  }

  // Aktif sekme içerik tespiti
  const tabResp = await send('GET_ACTIVE_TAB_INFO');
  $('loading').classList.add('hidden');

  if (!tabResp?.ok || !tabResp.data) {
    $('no-support').classList.remove('hidden');
    return;
  }

  const info = tabResp.data;
  $('det-title').textContent = info.title;

  const metaParts = [];
  if (info.site)          metaParts.push(info.site);
  if (info.episode != null) metaParts.push(`Bölüm ${info.episode}`);
  if (info.chapter != null) metaParts.push(`Bölüm ${info.chapter}`);
  if (info.type)          metaParts.push(info.type);
  $('det-meta').textContent = metaParts.join(' · ');

  $('detected').classList.remove('hidden');

  $('btn-add').addEventListener('click', async () => {
    $('btn-add').disabled = true;
    $('btn-add').textContent = 'Ekleniyor...';

    const resp = await send('CAPTURE', info);

    $('result').classList.remove('hidden', 'error');
    if (resp?.ok) {
      const d = resp.data;
      $('result-text').textContent = d.action === 'created'
        ? `✅ Eklendi: "${d.title}"`
        : `✅ Güncellendi: Bölüm ${d.progress}`;
    } else {
      $('result').classList.add('error');
      $('result-text').textContent = `❌ Hata: ${resp?.error || 'Bilinmiyor'}`;
    }

    $('btn-add').textContent = '+ KuroWatch\'a Ekle';
    $('btn-add').disabled = false;
  });
}

init();
