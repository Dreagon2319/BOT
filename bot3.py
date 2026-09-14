
import asyncio
from playwright.async_api import async_playwright


# ============================================================
# BROWSERLESS
# ============================================================

BROWSERLESS_TOKEN = "2VG4ZGB9ib6YKbd41b5cc2c6da0912f699bb257adaf54828d"

WS_ENDPOINT = (
    f"wss://production-sfo.browserless.io"
    f"?token={BROWSERLESS_TOKEN}"
)


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

# Playwright timeout is in milliseconds
PAGE_TIMEOUT = 60000000

# Stay connected for 2 minutes
SESSION_TIME = 110


# ============================================================
# LOAD ALL 5 SITES
# ============================================================

async def load_all_sites(context):

    pages = []

    # Create all 5 pages first
    for _ in SITES:
        page = await context.new_page()
        pages.append(page)

    print()
    print(f"Created {len(pages)} browser pages.")
    print()

    tasks = []

    for i, page in enumerate(pages):

        async def load(page=page, index=i):

            url = SITES[index]

            try:

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

    # Start all 5 sites simultaneously
    await asyncio.gather(*tasks)

    return pages


# ============================================================
# MAIN
# ============================================================

async def main():

    async with async_playwright() as p:

        cycle = 0

        while True:

            cycle += 1

            print()
            print("==========================================")
            print(f" Browserless cycle #{cycle}")
            print("==========================================")
            print()

            browser = None
            pages = []

            try:

                # ==================================================
                # CONNECT
                # ==================================================

                print("Connecting to Browserless...")

                browser = await p.chromium.connect_over_cdp(
                    WS_ENDPOINT
                )

                print("Connected successfully.")
                print()

                # Browserless default context
                context = browser.contexts[0]

                # ==================================================
                # LOAD ALL 5 SITES
                # ==================================================

                print("==========================================")
                print(" Loading all 5 sites simultaneously")
                print("==========================================")
                print()

                pages = await load_all_sites(context)

                print()
                print("==========================================")
                print(" ALL 5 SITES ARE OPEN")
                print("==========================================")
                print()

                # ==================================================
                # KEEP SESSION ALIVE FOR 2 MIN 10 SEC
                # ==================================================

                print("Connected for 2 minutes")
                print("Waiting...")

                await asyncio.sleep(SESSION_TIME)

                # ==================================================
                # DISCONNECT
                # ==================================================

                print()
                print("==========================================")
                print(" 2 MIN 10 SEC COMPLETE")
                print(" Disconnecting from Browserless...")
                print("==========================================")
                print()

            except Exception as e:

                print()
                print("==========================================")
                print(" Browserless error")
                print("==========================================")
                print()
                print(e)
                print()

            finally:

                # ==================================================
                # CLOSE PAGES
                # ==================================================

                for page in pages:

                    try:
                        await page.close()
                    except Exception:
                        pass

                # ==================================================
                # DISCONNECT BROWSERLESS
                # ==================================================

                if browser:

                    try:
                        await browser.close()
                    except Exception:
                        pass

                print("Disconnected from Browserless.")
                print()

            # ======================================================
            # RECONNECT
            # ======================================================

            print("Starting new Browserless connection...")
            print()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    try:

        asyncio.run(main())

    except KeyboardInterrupt:

        print()
        print("==========================================")
        print(" Script stopped by user.")
        print("==========================================")

