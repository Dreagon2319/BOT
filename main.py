import asyncio
from playwright.async_api import async_playwright


# ============================================================
# SITES
# ============================================================

SITES = [
    "https://bloxd.com/play/classic_survival?lobby=2025",
    "https://bloxd.dev/play/classic_survival?lobby=2025",
    "https://playbloxd.com/play/classic_survival?lobby=2025",
    "https://buildminecreate.com/play/classic_survival?lobby=2025",
    "https://buildhub.club/play/classic_survival?lobby=2025",
]


# ============================================================
# SETTINGS
# ============================================================

PAGE_TIMEOUT = 60000000


# ============================================================
# LOAD ALL SITES
# ============================================================

async def load_all_sites(pages):

    tasks = []

    for i, page in enumerate(pages):

        async def load(page=page, index=i):

            url = SITES[index]

            try:

                print()
                print(f"[OPEN] {index + 1}/{len(SITES)}")
                print(f"       {url}")

                await page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=PAGE_TIMEOUT
                )

                print(f"[OK]   Site {index + 1}")

            except Exception as e:

                print(f"[ERROR] Site {index + 1}")
                print(f"        {e}")

        tasks.append(load())

    # Load all sites at the same time
    await asyncio.gather(*tasks)


# ============================================================
# MAIN
# ============================================================

async def main():

    async with async_playwright() as p:

        print()
        print("==========================================")
        print(" Starting Railway Chromium")
        print("==========================================")
        print()

        try:

            # Launch Chromium directly on Railway
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                ]
            )

        except Exception as e:

            print("FAILED TO START CHROMIUM")
            print()
            print(e)
            return

        print("Chromium started successfully.")
        print()

        # Create browser context
        context = await browser.new_context()

        pages = []

        # Create one page for each site
        for _ in SITES:

            page = await context.new_page()
            pages.append(page)

        print(f"Created {len(pages)} browser pages.")
        print()

        # ====================================================
        # LOAD ALL 5 SITES TOGETHER
        # ====================================================

        print("==========================================")
        print(" Loading all 5 sites simultaneously")
        print("==========================================")
        print()

        await load_all_sites(pages)

        # ====================================================
        # KEEP EVERYTHING OPEN
        # ====================================================

        print()
        print("==========================================")
        print(" ALL 5 SITES ARE OPEN")
        print("==========================================")
        print()
        print(f"Total sites : {len(SITES)}")
        print()
        print("Chromium will remain running.")
        print("The Railway service will stay alive.")
        print()

        # Keep browser and pages alive
        while True:

            await asyncio.sleep(3600)


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    try:

        asyncio.run(main())

    except KeyboardInterrupt:

        print()
        print("==========================================")
        print(" Stopped by user.")
        print("==========================================")
