import asyncio
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
sys.path.insert(0, '.')
from backend.downloader.stream_finder import find_stream_url

async def test():
    url = 'https://www.tranimaci.com/video/konosuba-s3-bolum-1/'
    print('Testing:', url)
    result = await find_stream_url(url)
    print('RESULT:', result[:120] if result else 'None')
    if result and result != url:
        print('EMBED BULUNDU')
    else:
        print('EMBED BULUNAMADI - orijinal URL dondu')

asyncio.run(test())
