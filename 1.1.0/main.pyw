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
                                                              





# ============================================ #
# Importation & Vérification Bibliothèques
# ============================================ #


def install_requirements_graphically():
    import os
    import queue
    import subprocess
    import sys
    import threading
    from pathlib import Path

    import tkinter as tk
    from tkinter import messagebox, scrolledtext, ttk

    base_dir = Path(__file__).resolve().parent
    requirements_file = base_dir / "requirements.txt"
    if not requirements_file.exists():
        messagebox.showerror(
            "Installation impossible",
            f"Le fichier {requirements_file.name} est introuvable.",
        )
        raise FileNotFoundError(requirements_file)

    events = queue.Queue()
    result = {"ok": False, "message": ""}

    root = tk.Tk()
    root.title("Valane Statistiques - Installation")
    root.geometry("620x380")
    root.resizable(False, False)

    frame = tk.Frame(root, padx=18, pady=16)
    frame.pack(fill=tk.BOTH, expand=True)

    tk.Label(
        frame,
        text="Installation des bibliotheques requises",
        font=("Segoe UI", 15, "bold"),
        anchor="w",
    ).pack(fill=tk.X)

    status_var = tk.StringVar(value="Preparation de l'installation...")
    tk.Label(
        frame,
        textvariable=status_var,
        font=("Segoe UI", 10),
        anchor="w",
        justify=tk.LEFT,
        wraplength=570,
    ).pack(fill=tk.X, pady=(8, 12))

    progress = ttk.Progressbar(frame, mode="indeterminate")
    progress.pack(fill=tk.X, pady=(0, 12))
    progress.start(12)

    logs = scrolledtext.ScrolledText(frame, height=12, state=tk.DISABLED)
    logs.pack(fill=tk.BOTH, expand=True)

    close_btn = tk.Button(frame, text="Fermer", state=tk.DISABLED, command=root.destroy)
    close_btn.pack(anchor="e", pady=(12, 0))

    def append_log(text):
        logs.configure(state=tk.NORMAL)
        logs.insert(tk.END, text)
        logs.see(tk.END)
        logs.configure(state=tk.DISABLED)

    def worker():
        try:
            cmd = [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)]
            events.put(("status", "Installation en cours avec pip..."))
            process = subprocess.Popen(
                cmd,
                cwd=str(base_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            for line in process.stdout or []:
                events.put(("log", line))
            return_code = process.wait()
            if return_code == 0:
                result["ok"] = True
                result["message"] = "Installation terminee."
            else:
                result["message"] = f"pip a retourne le code {return_code}."
        except Exception as exc:
            result["message"] = str(exc)
        finally:
            events.put(("done", result["message"]))

    def pump_events():
        try:
            while True:
                kind, value = events.get_nowait()
                if kind == "status":
                    status_var.set(value)
                elif kind == "log":
                    append_log(value)
                elif kind == "done":
                    progress.stop()
                    status_var.set(value)
                    close_btn.configure(state=tk.NORMAL)
                    if result["ok"]:
                        root.after(700, root.destroy)
        except queue.Empty:
            pass
        try:
            root.after(100, pump_events)
        except tk.TclError:
            pass

    threading.Thread(target=worker, daemon=True).start()
    root.after(100, pump_events)
    root.mainloop()

    if not result["ok"]:
        messagebox.showerror(
            "Installation echouee",
            result["message"] or "Impossible d'installer les bibliotheques requises.",
        )
        raise RuntimeError(result["message"])


try:
    from pathlib import Path
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi import Form
    from fastapi.staticfiles import StaticFiles
    from typing import Annotated
    import os
    import subprocess
    import sys
    import fastapi
    import uvicorn
    import ui
    import threading
    import requests
    import time
except ImportError as e:
    print("Erreur d'importation, lancement de l'installation des bibliotèques requises...")
    import sys
    import subprocess
    try:
        # sys.executable récupère le chemin du Python actuellement utilisé
        install_requirements_graphically()
        print("Installation réussie !")
        from pathlib import Path
        from fastapi.responses import HTMLResponse, JSONResponse
        from fastapi import Form
        from fastapi.staticfiles import StaticFiles
        from typing import Annotated
        import os
        import fastapi
        import uvicorn
        import ui
        import threading
        import requests
        import time
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de l'installation : {e}")



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
    DEV = False

    if startMethod == 0:
        # Start the FastAPI server as a detached subprocess so it doesn't depend on the parent terminal
        try:
            server_code = (
                "import runpy, uvicorn; "
                f"ns = runpy.run_path({str(__file__)!r}); "
                "uvicorn.run(ns['app'], host=ns['HOST'], port=ns['PORT'])"
            )
            cmd = [sys.executable, "-c", server_code]
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

        # Enter the Qt main loop
        app_obj.exec()
    elif startMethod == 1:
        uvicorn.run(app, host=HOST, port=PORT)
    elif startMethod == 2:
        ui.run(URL=f"{BASE_URL}/", dev=DEV)
