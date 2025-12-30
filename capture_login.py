import asyncio
from playwright.async_api import async_playwright


async def capture():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto("http://localhost:80/login")
        await asyncio.sleep(3)
        await page.screenshot(path="login_snapshot.png", full_page=True)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(capture())
