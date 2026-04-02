import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth

async def test():
    p = await async_playwright().start()
    b = await p.chromium.launch()
    pg = await b.new_page()
    await stealth(pg)
    print("Stealth applied successfully")
    await b.close()
    await p.stop()

if __name__ == "__main__":
    asyncio.run(test())
