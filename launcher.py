
import asyncio
import os
import sys
import threading
import time

from flask import Flask, jsonify, render_template_string

# ============================================================
# CONFIG
# ============================================================

BOTS = [
    "bot1.py",
    "bot2.py",
    "bot3.py",
    "bot4.py",
]

START_DELAY = 30
RESTART_DELAY = 2

# ============================================================
# FLASK
# ============================================================

app = Flask(__name__)

# ============================================================
# GLOBAL STATE
# ============================================================

manager_thread = None
manager_loop = None

program_running = False
shutdown_event = None

processes = {}
process_lock = threading.Lock()


# ============================================================
# BOT START
# ============================================================

async def start_bot(bot_file):
    global processes

    print(f"[STARTING] {bot_file}", flush=True)

    process = await asyncio.create_subprocess_exec(
        sys.executable,
        bot_file,
        stdout=None,
        stderr=None,
    )

    with process_lock:
        processes[bot_file] = process

    print(
        f"[STARTED] {bot_file} | PID={process.pid}",
        flush=True
    )

    return process


# ============================================================
# BOT MONITOR
# ============================================================

async def monitor_bot(bot_file):
    global program_running

    while not shutdown_event.is_set():

        try:
            process = await start_bot(bot_file)

            # Wait until bot exits OR shutdown is requested
            while process.returncode is None:

                if shutdown_event.is_set():
                    break

                try:
                    await asyncio.wait_for(
                        process.wait(),
                        timeout=0.5
                    )
                except asyncio.TimeoutError:
                    pass

            # If OFF was pressed, stop the bot
            if shutdown_event.is_set():

                if process.returncode is None:
                    print(
                        f"[STOP] {bot_file} | PID={process.pid}",
                        flush=True
                    )

                    try:
                        process.terminate()
                    except Exception:
                        pass

                try:
                    await asyncio.wait_for(
                        process.wait(),
                        timeout=2
                    )
                except asyncio.TimeoutError:

                    try:
                        process.kill()
                    except Exception:
                        pass

                break

            return_code = process.returncode

            print(
                f"[EXITED] {bot_file} | code={return_code}",
                flush=True
            )

            if not shutdown_event.is_set():

                print(
                    f"[RESTART] {bot_file} "
                    f"in {RESTART_DELAY} seconds...",
                    flush=True
                )

                # Wait in small increments so OFF responds quickly
                for _ in range(RESTART_DELAY * 10):
                    if shutdown_event.is_set():
                        break

                    await asyncio.sleep(0.1)

        except asyncio.CancelledError:
            break

        except Exception as e:

            print(
                f"[ERROR] {bot_file}: {e}",
                flush=True
            )

            for _ in range(RESTART_DELAY * 10):
                if shutdown_event.is_set():
                    break

                await asyncio.sleep(0.1)

    with process_lock:
        processes.pop(bot_file, None)

    print(
        f"[MONITOR STOPPED] {bot_file}",
        flush=True
    )


# ============================================================
# LAUNCH ALL BOTS
# ============================================================

async def run_manager():
    global program_running

    print("==========================================", flush=True)
    print(" BOT MANAGER STARTED", flush=True)
    print("==========================================", flush=True)

    tasks = []

    for index, bot_file in enumerate(BOTS):

        if shutdown_event.is_set():
            break

        if index > 0:

            print(
                f"[WAIT] Waiting {START_DELAY} seconds "
                f"before starting {bot_file}...",
                flush=True
            )

            # Wait 30 seconds but allow OFF to interrupt it
            for _ in range(START_DELAY * 10):

                if shutdown_event.is_set():
                    break

                await asyncio.sleep(0.1)

        if shutdown_event.is_set():
            break

        print(
            f"[LAUNCH] {bot_file}",
            flush=True
        )

        task = asyncio.create_task(
            monitor_bot(bot_file)
        )

        tasks.append(task)

    if tasks:
        await asyncio.gather(*tasks)

    with process_lock:
        processes.clear()

    program_running = False

    print("==========================================", flush=True)
    print(" BOT MANAGER STOPPED", flush=True)
    print("==========================================", flush=True)


# ============================================================
# MANAGER THREAD
# ============================================================

def manager_worker():
    global manager_loop

    manager_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(manager_loop)

    try:
        manager_loop.run_until_complete(
            run_manager()
        )

    finally:
        manager_loop.close()


# ============================================================
# START PROGRAM
# ============================================================

def start_program():

    global manager_thread
    global shutdown_event
    global program_running

    if program_running:
        return False

    print("==========================================")
    print(" TURNING PROGRAM ON")
    print("==========================================")

    shutdown_event = threading.Event()

    program_running = True

    manager_thread = threading.Thread(
        target=manager_worker,
        daemon=True
    )

    manager_thread.start()

    return True


# ============================================================
# STOP PROGRAM
# ============================================================

def stop_program():

    global program_running

    if not program_running:
        return False

    print("==========================================")
    print(" TURNING PROGRAM OFF")
    print("==========================================")

    shutdown_event.set()

    # Stop all running processes immediately
    with process_lock:

        for bot_file, process in list(processes.items()):

            if process and process.returncode is None:

                print(
                    f"[STOP] {bot_file} | PID={process.pid}"
                )

                try:
                    process.terminate()
                except Exception:
                    pass

    # Give processes a moment to exit
    time.sleep(2)

    # Kill anything still alive
    with process_lock:

        for bot_file, process in list(processes.items()):

            if process and process.returncode is None:

                print(
                    f"[KILL] {bot_file} | PID={process.pid}"
                )

                try:
                    process.kill()
                except Exception:
                    pass

        processes.clear()

    program_running = False

    return True


# ============================================================
# STATUS
# ============================================================

def get_status():

    with process_lock:

        bot_status = {}

        for bot in BOTS:

            process = processes.get(bot)

            if process and process.returncode is None:

                bot_status[bot] = {
                    "running": True,
                    "pid": process.pid
                }

            else:

                bot_status[bot] = {
                    "running": False,
                    "pid": None
                }

    return bot_status


# ============================================================
# FLASK ROUTES
# ============================================================

@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/on")
def turn_on():

    started = start_program()

    return jsonify({
        "success": True,
        "running": program_running,
        "message": "Program turned ON"
            if started
            else "Program is already ON"
    })


@app.route("/off")
def turn_off():

    stopped = stop_program()

    return jsonify({
        "success": True,
        "running": program_running,
        "message": "Program turned OFF"
            if stopped
            else "Program is already OFF"
    })


@app.route("/status")
def status():

    return jsonify({
        "running": program_running,
        "bots": get_status()
    })


# ============================================================
# WEB UI
# ============================================================

HTML = r"""
<!DOCTYPE html>
<html>

<head>

<meta charset="UTF-8">

<title>Bot Controller</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    min-height: 100vh;

    display: flex;
    justify-content: center;
    align-items: center;

    background: #0d0d12;
    color: white;

    font-family: Arial, sans-serif;
}

.container {
    width: 500px;

    background: #15151d;

    border: 1px solid #292936;

    border-radius: 16px;

    padding: 30px;

    box-shadow:
        0 20px 60px rgba(0,0,0,.5);
}

h1 {
    margin-top: 0;
    margin-bottom: 8px;

    text-align: center;
}

.subtitle {
    text-align: center;

    color: #888;

    margin-bottom: 25px;
}

.status-box {
    padding: 18px;

    border-radius: 12px;

    background: #0d0d12;

    text-align: center;

    margin-bottom: 20px;
}

.status {
    font-size: 24px;
    font-weight: bold;
}

.online {
    color: #36e07f;
}

.offline {
    color: #ff4d5a;
}

.buttons {
    display: flex;

    gap: 12px;

    margin-bottom: 25px;
}

button {
    flex: 1;

    border: 0;

    padding: 15px;

    border-radius: 10px;

    font-size: 16px;

    font-weight: bold;

    cursor: pointer;
}

.on-btn {
    background: #36e07f;
    color: #07140c;
}

.off-btn {
    background: #ff4d5a;
    color: white;
}

button:hover {
    opacity: .85;
}

.bot {
    display: flex;

    justify-content: space-between;

    align-items: center;

    padding: 12px 14px;

    margin-top: 8px;

    background: #1c1c26;

    border-radius: 8px;
}

.bot-name {
    font-weight: bold;
}

.bot-status {
    font-size: 13px;

    color: #888;
}

.running {
    color: #36e07f;
}

.stopped {
    color: #ff4d5a;
}

</style>

</head>

<body>

<div class="container">

    <h1>BOT CONTROLLER</h1>

    <div class="subtitle">
        Flask Bot Manager
    </div>

    <div class="status-box">

        <div id="programStatus"
             class="status offline">
            OFF
        </div>

    </div>

    <div class="buttons">

        <button
            class="on-btn"
            onclick="turnOn()">
            ON
        </button>

        <button
            class="off-btn"
            onclick="turnOff()">
            OFF
        </button>

    </div>

    <h3>Bots</h3>

    <div id="bots"></div>

</div>


<script>

async function turnOn() {

    await fetch("/on");

    updateStatus();
}


async function turnOff() {

    await fetch("/off");

    updateStatus();
}


async function updateStatus() {

    try {

        const response =
            await fetch("/status");

        const data =
            await response.json();


        const status =
            document.getElementById(
                "programStatus"
            );


        if (data.running) {

            status.innerText = "ON";

            status.className =
                "status online";

        } else {

            status.innerText = "OFF";

            status.className =
                "status offline";
        }


        const bots =
            document.getElementById("bots");

        bots.innerHTML = "";


        for (
            const [name, info]
            of Object.entries(data.bots)
        ) {

            const div =
                document.createElement("div");

            div.className = "bot";


            if (info.running) {

                div.innerHTML = `
                    <div class="bot-name">
                        ${name}
                    </div>

                    <div class="bot-status running">
                        RUNNING | PID ${info.pid}
                    </div>
                `;

            } else {

                div.innerHTML = `
                    <div class="bot-name">
                        ${name}
                    </div>

                    <div class="bot-status stopped">
                        STOPPED
                    </div>
                `;
            }


            bots.appendChild(div);
        }

    } catch (error) {

        console.log(error);

    }

}


// Update every 1 second

setInterval(updateStatus, 1000);

updateStatus();

</script>

</body>

</html>
"""


# ============================================================
# START FLASK
# ============================================================

if __name__ == "__main__":

    print()
    print("==========================================")
    print(" BOT CONTROL WEB APP")
    print("==========================================")
    print()
    print("Open in browser:")
    print("http://127.0.0.1:5000")
    print()
    print("==========================================")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        threaded=True
    )
