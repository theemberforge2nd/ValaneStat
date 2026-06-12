#     /$$$$$$            /$$       /$$                                            /$$$$$$   /$$                     /$$ /$$          
#    /$$__  $$          | $$      | $$                                           /$$__  $$ | $$                    | $$|__/          
#   | $$  \ $$  /$$$$$$$| $$$$$$$ | $$$$$$$   /$$$$$$   /$$$$$$  /$$$$$$$       | $$  \__//$$$$$$   /$$   /$$  /$$$$$$$ /$$  /$$$$$$ 
#   | $$$$$$$$ /$$_____/| $$__  $$| $$__  $$ /$$__  $$ /$$__  $$| $$__  $$      |  $$$$$$|_  $$_/  | $$  | $$ /$$__  $$| $$ /$$__  $$
#   | $$__  $$|  $$$$$$ | $$  \ $$| $$  \ $$| $$  \ $$| $$  \__/| $$  \ $$       \____  $$ | $$    | $$  | $$| $$  | $$| $$| $$  \ $$
#   | $$  | $$ \____  $$| $$  | $$| $$  | $$| $$  | $$| $$      | $$  | $$       /$$  \ $$ | $$ /$$| $$  | $$| $$  | $$| $$| $$  | $$
#   | $$  | $$ /$$$$$$$/| $$  | $$| $$$$$$$/|  $$$$$$/| $$      | $$  | $$      |  $$$$$$/ |  $$$$/|  $$$$$$/|  $$$$$$$| $$|  $$$$$$/
#   |__/  |__/|_______/ |__/  |__/|_______/  \______/ |__/      |__/  |__/       \______/   \___/   \______/  \_______/|__/ \______/  
#    _   _       _                             _____ _        _   
#   | | | |     | |    V1.0.0 - 2024-06-01    /  ___| |      | |  
#   | | | | __ _| | __ _ _ __   ___   ______  \ `--.| |_ __ _| |_ 
#   | | | |/ _` | |/ _` | '_ \ / _ \ |______|  `--. \ __/ _` | __|
#   \ \_/ / (_| | | (_| | | | |  __/          /\__/ / || (_| | |_ 
#    \___/ \__,_|_|\__,_|_| |_|\___|          \____/ \__\__,_|\__|
                                                              
                                                     



from pathlib import Path
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi import Form
from fastapi.staticfiles import StaticFiles
from typing import Annotated
import fastapi
import uvicorn
import ui
import threading
import os
import sys
import subprocess
import requests
import updater
import time



# ============================================ #
# Commandes de démarrage
# ============================================ #
# Clear console only if running in a real terminal
try:
    if getattr(sys, "stdout", None) and sys.stdout.isatty():
        os.system("cls" if os.name == "nt" else "clear")
except Exception:
    pass



# ============================================ #
# Variables
# ============================================ #
BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
HOST = "127.0.0.1"
PORT = 8080
BASE_URL = f"http://{HOST}:{PORT}"

app = fastapi.FastAPI(title="Valane Statistiques")

# Serve static files (CSS, JS, images) from templates/static
static_dir = BASE_DIR / "templates" / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


def render_template(path: str):
    p = BASE_DIR / "templates" / path
    if not p.exists():
        return HTMLResponse(content=f"<h1>Template not found: {path}</h1>", status_code=404)
    return HTMLResponse(content=p.read_text(encoding="utf-8"), media_type="text/html")



# ============================================ #
# Frontend
# ============================================ #
@app.get("/", response_class=HTMLResponse)
async def home():
    return render_template("index.html")

@app.get("/about/", response_class=HTMLResponse)
async def about():
    return render_template("pages/about.html")

@app.get("/stats/ah/", response_class=HTMLResponse)
async def stats_ah():
    return render_template("pages/stats/ah.html")

@app.get("/stats/players/", response_class=HTMLResponse)
async def stats_players():
    return render_template("pages/stats/players.html")

@app.get("/stats/playersShop/", response_class=HTMLResponse)
async def stats_playerShop():
    return render_template("pages/stats/playersShop.html")



# ============================================ #
# API Définition
# ============================================ #
@app.get("/api/stats/ah", response_class=JSONResponse)
async def api_stats_ah():
    offset = 0
    resp = requests.get(f"https://api.valane.fr/api/v1/module/hdv/items?limit=500&offset={offset}")
    liste = [].append(resp.json()["data"]["items"])
    while resp.json()["data"]["count"] == resp.json()["data"]["limit"]:
        offset += 500
        resp = requests.get(f"https://api.valane.fr/api/v1/module/hdv/items?limit=500&offset={offset}")
        liste = [].append(resp.json()["data"]["items"])
    resp = resp.json()
    resp["data"]["shops"] = liste
    return JSONResponse(content=resp)

@app.get("/api/stats/playersShop", response_class=JSONResponse)
async def api_stats_playersShop():
    offset = 0
    resp = requests.get(f"https://api.valane.fr/api/v1/module/shop/shops?limit=500&offset={offset}")
    liste = [].append(resp.json()["data"]["shops"])
    while resp.json()["data"]["count"] == resp.json()["data"]["limit"]:
        offset += 500
        resp = requests.get(f"https://api.valane.fr/api/v1/module/shop/shops?limit=500&offset={offset}")
        liste = [].append(resp.json()["data"]["shops"])
    resp = resp.json()
    resp["data"]["shops"] = liste
    return JSONResponse(content=resp)

# Normalement ce sont les autres fonctions qui y font appel
@app.post("/api/stats/players", response_class=JSONResponse)
async def api_stats_players(player: Annotated[str, Form()]):
    resp = requests.get(f"https://api.valane.fr/api/v1/module/seen/players/{player}")
    return JSONResponse(content=resp.json())



if __name__ == "__main__":
    
    startMethod = 0
    DEV = True

    if not DEV:
        updater.checkUpdate()

    if startMethod == 0:
        # Start the FastAPI server as a detached subprocess so it doesn't depend on the parent terminal
        try:
            cmd = [sys.executable, "-m", "uvicorn", "main:app", "--host", HOST, "--port", str(PORT)]
            if os.name == "nt":
                creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
                subprocess.Popen(cmd, cwd=str(BASE_DIR), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, creationflags=creationflags)
            else:
                subprocess.Popen(cmd, cwd=str(BASE_DIR), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, preexec_fn=os.setsid)
        except Exception:
            # Fallback to starting uvicorn in a background thread
            server_thread = threading.Thread(target=lambda: uvicorn.run(app, host=HOST, port=PORT), daemon=True)
            server_thread.start()

        time.sleep(0.2)

        # QApplication and all Qt objects must be created and used from the main thread
        # Create the app/window first so we can show an update dialog while checking for updates.
        app_obj, window = ui.create_app(URL=f"{BASE_URL}/", dev=DEV)

        # Run updater in background so it can interact with the GUI (show dialog/progress)
        if not DEV:
            updater_thread = threading.Thread(target=lambda: updater.checkUpdate(ui_handler=window), daemon=True)
            updater_thread.start()

        # Enter the Qt main loop
        app_obj.exec()
    elif startMethod == 1:
        uvicorn.run(app, host=HOST, port=PORT)
    elif startMethod == 2:
        ui.run(URL=f"{BASE_URL}/", dev=DEV)