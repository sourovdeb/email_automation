import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, 
                             QFileDialog, QLineEdit, QLabel, QTextEdit, QFormLayout,
                             QSpinBox, QCheckBox, QComboBox)
from PyQt6.QtGui import QFont
import os

# Import our automation modules
from data_parser import read_company_list, extract_cv_text
from researcher import search_company_website
from email_generator import generate_email_body
from email_sender import send_email_with_protonmail

class JobAutomatorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.cv_path = ""
        self.company_list_path = ""
        self.initUI()

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
        QApplication.processEvents() # Update the GUI

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

        self.log("--- Starting Automation ---")
        
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
                continue

            self.log(f"\nProcessing {company_name}...")

            # 2. Research company
            company_research = search_company_website(company_name)
            if not company_research:
                self.log(f"Could not find information for {company_name}. Skipping.")
                continue

            # 3. Generate email
            email_subject = f"Inquiry from a skilled professional regarding opportunities at {company_name}"
            email_body = generate_email_body(cv_text, row, company_research)
            
            # 4. Send email
            if not contact_email:
                self.log(f"No contact email found for {company_name}. Skipping.")
                continue

            if self.dry_run_check.isChecked():
                self.log(f"Dry run: prepared email to {contact_email} for {company_name}.")
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
            else:
                self.log(f"Failed to send email to {company_name}.")
        
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
