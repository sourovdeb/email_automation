# Wiki: How to Use the Job Automator Dashboard

Date: 2026-04-21

---

## Table of Contents

1. [Overview](#1-overview)
2. [Prerequisites](#2-prerequisites)
3. [Installation](#3-installation)
4. [Running the Dashboard](#4-running-the-dashboard)
5. [Email Automation (Job Outreach)](#5-email-automation-job-outreach)
6. [WordPress Post Automator](#6-wordpress-post-automator)
   - [6.1 Generate a WordPress Application Password](#61-generate-a-wordpress-application-password)
   - [6.2 Open the WordPress Automator](#62-open-the-wordpress-automator)
   - [6.3 Test the Connection](#63-test-the-connection)
   - [6.4 Write and Publish a Post](#64-write-and-publish-a-post)
   - [6.5 Schedule a Post](#65-schedule-a-post)
   - [6.6 Add Categories and Tags](#66-add-categories-and-tags)
   - [6.7 Add a Featured Image](#67-add-a-featured-image)
   - [6.8 SEO / Excerpt](#68-seo--excerpt)
7. [Project File Structure](#7-project-file-structure)
8. [Troubleshooting](#8-troubleshooting)
9. [Security Notes](#9-security-notes)

---

## 1. Overview

The **Job Automator Dashboard** is a desktop application built with Python and PyQt6
that runs natively on Linux. It has two main tools:

| Tool | Purpose |
|------|---------|
| **Email Automation** | Sends personalised job-application emails to companies from an XLSX list, using your CV (PDF) and ProtonMail. |
| **WordPress Automator** | Creates, schedules and publishes blog posts on any self-hosted WordPress site via the REST API. |

Both tools are launched from the same dashboard window. No web browser is required
to use the WordPress feature — everything is controlled from the desktop GUI.

---

## 2. Prerequisites

- Linux (Ubuntu 20.04+ recommended)
- Python 3.9 or later
- A self-hosted WordPress site with REST API enabled (WordPress 5.6+)
- A ProtonMail account (for the email tool)
- Internet access

---

## 3. Installation

```bash
# 1. Clone the repository
git clone https://github.com/sourovdeb/email_automation.git
cd email_automation

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install Playwright browser drivers (only needed for email automation)
playwright install chromium firefox
```

---

## 4. Running the Dashboard

```bash
source .venv/bin/activate
python main_app.py
```

The dashboard window opens. All features are accessible from the buttons on this window.

---

## 5. Email Automation (Job Outreach)

1. Click **Select CV (PDF)** and choose your CV file.
2. Click **Select Company List (XLSX)** and choose your company spreadsheet.
   - The sheet must have at least a column named `NOM` (company name).
   - An email/contact column is used when present.
3. Enter your **ProtonMail** username and password.
4. Adjust optional settings:
   - **Browser**: `chromium` or `firefox`
   - **Headless**: run the browser invisibly in the background
   - **Dry run**: generate emails without actually sending (recommended for first test)
   - **Max companies**: how many rows to process in one run
5. Click **Save Login Options to .env** to store credentials locally.
6. Click **Send Test Email** to verify the setup sends one email to `sourovdeb.is@gmail.com`.
7. When satisfied, uncheck **Dry run** and click **Start Automation**.

Logs appear live in the bottom panel and are also saved to `logs/automation.log`.

---

## 6. WordPress Post Automator

The WordPress Automator lets you create, schedule and publish blog posts from
the desktop — without opening a web browser.

### 6.1 Generate a WordPress Application Password

WordPress Application Passwords are safer than your main login password because
they can be revoked at any time without changing your password.

1. Log in to your WordPress admin panel.
2. Go to **Users → Profile** (or **Users → All Users → Edit your user**).
3. Scroll down to the **Application Passwords** section.
4. Type a name for the password (e.g. `Desktop Automator`) and click **Add New Application Password**.
5. Copy the generated password — it looks like `xxxx xxxx xxxx xxxx xxxx xxxx`.
   You will only see it once.

> **Tip:** If you do not see the Application Passwords section, make sure your site
> uses HTTPS and that the WordPress REST API is not disabled by a security plugin.

---

### 6.2 Open the WordPress Automator

1. Start the dashboard (`python main_app.py`).
2. Click the **WordPress Automator** button (blue, near the bottom of the dashboard).
3. The WordPress Post Editor dialog opens in a new window.

---

### 6.3 Test the Connection

Fill in the **Site Credentials** section:

| Field | Example |
|-------|---------|
| Site URL | `https://myblog.com` |
| Username | `admin` |
| App Password | `xxxx xxxx xxxx xxxx xxxx xxxx` |

Click **Test Connection**. The status log at the bottom of the dialog shows either:

- ✓ `Connected as 'Admin Name'` — credentials are correct.
- ✗ Error message — check the URL (must include `https://`) and password.

---

### 6.4 Write and Publish a Post

1. In the **Post Editor** section, type a **title** in the large title field.
2. Type or paste the post **content** in the text area below.
3. In the **Publish** section, choose **Publish Now** from the Status dropdown.
4. Click **Publish Now** (blue button).

The status log shows `✓ Post created (ID 42): https://myblog.com/?p=42` on success.

---

### 6.5 Schedule a Post

1. Choose **Schedule** from the Status dropdown in the **Publish** section.
2. A date/time picker appears — select the date and time you want the post to go live.
3. Click **Schedule Post** (green button).

The post is saved in WordPress with status `future` and will be published automatically
at the chosen time by the WordPress cron system.

---

### 6.6 Add Categories and Tags

In the **Categories & Tags** section:

- **Categories**: Enter category names separated by commas.
  Example: `News, Technology, Career`
- **Tags**: Enter tag names separated by commas.
  Example: `python, automation, linux`

If a category or tag does not yet exist on your site, it is created automatically.
Existing categories and tags are reused — no duplicates are created.

---

### 6.7 Add a Featured Image

1. In the **Featured Image** section, click **Choose Image…**.
2. Select a `.jpg`, `.png`, `.gif` or `.webp` file from your computer.
3. The image is uploaded to your WordPress Media Library when you submit the post.
4. It is automatically set as the featured image for that post.

---

### 6.8 SEO / Excerpt

In the **SEO / Excerpt** section, enter a short description (ideally under 160
characters). This text is stored as the WordPress post excerpt, which:

- Appears in search engine results (when used by your SEO plugin such as Yoast or RankMath).
- Is shown on archive and category pages as the post summary.
- Is used by social sharing plugins for Open Graph descriptions.

---

## 7. Project File Structure

```
email_automation/
│
├── main_app.py              # Dashboard entry point (PyQt6 GUI)
├── wordpress_automation.py  # WordPress REST API client
├── wordpress_dialog.py      # WordPress post editor dialog (PyQt6)
├── email_generator.py       # Personalised email body generator
├── email_sender.py          # ProtonMail send automation (Playwright)
├── data_parser.py           # CV PDF and XLSX list reader
├── researcher.py            # Company web research
├── requirements.txt         # Python dependencies
├── README.md                # Project overview
├── how_it_woks.md           # Test and validation log (filename preserved for compatibility)
├── wiki_how.md              # This file
│
├── .env                     # Local credentials (never committed)
├── logs/
│   └── automation.log       # Timestamped runtime log
└── data/
    ├── metadata/
    │   └── runs.jsonl       # Per-run metadata (local learning)
    └── attachments/         # Optional extra attachments
```

---

## 8. Troubleshooting

| Problem | Solution |
|---------|----------|
| "Could not reach the site" | Check the Site URL (must start with `https://`). Verify internet access. |
| "Auth failed (HTTP 401)" | Re-generate the Application Password in WP admin. Ensure username is correct. |
| Application Passwords section missing | Ensure HTTPS is configured. Check that a security plugin is not disabling the REST API. |
| Post created but not published immediately | For `future` status, WordPress uses its own cron. Ensure WP-Cron is running, or use a real cron job: `*/5 * * * * curl https://yoursite.com/wp-cron.php?doing_wp_cron` |
| Image upload fails | Check that your WordPress user role has permission to upload files (Author or above). |
| "Failed to create post (HTTP 403)" | Your user may not have permission to publish posts. Use an Administrator or Editor account. |
| PyQt6 not found | Run `pip install PyQt6` inside the activated virtual environment. |
| Playwright browser not installed | Run `playwright install chromium firefox`. |

---

## 9. Security Notes

1. **Application Passwords** are preferable to your main WordPress password.
   Revoke them in WP admin at any time without affecting your login.
2. **Never commit** your `.env` file or any file containing passwords.
   The `.gitignore` already excludes `.env`.
3. **HTTPS is required** by WordPress for Application Password authentication.
   Plain HTTP sites will reject the credentials.
4. Credentials entered in the WordPress dialog are used only for the current
   session. They are not saved to disk automatically.
5. Do not paste raw passwords into the `Site URL` field by mistake.
