import json
import requests
import os
os.system("cls" if os.name == "nt" else "clear")



# ============================================ #
# Variables de bases
# ============================================ #
GITHUB_URL = "https://github.com/theemberforge2nd/ValaneStat/raw/refs/heads/main/"
versions = json.load(open("version.json", "r"))["current"] 
onlineVersions = json.loads(requests.get(f"{GITHUB_URL}versions.json").text)



# ============================================ #
# Fonction de téléchargement d'une update
# ============================================ #
def downloadUpdate(version):
    files = requests.get(f"{GITHUB_URL}{version}/files.json").json()["files"]
    for file in files:
        if not os.path.exists(file) or (os.path.exists(file) and requests.get(f"{GITHUB_URL}{version}/{file}").text != open(file, "r").read()):
            print(f"Downloading {file}...")
            with open(file, "w", encoding="utf-8") as f:
                f.write(requests.get(f"{GITHUB_URL}{version}/{file}").text)
        else:
            print(f"{file} is already up to date.")

            


# ============================================ #
# Check les updates
# ============================================ #
def checkUpdate():

    for forcedVersion in onlineVersions["forceUpdate"]:
        if forcedVersion.startswith(versions):
            print(f"\nForced update: {forcedVersion}\n")
            downloadUpdate(forcedVersion.split(f"{versions} to ")[1])
            return
        
    if versions != onlineVersions["last"]:
        print(f"New version available: {onlineVersions['last']} (current: {versions})")

checkUpdate()
