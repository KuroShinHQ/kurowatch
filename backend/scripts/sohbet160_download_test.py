"""WSL-based download tests"""
import asyncio, subprocess, os

script_dir = os.path.dirname(os.path.abspath(__file__))
download_dir = os.path.join(script_dir, "..", "..", "downloads")
os.makedirs(download_dir, exist_ok=True)

async def run_wsl(cmd, timeout=120):
    full_cmd = f'bash -c "cd /mnt/c/Kuroshin/kurowatch/backend/scripts && source /root/kuroshin/venv/bin/activate && {cmd}"'
    proc = await asyncio.create_subprocess_exec(
        'wsl', '-e', 'bash', '-c', full_cmd,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return stdout.decode('utf-8', errors='replace'), stderr.decode('utf-8', errors='replace'), proc.returncode
    except asyncio.TimeoutError:
        proc.kill()
        return "", "TIMEOUT", -1

async def main():
    # Test 1: yt-dlp with playlist extractor on hdfc page  
    print("=== yt-dlp EXTRACT INFO ===")
    stdout, stderr, rc = await run_wsl(
        'cd /mnt/c/Kuroshin/kurowatch/downloads && '
        'yt-dlp --extractor-args "generic:no-playlist" '
        '--dump-json "https://www.hdfilmcehennemi.nl/american-psycho-6/" 2>&1; '
        'echo "EXIT:$?"',
        timeout=30
    )
    print(f"yt-dlp output: {stdout[:1500]}")
    print(f"stderr: {stderr[:500]}")

    # Test 2: Try with a different approach - check page for m3u8  
    stdout2, stderr2, rc2 = await run_wsl(
        'cd /mnt/c/Kuroshin/kurowatch && '
        'python3 -c "
import asyncio, httpx, re
async def main():
    async with httpx.AsyncClient() as cl:
        r = await cl.get(\"https://www.hdfilmcehennemi.nl/american-psycho-6/\",
            headers={\"User-Agent\":\"Mozilla/5.0\"})
        # Search for video URLs
        for pat in [r\"src=\\\\\\\"([^\\\\\\\"]*\.m3u8[^\\\\\\\"]*)\\\\\\\"\", 
                    r\"src=\\\\\\\"([^\\\\\\\"]*\.mp4[^\\\\\\\"]*)\\\\\\\"\",
                    r\"file:\s*\\\\\\\"([^\\\\\\\"]*)\\\\\\\"\", 
                    r\"src:\s*\\\\\\\"([^\\\\\\\"]*)\\\\\\\"\"]:
            matches = re.findall(pat, r.text)
            if matches:
                print(f\"Found {pat[:30]}: {matches[:5]}\")
        # Check for iframe src
        iframes = re.findall(r\"<iframe[^>]+src=\\\\\\\"([^\\\\\\\"]*)\\\\\\\"\", r.text)
        print(f\"iframes: {iframes}\")
asyncio.run(main())
" 2>&1',
        timeout=30
    )
    print(f"\n=== VIDEO URL SEARCH ===")
    print(f"{stdout2[:1000]}")

    # Test 3: Playwright
    print(f"\n=== PLAYWRIGHT ===")
    stdout3, stderr3, rc3 = await run_wsl(
        'cd /mnt/c/Kuroshin/kurowatch && '
        'python3 backend/scripts/sohbet160_pw_manga.py 2>&1',
        timeout=90
    )
    print(f"Playwright: {stdout3[:2000]}")
    if stderr3 and len(stderr3) > 10:
        print(f"stderr: {stderr3[:500]}")

if __name__ == "__main__":
    asyncio.run(main())
