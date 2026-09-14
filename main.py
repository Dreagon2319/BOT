import asyncio
from playwright.async_api import async_playwright

SITES = [
    "https://bloxd.com/play/classic_survival?lobby=2025",
    "https://bloxd.dev/play/classic_survival?lobby=2025",
    "https://playbloxd.com/play/classic_survival?lobby=2025",
    "https://buildminecreate.com/play/classic_survival?lobby=2025",
    "https://buildhub.club/play/classic_survival?lobby=2025",
]


async def main():

    async with async_playwright() as p:

        print("Starting Chromium...")

        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
            ]
        )

        context = await browser.new_context()

        for url in SITES:

            page = await context.new_page()

            print(f"Opening: {url}")

            try:
                await page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=60000
                )

                print(f"Opened: {url}")

            except Exception as e:
                print(f"Failed: {url}")
                print(e)

        print()
        print("All pages are open.")
        print("Keeping Chromium running forever.")

        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
