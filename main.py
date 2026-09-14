import asyncio
from playwright.async_api import async_playwright

print("===== MAIN.PY STARTED =====", flush=True)

SITES = [
    "https://bloxd.com/play/classic_survival?lobby=2025",
    "https://bloxd.dev/play/classic_survival?lobby=2025",
    "https://playbloxd.com/play/classic_survival?lobby=2025",
    "https://buildminecreate.com/play/classic_survival?lobby=2025",
    "https://buildhub.club/play/classic_survival?lobby=2025",
]


async def main():

    print("===== ENTERING MAIN =====", flush=True)

    async with async_playwright() as p:

        print("Starting Chromium...", flush=True)

        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
            ]
        )

        print("Chromium started.", flush=True)

        context = await browser.new_context()

        for url in SITES:

            page = await context.new_page()

            print(f"Opening: {url}", flush=True)

            try:
                await page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=60000
                )

                print(f"Opened: {url}", flush=True)

            except Exception as e:
                print(f"Failed: {url}", flush=True)
                print(repr(e), flush=True)

        print("All pages are open.", flush=True)
        print("Keeping Chromium running forever.", flush=True)

        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
