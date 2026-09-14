import asyncio
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from playwright.async_api import async_playwright


# ============================================================
# RAILWAY
# ============================================================

PORT = int(os.environ.get("PORT", "8080"))
HOST = "0.0.0.0"


class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Browser bot is running.")

    def log_message(self, format, *args):
        pass


def start_health_server():
    server = HTTPServer((HOST, PORT), HealthHandler)

    print("==========================================")
    print(" Railway health server started")
    print(f" Listening on {HOST}:{PORT}")
    print("==========================================")

    server.serve_forever()


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

PAGE_TIMEOUT = 60000


# ============================================================
# LOAD SITES
# ============================================================

async def load_all_sites(pages):

    tasks = []

    for i, page in enumerate(pages):

        async def load(page=page, index=i):

            url = SITES[index]

            print()
            print(f"[OPEN] {index + 1}/{len(SITES)}")
            print(f"       {url}")

            try:

                await page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=PAGE_TIMEOUT
                )

                print(f"[OK]   Site {index + 1}")

            except Exception as e:

                print(f"[ERROR] Site {index + 1}")
                print(f"        {type(e).__name__}: {e}")

        tasks.append(load())

    await asyncio.gather(*tasks)


# ============================================================
# MAIN
# ============================================================

async def main():

    # --------------------------------------------------------
    # Start Railway health server
    # --------------------------------------------------------

    health_thread = threading.Thread(
        target=start_health_server,
        daemon=True
    )

    health_thread.start()

    await asyncio.sleep(1)

    # --------------------------------------------------------
    # Start Playwright
    # --------------------------------------------------------

    async with async_playwright() as p:

        print()
        print("==========================================")
        print(" Starting Railway Chromium")
        print("==========================================")
        print()

        try:

            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-software-rasterizer",
                ]
            )

        except Exception as e:

            print()
            print("==========================================")
            print(" FAILED TO START CHROMIUM")
            print("==========================================")
            print()
            print(e)

            return

        print("Chromium started successfully.")
        print()

        # ----------------------------------------------------
        # Create browser context
        # ----------------------------------------------------

        context = await browser.new_context()

        pages = []

        # One page for each site
        for _ in SITES:

            page = await context.new_page()
            pages.append(page)

        print(f"Created {len(pages)} browser pages.")
        print()

        # ----------------------------------------------------
        # Open all 5 sites
        # ----------------------------------------------------

        print("==========================================")
        print(" Loading all 5 sites simultaneously")
        print("==========================================")
        print()

        await load_all_sites(pages)

        # ----------------------------------------------------
        # Keep browser alive
        # ----------------------------------------------------

        print()
        print("==========================================")
        print(" ALL 5 SITES ARE OPEN")
        print("==========================================")
        print()
        print(f"Total sites : {len(SITES)}")
        print()
        print("Chromium will remain running.")
        print("All browser pages will remain open.")
        print("Script will continue until Railway stops it.")
        print()

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
        print("Stopped.")
