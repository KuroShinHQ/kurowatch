"""stream_finder ile tranimaci.com testi - www. olmadan"""
import asyncio, sys, logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
sys.path.insert(0, '.')
from backend.downloader.stream_finder import find_stream_url

async def test():
    url = 'https://tranimaci.com/video/kono-subarashii-sekai-ni-shukufuku-wo-3-1-bolum'
    print(f"Testing: {url}")
    result = await find_stream_url(url)
    print(f"\nRESULT: {result[:120]}")
    if result != url:
        print("EMBED BULUNDU!")
    else:
        print("EMBED BULUNAMADI")

asyncio.run(test())
