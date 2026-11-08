
import asyncio
import os
import signal
import sys
from pathlib import Path

# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

BOTS = [
    "bot1.py",
    "bot2.py",
    "bot3.py",
    "bot4.py",
]

START_DELAY = 30
RESTART_DELAY = 2
CHECK_INTERVAL = 0.5

# ============================================================
# GLOBAL STATE
# ============================================================

shutdown_event = None
processes = {}


# ============================================================
# LOGGING
# ============================================================

def log(message):
    print(message, flush=True)


# ============================================================
# START BOT
# ============================================================

async def start_bot(bot_file):

    bot_path = BASE_DIR / bot_file

    log(f"[STARTING] {bot_file}")

    process = await asyncio.create_subprocess_exec(
        sys.executable,
        str(bot_path),
        cwd=str(BASE_DIR),
        stdout=None,
        stderr=None
    )

    processes[bot_file] = process

    log(
        f"[STARTED] {bot_file} | PID={process.pid}"
    )

    return process


# ============================================================
# STOP BOT
# ============================================================

async def stop_bot(bot_file, process):

    if process.returncode is not None:
        return

    log(
        f"[STOP] {bot_file} | PID={process.pid}"
    )

    try:
        process.terminate()
    except ProcessLookupError:
        pass

    try:
        await asyncio.wait_for(
            process.wait(),
            timeout=5
        )

    except asyncio.TimeoutError:

        log(f"[KILL] {bot_file} | PID={process.pid}")

        try:
            process.kill()
        except ProcessLookupError:
            pass

        await process.wait()


# ============================================================
# BOT MONITOR
# ============================================================

async def monitor_bot(bot_file):

    while not shutdown_event.is_set():

        process = None

        try:

            process = await start_bot(bot_file)

            # Monitor the bot continuously

            while (
                process.returncode is None
                and not shutdown_event.is_set()
            ):

                await asyncio.sleep(CHECK_INTERVAL)

            # Shutdown requested

            if shutdown_event.is_set():

                await stop_bot(bot_file, process)
                break

            # Bot exited unexpectedly

            return_code = await process.wait()

            log(
                f"[EXITED] {bot_file} | code={return_code}"
            )

        except asyncio.CancelledError:
            raise

        except Exception as e:

            log(
                f"[ERROR] {bot_file}: {e}"
            )

        finally:

            if process is not None:
                processes.pop(bot_file, None)

        # Restart after 2 seconds

        if not shutdown_event.is_set():

            log(
                f"[RESTART] {bot_file} "
                f"in {RESTART_DELAY} seconds..."
            )

            try:
                await asyncio.wait_for(
                    shutdown_event.wait(),
                    timeout=RESTART_DELAY
                )

            except asyncio.TimeoutError:
                pass

    log(f"[MONITOR STOPPED] {bot_file}")


# ============================================================
# DELAY WITH SHUTDOWN SUPPORT
# ============================================================

async def wait_or_shutdown(seconds):

    try:

        await asyncio.wait_for(
            shutdown_event.wait(),
            timeout=seconds
        )

        return True

    except asyncio.TimeoutError:

        return False


# ============================================================
# BOT MANAGER
# ============================================================

async def run_manager():

    log("==========================================")
    log(" AUTOMATIC BOT MANAGER STARTED")
    log("==========================================")

    tasks = []

    try:

        for index, bot_file in enumerate(BOTS):

            if shutdown_event.is_set():
                break

            # Wait before starting the next bot

            if index > 0:

                log(
                    f"[WAIT] Waiting {START_DELAY} seconds "
                    f"before starting {bot_file}..."
                )

                stopped = await wait_or_shutdown(
                    START_DELAY
                )

                if stopped:
                    break

            if shutdown_event.is_set():
                break

            log(f"[LAUNCH] {bot_file}")

            task = asyncio.create_task(
                monitor_bot(bot_file)
            )

            tasks.append(task)

        # Keep all bot monitors alive

        if tasks:

            await asyncio.gather(*tasks)

    finally:

        shutdown_event.set()

        # Wait for all monitors to stop

        if tasks:

            await asyncio.gather(
                *tasks,
                return_exceptions=True
            )

        log("==========================================")
        log(" ALL BOTS STOPPED")
        log(" BOT MANAGER SHUTDOWN COMPLETE")
        log("==========================================")


# ============================================================
# MAIN
# ============================================================

async def main():

    global shutdown_event

    shutdown_event = asyncio.Event()

    loop = asyncio.get_running_loop()

    # Handle Railway shutdown signals

    for sig in (signal.SIGTERM, signal.SIGINT):

        try:

            loop.add_signal_handler(
                sig,
                shutdown_event.set
            )

        except (NotImplementedError, RuntimeError):

            pass

    log("")
    log("==========================================")
    log(" RAILWAY 24/7 BOT LAUNCHER")
    log("==========================================")
    log(" Automatic startup enabled")
    log(" No ON/OFF endpoint required")
    log(" Restart delay: 2 seconds")
    log(" Bot start interval: 30 seconds")
    log("==========================================")
    log("")

    await run_manager()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    try:

        asyncio.run(main())

    except KeyboardInterrupt:

        log("[SHUTDOWN] Keyboard interrupt received")

