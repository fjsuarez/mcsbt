import asyncio
from pyppeteer import launch

async def main():
    url = f"https://www.glassdoor.es/Opiniones/index.htm?overall_rating_low=3.5&page=1&filterType=RATING_OVERALL"
    browser = await launch()
    page = await browser.newPage()
    await page.goto(url)
    await page.screenshot({'path': 'example.png'})
    await browser.close()

asyncio.get_event_loop().run_until_complete(main())