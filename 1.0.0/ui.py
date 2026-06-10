#     /$$$$$$            /$$       /$$                                            /$$$$$$   /$$                     /$$ /$$          
#    /$$__  $$          | $$      | $$                                           /$$__  $$ | $$                    | $$|__/          
#   | $$  \ $$  /$$$$$$$| $$$$$$$ | $$$$$$$   /$$$$$$   /$$$$$$  /$$$$$$$       | $$  \__//$$$$$$   /$$   /$$  /$$$$$$$ /$$  /$$$$$$ 
#   | $$$$$$$$ /$$_____/| $$__  $$| $$__  $$ /$$__  $$ /$$__  $$| $$__  $$      |  $$$$$$|_  $$_/  | $$  | $$ /$$__  $$| $$ /$$__  $$
#   | $$__  $$|  $$$$$$ | $$  \ $$| $$  \ $$| $$  \ $$| $$  \__/| $$  \ $$       \____  $$ | $$    | $$  | $$| $$  | $$| $$| $$  \ $$
#   | $$  | $$ \____  $$| $$  | $$| $$  | $$| $$  | $$| $$      | $$  | $$       /$$  \ $$ | $$ /$$| $$  | $$| $$  | $$| $$| $$  | $$
#   | $$  | $$ /$$$$$$$/| $$  | $$| $$$$$$$/|  $$$$$$/| $$      | $$  | $$      |  $$$$$$/ |  $$$$/|  $$$$$$/|  $$$$$$$| $$|  $$$$$$/
#   |__/  |__/|_______/ |__/  |__/|_______/  \______/ |__/      |__/  |__/       \______/   \___/   \______/  \_______/|__/ \______/  
#    _____       _             __               
#   |_   _|     | |   V1.0.0  / _|  
#     | |  _ __ | |_ ___ _ __| |_ __ _  ___ ___ 
#     | | | '_ \| __/ _ \ '__|  _/ _` |/ __/ _ \
#    _| |_| | | | ||  __/ |  | || (_| | (_|  __/
#   |_____|_| |_|\__\___|_|  |_| \__,_|\___\___|





from PyQt6.QtCore import QSize, Qt, QUrl, QTimer
from PyQt6.QtGui import QAction, QIcon, QFont
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QLabel,
    QMainWindow,
    QStatusBar,
    QToolBar,
    QWidget,
    QHBoxLayout,
    QDialog,
    QVBoxLayout,
    QPlainTextEdit,
    QPushButton,
    QProgressBar,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
import sys
import threading



class MainWindow(QMainWindow):
    def __init__(self, url: str = "exemple.com", dev: bool = False):
        super().__init__()

        # Configuration de la fenêtre principale
        self.setWindowTitle("Valane Statistiques — Navigateur intégré")
        self.resize(1100, 760)

        # Création du composant de navigation web
        self.navigateur = QWebEngineView()
        self.navigateur.setUrl(QUrl(url))

        # Définir le composant web comme widget central de la fenêtre
        central = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.navigateur)
        central.setLayout(layout)
        self.setCentralWidget(central)

        # status bar
        self.setStatusBar(QStatusBar())

        # simple developer toolbar when dev mode
        if dev:
            tb = QToolBar("Navigation")
            tb.setIconSize(QSize(16, 16))
            tb.setMovable(False)

            back_action = QAction("◀ Back", self)
            back_action.triggered.connect(self.navigateur.back)
            tb.addAction(back_action)

            forward_action = QAction("Forward ▶", self)
            forward_action.triggered.connect(self.navigateur.forward)
            tb.addAction(forward_action)

            reload_action = QAction("⟳ Reload", self)
            reload_action.triggered.connect(self.navigateur.reload)
            tb.addAction(reload_action)

            home_action = QAction("Home", self)
            home_action.triggered.connect(lambda: self.navigateur.setUrl(QUrl(url)))
            tb.addAction(home_action)

            # view current HTML source action (dev mode)
            view_html_action = QAction("Voir HTML", self)
            view_html_action.triggered.connect(self.show_html)
            tb.addAction(view_html_action)

            # add address label
            self.addr_label = QLabel(url)
            self.addr_label.setContentsMargins(8, 0, 8, 0)
            tb.addWidget(self.addr_label)

            self.addToolBar(tb)

            # update address on url change
            self.navigateur.urlChanged.connect(lambda u: self.addr_label.setText(u.toString()))

    # Utility to schedule a callable on the Qt main thread
    def run_on_main(self, fn):
        QTimer.singleShot(0, fn)

    # --- Update dialog API ---
    def show_update_dialog(self, title: str, message: str = "", forced: bool = False):
        """Affiche une boîte de dialogue d'information de mise à jour.
        Le choix de l'utilisateur (installer / plus tard) est exposé via
        `self._update_choice_event` et `self._update_choice_install`.
        """
        # prepare synchronization primitives
        self._update_choice_event = threading.Event()
        self._update_choice_install = False

        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        dlg.resize(700, 360)
        dlg.setModal(False)

        v = QVBoxLayout()
        lbl = QLabel(message)
        lbl.setWordWrap(True)
        lbl.setContentsMargins(6, 6, 6, 6)
        v.addWidget(lbl)

        prog = QProgressBar()
        prog.setRange(0, 100)
        prog.setValue(0)
        prog.setTextVisible(True)
        prog.setVisible(False)
        v.addWidget(prog)

        # actions
        btn_install = QPushButton("Installer")
        btn_later = QPushButton("Plus tard")

        def _on_install():
            btn_install.setEnabled(False)
            btn_later.setEnabled(False)
            prog.setVisible(True)
            self._update_choice_install = True
            # signal the background thread that the user chose to install
            self._update_choice_event.set()

        def _on_later():
            self._update_choice_install = False
            self._update_choice_event.set()
            dlg.accept()

        btn_install.clicked.connect(_on_install)
        btn_later.clicked.connect(_on_later)

        # pack buttons right-aligned
        hl = QHBoxLayout()
        hl.addStretch()
        hl.addWidget(btn_install)
        hl.addWidget(btn_later)
        v.addLayout(hl)

        dlg.setLayout(v)

        # store references for updates
        self._update_dialog = dlg
        self._update_progress_bar = prog
        self._update_message_label = lbl
        self._update_install_btn = btn_install
        self._update_later_btn = btn_later

        # if forced, auto-trigger install (after short delay to let UI render)
        if forced:
            def _auto():
                if not self._update_choice_event.is_set():
                    _on_install()
            QTimer.singleShot(200, _auto)

        dlg.show()

    def update_update_progress(self, percent: int, message: str | None = None):
        """Met à jour la barre de progression et le message dans le dialogue d'update.
        Can be safely called from background threads.
        """
        def _u():
            try:
                if hasattr(self, '_update_progress_bar') and self._update_progress_bar:
                    self._update_progress_bar.setVisible(True)
                    self._update_progress_bar.setValue(int(percent))
                if message and hasattr(self, '_update_message_label') and self._update_message_label:
                    self._update_message_label.setText(str(message))
            except Exception:
                pass
        self.run_on_main(_u)

    def close_update_dialog(self):
        def _c():
            try:
                if hasattr(self, '_update_dialog') and self._update_dialog:
                    self._update_dialog.accept()
            except Exception:
                pass
        self.run_on_main(_c)

    def show_html(self):
        """Récupère le HTML courant de la page et l'affiche dans une boîte de dialogue (lecture seule)."""
        page = self.navigateur.page()

        def _got_html(html: str):
            dlg = QDialog(self)
            dlg.setWindowTitle("Code HTML de la page")
            dlg.resize(900, 600)
            v = QVBoxLayout()
            edit = QPlainTextEdit()
            edit.setReadOnly(True)
            # try to use a monospace font for readability
            try:
                edit.setFont(QFont('Consolas'))
            except Exception:
                pass
            edit.setPlainText(html)
            v.addWidget(edit)
            # buttons
            btn_close = QPushButton("Fermer")
            btn_close.clicked.connect(dlg.accept)
            btn_copy = QPushButton("Copier")
            def _copy():
                QApplication.clipboard().setText(html)
            btn_copy.clicked.connect(_copy)
            hl = QHBoxLayout()
            hl.addStretch()
            hl.addWidget(btn_copy)
            hl.addWidget(btn_close)
            v.addLayout(hl)
            dlg.setLayout(v)
            dlg.exec()

        # QWebEnginePage.toHtml is asynchronous and delivers the HTML to the callback
        page.toHtml(_got_html)


def run(URL, dev: bool = False):
    app, wnd = create_app(URL, dev=dev)
    return app.exec()


def create_app(URL, dev: bool = False):
    """Create and return `(app, window)` without entering the Qt event loop.
    Use this to start background tasks that interact with the window before calling `app.exec()`.
    """
    app = QApplication(sys.argv)
    window = MainWindow(url=URL, dev=dev)
    window.show()
    return app, window