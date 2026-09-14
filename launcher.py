import asyncio
import os
import signal
import sys
BOTS = [
    "bot1.py",
    "bot2.py",
    "bot3.py",
    "bot4.py",
]

START_DELAY = 30
RESTART_DELAY = 5
processes = {}
async def start_bot(bot_file):
    print(f"[STARTING] {bot_file}", flush=True)

    process = await asyncio.create_subprocess_exec(
        sys.executable,
        bot_file,
        stdout=None,
        stderr=None,
    )

    processes[bot_file] = process

    print(
        f"[STARTED] {bot_file} | PID={process.pid}",
        flush=True
    )

    return process


async def monitor_bot(bot_file):
    while True:
        try:
            process = await start_bot(bot_file)

            return_code = await process.wait()

            print(
                f"[EXITED] {bot_file} | code={return_code}",
                flush=True
            )

            print(
                f"[RESTART] {bot_file} in {RESTART_DELAY} seconds...",
                flush=True
            )

            await asyncio.sleep(RESTART_DELAY)

        except asyncio.CancelledError:
            raise

        except Exception as e:
            print(
                f"[ERROR] {bot_file}: {e}",
                flush=True
            )

            await asyncio.sleep(RESTART_DELAY)


async def main():
    print("==========================================", flush=True)
    print(" BOT LAUNCHER", flush=True)
    print("==========================================", flush=True)
    print(flush=True)

    tasks = []

    for index, bot_file in enumerate(BOTS):

        if index > 0:
            print(
                f"[WAIT] Waiting {START_DELAY} seconds before "
                f"starting {bot_file}...",
                flush=True
            )

            await asyncio.sleep(START_DELAY)

        task = asyncio.create_task(
            monitor_bot(bot_file)
        )

        tasks.append(task)

        print(
            f"[LAUNCH] {bot_file}",
            flush=True
        )

    print(flush=True)
    print("==========================================", flush=True)
    print(" ALL BOT PROCESSES HAVE BEEN STARTED", flush=True)
    print("==========================================", flush=True)
    print(flush=True)

    await asyncio.gather(*tasks)


async def shutdown():
    print(flush=True)
    print("==========================================", flush=True)
    print(" SHUTTING DOWN ALL BOTS", flush=True)
    print("==========================================", flush=True)

    for bot_file, process in list(processes.items()):
        if process and process.returncode is None:
            print(
                f"[STOP] {bot_file} | PID={process.pid}",
                flush=True
            )

            try:
                process.terminate()
            except Exception:
                pass

    await asyncio.sleep(2)

    for bot_file, process in list(processes.items()):
        if process and process.returncode is None:
            try:
                process.kill()
            except Exception:
                pass


def handle_signal():
    for task in asyncio.all_tasks():
        if task is not asyncio.current_task():
            task.cancel()


if __name__ == "__main__":
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        print("Launcher stopped.", flush=True)

    except asyncio.CancelledError:
        pass
