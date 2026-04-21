import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, 
                             QFileDialog, QLineEdit, QLabel, QTextEdit, QFormLayout,
                             QSpinBox, QCheckBox, QComboBox)
from PyQt6.QtGui import QFont
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Import our automation modules
from data_parser import read_company_list, extract_cv_text
from researcher import search_company_website
from email_generator import generate_email_body
from email_sender import send_email_with_protonmail

class JobAutomatorApp(QWidget):
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
        self.initUI()
        self.load_settings_from_env()
        self.apply_adaptive_defaults()

    def initUI(self):
        self.setWindowTitle('Job Application Automator')
        self.setGeometry(80, 80, 860, 820)

        layout = QVBoxLayout()
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(form_layout.labelAlignment())

        # Accessibility-first sizing and contrast.
        app_font = QFont("DejaVu Sans", 12)
        self.setFont(app_font)
        self.setStyleSheet(
            "QWidget { background: #f7f8fa; color: #111; }"
            "QPushButton { min-height: 44px; font-size: 14px; font-weight: 600; background: #0b5fff; color: white; border-radius: 8px; padding: 8px 12px; }"
            "QPushButton:focus { border: 3px solid #ff8c00; }"
            "QLineEdit, QComboBox, QSpinBox, QTextEdit { min-height: 38px; font-size: 14px; border: 2px solid #c4c7ce; border-radius: 6px; padding: 6px; background: #fff; }"
            "QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QTextEdit:focus { border: 3px solid #ff8c00; }"
            "QLabel { font-size: 13px; }"
            "QCheckBox { font-size: 14px; spacing: 8px; }"
        )

        # File selection buttons
        self.btn_cv = QPushButton('Select CV (PDF)', self)
        self.btn_cv.clicked.connect(self.select_cv_file)
        self.lbl_cv = QLabel('No file selected')
        self.lbl_cv.setWordWrap(True)
        form_layout.addRow(self.btn_cv, self.lbl_cv)

        self.btn_companies = QPushButton('Select Company List (XLSX)', self)
        self.btn_companies.clicked.connect(self.select_company_file)
        self.lbl_companies = QLabel('No file selected')
        self.lbl_companies.setWordWrap(True)
        form_layout.addRow(self.btn_companies, self.lbl_companies)

        # ProtonMail credentials
        self.email_input = QLineEdit(self)
        self.email_input.setPlaceholderText("Your ProtonMail Email")
        self.email_input.setAccessibleName("ProtonMail user email")
        form_layout.addRow(QLabel("ProtonMail User:"), self.email_input)

        self.password_input = QLineEdit(self)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Your ProtonMail Password")
        self.password_input.setAccessibleName("ProtonMail password")
        form_layout.addRow(QLabel("ProtonMail Pass:"), self.password_input)

        self.save_credentials_check = QCheckBox("Save login options to .env", self)
        self.save_credentials_check.setChecked(True)
        form_layout.addRow(QLabel("Credentials:"), self.save_credentials_check)

        # Runtime options for reuse without AI.
        self.browser_select = QComboBox(self)
        self.browser_select.addItems(["chromium", "firefox"])
        self.browser_select.setCurrentText("chromium")
        form_layout.addRow(QLabel("Browser:"), self.browser_select)

        self.headless_check = QCheckBox("Run browser in background (headless)", self)
        self.headless_check.setChecked(False)
        form_layout.addRow(QLabel("Mode:"), self.headless_check)

        self.dry_run_check = QCheckBox("Dry run only (generate and log emails, do not send)", self)
        self.dry_run_check.setChecked(False)
        form_layout.addRow(QLabel("Safety:"), self.dry_run_check)

        self.max_companies = QSpinBox(self)
        self.max_companies.setMinimum(1)
        self.max_companies.setMaximum(260)
        self.max_companies.setValue(5)
        form_layout.addRow(QLabel("Max companies:"), self.max_companies)

        layout.addLayout(form_layout)

        # Action buttons
        self.btn_test = QPushButton('Send Test Email to sourovdeb.is@gmail.com', self)
        self.btn_test.clicked.connect(self.send_test_email)
        layout.addWidget(self.btn_test)

        self.btn_save_env = QPushButton('Save Login Options to .env', self)
        self.btn_save_env.clicked.connect(self.save_settings_to_env)
        layout.addWidget(self.btn_save_env)

        self.btn_start = QPushButton('Start Automation', self)
        self.btn_start.clicked.connect(self.start_automation)
        layout.addWidget(self.btn_start)

        # Log display
        self.log_display = QTextEdit(self)
        self.log_display.setReadOnly(True)
        self.log_display.setAccessibleName("Live automation log")
        layout.addWidget(QLabel("Logs:"))
        layout.addWidget(self.log_display)

        self.setLayout(layout)

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
            self.log("Loaded login options from .env")
        else:
            self.log("No .env found yet. Use 'Save Login Options to .env' after entering values.")

    def save_settings_to_env(self):
        env_content = (
            f"PROTON_USER={self.email_input.text().strip()}\n"
            f"PROTON_PASS={self.password_input.text().strip()}\n"
            f"BROWSER={self.browser_select.currentText()}\n"
            f"HEADLESS={str(self.headless_check.isChecked()).lower()}\n"
            f"DRY_RUN={str(self.dry_run_check.isChecked()).lower()}\n"
            f"MAX_COMPANIES={self.max_companies.value()}\n"
        )
        with open(self.env_path, "w", encoding="utf-8") as env_file:
            env_file.write(env_content)
        self.log(f"Saved login options to {self.env_path}")

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
