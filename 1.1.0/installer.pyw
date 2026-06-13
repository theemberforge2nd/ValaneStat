#!/usr/bin/env python3
"""Installateur avec interface CustomTkinter (remplace les sorties console)."""

import os
import shutil
import sys
import threading
import queue
from pathlib import Path

import customtkinter as tk
from tkinter import messagebox
import tempfile
import subprocess

try:
    import requests
except Exception:
    root = tk.CTk()
    root.withdraw()
    messagebox.showerror(
        "Dépendance manquante",
        "Le paquet 'requests' est requis. Installez-le avec : pip install requests",
    )
    sys.exit(1)


REPO_RAW = "https://raw.githubusercontent.com/theemberforge2nd/ValaneStat/main/"
PYTHON_INSTALLER_URL = "https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe"
DEV = False  # True: simule une premiere installation meme si l'application existe deja.
PYTHON_INSTALLER_NAMES = (
    "python-installer.exe",
    "python-3.12.8-amd64.exe",
    "python-3.12-amd64.exe",
)


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def app_base_dir() -> Path:
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def bundled_base_dir() -> Path:
    return Path(getattr(sys, "_MEIPASS", app_base_dir()))


def candidate_python_installers():
    bases = [app_base_dir(), bundled_base_dir(), Path.cwd()]
    seen = set()
    for base in bases:
        for name in PYTHON_INSTALLER_NAMES:
            candidate = (base / name).resolve()
            if candidate not in seen:
                seen.add(candidate)
                yield candidate


def _valid_python_executable(path: str | Path) -> bool:
    try:
        candidate = Path(path)
        if is_frozen() and candidate.resolve() == Path(sys.executable).resolve():
            return False
        result = subprocess.run(
            [str(candidate), "-c", "import sys; print(sys.version_info[0])"],
            capture_output=True,
            text=True,
            timeout=8,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        return result.returncode == 0 and result.stdout.strip() == "3"
    except Exception:
        return False


def find_python_executable(prefer_windowed: bool = False) -> str | None:
    names = ("pythonw.exe", "python.exe") if prefer_windowed else ("python.exe", "pythonw.exe")

    for name in names:
        found = shutil.which(name)
        if found and _valid_python_executable(found):
            return found

    launcher = shutil.which("py.exe") or shutil.which("py")
    if launcher and not prefer_windowed:
        try:
            result = subprocess.run(
                [launcher, "-3", "-c", "import sys; print(sys.executable)"],
                capture_output=True,
                text=True,
                timeout=8,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            candidate = result.stdout.strip()
            if result.returncode == 0 and candidate and _valid_python_executable(candidate):
                return candidate
        except Exception:
            pass

    roots = [
        Path(os.getenv("LOCALAPPDATA", "")) / "Programs" / "Python",
        Path(os.getenv("ProgramFiles", "")) / "Python312",
        Path(os.getenv("ProgramFiles", "")) / "Python311",
        Path(os.getenv("ProgramFiles(x86)", "")) / "Python312",
        Path(os.getenv("ProgramFiles(x86)", "")) / "Python311",
    ]
    for root in roots:
        if not str(root) or not root.exists():
            continue
        search_roots = root.iterdir() if root.name == "Python" else (root,)
        for install_dir in search_roots:
            for name in names:
                candidate = install_dir / name
                if candidate.exists() and _valid_python_executable(candidate):
                    return str(candidate)

    if not is_frozen() and _valid_python_executable(sys.executable):
        return sys.executable

    return None


def _run_python_installer(installer: Path, log=None) -> int:
    if log:
        log(
            "Ouverture de l'installateur Python. "
            "Choisissez les options souhaitees, puis terminez l'installation."
        )
    result = subprocess.run([str(installer)])
    return result.returncode


def ensure_python_installed(log=None) -> str:
    python_exe = None if DEV else find_python_executable()
    if python_exe:
        if log:
            log(f"Python détecté: {python_exe}")
        return python_exe
    if DEV and log:
        log("Mode DEV: detection de Python ignoree")

    installer = next((path for path in candidate_python_installers() if path.exists()), None)
    if installer:
        if log:
            log(f"Installation de Python depuis le fichier fourni: {installer.name}")
    else:
        if log:
            log("Python introuvable, téléchargement de l'installateur Python...")
        tmp_dir = Path(tempfile.gettempdir()) / "ValaneStatInstaller"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        installer = tmp_dir / Path(PYTHON_INSTALLER_URL).name
        response = requests.get(PYTHON_INSTALLER_URL, timeout=60)
        response.raise_for_status()
        write_bytes(installer, response.content)

    result_code = _run_python_installer(installer, log=log)

    if result_code != 0:
        raise RuntimeError(
            "L'installation de Python a echoue. "
            f"Code retour: {result_code}"
        )

    python_exe = find_python_executable()
    if not python_exe:
        raise RuntimeError("Python a été installé, mais python.exe reste introuvable.")
    if log:
        log(f"Python installé: {python_exe}")
    return python_exe


def fetch_json(url: str):
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    return r.json()


def write_bytes(dest: Path, content: bytes):
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "wb") as f:
        f.write(content)


def create_start_menu_shortcut(app_path: Path, shortcut_name: str = "Valane Statistiques", app_folder: str = "AshbornStudio"):
    """Crée un raccourci .lnk dans le menu Démarrer de l'utilisateur.

    Retour: (True, None) si OK, sinon (False, message)
    """
    try:
        programs = Path(os.getenv("APPDATA")) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
        target_dir = programs / app_folder
        target_dir.mkdir(parents=True, exist_ok=True)
        link_path = target_dir / f"{shortcut_name}.lnk"

        # script principal: privilégier main.pyw pour éviter console
        script = app_path / "main.pyw" if (app_path / "main.pyw").exists() else app_path / "main.py"
        if not script.exists():
            return False, "Fichier principal introuvable pour créer le raccourci."

        interpreter = find_python_executable(prefer_windowed=True)
        if not interpreter:
            return False, "Python est introuvable pour créer le raccourci."

        # Premier essai avec pywin32 (win32com)
        try:
            from win32com.client import Dispatch

            shell = Dispatch("WScript.Shell")
            shortcut = shell.CreateShortcut(str(link_path))
            shortcut.TargetPath = interpreter
            shortcut.Arguments = f'"{str(script)}"'
            shortcut.WorkingDirectory = str(app_path)
            ico = app_path / "icon.ico"
            if ico.exists():
                shortcut.IconLocation = str(ico)
            shortcut.Save()
            return True, None
        except Exception:
            # fallback: écrire un script VBScript et l'exécuter avec cscript
            ico = app_path / "icon.ico"
            iconline = f'lnk.IconLocation = "{str(ico)}"' if ico.exists() else ""
            vbs = f'''Set sh = CreateObject("WScript.Shell")
                    Set lnk = sh.CreateShortcut("{str(link_path)}")
                    lnk.TargetPath = "{str(interpreter)}"
                    lnk.Arguments = Chr(34) & "{str(script)}" & Chr(34)
                    lnk.WorkingDirectory = "{str(app_path)}"
                    {iconline}
                    lnk.Save
                    '''
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".vbs", mode="w", encoding="utf-8")
            try:
                tmp.write(vbs)
                tmp.flush()
                tmp.close()
                subprocess.run(["cscript", "//nologo", tmp.name], check=True)
            finally:
                try:
                    os.unlink(tmp.name)
                except Exception:
                    pass
            return True, None
    except Exception as e:
        return False, str(e)


class InstallerApp:
    def __init__(self, root: tk.CTk):
        self.root = root
        self.root.title("Valane Statistiques — Installateur")
        self.root.geometry("900x650")
        self.root.overrideredirect(True)
        self.root.resizable(False, False)
        
        # Centrer la fenêtre
        largeur_fenetre = 900
        hauteur_fenetre = 650
        largeur_ecran = self.root.winfo_screenwidth()
        hauteur_ecran = self.root.winfo_screenheight()
        x = (largeur_ecran // 2) - (largeur_fenetre // 2)
        y = (hauteur_ecran // 2) - (hauteur_fenetre // 2)
        self.root.geometry(f"{largeur_fenetre}x{hauteur_fenetre}+{x}+{y}")
        
        # Mode sombre par défaut
        tk.set_appearance_mode("dark")
        tk.set_default_color_theme("blue")
        
        self.q = queue.Queue()
        self.cancel_event = threading.Event()

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_quit)
        self.root.after(100, self._process_queue)

    def _build_ui(self):
        # En-tête avec titre
        header = tk.CTkFrame(self.root, fg_color="#1f6aa5", corner_radius=0)
        header.pack(fill=tk.X, side=tk.TOP)
        
        title_frame = tk.CTkFrame(header, fg_color="#1f6aa5")
        title_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        tk.CTkLabel(
            title_frame,
            text="⬇ Valane Statistiques",
            font=("Segoe UI", 22, "bold"),
            text_color="white"
        ).pack(anchor="w")
        
        tk.CTkLabel(
            title_frame,
            text="Installation de l'application",
            font=("Segoe UI", 11),
            text_color="#cccccc"
        ).pack(anchor="w")
        
        # Contenu principal
        main_frame = tk.CTkFrame(self.root, fg_color="transparent")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Zone d'informations
        info_frame = tk.CTkFrame(main_frame, fg_color="transparent")
        info_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.status_var = tk.StringVar(value="Prêt à installer")
        status_label = tk.CTkLabel(
            info_frame,
            textvariable=self.status_var,
            font=("Segoe UI", 11),
            text_color="white",
            justify=tk.LEFT,
            wraplength=700
        )
        status_label.pack(fill=tk.X)
        
        # Barre de progression
        progress_frame = tk.CTkFrame(main_frame, fg_color="transparent")
        progress_frame.pack(fill=tk.X, pady=(15, 0))
        
        tk.CTkLabel(
            progress_frame,
            text="Progression:",
            font=("Segoe UI", 10),
            text_color="white"
        ).pack(anchor="w")
        
        self.progress_var = tk.StringVar(value="0%")
        self.progress = tk.CTkProgressBar(progress_frame, height=8)
        self.progress.pack(fill=tk.X, pady=(8, 0))
        self.progress.set(0)
        
        progress_label = tk.CTkLabel(
            progress_frame,
            textvariable=self.progress_var,
            font=("Segoe UI", 9),
            text_color="gray"
        )
        progress_label.pack(anchor="e", pady=(3, 0))
        
        # Liste des fichiers
        files_label = tk.CTkLabel(
            main_frame,
            text="📋 Fichiers en cours de téléchargement:",
            font=("Segoe UI", 10, "bold"),
            text_color="white"
        )
        files_label.pack(anchor="w", pady=(15, 8))
        
        files_frame = tk.CTkFrame(main_frame, fg_color="transparent")
        files_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        self.files_list = tk.CTkTextbox(
            files_frame,
            font=("Courier New", 9),
            text_color="white",
            state=tk.DISABLED
        )
        self.files_list.pack(fill=tk.BOTH, expand=True)

        # Frame pour les boutons
        btn_frame = tk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        # Boutons
        self.install_btn = tk.CTkButton(
            btn_frame,
            text="📦 Installer",
            command=self.start_install,
            font=("Segoe UI", 11, "bold"),
            height=38,
            corner_radius=6
        )
        self.install_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.cancel_btn = tk.CTkButton(
            btn_frame,
            text="⏹ Annuler",
            command=self.cancel,
            state=tk.DISABLED,
            font=("Segoe UI", 11),
            height=38,
            fg_color="#cc3333",
            hover_color="#aa2222",
            corner_radius=6
        )
        self.cancel_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.quit_btn = tk.CTkButton(
            btn_frame,
            text="❌ Quitter",
            command=self._on_quit,
            font=("Segoe UI", 11),
            height=38,
            fg_color="#555555",
            hover_color="#444444",
            corner_radius=6
        )
        self.quit_btn.pack(side=tk.RIGHT)

    def start_install(self):
        self.install_btn.configure(state=tk.DISABLED)
        self.cancel_btn.configure(state=tk.NORMAL)
        self.files_list.configure(state=tk.NORMAL)
        self.files_list.delete("1.0", tk.END)
        self.files_list.configure(state=tk.DISABLED)
        self.progress.set(0)
        self.progress_var.set("0%")
        self.status_var.set("Vérification de l'installation existante...")
        
        self.files_list.configure(state=tk.NORMAL)
        self.files_list.insert(tk.END, "Démarrage de l'installation...\n")
        self.files_list.configure(state=tk.DISABLED)
        
        default_path = os.getenv("APPDATA") or str(Path.home())
        app_path = Path(default_path) / "AshbornStudio" / "Valane-Stat"
        app_path.mkdir(parents=True, exist_ok=True)

        main_py = app_path / "main.py"
        if not DEV and main_py.exists():
            proceed = messagebox.askyesno(
                "⚠ Déjà installé",
                "L'application semble déjà installée.\n\nVoulez-vous réinstaller ?"
            )
            if not proceed:
                self.install_btn.configure(state=tk.NORMAL)
                self.cancel_btn.configure(state=tk.DISABLED)
                self.status_var.set("Installation annulée")
                self.files_list.configure(state=tk.NORMAL)
                self.files_list.delete("1.0", tk.END)
                self.files_list.configure(state=tk.DISABLED)
                self.progress.set(0)
                self.progress_var.set("0%")
                return

        self.status_var.set("⏳ Installation en cours...")
        thread = threading.Thread(target=self._install_worker, args=(app_path,), daemon=True)
        thread.start()

    def cancel(self):
        self.cancel_event.set()
        self.q.put(("log", "Annulation demandée..."))

    def _install_worker(self, app_path: Path):
        try:
            self.q.put(("status", "Vérification de Python..."))
            self.q.put(("log", "Vérification de Python..."))
            ensure_python_installed(log=lambda message: self.q.put(("log", message)))

            self.q.put(("log", "Récupération de la liste des versions..."))
            
            versions = None
            for candidate in ("versions.json", "version.json"):
                try:
                    versions = fetch_json(REPO_RAW + candidate)
                    break
                except Exception:
                    continue

            if not versions or not isinstance(versions, dict):
                self.q.put(("error", "⚠ Impossible de récupérer les informations de version"))
                return

            last = versions.get("last")
            if not last:
                self.q.put(("error", "⚠ Champ 'last' introuvable dans le fichier de versions"))
                return

            try:
                self.q.put(("log", f"Récupération de la liste des fichiers (v{last})..."))
                files_info = fetch_json(REPO_RAW + f"{last}/files.json")
            except Exception as e:
                self.q.put(("error", f"⚠ Impossible de récupérer les fichiers pour la version {last}"))
                return

            files_list = files_info if isinstance(files_info, list) else files_info.get("files", [])
            if not files_list:
                self.q.put(("error", "⚠ Aucun fichier trouvé à télécharger"))
                return

            self.q.put(("log", f"Trouvé {len(files_list)} fichier(s) à télécharger"))

            total = len(files_list)
            for idx, rel in enumerate(files_list, start=1):
                if self.cancel_event.is_set():
                    self.q.put(("log", "Installation annulée par l'utilisateur"))
                    self.q.put(("done", "Installation annulée"))
                    return

                self.q.put(("status", f"Téléchargement: {rel} — {idx}/{total}"))
                self.q.put(("file", rel))
                progress_value = int(idx / total * 100)
                self.q.put(("progress", progress_value))

                if rel.endswith("/") or rel.endswith("\\"):
                    dest_dir = app_path.joinpath(*Path(rel).parts)
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    continue

                try:
                    url = REPO_RAW + f"{last}/{rel}"
                    r = requests.get(url, timeout=30)
                    r.raise_for_status()
                    dest = app_path.joinpath(*Path(rel).parts)
                    write_bytes(dest, r.content)
                except Exception as e:
                    self.q.put(("error", f"⚠ Erreur lors du téléchargement de {rel}"))
                    return

            # tenter de créer un raccourci dans le menu Démarrer
            try:
                self.q.put(("log", "Création du raccourci dans le menu Démarrer..."))
                ok, err = create_start_menu_shortcut(app_path)
                if ok:
                    self.q.put(("log", "Raccourci créé avec succès"))
                else:
                    self.q.put(("log", f"⚠ Impossible de créer le raccourci: {err}"))
            except Exception as e:
                self.q.put(("log", f"⚠ Erreur lors de la création du raccourci"))

            self.q.put(("progress", 100))
            self.q.put(("done", "✅ Installation terminée avec succès!\n\nL'application est prête à être utilisée."))
        except Exception as e:
            self.q.put(("error", f"⚠ Erreur inattendue : {e}"))

    def _process_queue(self):
        try:
            while True:
                item = self.q.get_nowait()
                kind = item[0]
                if kind == "status":
                    self.status_var.set(item[1])
                elif kind == "file":
                    self.files_list.configure(state=tk.NORMAL)
                    self.files_list.insert(tk.END, f"  ✓ {item[1]}\n")
                    self.files_list.see(tk.END)
                    self.files_list.configure(state=tk.DISABLED)
                elif kind == "progress":
                    progress_value = item[1]
                    self.progress.set(progress_value / 100)
                    self.progress_var.set(f"{progress_value}%")
                elif kind == "log":
                    self.files_list.configure(state=tk.NORMAL)
                    self.files_list.insert(tk.END, f"  ℹ {item[1]}\n")
                    self.files_list.see(tk.END)
                    self.files_list.configure(state=tk.DISABLED)
                elif kind == "error":
                    messagebox.showerror("❌ Erreur", item[1])
                    self.install_btn.configure(state=tk.NORMAL)
                    self.cancel_btn.configure(state=tk.DISABLED)
                    self.status_var.set("❌ Erreur lors de l'installation")
                elif kind == "done":
                    messagebox.showinfo("✅ Terminé", item[1])
                    self.install_btn.configure(state=tk.NORMAL)
                    self.cancel_btn.configure(state=tk.DISABLED)
                    self.status_var.set("✅ Installation terminée avec succès")
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self._process_queue)

    def _on_quit(self):
        self.root.quit()


def main():
    root = tk.CTk()
    app = InstallerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
