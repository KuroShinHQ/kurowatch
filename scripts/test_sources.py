"""Test domain resolver + health check."""
import asyncio
import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent.parent))

from backend.scraper.sources import get_active_domain, get_source_config


async def test():
    for site in ['hdfilmcehennemi', 'dizigom']:
        cfg = get_source_config(site)
        print(f'{site}: domains={cfg["domains"]}')
        domain = await get_active_domain(site)
        print(f'  -> aktif: {domain}')
        print()


if __name__ == '__main__':
    asyncio.run(test())
