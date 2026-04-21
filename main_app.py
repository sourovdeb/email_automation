"""
Job Application Automator – Main GUI
Tabbed interface: Setup | Run | Preview | Settings | History
"""
import sys, os, json, threading
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QLineEdit, QLabel, QTextEdit,
    QFormLayout, QSpinBox, QCheckBox, QComboBox, QTabWidget,
    QProgressBar, QGroupBox, QScrollArea, QSplitter, QStatusBar,
    QMessageBox, QFrame
)
from PyQt6.QtGui import QFont, QColor, QPalette
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject

from dotenv import load_dotenv

from data_parser import read_company_list, extract_cv_text, extract_motivation_letter
from researcher import search_company_info
from email_generator import generate_email
from email_sender import send_email_with_protonmail


# ---------------------------------------------------------------------------
# Worker thread so GUI stays responsive during automation
# ---------------------------------------------------------------------------

class AutomationWorker(QObject):
    log_signal     = pyqtSignal(str)
    progress       = pyqtSignal(int, int)   # (current, total)
    preview_ready  = pyqtSignal(str, str, str, str)  # (company, email, subject, body)
    finished       = pyqtSignal(dict)       # stats dict

    def __init__(self, config):
        super().__init__()
        self._config = config
        self._stop   = False

    def stop(self):
        self._stop = True

    def run(self):
        cfg = self._config
        stats = {"processed": 0, "sent": 0, "skipped": 0, "failed": 0}

        self.log_signal.emit("=== Démarrage de l'automatisation ===")

        result = read_company_list(cfg["company_path"])
        if result is None:
            self.log_signal.emit("ERREUR: impossible de lire la liste d'entreprises.")
            self.finished.emit(stats)
            return
        df, name_col, email_col = result

        cv_text = extract_cv_text(cfg["cv_path"])
        if not cv_text:
            self.log_signal.emit("ERREUR: impossible de lire le CV.")
            self.finished.emit(stats)
            return

        letter_text = extract_motivation_letter(cfg.get("letter_path", "")) or ""
        combined_profile = f"=== CV ===\n{cv_text}\n\n=== LETTRE ===\n{letter_text}"

        limit = cfg["max_companies"]
        subset = df.head(limit)
        total  = len(subset)

        self.log_signal.emit(f"Traitement de {total} entreprise(s) | dry_run={cfg['dry_run']}")

        run_log = []

        for idx, (_, row) in enumerate(subset.iterrows()):
            if self._stop:
                self.log_signal.emit("Arrêté par l'utilisateur.")
                break

            company_name = str(row.get(name_col, "")).strip()
            city         = str(row.get("Ville", "")).strip()
            postal_code  = str(row.get("CP", "")).strip()
            ca           = str(row.get("C.A.", "")).strip()

            if not company_name:
                self.log_signal.emit(f"[{idx+1}/{total}] Ligne ignorée (nom manquant)")
                stats["skipped"] += 1
                self.progress.emit(idx + 1, total)
                continue

            self.log_signal.emit(f"\n[{idx+1}/{total}] {company_name} – {city}")
            stats["processed"] += 1

            # Research
            contact_email_in_xlsx = None
            if email_col:
                val = row.get(email_col)
                if val and "@" in str(val):
                    contact_email_in_xlsx = str(val).strip()

            if contact_email_in_xlsx:
                research = {"about_text": "", "contact_email": contact_email_in_xlsx, "website": None}
                self.log_signal.emit(f"  Email trouvé dans le fichier: {contact_email_in_xlsx}")
            else:
                self.log_signal.emit(f"  Recherche web en cours …")
                research = search_company_info(company_name, city)

            contact_email = research.get("contact_email")

            if not contact_email:
                self.log_signal.emit(f"  Aucun email trouvé — ignoré")
                stats["skipped"] += 1
                run_log.append({"company": company_name, "status": "skipped", "reason": "no email"})
                self.progress.emit(idx + 1, total)
                continue

            # Generate email
            company_info = {
                "company_name": company_name,
                "city": city,
                "ca": ca,
                "postal_code": postal_code,
            }
            subject, body = generate_email(
                combined_profile, company_info, research,
                api_key      = cfg.get("api_key"),
                provider     = cfg.get("provider", "template"),
                ollama_model = cfg.get("ollama_model", "mistral"),
                ollama_url   = cfg.get("ollama_url", "http://localhost:11434"),
            )
            self.log_signal.emit(f"  Email généré → {contact_email}")
            self.preview_ready.emit(company_name, contact_email, subject, body)

            if cfg["dry_run"]:
                self.log_signal.emit(f"  [DRY RUN] Email non envoyé.")
                run_log.append({"company": company_name, "status": "dry_run", "email": contact_email})
                self.progress.emit(idx + 1, total)
                continue

            # Send
            self.log_signal.emit(f"  Envoi en cours …")
            ok = send_email_with_protonmail(
                username         = cfg["proton_user"],
                password         = cfg["proton_pass"],
                recipient_email  = contact_email,
                subject          = subject,
                body             = body,
                attachment_path  = cfg["cv_path"],
                browser_name     = cfg["browser"],
                headless         = cfg["headless"],
            )
            if ok:
                self.log_signal.emit(f"  Envoyé !")
                stats["sent"] += 1
                run_log.append({"company": company_name, "status": "sent", "email": contact_email})
            else:
                self.log_signal.emit(f"  ECHEC de l'envoi")
                stats["failed"] += 1
                run_log.append({"company": company_name, "status": "failed", "email": contact_email})

            self.progress.emit(idx + 1, total)

        stats["run_log"] = run_log
        self.log_signal.emit(f"\n=== Terminé | Traités:{stats['processed']} Envoyés:{stats['sent']} Ignorés:{stats['skipped']} Echecs:{stats['failed']} ===")
        self.finished.emit(stats)


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

STYLE = """
QMainWindow, QWidget { background: #f4f6fb; color: #1a1a2e; font-family: 'Segoe UI', 'DejaVu Sans', sans-serif; }
QTabWidget::pane { border: 1px solid #ccd1e0; border-radius: 8px; }
QTabBar::tab { padding: 8px 20px; font-size: 13px; font-weight: 600; border-radius: 6px 6px 0 0; }
QTabBar::tab:selected { background: #1a73e8; color: white; }
QTabBar::tab:!selected { background: #dde3f0; color: #444; }
QPushButton { min-height: 40px; font-size: 13px; font-weight: 600; background: #1a73e8; color: white; border-radius: 8px; padding: 6px 16px; border: none; }
QPushButton:hover { background: #1558b0; }
QPushButton:disabled { background: #9db0d0; }
QPushButton#danger { background: #d93025; }
QPushButton#success { background: #188038; }
QPushButton#secondary { background: #5f6368; }
QLineEdit, QComboBox, QSpinBox { min-height: 36px; font-size: 13px; border: 2px solid #c8cedf; border-radius: 6px; padding: 4px 8px; background: white; }
QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border: 2px solid #1a73e8; }
QTextEdit { font-size: 13px; border: 2px solid #c8cedf; border-radius: 6px; background: white; }
QGroupBox { font-size: 13px; font-weight: 700; border: 2px solid #c8cedf; border-radius: 8px; margin-top: 12px; padding-top: 8px; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #1a73e8; }
QLabel { font-size: 13px; }
QProgressBar { border: 2px solid #c8cedf; border-radius: 6px; text-align: center; font-weight: 700; height: 22px; }
QProgressBar::chunk { background: #1a73e8; border-radius: 4px; }
QCheckBox { font-size: 13px; spacing: 8px; }
QStatusBar { font-size: 12px; color: #555; }
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.base_dir      = os.path.dirname(os.path.abspath(__file__))
        self.env_path      = os.path.join(self.base_dir, ".env")
        self.logs_dir      = os.path.join(self.base_dir, "logs")
        self.data_dir      = os.path.join(self.base_dir, "data")
        self.meta_dir      = os.path.join(self.data_dir, "metadata")
        self.log_file      = os.path.join(self.logs_dir, "automation.log")
        self.meta_file     = os.path.join(self.meta_dir, "runs.jsonl")
        self.cv_path       = ""
        self.company_path  = ""
        self.letter_path   = ""
        self._worker       = None
        self._thread       = None
        self._preview_buf  = []   # [(company, email, subject, body)]

        os.makedirs(self.logs_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.meta_dir, exist_ok=True)

        self.setWindowTitle("Job Application Automator v2")
        self.setMinimumSize(980, 760)
        self.setStyleSheet(STYLE)

        self._build_ui()
        self._load_env()

    # ------------------------------------------------------------------ UI --

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(12, 12, 12, 8)

        tabs = QTabWidget()
        root.addWidget(tabs)

        tabs.addTab(self._tab_setup(),    "⚙  Configuration")
        tabs.addTab(self._tab_run(),      "▶  Lancement")
        tabs.addTab(self._tab_preview(),  "📧  Aperçu emails")
        tabs.addTab(self._tab_settings(), "🔧  Paramètres")
        tabs.addTab(self._tab_history(),  "📋  Historique")

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Prêt")

    # ---- Tab: Setup ----
    def _tab_setup(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setSpacing(14)

        # Files
        grp_files = QGroupBox("Fichiers")
        ff = QFormLayout(grp_files)

        row_cv = QHBoxLayout()
        self.btn_cv   = QPushButton("Choisir CV (PDF)")
        self.btn_cv.clicked.connect(self._pick_cv)
        self.lbl_cv   = QLabel("Aucun fichier sélectionné")
        self.lbl_cv.setWordWrap(True)
        row_cv.addWidget(self.btn_cv, 1)
        row_cv.addWidget(self.lbl_cv, 3)
        ff.addRow(row_cv)

        row_comp = QHBoxLayout()
        self.btn_comp  = QPushButton("Liste entreprises (XLSX)")
        self.btn_comp.clicked.connect(self._pick_company)
        self.lbl_comp  = QLabel("Aucun fichier sélectionné")
        self.lbl_comp.setWordWrap(True)
        row_comp.addWidget(self.btn_comp, 1)
        row_comp.addWidget(self.lbl_comp, 3)
        ff.addRow(row_comp)

        row_ltr = QHBoxLayout()
        self.btn_letter = QPushButton("Lettre motivation (PDF) [optionnel]")
        self.btn_letter.setObjectName("secondary")
        self.btn_letter.clicked.connect(self._pick_letter)
        self.lbl_letter = QLabel("Aucun fichier (optionnel)")
        self.lbl_letter.setWordWrap(True)
        row_ltr.addWidget(self.btn_letter, 1)
        row_ltr.addWidget(self.lbl_letter, 3)
        ff.addRow(row_ltr)

        v.addWidget(grp_files)

        # Credentials
        grp_cred = QGroupBox("Compte ProtonMail")
        cf = QFormLayout(grp_cred)
        self.email_in = QLineEdit(); self.email_in.setPlaceholderText("vous@proton.me")
        self.pass_in  = QLineEdit(); self.pass_in.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_in.setPlaceholderText("Mot de passe ProtonMail")
        cf.addRow("Email ProtonMail:", self.email_in)
        cf.addRow("Mot de passe:",     self.pass_in)

        row_save = QHBoxLayout()
        self.chk_save = QCheckBox("Mémoriser dans .env")
        self.chk_save.setChecked(True)
        btn_save_env  = QPushButton("Sauvegarder .env")
        btn_save_env.setObjectName("secondary")
        btn_save_env.clicked.connect(self._save_env)
        row_save.addWidget(self.chk_save)
        row_save.addStretch()
        row_save.addWidget(btn_save_env)
        cf.addRow(row_save)
        v.addWidget(grp_cred)

        # Test email
        grp_test = QGroupBox("Email de test")
        tf = QFormLayout(grp_test)
        self.test_recipient = QLineEdit("sourovdeb.is@gmail.com")
        tf.addRow("Destinataire test:", self.test_recipient)
        btn_test = QPushButton("Envoyer email de test (avec CV joint)")
        btn_test.setObjectName("success")
        btn_test.clicked.connect(self._send_test)
        tf.addRow(btn_test)
        v.addWidget(grp_test)

        v.addStretch()
        return w

    # ---- Tab: Run ----
    def _tab_run(self):
        w  = QWidget()
        v  = QVBoxLayout(w)
        v.setSpacing(12)

        # Summary
        self.run_summary = QLabel("Configurez les fichiers dans l'onglet Configuration puis lancez.")
        self.run_summary.setWordWrap(True)
        v.addWidget(self.run_summary)

        # Progress
        grp_prog = QGroupBox("Progression")
        pv = QVBoxLayout(grp_prog)
        self.progress_bar   = QProgressBar(); self.progress_bar.setValue(0)
        self.progress_label = QLabel("0 / 0")
        pv.addWidget(self.progress_bar)
        pv.addWidget(self.progress_label)
        v.addWidget(grp_prog)

        # Buttons
        btn_row = QHBoxLayout()
        self.btn_start = QPushButton("▶  Lancer l'automatisation")
        self.btn_start.setObjectName("success")
        self.btn_start.clicked.connect(self._start_automation)
        self.btn_stop  = QPushButton("⏹  Arrêter")
        self.btn_stop.setObjectName("danger")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._stop_automation)
        btn_row.addWidget(self.btn_start)
        btn_row.addWidget(self.btn_stop)
        v.addLayout(btn_row)

        # Log display
        v.addWidget(QLabel("Journal en direct:"))
        self.log_display = QTextEdit(); self.log_display.setReadOnly(True)
        self.log_display.setFont(QFont("Monospace", 11))
        v.addWidget(self.log_display)

        return w

    # ---- Tab: Preview ----
    def _tab_preview(self):
        w = QWidget()
        v = QVBoxLayout(w)

        self.preview_selector = QComboBox()
        self.preview_selector.currentIndexChanged.connect(self._show_preview)
        v.addWidget(QLabel("Sélectionner un email généré:"))
        v.addWidget(self.preview_selector)

        splitter = QSplitter(Qt.Orientation.Vertical)
        self.preview_meta    = QLabel("—")
        self.preview_meta.setWordWrap(True)
        self.preview_subject = QLineEdit(); self.preview_subject.setReadOnly(True)
        self.preview_body    = QTextEdit(); self.preview_body.setReadOnly(True)
        top = QWidget(); tl = QFormLayout(top)
        tl.addRow("Destinataire:", self.preview_meta)
        tl.addRow("Objet:",        self.preview_subject)
        splitter.addWidget(top)
        splitter.addWidget(self.preview_body)
        v.addWidget(splitter)
        return w

    # ---- Tab: Settings ----
    def _tab_settings(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setSpacing(14)

        grp_run = QGroupBox("Paramètres d'exécution")
        sf = QFormLayout(grp_run)

        self.browser_sel = QComboBox(); self.browser_sel.addItems(["chromium", "firefox"])
        sf.addRow("Navigateur:", self.browser_sel)

        self.chk_headless = QCheckBox("Mode invisible (headless)"); self.chk_headless.setChecked(False)
        sf.addRow(self.chk_headless)

        self.chk_dry = QCheckBox("Dry run — générer mais ne PAS envoyer"); self.chk_dry.setChecked(True)
        sf.addRow(self.chk_dry)

        self.spin_max = QSpinBox(); self.spin_max.setRange(1, 500); self.spin_max.setValue(5)
        sf.addRow("Max entreprises:", self.spin_max)

        v.addWidget(grp_run)

        grp_ai = QGroupBox("Intelligence artificielle — Fournisseur (optionnel)")
        af = QFormLayout(grp_ai)

        self.provider_sel = QComboBox()
        self.provider_sel.addItems(["template (sans IA)", "anthropic", "mistral", "deepseek", "ollama"])
        self.provider_sel.currentTextChanged.connect(self._on_provider_changed)
        af.addRow("Fournisseur IA:", self.provider_sel)

        self.api_key_in = QLineEdit()
        self.api_key_in.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_in.setPlaceholderText("Clé API (Anthropic / Mistral / DeepSeek)")
        af.addRow("Clé API:", self.api_key_in)

        self.ollama_model_in = QLineEdit("mistral")
        self.ollama_model_in.setPlaceholderText("Modèle Ollama (ex: mistral, llama3, gemma3)")
        af.addRow("Modèle Ollama:", self.ollama_model_in)

        self.ollama_url_in = QLineEdit("http://localhost:11434")
        self.ollama_url_in.setPlaceholderText("URL Ollama (défaut: http://localhost:11434)")
        af.addRow("URL Ollama:", self.ollama_url_in)

        note = QLabel(
            "• Template : aucune IA requise, email de qualité en français.\n"
            "• Anthropic (Claude Haiku) : nécessite une clé API Anthropic (sk-ant-…).\n"
            "• Mistral : nécessite une clé API Mistral (pip install mistralai).\n"
            "• DeepSeek : nécessite une clé API DeepSeek (pip install openai).\n"
            "• Ollama : modèle local gratuit — installez Ollama et lancez-le d'abord."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #555; font-size: 11px;")
        af.addRow(note)
        v.addWidget(grp_ai)

        btn_save = QPushButton("Sauvegarder tous les paramètres")
        btn_save.clicked.connect(self._save_env)
        v.addWidget(btn_save)
        v.addStretch()
        return w

    # ---- Tab: History ----
    def _tab_history(self):
        w = QWidget()
        v = QVBoxLayout(w)
        self.history_view = QTextEdit(); self.history_view.setReadOnly(True)
        self.history_view.setFont(QFont("Monospace", 11))
        btn_refresh = QPushButton("Actualiser l'historique")
        btn_refresh.setObjectName("secondary")
        btn_refresh.clicked.connect(self._load_history)
        v.addWidget(btn_refresh)
        v.addWidget(self.history_view)
        self._load_history()
        return w

    # ---------------------------------------------------------------- Logic --

    def _on_provider_changed(self, text):
        is_ollama = text == "ollama"
        is_template = text == "template (sans IA)"
        self.api_key_in.setEnabled(not is_ollama and not is_template)
        self.ollama_model_in.setEnabled(is_ollama)
        self.ollama_url_in.setEnabled(is_ollama)

    def _log(self, msg):
        self.log_display.append(msg)
        ts = datetime.now().isoformat(timespec="seconds")
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"[{ts}] {msg}\n")
        except Exception:
            pass
        QApplication.processEvents()

    def _load_env(self):
        if os.path.exists(self.env_path):
            load_dotenv(self.env_path, override=True)
        self.email_in.setText(os.getenv("PROTON_USER", ""))
        self.pass_in.setText(os.getenv("PROTON_PASS", ""))
        self.browser_sel.setCurrentText(os.getenv("BROWSER", "chromium"))
        self.chk_headless.setChecked(os.getenv("HEADLESS", "false").lower() == "true")
        self.chk_dry.setChecked(os.getenv("DRY_RUN", "true").lower() == "true")
        try:
            self.spin_max.setValue(int(os.getenv("MAX_COMPANIES", "5")))
        except ValueError:
            pass
        provider = os.getenv("PROVIDER", "template")
        display = provider if provider in ["anthropic", "mistral", "deepseek", "ollama"] else "template (sans IA)"
        self.provider_sel.setCurrentText(display)
        self.api_key_in.setText(
            os.getenv("ANTHROPIC_API_KEY") or
            os.getenv("MISTRAL_API_KEY") or
            os.getenv("DEEPSEEK_API_KEY") or ""
        )
        self.ollama_model_in.setText(os.getenv("OLLAMA_MODEL", "mistral"))
        self.ollama_url_in.setText(os.getenv("OLLAMA_URL", "http://localhost:11434"))
        self._on_provider_changed(self.provider_sel.currentText())
        self._log("Paramètres chargés depuis .env")

    def _save_env(self):
        provider_raw = self.provider_sel.currentText()
        provider = provider_raw if provider_raw != "template (sans IA)" else "template"
        api_key  = self.api_key_in.text().strip()
        lines = [
            f"PROTON_USER={self.email_in.text().strip()}",
            f"PROTON_PASS={self.pass_in.text().strip()}",
            f"BROWSER={self.browser_sel.currentText()}",
            f"HEADLESS={str(self.chk_headless.isChecked()).lower()}",
            f"DRY_RUN={str(self.chk_dry.isChecked()).lower()}",
            f"MAX_COMPANIES={self.spin_max.value()}",
            f"PROVIDER={provider}",
            f"ANTHROPIC_API_KEY={api_key if provider == 'anthropic' else ''}",
            f"MISTRAL_API_KEY={api_key if provider == 'mistral' else ''}",
            f"DEEPSEEK_API_KEY={api_key if provider == 'deepseek' else ''}",
            f"OLLAMA_MODEL={self.ollama_model_in.text().strip()}",
            f"OLLAMA_URL={self.ollama_url_in.text().strip()}",
        ]
        with open(self.env_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        self.status_bar.showMessage("Paramètres sauvegardés dans .env", 3000)

    def _pick_cv(self):
        f, _ = QFileDialog.getOpenFileName(self, "Sélectionner le CV", "", "PDF (*.pdf)")
        if f:
            self.cv_path = f
            self.lbl_cv.setText(os.path.basename(f))
            self._log(f"CV: {f}")

    def _pick_company(self):
        f, _ = QFileDialog.getOpenFileName(self, "Liste des entreprises", "", "Excel (*.xlsx *.xls)")
        if f:
            self.company_path = f
            self.lbl_comp.setText(os.path.basename(f))
            self._log(f"Entreprises: {f}")

    def _pick_letter(self):
        f, _ = QFileDialog.getOpenFileName(self, "Lettre de motivation", "", "PDF (*.pdf)")
        if f:
            self.letter_path = f
            self.lbl_letter.setText(os.path.basename(f))
            self._log(f"Lettre: {f}")

    def _validate_setup(self, require_cv=True, require_company=True):
        errors = []
        if not self.email_in.text().strip():
            errors.append("Email ProtonMail manquant")
        if not self.pass_in.text().strip():
            errors.append("Mot de passe ProtonMail manquant")
        if require_cv and not self.cv_path:
            errors.append("Aucun CV sélectionné")
        if require_company and not self.company_path:
            errors.append("Aucune liste d'entreprises sélectionnée")
        if errors:
            QMessageBox.warning(self, "Configuration incomplète", "\n".join(errors))
            return False
        return True

    def _send_test(self):
        if not self._validate_setup(require_company=False):
            return
        if self.chk_save.isChecked():
            self._save_env()

        recipient = self.test_recipient.text().strip() or "sourovdeb.is@gmail.com"
        self._log(f"Envoi email de test à {recipient} …")

        cv_text = extract_cv_text(self.cv_path) if self.cv_path else ""
        company_info = {
            "company_name": "TEST – Job Automator",
            "city": "La Réunion",
            "ca": "",
            "postal_code": "",
        }
        research = {"about_text": "Ceci est un email de test automatisé."}
        provider_raw = self.provider_sel.currentText()
        provider = provider_raw if provider_raw != "template (sans IA)" else "template"
        subject, body = generate_email(
            cv_text or "CV de Sourov Deb, formateur CELTA.",
            company_info, research,
            api_key      = self.api_key_in.text().strip() or None,
            provider     = provider,
            ollama_model = self.ollama_model_in.text().strip(),
            ollama_url   = self.ollama_url_in.text().strip(),
        )
        subject = "[TEST] " + subject

        def _run():
            ok = send_email_with_protonmail(
                username        = self.email_in.text().strip(),
                password        = self.pass_in.text().strip(),
                recipient_email = recipient,
                subject         = subject,
                body            = body,
                attachment_path = self.cv_path or None,
                browser_name    = self.browser_sel.currentText(),
                headless        = self.chk_headless.isChecked(),
            )
            self._log("Test : OK !" if ok else "Test : ECHEC")
            self.status_bar.showMessage("Test envoyé !" if ok else "Echec du test")

        threading.Thread(target=_run, daemon=True).start()

    def _start_automation(self):
        if not self._validate_setup():
            return
        if self.chk_save.isChecked():
            self._save_env()

        self._preview_buf.clear()
        self.preview_selector.clear()
        self.progress_bar.setValue(0)

        provider_raw = self.provider_sel.currentText()
        provider = provider_raw if provider_raw != "template (sans IA)" else "template"
        cfg = {
            "cv_path":       self.cv_path,
            "company_path":  self.company_path,
            "letter_path":   self.letter_path,
            "proton_user":   self.email_in.text().strip(),
            "proton_pass":   self.pass_in.text().strip(),
            "browser":       self.browser_sel.currentText(),
            "headless":      self.chk_headless.isChecked(),
            "dry_run":       self.chk_dry.isChecked(),
            "max_companies": self.spin_max.value(),
            "provider":      provider,
            "api_key":       self.api_key_in.text().strip() or None,
            "ollama_model":  self.ollama_model_in.text().strip(),
            "ollama_url":    self.ollama_url_in.text().strip(),
        }

        self.run_summary.setText(
            f"CV: {os.path.basename(cfg['cv_path'])} | "
            f"Entreprises: {os.path.basename(cfg['company_path'])} | "
            f"Max: {cfg['max_companies']} | "
            f"Dry run: {cfg['dry_run']}"
        )

        self._worker = AutomationWorker(cfg)
        self._thread = QThread()
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.log_signal.connect(self._log)
        self._worker.progress.connect(self._on_progress)
        self._worker.preview_ready.connect(self._on_preview)
        self._worker.finished.connect(self._on_finished)

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self._thread.start()

    def _stop_automation(self):
        if self._worker:
            self._worker.stop()

    def _on_progress(self, current, total):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.progress_label.setText(f"{current} / {total}")

    def _on_preview(self, company, email, subject, body):
        self._preview_buf.append((company, email, subject, body))
        label = f"{company} → {email}"
        self.preview_selector.addItem(label)

    def _show_preview(self, idx):
        if 0 <= idx < len(self._preview_buf):
            company, email, subject, body = self._preview_buf[idx]
            self.preview_meta.setText(f"{company}  <{email}>")
            self.preview_subject.setText(subject)
            self.preview_body.setPlainText(body)

    def _on_finished(self, stats):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        if self._thread:
            self._thread.quit()
            self._thread.wait()
        self._save_run_meta(stats)
        self._load_history()
        self.status_bar.showMessage(
            f"Terminé – Envoyés: {stats.get('sent',0)} | Ignorés: {stats.get('skipped',0)} | Echecs: {stats.get('failed',0)}"
        )

    def _save_run_meta(self, stats):
        record = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "browser":   self.browser_sel.currentText(),
            "dry_run":   self.chk_dry.isChecked(),
            "stats":     {k: v for k, v in stats.items() if k != "run_log"},
            "log":       stats.get("run_log", []),
        }
        try:
            with open(self.meta_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception as e:
            self._log(f"Avertissement: impossible de sauvegarder les métadonnées ({e})")

    def _load_history(self):
        self.history_view.clear()
        if not os.path.exists(self.meta_file):
            self.history_view.setPlainText("Aucun historique disponible.")
            return
        lines = []
        try:
            with open(self.meta_file, "r", encoding="utf-8") as f:
                for raw in f:
                    raw = raw.strip()
                    if not raw:
                        continue
                    rec = json.loads(raw)
                    ts  = rec.get("timestamp", "?")
                    s   = rec.get("stats", {})
                    dr  = "DRY" if rec.get("dry_run") else "LIVE"
                    lines.append(
                        f"[{ts}] [{dr}] "
                        f"Traités:{s.get('processed',0)}  "
                        f"Envoyés:{s.get('sent',0)}  "
                        f"Ignorés:{s.get('skipped',0)}  "
                        f"Echecs:{s.get('failed',0)}"
                    )
        except Exception as e:
            lines.append(f"Erreur lecture historique: {e}")
        self.history_view.setPlainText("\n".join(reversed(lines)))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 12))
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
