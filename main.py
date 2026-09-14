import asyncio
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from playwright.async_api import async_playwright


# ============================================================
# RAILWAY HTTP SERVER
# ============================================================

PORT = int(os.environ.get("PORT", "8080"))
HOST = "0.0.0.0"


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()

        self.wfile.write(
            b"Railway Chromium bot is running.\n"
        )

    def log_message(self, format, *args):
        # Prevent unnecessary HTTP request logs
        return


def start_http_server():
    server = HTTPServer((HOST, PORT), HealthHandler)

    print("==========================================")
    print(" Railway HTTP server started")
    print(f" Host : {HOST}")
    print(f" Port : {PORT}")
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

# 60 seconds is enough for normal page loading.
# A failed/slow site will not block the whole program for hours.
PAGE_TIMEOUT = 60_000


# ============================================================
# LOAD ALL SITES
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
                    timeout=PAGE_TIMEOUT,
                )

                print(f"[OK] Site {index + 1} loaded")

            except Exception as e:
                print(f"[ERROR] Site {index + 1}")
                print(f"        {type(e).__name__}: {e}")

        tasks.append(load())

    await asyncio.gather(*tasks)


# ============================================================
# MAIN
# ============================================================

async def main():

    print()
    print("==========================================")
    print(" Starting Railway Chromium")
    print("==========================================")
    print()

    print(f"Railway PORT: {PORT}")
    print(f"Sites to open: {len(SITES)}")
    print()

    # --------------------------------------------------------
    # Start Railway HTTP server in background
    # --------------------------------------------------------

    http_thread = threading.Thread(
        target=start_http_server,
        daemon=True,
    )

    http_thread.start()

    # Give the HTTP server a moment to start
    await asyncio.sleep(1)

    # --------------------------------------------------------
    # Start Playwright
    # --------------------------------------------------------

    async with async_playwright() as p:

        print("Starting Chromium...")

        try:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-software-rasterizer",
                ],
            )

        except Exception as e:
            print()
            print("==========================================")
            print(" FAILED TO START CHROMIUM")
            print("==========================================")
            print()
            print(type(e).__name__)
            print(e)
            return

        print("Chromium started successfully.")
        print()

        # ----------------------------------------------------
        # Browser context
        # ----------------------------------------------------

        context = await browser.new_context()

        pages = []

        for _ in SITES:
            page = await context.new_page()
            pages.append(page)

        print(f"Created {len(pages)} browser pages.")
        print()

        # ----------------------------------------------------
        # Load all sites
        # ----------------------------------------------------

        print("==========================================")
        print(" Loading all sites")
        print("==========================================")
        print()

        await load_all_sites(pages)

        # ----------------------------------------------------
        # Finished
        # ----------------------------------------------------

        print()
        print("==========================================")
        print(" ALL SITES HAVE BEEN PROCESSED")
        print("==========================================")
        print()

        print(f"Total sites : {len(SITES)}")
        print(f"HTTP port  : {PORT}")
        print()
        print("Chromium will remain running.")
        print("Railway HTTP server will remain running.")
        print()

        # ----------------------------------------------------
        # Keep Chromium and pages alive
        # ----------------------------------------------------

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
