#     /$$$$$$            /$$       /$$                                            /$$$$$$   /$$                     /$$ /$$          
#    /$$__  $$          | $$      | $$                                           /$$__  $$ | $$                    | $$|__/          
#   | $$  \ $$  /$$$$$$$| $$$$$$$ | $$$$$$$   /$$$$$$   /$$$$$$  /$$$$$$$       | $$  \__//$$$$$$   /$$   /$$  /$$$$$$$ /$$  /$$$$$$ 
#   | $$$$$$$$ /$$_____/| $$__  $$| $$__  $$ /$$__  $$ /$$__  $$| $$__  $$      |  $$$$$$|_  $$_/  | $$  | $$ /$$__  $$| $$ /$$__  $$
#   | $$__  $$|  $$$$$$ | $$  \ $$| $$  \ $$| $$  \ $$| $$  \__/| $$  \ $$       \____  $$ | $$    | $$  | $$| $$  | $$| $$| $$  \ $$
#   | $$  | $$ \____  $$| $$  | $$| $$  | $$| $$  | $$| $$      | $$  | $$       /$$  \ $$ | $$ /$$| $$  | $$| $$  | $$| $$| $$  | $$
#   | $$  | $$ /$$$$$$$/| $$  | $$| $$$$$$$/|  $$$$$$/| $$      | $$  | $$      |  $$$$$$/ |  $$$$/|  $$$$$$/|  $$$$$$$| $$|  $$$$$$/
#   |__/  |__/|_______/ |__/  |__/|_______/  \______/ |__/      |__/  |__/       \______/   \___/   \______/  \_______/|__/ \______/ 
#    _   _           _       _            
#   | | | |  V1.0.0 | |     | |           
#   | | | |_ __   __| | __ _| |_ ___ _ __ 
#   | | | | '_ \ / _` |/ _` | __/ _ \ '__|
#   | |_| | |_) | (_| | (_| | ||  __/ |   
#    \___/| .__/ \__,_|\__,_|\__\___|_|   
#         | |                             
#         |_|   





# ============================================ #
# Importations
# ============================================ #
import json
import requests
import os



# ============================================ #
# Variables de bases
# ============================================ #
GITHUB_URL = "https://github.com/theemberforge2nd/ValaneStat/raw/refs/heads/main/"
versions = json.load(open("version.json", "r"))["current"] 
onlineVersions = json.loads(requests.get(f"{GITHUB_URL}versions.json").text)



# ============================================ #
# Fonction de téléchargement d'une update
# ============================================ #
def downloadUpdate(version, ui_handler=None):
    files = requests.get(f"{GITHUB_URL}{version}/files.json").json()["files"]
    total = len(files)
    for idx, file in enumerate(files):
        try:
            remote = requests.get(f"{GITHUB_URL}{version}/{file}").text
        except Exception as e:
            if ui_handler:
                ui_handler.update_update_progress(0, f"Erreur réseau: {e}")
            else:
                print(f"Network error: {e}")
            continue

        need_write = True
        if os.path.exists(file):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    local = f.read()
                if local == remote:
                    need_write = False
            except Exception:
                need_write = True

        if need_write:
            if ui_handler:
                ui_handler.update_update_progress(int((idx / total) * 100), f"Téléchargement: {file} ({idx+1}/{total})")
            with open(file, "w", encoding="utf-8") as f:
                f.write(remote)
        else:
            if not ui_handler:
                print(f"{file} is already up to date.")

        # update progress after each file
        if ui_handler:
            ui_handler.update_update_progress(int(((idx + 1) / total) * 100), f"Traitement: {file} ({idx+1}/{total})")

            

# ============================================ #
# Check les updates
# ============================================ #
def checkUpdate(ui_handler=None):

    for forcedVersion in onlineVersions.get("forceUpdate", []):
        if forcedVersion.startswith(versions):
            version_to = forcedVersion.split(f"{versions} to ")[1]
            if ui_handler:
                # show forced update dialog and auto-start install
                ui_handler.run_on_main(lambda: ui_handler.show_update_dialog("Mise à jour forcée", f"Une mise à jour vers {version_to} est requise.", forced=True))
                # wait for user's install choice (or auto for forced)
                try:
                    ui_handler._update_choice_event.wait()
                except Exception:
                    pass
                # proceed with download if install chosen
                if getattr(ui_handler, '_update_choice_install', True):
                    downloadUpdate(version_to, ui_handler=ui_handler)
                    ui_handler.update_update_progress(100, "Mise à jour terminée")
                    ui_handler.run_on_main(lambda: ui_handler.close_update_dialog())
                return
            else:
                print(f"\nForced update: {forcedVersion}\n")
                downloadUpdate(forcedVersion.split(f"{versions} to ")[1])
                return

    if versions != onlineVersions.get("last"):
        latest = onlineVersions.get('last')
        if ui_handler:
            ui_handler.run_on_main(lambda: ui_handler.show_update_dialog("Mise à jour disponible", f"Nouvelle version disponible: {latest} (actuelle: {versions})", forced=False))
            try:
                ui_handler._update_choice_event.wait()
            except Exception:
                pass
            if getattr(ui_handler, '_update_choice_install', False):
                downloadUpdate(latest, ui_handler=ui_handler)
                ui_handler.update_update_progress(100, "Mise à jour terminée")
                ui_handler.run_on_main(lambda: ui_handler.close_update_dialog())
            return
        else:
            print(f"New version available: {onlineVersions['last']} (current: {versions})")



# ============================================ #
# Lancement de l'updater manuellement
# ============================================ #
if __name__ == "__main__":
    os.system("cls" if os.name == "nt" else "clear")
    checkUpdate()