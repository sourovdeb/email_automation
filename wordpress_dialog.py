"""
wordpress_dialog.py

WordPress Automation panel for the Job Automator dashboard.

Opens as a child window from the main dashboard.  Layout mirrors the
WordPress post editor so users already familiar with WordPress feel at home.
"""

import sys
from datetime import datetime

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QLineEdit, QLabel, QTextEdit,
    QComboBox, QDateTimeEdit, QCheckBox, QGroupBox,
    QFileDialog, QSizePolicy
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QDateTime

from wordpress_automation import WordPressClient


class WordPressDialog(QDialog):
    """
    WordPress-like post editor dialog.

    Sections
    --------
    1. Site credentials  (URL, username, application password)
    2. Post editor       (title + full content, mirrors WP classic editor)
    3. Publish panel     (status, schedule date/time)
    4. Categorisation    (categories + tags – comma-separated)
    5. SEO / Excerpt     (short description sent as WP excerpt)
    6. Optional featured image upload
    7. Action buttons    (Test Connection · Save Draft · Schedule · Publish Now)
    8. Live status log
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("WordPress Post Automator")
        self.setMinimumSize(820, 900)
        self._apply_stylesheet()
        self._build_ui()

    # ------------------------------------------------------------------
    # Stylesheet
    # ------------------------------------------------------------------

    def _apply_stylesheet(self):
        self.setStyleSheet(
            "QDialog { background: #f0f0f1; color: #1d2327; }"
            "QGroupBox { font-weight: 700; font-size: 13px; border: 1px solid #c3c4c7;"
            "            border-radius: 6px; margin-top: 12px; padding-top: 8px; background: #fff; }"
            "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left;"
            "                   padding: 0 6px; }"
            "QPushButton { min-height: 36px; font-size: 13px; font-weight: 600;"
            "              border-radius: 4px; padding: 6px 14px; }"
            "QPushButton#btn_publish { background: #2271b1; color: #fff; }"
            "QPushButton#btn_publish:hover { background: #135e96; }"
            "QPushButton#btn_draft  { background: #f6f7f7; color: #2271b1;"
            "                         border: 1px solid #2271b1; }"
            "QPushButton#btn_draft:hover  { background: #f0f6fc; }"
            "QPushButton#btn_schedule { background: #00a32a; color: #fff; }"
            "QPushButton#btn_schedule:hover { background: #007017; }"
            "QPushButton#btn_test { background: #f6f7f7; color: #1d2327;"
            "                       border: 1px solid #c3c4c7; }"
            "QPushButton#btn_test:hover { background: #ededed; }"
            "QLineEdit, QTextEdit, QComboBox, QDateTimeEdit {"
            "    min-height: 34px; font-size: 13px; border: 1px solid #c3c4c7;"
            "    border-radius: 4px; padding: 4px 8px; background: #fff; }"
            "QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateTimeEdit:focus {"
            "    border: 2px solid #2271b1; }"
            "QLabel { font-size: 13px; color: #1d2327; }"
            "QCheckBox { font-size: 13px; spacing: 6px; }"
        )

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(12)
        root.setContentsMargins(16, 16, 16, 16)

        # ── 1. Site credentials ────────────────────────────────────────
        cred_group = QGroupBox("Site Credentials")
        cred_form = QFormLayout(cred_group)
        cred_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.inp_site_url = QLineEdit()
        self.inp_site_url.setPlaceholderText("https://yoursite.com")
        self.inp_site_url.setAccessibleName("WordPress site URL")
        cred_form.addRow("Site URL:", self.inp_site_url)

        self.inp_wp_user = QLineEdit()
        self.inp_wp_user.setPlaceholderText("WordPress username")
        self.inp_wp_user.setAccessibleName("WordPress username")
        cred_form.addRow("Username:", self.inp_wp_user)

        self.inp_wp_pass = QLineEdit()
        self.inp_wp_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.inp_wp_pass.setPlaceholderText("Application Password (Settings → Application Passwords)")
        self.inp_wp_pass.setAccessibleName("WordPress application password")
        cred_form.addRow("App Password:", self.inp_wp_pass)

        self.btn_test = QPushButton("Test Connection")
        self.btn_test.setObjectName("btn_test")
        self.btn_test.clicked.connect(self._test_connection)
        cred_form.addRow("", self.btn_test)

        root.addWidget(cred_group)

        # ── 2. Post editor ─────────────────────────────────────────────
        editor_group = QGroupBox("Post Editor")
        editor_layout = QVBoxLayout(editor_group)

        self.inp_title = QLineEdit()
        self.inp_title.setPlaceholderText("Add title")
        self.inp_title.setAccessibleName("Post title")
        font_title = QFont()
        font_title.setPointSize(16)
        font_title.setWeight(QFont.Weight.Bold)
        self.inp_title.setFont(font_title)
        self.inp_title.setStyleSheet("min-height: 42px; font-size: 18px; font-weight: bold; padding: 6px 10px;")
        editor_layout.addWidget(self.inp_title)

        editor_layout.addWidget(QLabel("Content:"))
        self.inp_content = QTextEdit()
        self.inp_content.setPlaceholderText("Start writing or paste your post content here…")
        self.inp_content.setMinimumHeight(200)
        self.inp_content.setAccessibleName("Post content")
        editor_layout.addWidget(self.inp_content)

        root.addWidget(editor_group)

        # ── 3. Publish panel ───────────────────────────────────────────
        pub_group = QGroupBox("Publish")
        pub_form = QFormLayout(pub_group)
        pub_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.cmb_status = QComboBox()
        self.cmb_status.addItems(["Draft", "Publish Now", "Schedule"])
        self.cmb_status.currentTextChanged.connect(self._on_status_changed)
        self.cmb_status.setAccessibleName("Post status")
        pub_form.addRow("Status:", self.cmb_status)

        self.chk_schedule = QCheckBox("Schedule for:")
        self.chk_schedule.setVisible(False)
        self.inp_schedule_dt = QDateTimeEdit(QDateTime.currentDateTime())
        self.inp_schedule_dt.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.inp_schedule_dt.setCalendarPopup(True)
        self.inp_schedule_dt.setVisible(False)
        self.inp_schedule_dt.setAccessibleName("Schedule date and time")
        sched_row = QHBoxLayout()
        sched_row.addWidget(self.chk_schedule)
        sched_row.addWidget(self.inp_schedule_dt)
        sched_row.addStretch()
        pub_form.addRow("", sched_row)

        root.addWidget(pub_group)

        # ── 4. Categorisation ──────────────────────────────────────────
        cat_group = QGroupBox("Categories & Tags")
        cat_form = QFormLayout(cat_group)
        cat_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.inp_categories = QLineEdit()
        self.inp_categories.setPlaceholderText("News, Technology, Business (comma-separated)")
        self.inp_categories.setAccessibleName("Post categories, comma separated")
        cat_form.addRow("Categories:", self.inp_categories)

        self.inp_tags = QLineEdit()
        self.inp_tags.setPlaceholderText("python, automation, jobs (comma-separated)")
        self.inp_tags.setAccessibleName("Post tags, comma separated")
        cat_form.addRow("Tags:", self.inp_tags)

        root.addWidget(cat_group)

        # ── 5. SEO / Excerpt ───────────────────────────────────────────
        seo_group = QGroupBox("SEO / Excerpt")
        seo_form = QFormLayout(seo_group)
        seo_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.inp_excerpt = QTextEdit()
        self.inp_excerpt.setPlaceholderText("Short description used by search engines and social shares (max ~160 chars).")
        self.inp_excerpt.setMaximumHeight(80)
        self.inp_excerpt.setAccessibleName("Post excerpt / SEO description")
        seo_form.addRow("Excerpt / Meta:", self.inp_excerpt)

        root.addWidget(seo_group)

        # ── 6. Featured image ──────────────────────────────────────────
        img_group = QGroupBox("Featured Image (optional)")
        img_layout = QHBoxLayout(img_group)

        self.lbl_image_path = QLabel("No image selected")
        self.lbl_image_path.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.lbl_image_path.setWordWrap(True)
        img_layout.addWidget(self.lbl_image_path)

        self.btn_image = QPushButton("Choose Image…")
        self.btn_image.setObjectName("btn_image")
        self.btn_image.clicked.connect(self._select_image)
        img_layout.addWidget(self.btn_image)

        self._image_path = ""
        root.addWidget(img_group)

        # ── 7. Action buttons ──────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.btn_draft = QPushButton("Save Draft")
        self.btn_draft.setObjectName("btn_draft")
        self.btn_draft.clicked.connect(lambda: self._submit_post("draft"))
        btn_row.addWidget(self.btn_draft)

        self.btn_schedule = QPushButton("Schedule Post")
        self.btn_schedule.setObjectName("btn_schedule")
        self.btn_schedule.clicked.connect(lambda: self._submit_post("future"))
        self.btn_schedule.setVisible(False)
        btn_row.addWidget(self.btn_schedule)

        self.btn_publish = QPushButton("Publish Now")
        self.btn_publish.setObjectName("btn_publish")
        self.btn_publish.clicked.connect(lambda: self._submit_post("publish"))
        btn_row.addWidget(self.btn_publish)

        root.addLayout(btn_row)

        # ── 8. Live status log ─────────────────────────────────────────
        root.addWidget(QLabel("Status:"))
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setMaximumHeight(130)
        self.log_display.setAccessibleName("WordPress automation status log")
        root.addWidget(self.log_display)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_status_changed(self, text):
        is_scheduled = text == "Schedule"
        self.chk_schedule.setVisible(is_scheduled)
        self.inp_schedule_dt.setVisible(is_scheduled)
        self.btn_schedule.setVisible(is_scheduled)

    def _select_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Featured Image", "",
            "Image Files (*.png *.jpg *.jpeg *.gif *.webp)"
        )
        if path:
            self._image_path = path
            self.lbl_image_path.setText(path.split("/")[-1])
            self._log(f"Image selected: {path}")

    # ------------------------------------------------------------------
    # Core actions
    # ------------------------------------------------------------------

    def _log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_display.append(f"[{timestamp}] {message}")

    def _build_client(self):
        """Creates a WordPressClient from the current credential fields."""
        site_url = self.inp_site_url.text().strip()
        username = self.inp_wp_user.text().strip()
        app_password = self.inp_wp_pass.text().strip()

        if not site_url or not username or not app_password:
            self._log("Please fill in Site URL, Username, and Application Password.")
            return None

        return WordPressClient(site_url, username, app_password)

    def _test_connection(self):
        client = self._build_client()
        if not client:
            return
        self._log("Testing connection…")
        ok, msg = client.test_connection()
        self._log(("✓ " if ok else "✗ ") + msg)

    def _submit_post(self, forced_status: str = None):
        client = self._build_client()
        if not client:
            return

        title = self.inp_title.text().strip()
        content = self.inp_content.toPlainText().strip()
        if not title:
            self._log("A post title is required.")
            return
        if not content:
            self._log("Post content cannot be empty.")
            return

        # Determine status
        if forced_status:
            status = forced_status
        else:
            mapping = {"Draft": "draft", "Publish Now": "publish", "Schedule": "future"}
            status = mapping.get(self.cmb_status.currentText(), "draft")

        # Schedule datetime
        scheduled_at = None
        if status == "future":
            qdt = self.inp_schedule_dt.dateTime()
            scheduled_at = datetime(
                qdt.date().year(), qdt.date().month(), qdt.date().day(),
                qdt.time().hour(), qdt.time().minute()
            )

        # Categorisation
        categories = [c.strip() for c in self.inp_categories.text().split(",") if c.strip()]
        tags = [t.strip() for t in self.inp_tags.text().split(",") if t.strip()]

        # SEO excerpt
        excerpt = self.inp_excerpt.toPlainText().strip()

        self._log(f"Submitting post '{title}' (status={status})…")

        # Upload featured image first (if any)
        featured_media_id = None
        if self._image_path:
            self._log("Uploading featured image…")
            media_id, media_msg = client.upload_media(self._image_path, alt_text=title)
            self._log(media_msg)
            featured_media_id = media_id

        # Create the post
        post_id, post_msg = client.create_post(
            title=title,
            content=content,
            status=status,
            categories=categories,
            tags=tags,
            excerpt=excerpt,
            scheduled_at=scheduled_at,
        )

        # Attach featured image if uploaded
        if post_id and featured_media_id:
            try:
                client.session.post(
                    f"{client.base_url}/posts/{post_id}",
                    json={"featured_media": featured_media_id},
                    timeout=15,
                )
                self._log("Featured image attached.")
            except Exception as exc:
                self._log(f"Warning: could not attach featured image ({exc})")

        self._log(("✓ " if post_id else "✗ ") + post_msg)


# ---------------------------------------------------------------------------
# Standalone launch (for development / testing)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    _app = QApplication(sys.argv)
    dlg = WordPressDialog()
    dlg.show()
    sys.exit(_app.exec())
