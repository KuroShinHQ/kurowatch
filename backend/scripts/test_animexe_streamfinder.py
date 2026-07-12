import asyncio, sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
from backend.downloader.stream_finder import find_stream_url

async def main():
    url = "https://animexe.com/watch/naruto/1/1"
    print("Testing:", url)
    result = await find_stream_url(url, media_type="anime")
    print(f"Result: {result[:120] if result else 'None'}")
    if result and result != url:
        print("SUCCESS: stream_finder found video!")
    else:
        print("FAIL: stream_finder returned original URL")

asyncio.run(main())
