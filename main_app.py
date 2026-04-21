import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QLineEdit, QLabel, QTextEdit, QFormLayout,
    QSpinBox, QCheckBox, QComboBox, QTabWidget, QFrame, QTimeEdit,
    QScrollArea, QSizePolicy, QGroupBox,
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QTime, QTimer, pyqtSignal
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Import our automation modules
from data_parser import read_company_list, extract_cv_text
from researcher import search_company_website
from email_generator import generate_email_body
from email_sender import send_email_with_protonmail
from scheduler import AutomationScheduler

# ---------------------------------------------------------------------------
# Shared stylesheet – WordPress-admin-inspired palette
# ---------------------------------------------------------------------------
_STYLE = (
    # Base
    "QWidget { background: #f0f0f1; color: #1d2327; font-family: 'DejaVu Sans', sans-serif; }"
    # Tabs bar (top navigation like WP admin)
    "QTabWidget::pane { border: none; background: #f0f0f1; }"
    "QTabBar::tab { background: #2271b1; color: #fff; font-size: 13px; font-weight: 600;"
    "  min-width: 130px; min-height: 38px; padding: 6px 18px; border-radius: 0; margin-right: 2px; }"
    "QTabBar::tab:selected { background: #135e96; border-bottom: 3px solid #f0b849; }"
    "QTabBar::tab:hover:!selected { background: #1a6198; }"
    # Cards / group boxes
    "QGroupBox { background: #fff; border: 1px solid #c3c4c7; border-radius: 4px;"
    "  font-size: 13px; font-weight: 600; padding-top: 16px; margin-top: 8px; }"
    "QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 4px; color: #1d2327; }"
    # Buttons
    "QPushButton { min-height: 38px; font-size: 13px; font-weight: 600;"
    "  background: #2271b1; color: #fff; border-radius: 3px; padding: 6px 16px;"
    "  border: 1px solid #135e96; }"
    "QPushButton:hover { background: #135e96; }"
    "QPushButton:focus { outline: 2px solid #f0b849; outline-offset: 2px; }"
    # Text areas
    "QTextEdit { font-size: 12px; border: 1px solid #8c8f94; border-radius: 3px;"
    "  background: #fff; padding: 6px; }"
    # Labels
    "QLabel { font-size: 13px; background: transparent; }"
    "QLabel#heading { font-size: 20px; font-weight: 700; color: #1d2327; }"
    "QLabel#subheading { font-size: 14px; font-weight: 600; color: #50575e; }"
    "QLabel#stat_number { font-size: 28px; font-weight: 700; color: #2271b1; }"
    "QLabel#stat_label { font-size: 12px; color: #646970; }"
    # Checkboxes
    "QCheckBox { font-size: 13px; spacing: 8px; background: transparent; }"
    # Dividers
    "QFrame[frameShape='4'] { color: #c3c4c7; }"
)


class JobAutomatorApp(QWidget):
    # Emitted by the background scheduler thread; connected to a slot on the main
    # thread so all GUI/automation work runs safely on the Qt main thread.
    _schedule_triggered = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.env_path = os.path.join(self.base_dir, ".env")
        self.logs_dir = os.path.join(self.base_dir, "logs")
        self.data_dir = os.path.join(self.base_dir, "data")
        self.attachments_dir = os.path.join(self.data_dir, "attachments")
        self.metadata_dir = os.path.join(self.data_dir, "metadata")
        self.log_file_path = os.path.join(self.logs_dir, "automation.log")
        self.metadata_file_path = os.path.join(self.metadata_dir, "runs.jsonl")
        self.run_meta = None
        self.cv_path = ""
        self.company_list_path = ""
        self.initialize_runtime_directories()
        # Wire the cross-thread signal before creating the scheduler so the
        # callback always dispatches work safely onto the Qt main thread.
        self._schedule_triggered.connect(self._on_schedule_triggered)
        self.scheduler = AutomationScheduler(callback=self._scheduled_run)
        self.initUI()
        self.load_settings_from_env()
        self.apply_adaptive_defaults()
        # Refresh the dashboard stats every 30 s
        self._stats_timer = QTimer(self)
        self._stats_timer.timeout.connect(self._refresh_dashboard_stats)
        self._stats_timer.start(30_000)

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def initUI(self):
        self.setWindowTitle("Job Automation Dashboard")
        self.setGeometry(80, 80, 960, 760)
        self.setFont(QFont("DejaVu Sans", 12))
        self.setStyleSheet(_STYLE)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Top header bar (like WP admin bar) ──────────────────────────
        header = QFrame()
        header.setFixedHeight(50)
        header.setStyleSheet("background: #1d2327; color: #f0f0f1;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 0, 16, 0)
        title_lbl = QLabel("📧  Job Automation Dashboard")
        title_lbl.setStyleSheet("color: #f0f0f1; font-size: 15px; font-weight: 700; background: transparent;")
        h_layout.addWidget(title_lbl)
        h_layout.addStretch()
        self.header_clock = QLabel("")
        self.header_clock.setStyleSheet("color: #a7aaad; font-size: 12px; background: transparent;")
        h_layout.addWidget(self.header_clock)
        root.addWidget(header)

        # Update clock every second
        clock_timer = QTimer(self)
        clock_timer.timeout.connect(self._update_clock)
        clock_timer.start(1000)
        self._update_clock()

        # ── Tab widget ───────────────────────────────────────────────────
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.tabs.addTab(self._build_dashboard_tab(), "🏠  Dashboard")
        self.tabs.addTab(self._build_settings_tab(), "⚙️  Settings")
        self.tabs.addTab(self._build_schedule_tab(), "🕐  Schedule")
        self.tabs.addTab(self._build_logs_tab(), "📋  Logs")
        root.addWidget(self.tabs)

        self.setLayout(root)

    # ── Dashboard tab ────────────────────────────────────────────────────

    def _build_dashboard_tab(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # Welcome heading
        heading = QLabel("At a Glance")
        heading.setObjectName("heading")
        layout.addWidget(heading)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)

        # Stats row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(16)
        self.stat_runs = self._stat_card("Total Runs", "0")
        self.stat_sent = self._stat_card("Emails Sent", "0")
        self.stat_processed = self._stat_card("Companies Processed", "0")
        self.stat_failed = self._stat_card("Failed Sends", "0")
        for card in (self.stat_runs, self.stat_sent, self.stat_processed, self.stat_failed):
            stats_row.addWidget(card[0])
        layout.addLayout(stats_row)

        sep2 = QFrame(); sep2.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep2)

        # Quick-start group
        quick = QGroupBox("Quick Start")
        q_layout = QVBoxLayout(quick)
        q_layout.setSpacing(10)

        info = QLabel(
            "1. Go to <b>Settings</b> to configure credentials and select your files.<br>"
            "2. Click <b>Run Now</b> to start the automation immediately.<br>"
            "3. Go to <b>Schedule</b> to set up a daily automated run.<br>"
            "4. Monitor progress in the <b>Logs</b> tab."
        )
        info.setWordWrap(True)
        info.setTextFormat(Qt.TextFormat.RichText)
        q_layout.addWidget(info)

        btn_row = QHBoxLayout()
        btn_run = QPushButton("▶  Run Now")
        btn_run.setObjectName("success")
        btn_run.clicked.connect(self._quick_run)
        btn_test = QPushButton("✉  Send Test Email")
        btn_test.clicked.connect(self.send_test_email)
        btn_logs = QPushButton("📋  View Logs")
        btn_logs.clicked.connect(lambda: self.tabs.setCurrentIndex(3))
        btn_row.addWidget(btn_run)
        btn_row.addWidget(btn_test)
        btn_row.addWidget(btn_logs)
        btn_row.addStretch()
        q_layout.addLayout(btn_row)
        layout.addWidget(quick)

        # Schedule status
        sched_group = QGroupBox("Scheduler Status")
        s_layout = QHBoxLayout(sched_group)
        self.lbl_sched_status = QLabel("Scheduler: <b>Disabled</b>")
        self.lbl_sched_status.setTextFormat(Qt.TextFormat.RichText)
        self.lbl_next_run = QLabel("Next run: —")
        s_layout.addWidget(self.lbl_sched_status)
        s_layout.addSpacing(32)
        s_layout.addWidget(self.lbl_next_run)
        s_layout.addStretch()
        layout.addWidget(sched_group)

        layout.addStretch()
        self._refresh_dashboard_stats()
        return container

    def _stat_card(self, label_text: str, value_text: str):
        """Return (card_widget, number_label) for a dashboard stat card."""
        card = QGroupBox(label_text)
        card_layout = QVBoxLayout(card)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        num = QLabel(value_text)
        num.setObjectName("stat_number")
        num.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(num)
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return card, num

    # ── Settings tab ─────────────────────────────────────────────────────

    def _build_settings_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        heading = QLabel("Settings")
        heading.setObjectName("heading")
        layout.addWidget(heading)
        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)

        # ── Files group
        files_group = QGroupBox("Input Files")
        files_layout = QFormLayout(files_group)
        files_layout.setSpacing(10)

        self.btn_cv = QPushButton("Select CV (PDF)")
        self.btn_cv.clicked.connect(self.select_cv_file)
        self.lbl_cv = QLabel("No file selected")
        self.lbl_cv.setWordWrap(True)
        files_layout.addRow(self.btn_cv, self.lbl_cv)

        self.btn_companies = QPushButton("Select Company List (XLSX)")
        self.btn_companies.clicked.connect(self.select_company_file)
        self.lbl_companies = QLabel("No file selected")
        self.lbl_companies.setWordWrap(True)
        files_layout.addRow(self.btn_companies, self.lbl_companies)
        layout.addWidget(files_group)

        # ── Credentials group
        creds_group = QGroupBox("ProtonMail Credentials")
        creds_layout = QFormLayout(creds_group)
        creds_layout.setSpacing(10)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("your@proton.me")
        self.email_input.setAccessibleName("ProtonMail user email")
        creds_layout.addRow(QLabel("Email:"), self.email_input)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("ProtonMail password")
        self.password_input.setAccessibleName("ProtonMail password")
        creds_layout.addRow(QLabel("Password:"), self.password_input)

        self.save_credentials_check = QCheckBox("Auto-save credentials to .env on run")
        self.save_credentials_check.setChecked(True)
        creds_layout.addRow(QLabel(""), self.save_credentials_check)
        layout.addWidget(creds_group)

        # ── Run options group
        opts_group = QGroupBox("Run Options")
        opts_layout = QFormLayout(opts_group)
        opts_layout.setSpacing(10)

        self.browser_select = QComboBox()
        self.browser_select.addItems(["chromium", "firefox"])
        self.browser_select.setCurrentText("chromium")
        opts_layout.addRow(QLabel("Browser:"), self.browser_select)

        self.headless_check = QCheckBox("Run browser in background (headless)")
        self.headless_check.setChecked(False)
        opts_layout.addRow(QLabel("Mode:"), self.headless_check)

        self.dry_run_check = QCheckBox("Dry run only — generate emails but do not send")
        self.dry_run_check.setChecked(False)
        opts_layout.addRow(QLabel("Safety:"), self.dry_run_check)

        self.max_companies = QSpinBox()
        self.max_companies.setMinimum(1)
        self.max_companies.setMaximum(260)
        self.max_companies.setValue(5)
        self.max_companies.setAccessibleName("Maximum companies per run")
        opts_layout.addRow(QLabel("Max companies:"), self.max_companies)
        layout.addWidget(opts_group)

        # ── Action buttons
        btn_row = QHBoxLayout()
        btn_save = QPushButton("💾  Save Settings to .env")
        btn_save.clicked.connect(self.save_settings_to_env)
        btn_test = QPushButton("✉  Send Test Email")
        btn_test.clicked.connect(self.send_test_email)
        btn_start = QPushButton("▶  Start Automation")
        btn_start.setObjectName("success")
        btn_start.clicked.connect(self.start_automation)
        btn_row.addWidget(btn_save)
        btn_row.addWidget(btn_test)
        btn_row.addWidget(btn_start)
        btn_row.addStretch()
        layout.addLayout(btn_row)
        layout.addStretch()

        scroll.setWidget(container)
        return scroll

    # ── Schedule tab ──────────────────────────────────────────────────────

    def _build_schedule_tab(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        heading = QLabel("Scheduled Automation")
        heading.setObjectName("heading")
        layout.addWidget(heading)
        info = QLabel(
            "Set a daily time for the automation to run automatically. "
            "No AI or external service required — runs locally on your Linux machine."
        )
        info.setObjectName("subheading")
        info.setWordWrap(True)
        layout.addWidget(info)
        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)

        sched_group = QGroupBox("Daily Schedule")
        sched_layout = QFormLayout(sched_group)
        sched_layout.setSpacing(12)

        self.schedule_enabled_check = QCheckBox("Enable daily scheduled run")
        self.schedule_enabled_check.setChecked(False)
        self.schedule_enabled_check.stateChanged.connect(self._toggle_scheduler)
        sched_layout.addRow(QLabel("Enable:"), self.schedule_enabled_check)

        self.schedule_time_edit = QTimeEdit()
        self.schedule_time_edit.setDisplayFormat("HH:mm")
        self.schedule_time_edit.setTime(QTime(9, 0))
        self.schedule_time_edit.setAccessibleName("Scheduled run time (24-hour)")
        self.schedule_time_edit.timeChanged.connect(self._update_scheduler_time)
        sched_layout.addRow(QLabel("Run at:"), self.schedule_time_edit)

        layout.addWidget(sched_group)

        # Status display
        status_group = QGroupBox("Status")
        status_layout = QFormLayout(status_group)
        self.lbl_sched_detail = QLabel("Scheduler is currently <b>disabled</b>.")
        self.lbl_sched_detail.setTextFormat(Qt.TextFormat.RichText)
        self.lbl_next_run_detail = QLabel("—")
        status_layout.addRow(QLabel("State:"), self.lbl_sched_detail)
        status_layout.addRow(QLabel("Next run:"), self.lbl_next_run_detail)
        layout.addWidget(status_group)

        # Manual trigger
        btn_row = QHBoxLayout()
        btn_run_now = QPushButton("▶  Run Now (manual trigger)")
        btn_run_now.setObjectName("success")
        btn_run_now.clicked.connect(self._quick_run)
        btn_row.addWidget(btn_run_now)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        layout.addStretch()
        return container

    # ── Logs tab ─────────────────────────────────────────────────────────

    def _build_logs_tab(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        heading = QLabel("Logs")
        heading.setObjectName("heading")
        layout.addWidget(heading)
        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)

        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setAccessibleName("Live automation log")
        self.log_display.setMinimumHeight(420)
        layout.addWidget(self.log_display)

        btn_row = QHBoxLayout()
        btn_clear = QPushButton("🗑  Clear Log View")
        btn_clear.setObjectName("danger")
        btn_clear.clicked.connect(self.log_display.clear)
        btn_row.addWidget(btn_clear)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        return container

    # ------------------------------------------------------------------
    # Helpers – clock and stats
    # ------------------------------------------------------------------

    def _update_clock(self):
        self.header_clock.setText(datetime.now().strftime("%Y-%m-%d  %H:%M:%S"))

    def _refresh_dashboard_stats(self):
        runs = sent = processed = failed = 0
        if os.path.exists(self.metadata_file_path):
            try:
                with open(self.metadata_file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        record = json.loads(line)
                        runs += 1
                        stats = record.get("stats", {})
                        sent += int(stats.get("sent_ok", 0))
                        processed += int(stats.get("processed", 0))
                        failed += int(stats.get("sent_failed", 0))
            except Exception:
                pass
        self.stat_runs[1].setText(str(runs))
        self.stat_sent[1].setText(str(sent))
        self.stat_processed[1].setText(str(processed))
        self.stat_failed[1].setText(str(failed))

        # Scheduler status on dashboard
        if self.scheduler.is_enabled():
            self.lbl_sched_status.setText("Scheduler: <b>Active ✓</b>")
            self.lbl_next_run.setText(f"Next run: {self.scheduler.next_run_str()}")
        else:
            self.lbl_sched_status.setText("Scheduler: <b>Disabled</b>")
            self.lbl_next_run.setText("Next run: —")

    # ------------------------------------------------------------------
    # Scheduler helpers
    # ------------------------------------------------------------------

    def _toggle_scheduler(self, state):
        if state == Qt.CheckState.Checked.value:  # int 2
            self.scheduler.set_time(self.schedule_time_edit.time().toString("HH:mm"))
            self.scheduler.enable()
            next_run = self.scheduler.next_run_str()
            self.lbl_sched_detail.setText("Scheduler is <b>active ✓</b>")
            self.lbl_next_run_detail.setText(next_run)
            self.log(f"Scheduler enabled — next run at {next_run}")
        else:
            self.scheduler.disable()
            self.lbl_sched_detail.setText("Scheduler is currently <b>disabled</b>.")
            self.lbl_next_run_detail.setText("—")
            self.log("Scheduler disabled.")
        self._refresh_dashboard_stats()

    def _update_scheduler_time(self, new_time: QTime):
        hhmm = new_time.toString("HH:mm")
        self.scheduler.set_time(hhmm)
        if self.scheduler.is_enabled():
            next_run = self.scheduler.next_run_str()
            self.lbl_next_run_detail.setText(next_run)
            self.log(f"Scheduler rescheduled — next run at {next_run}")
        self._refresh_dashboard_stats()

    def _scheduled_run(self):
        """Called from the background scheduler thread — emit signal only."""
        self._schedule_triggered.emit()

    def _on_schedule_triggered(self):
        """Slot executed on the Qt main thread when the scheduler fires."""
        self.log("⏰ Scheduled run triggered.")
        self._quick_run()

    def _quick_run(self):
        """Triggered from Dashboard or Schedule tab — switches to Logs then runs."""
        self.tabs.setCurrentIndex(3)
        self.start_automation()

    def log(self, message):
        self.log_display.append(message)
        timestamp = datetime.now().isoformat(timespec="seconds")
        try:
            with open(self.log_file_path, "a", encoding="utf-8") as log_file:
                log_file.write(f"[{timestamp}] {message}\n")
        except Exception:
            # Keep UI responsive even if file logging fails.
            pass
        QApplication.processEvents() # Update the GUI

    def initialize_runtime_directories(self):
        os.makedirs(self.logs_dir, exist_ok=True)
        os.makedirs(self.attachments_dir, exist_ok=True)
        os.makedirs(self.metadata_dir, exist_ok=True)

    def init_run_metadata(self):
        self.run_meta = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "browser": self.browser_select.currentText(),
            "headless": self.headless_check.isChecked(),
            "dry_run": self.dry_run_check.isChecked(),
            "max_companies": self.max_companies.value(),
            "companies": [],
            "stats": {
                "processed": 0,
                "research_ok": 0,
                "email_found": 0,
                "sent_ok": 0,
                "sent_failed": 0,
                "skipped": 0
            }
        }

    def record_company_result(self, company_name, status, reason="", contact_email_found=False):
        if self.run_meta is None:
            return

        self.run_meta["companies"].append(
            {
                "time": datetime.now().isoformat(timespec="seconds"),
                "company": company_name,
                "status": status,
                "reason": reason,
                "contact_email_found": contact_email_found
            }
        )

        self.run_meta["stats"]["processed"] += 1
        if status == "dry_run_ready":
            self.run_meta["stats"]["research_ok"] += 1
            self.run_meta["stats"]["email_found"] += 1
        elif status == "sent_ok":
            self.run_meta["stats"]["research_ok"] += 1
            self.run_meta["stats"]["email_found"] += 1
            self.run_meta["stats"]["sent_ok"] += 1
        elif status == "sent_failed":
            self.run_meta["stats"]["research_ok"] += 1
            self.run_meta["stats"]["email_found"] += 1
            self.run_meta["stats"]["sent_failed"] += 1
        else:
            self.run_meta["stats"]["skipped"] += 1
            if contact_email_found:
                self.run_meta["stats"]["email_found"] += 1

    def save_run_metadata(self):
        if self.run_meta is None:
            return

        try:
            with open(self.metadata_file_path, "a", encoding="utf-8") as meta_file:
                meta_file.write(json.dumps(self.run_meta, ensure_ascii=True) + "\n")
            self.log(f"Run metadata saved to {self.metadata_file_path}")
        except Exception as exc:
            self.log(f"Warning: could not save metadata ({exc})")

    def get_adaptive_browser(self):
        if not os.path.exists(self.metadata_file_path):
            return None

        browser_stats = {
            "chromium": {"ok": 0, "total": 0},
            "firefox": {"ok": 0, "total": 0}
        }

        try:
            with open(self.metadata_file_path, "r", encoding="utf-8") as meta_file:
                for line in meta_file:
                    line = line.strip()
                    if not line:
                        continue
                    record = json.loads(line)
                    browser = record.get("browser", "chromium")
                    stats = record.get("stats", {})
                    sent_total = int(stats.get("sent_ok", 0)) + int(stats.get("sent_failed", 0))
                    if browser in browser_stats and sent_total > 0:
                        browser_stats[browser]["ok"] += int(stats.get("sent_ok", 0))
                        browser_stats[browser]["total"] += sent_total
        except Exception:
            return None

        candidates = []
        for browser, values in browser_stats.items():
            if values["total"] > 0:
                success_rate = values["ok"] / values["total"]
                candidates.append((success_rate, browser))

        if not candidates:
            return None

        candidates.sort(reverse=True)
        return candidates[0][1]

    def apply_adaptive_defaults(self):
        suggested = self.get_adaptive_browser()
        if suggested:
            self.browser_select.setCurrentText(suggested)
            self.log(f"Adaptive default browser: {suggested}")

    def load_settings_from_env(self):
        if os.path.exists(self.env_path):
            load_dotenv(self.env_path, override=True)
            self.email_input.setText(os.getenv("PROTON_USER", ""))
            self.password_input.setText(os.getenv("PROTON_PASS", ""))
            self.browser_select.setCurrentText(os.getenv("BROWSER", "chromium"))
            self.headless_check.setChecked(os.getenv("HEADLESS", "false").lower() == "true")
            self.dry_run_check.setChecked(os.getenv("DRY_RUN", "false").lower() == "true")
            try:
                self.max_companies.setValue(int(os.getenv("MAX_COMPANIES", "5")))
            except ValueError:
                self.max_companies.setValue(5)
            # Restore schedule settings
            schedule_time = os.getenv("SCHEDULE_TIME", "09:00")
            try:
                h, m = [int(x) for x in schedule_time.split(":")]
                self.schedule_time_edit.setTime(QTime(h, m))
            except (ValueError, AttributeError):
                self.schedule_time_edit.setTime(QTime(9, 0))
            schedule_enabled = os.getenv("SCHEDULE_ENABLED", "false").lower() == "true"
            self.schedule_enabled_check.setChecked(schedule_enabled)
            self.log("Loaded login options from .env")
        else:
            self.log("No .env found yet. Use 'Save Settings to .env' in the Settings tab.")

    def save_settings_to_env(self):
        env_content = (
            f"PROTON_USER={self.email_input.text().strip()}\n"
            f"PROTON_PASS={self.password_input.text().strip()}\n"
            f"BROWSER={self.browser_select.currentText()}\n"
            f"HEADLESS={str(self.headless_check.isChecked()).lower()}\n"
            f"DRY_RUN={str(self.dry_run_check.isChecked()).lower()}\n"
            f"MAX_COMPANIES={self.max_companies.value()}\n"
            f"SCHEDULE_TIME={self.schedule_time_edit.time().toString('HH:mm')}\n"
            f"SCHEDULE_ENABLED={str(self.schedule_enabled_check.isChecked()).lower()}\n"
        )
        with open(self.env_path, "w", encoding="utf-8") as env_file:
            env_file.write(env_content)
        self.log(f"Saved settings to {self.env_path}")

    def get_email_from_row(self, row):
        for key, value in row.items():
            if value is None:
                continue
            text = str(value).strip()
            if "@" in text and "." in text and len(text) > 5:
                return text
            key_name = str(key).lower()
            if "mail" in key_name and "@" in text:
                return text
        return None

    def select_cv_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select CV", "", "PDF Files (*.pdf)")
        if file_name:
            self.cv_path = file_name
            self.lbl_cv.setText(os.path.basename(file_name))
            self.log(f"CV selected: {self.cv_path}")

    def select_company_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Company List", "", "Excel Files (*.xlsx)")
        if file_name:
            self.company_list_path = file_name
            self.lbl_companies.setText(os.path.basename(file_name))
            self.log(f"Company list selected: {self.company_list_path}")

    def send_test_email(self):
        if not self.are_credentials_valid(): return
        if not self.cv_path:
            self.log("Please select a CV file first.")
            return

        if self.save_credentials_check.isChecked():
            self.save_settings_to_env()
            
        self.log("Sending test email...")
        
        test_subject = "Test Email from Job Automator"
        test_body = "This is a test email sent automatically. The CV is attached."
        
        success = send_email_with_protonmail(
            username=self.email_input.text(),
            password=self.password_input.text(),
            recipient_email="sourovdeb.is@gmail.com",
            subject=test_subject,
            body=test_body,
            attachment_path=self.cv_path,
            browser_name=self.browser_select.currentText(),
            headless=self.headless_check.isChecked()
        )
        
        if success:
            self.log("Test email sent successfully!")
        else:
            self.log("Failed to send test email. Check logs and credentials.")

    def start_automation(self):
        if not self.are_inputs_valid(): return

        if self.save_credentials_check.isChecked():
            self.save_settings_to_env()

        self.log("--- Starting Automation ---")
        self.init_run_metadata()
        
        # 1. Read data
        cv_text = extract_cv_text(self.cv_path)
        companies_df = read_company_list(self.company_list_path)

        if cv_text is None or companies_df is None:
            self.log("Failed to read CV or company list. Aborting.")
            return

        limit = self.max_companies.value()
        self.log(f"Configured run: browser={self.browser_select.currentText()}, headless={self.headless_check.isChecked()}, dry_run={self.dry_run_check.isChecked()}, max_companies={limit}")

        for index, row in companies_df.head(limit).iterrows():
            company_name = row.get('NOM')
            contact_email = self.get_email_from_row(row)

            if not company_name:
                self.log(f"Skipping row {index} due to missing company name.")
                self.record_company_result("UNKNOWN", "skipped", "missing company name", contact_email_found=bool(contact_email))
                continue

            self.log(f"\nProcessing {company_name}...")

            # 2. Research company
            company_research = search_company_website(company_name)
            if not company_research:
                self.log(f"Could not find information for {company_name}. Skipping.")
                self.record_company_result(company_name, "skipped", "research not found", contact_email_found=bool(contact_email))
                continue

            # 3. Generate email
            email_subject = f"Inquiry from a skilled professional regarding opportunities at {company_name}"
            email_body = generate_email_body(cv_text, row, company_research)
            
            # 4. Send email
            if not contact_email:
                self.log(f"No contact email found for {company_name}. Skipping.")
                self.record_company_result(company_name, "skipped", "contact email not found", contact_email_found=False)
                continue

            if self.dry_run_check.isChecked():
                self.log(f"Dry run: prepared email to {contact_email} for {company_name}.")
                self.record_company_result(company_name, "dry_run_ready", "email generated only", contact_email_found=True)
                continue

            self.log(f"Sending email to {contact_email} for {company_name}...")
            success = send_email_with_protonmail(
                username=self.email_input.text(),
                password=self.password_input.text(),
                recipient_email=contact_email,
                subject=email_subject,
                body=email_body,
                attachment_path=self.cv_path,
                browser_name=self.browser_select.currentText(),
                headless=self.headless_check.isChecked()
            )

            if success:
                self.log(f"Email to {company_name} sent successfully!")
                self.record_company_result(company_name, "sent_ok", "", contact_email_found=True)
            else:
                self.log(f"Failed to send email to {company_name}.")
                self.record_company_result(company_name, "sent_failed", "send function returned failure", contact_email_found=True)

        self.save_run_metadata()
        self.log("--- Automation Finished ---")

    def are_credentials_valid(self):
        if not self.email_input.text() or not self.password_input.text():
            self.log("Please enter your ProtonMail credentials.")
            return False
        return True

    def are_inputs_valid(self):
        if not self.are_credentials_valid(): return False
        if not self.cv_path or not self.company_list_path:
            self.log("Please select both a CV and a company list file.")
            return False
        return True


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = JobAutomatorApp()
    ex.show()
    sys.exit(app.exec())
