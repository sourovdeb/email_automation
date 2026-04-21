# Job Application Automator — Wiki & User Manual

> Version 2.0 | Language: English & Français | Last updated: 2026-04-21

---

## Table of Contents

1. [What this does](#1-what-this-does)
2. [Quick Start (5 minutes)](#2-quick-start)
3. [File & Folder Structure](#3-file--folder-structure)
4. [Tab-by-Tab Guide](#4-tab-by-tab-guide)
5. [AI Providers — choosing one](#5-ai-providers)
6. [Sending without AI (Template Mode)](#6-sending-without-ai)
7. [Email & Attachment Guidelines](#7-email--attachment-guidelines)
8. [How company research works](#8-how-company-research-works)
9. [ProtonMail & Playwright — how it works](#9-protonmail--playwright)
10. [Bulk sending strategy](#10-bulk-sending-strategy)
11. [Troubleshooting](#11-troubleshooting)
12. [How it was built — technical log](#12-how-it-was-built)
13. [Reusing this system for any job search](#13-reusing-this-system)

---

## 1. What this does

This system reads your **CV** and a **list of companies** (Excel), then:

1. Searches the web for each company's website (DuckDuckGo, no API key required)
2. Scrapes the site to find a **contact / HR email address**
3. Generates a **personalised French email** (via AI or a high-quality template)
4. Logs into **ProtonMail** using your browser (via Playwright)
5. Composes and sends the email with your **CV attached**
6. Logs every result to a local file

All steps are visible in the GUI, controllable, and replayable.

---

## 2. Quick Start

### Prerequisites

```bash
# 1 — Install Python dependencies
pip install -r requirements.txt

# 2 — Install Playwright browsers (once)
playwright install chromium firefox

# 3 — Copy and fill in your settings
cp .env.example .env   # then edit .env with your ProtonMail credentials
```

### Run the GUI

```bash
python main_app.py
# or from Aeon Dashboard:
python ../aeon_dashboard/aeon_dashboard.py
```

### First run checklist

- [ ] Tab **Configuration** → select your CV (PDF)
- [ ] Tab **Configuration** → select the company list (XLSX)
- [ ] Tab **Configuration** → enter your ProtonMail email + password
- [ ] Tab **Paramètres** → set AI provider (or leave as "Template")
- [ ] Tab **Paramètres** → set **Dry run = ON** (safe preview mode)
- [ ] Tab **Lancement** → click **Lancer l'automatisation**
- [ ] Tab **Aperçu** → review generated emails
- [ ] Uncheck Dry run, run again to actually send

---

## 3. File & Folder Structure

```
job_automator/
├── main_app.py          # GUI (PyQt6) — run this
├── data_parser.py       # reads XLSX company list + PDF CV
├── researcher.py        # DuckDuckGo search + web scraping + email finder
├── email_generator.py   # AI or template email generation
├── email_sender.py      # ProtonMail automation via Playwright
├── requirements.txt     # Python dependencies
├── .env                 # credentials & settings (never commit this!)
├── wiki.md              # this file
├── logs/
│   └── automation.log   # timestamped log of every run
└── data/
    ├── attachments/     # put extra files to attach here
    └── metadata/
        └── runs.jsonl   # JSON log of every automation run
```

**Where to put your files:**

| File | Recommended path |
|------|-----------------|
| CV (PDF) | anywhere — you select it via the GUI |
| Company list (XLSX) | anywhere — you select it via the GUI |
| Motivation letter (PDF) | anywhere — optional, select via GUI |

---

## 4. Tab-by-Tab Guide

### ⚙ Configuration

| Field | What to do |
|-------|-----------|
| **Choisir CV** | Click, select your CV PDF. Required. |
| **Liste entreprises** | Click, select your `.xlsx` company list. Required. |
| **Lettre motivation** | Optional. Adds extra context to AI-generated emails. |
| **Email ProtonMail** | Your full ProtonMail address, e.g. `you@proton.me` |
| **Mot de passe** | Your ProtonMail login password |
| **Mémoriser dans .env** | When checked, saves credentials locally on "Save" |
| **Envoyer email de test** | Sends ONE test email to verify everything works |

### ▶ Lancement

- Click **Lancer l'automatisation** to start
- Watch the live log — each company is processed one by one
- The progress bar fills as companies are processed
- Click **Arrêter** at any time to stop safely

### 📧 Aperçu

After running, select any company from the dropdown to see the exact email that was (or would be) sent. Subject and body are both shown. Use this in Dry Run mode to review before sending.

### 🔧 Paramètres

| Setting | Explanation |
|---------|------------|
| **Navigateur** | chromium (recommended) or firefox |
| **Mode invisible** | Headless = browser runs hidden. Leave OFF for troubleshooting. |
| **Dry run** | ON = generate emails but do NOT send. Use for review. |
| **Max entreprises** | How many companies to process per run (start with 5–10) |
| **Fournisseur IA** | See section 5 below |

### 📋 Historique

Each time you run the automator, a record is saved. The History tab shows:
- Timestamp of each run
- Whether it was a Dry run or Live send
- Count of: processed, sent, skipped, failed

---

## 5. AI Providers

The system works with **any one** of these. Choose based on what you have:

### Option A — Template (no AI, always works)

**No account, no key, no internet needed for email generation.**
Uses a high-quality French template with company-specific personalisation.
Good enough for 90% of use cases.

```
Paramètres → Fournisseur IA → "template (sans IA)"
```

### Option B — Anthropic (Claude Haiku)

Best quality. Fast. Pay-per-use (very cheap).

```
1. Go to: https://console.anthropic.com
2. Create account → API Keys → New Key
3. Copy key (starts with sk-ant-…)
4. Paramètres → Fournisseur IA → "anthropic"
5. Paste key into "Clé API"
```

Model used: `claude-haiku-4-5-20251001` — optimised for speed and cost.

### Option C — Mistral AI

Good quality, EU-based, cheaper than Claude.

```
1. Go to: https://console.mistral.ai
2. Create account → API Keys → New Key
3. Copy key
4. Install: pip install mistralai
5. Paramètres → Fournisseur IA → "mistral"
6. Paste key into "Clé API"
```

Model used: `mistral-small-latest`

### Option D — DeepSeek

Cheapest paid option. OpenAI-compatible API.

```
1. Go to: https://platform.deepseek.com
2. Create account → API Keys → New Key  
3. Key starts with: sk-…
4. Install: pip install openai
5. Paramètres → Fournisseur IA → "deepseek"
6. Paste key into "Clé API"
```

Model used: `deepseek-chat`

### Option E — Ollama (local, free forever)

Runs 100% on your computer. No account needed. No cost. Privacy-first.

```
1. Install Ollama: https://ollama.com
2. In terminal: ollama pull mistral
3. Ollama runs automatically in background
4. Paramètres → Fournisseur IA → "ollama"
5. Modèle Ollama: mistral  (or llama3, gemma3, etc.)
6. URL Ollama: http://localhost:11434  (default)
```

Recommended models for French email writing: `mistral`, `llama3`, `mistral-nemo`

**Priority order (automatic detection):** Anthropic → Mistral → DeepSeek → Ollama → Template

---

## 6. Sending without AI

The **Template mode** generates professional French emails without any AI:

**What the template does:**
1. Addresses the hiring manager generically
2. Introduces the candidate with key credentials (CELTA, IELTS, years of experience)
3. Adds a company-specific paragraph if website info was found
4. Closes with an invitation to meet

**To customise the template**, edit `email_generator.py` → `_TEMPLATE` variable.

**The template is always the fallback** — if any AI provider fails, the template is used automatically.

---

## 7. Email & Attachment Guidelines

### Subject line format

```
Candidature Formateur d'Anglais CELTA – [Company Name]
```

Keep it short and professional. The AI respects this format.

### Attachment rules

| Rule | Why |
|------|-----|
| CV must be a **PDF** | Universal, looks professional on all devices |
| Max attachment size: **5 MB** | ProtonMail limit |
| Filename: use your name, e.g. `Sourov_Deb_CV_2026.pdf` | Easier for HR to file |
| **Do not attach more than 2 files** | Avoid spam filters |

### Email body rules

| Rule | Why |
|------|-----|
| Written in **French** | Companies in DOM-TOM, La Réunion |
| Max **200 words** in the body | Hiring managers skim |
| **No HTML** — plain text only | Better deliverability, less likely spam |
| One clear **call to action** at the end | "I am available for an interview at your convenience" |

### Company list XLSX format

Your spreadsheet must have at minimum a **company name column**. The system auto-detects:

| Column name | Auto-detected as |
|-------------|-----------------|
| `Raison sociale`, `NOM`, `Company`, `Entreprise` | Company name |
| `Email`, `email`, `Mail`, `Courriel` | Email (skips web search if present) |
| `Ville`, `City` | City (used for search + personalisation) |
| `CP` | Postal code |
| `C.A.` | Revenue (used for context) |

If no email column is present, the system searches the web for each company's contact email.

---

## 8. How Company Research Works

```
Company name → DuckDuckGo search → Company website → Scrape contact/HR pages → Extract email
```

**Step by step:**

1. Search query: `[Company Name] [City] site officiel`
2. Parse DuckDuckGo HTML results (no API key required)
3. Filter out directories, LinkedIn, social media
4. Visit the top result
5. Try `/contact`, `/recrutement`, `/emploi`, `/carrieres`, `/rh` pages
6. Extract email addresses using regex
7. Rank emails: prefer `recrutement@`, `rh@`, `contact@` over generic ones
8. Save the company's About/Home text for AI personalisation

**When no email is found:**
- Company is logged as "skipped"
- You can manually add emails to the XLSX and re-run
- The run metadata shows exactly which companies were skipped

**Rate limiting:** The researcher waits 1–2 seconds between requests to be a good web citizen and avoid being blocked.

---

## 9. ProtonMail & Playwright — How it Works

Playwright is a browser automation library that controls a real browser (Chromium or Firefox) exactly as a human would.

**The send flow:**

```
Launch browser → Navigate to mail.proton.me/login →
Fill username + password → Click Sign In →
Wait for inbox to load → Click "New Message" →
Fill To: field → Fill Subject: → Fill body (via iframe editor) →
Attach CV file → Click Send → Wait for composer to close →
Close browser
```

**Why this approach?**
- ProtonMail uses end-to-end encryption — direct SMTP without Bridge is not supported on free plans
- Playwright controls a real browser, so it works exactly like a human
- The session is authenticated with your full password

**Resilience features:**
- Multiple CSS selector strategies per UI element (ProtonMail updates frequently)
- Auto-retry once on failure
- Headed mode (visible browser) for debugging; headless for speed

**Browser sessions for bulk sending:**
For multiple emails, the system logs in ONCE and sends all emails in that session — much faster than logging in per email.

---

## 10. Bulk Sending Strategy

### Recommended batch sizes

| Situation | Recommended max |
|-----------|----------------|
| First test | 1 (dry run) |
| First live send | 5 |
| Daily production | 30–50 |
| Full campaign | 50/day over multiple days |

### Why not all 500 at once?

- ProtonMail free plan: ~150 emails/day limit
- ProtonMail paid plan: much higher but not unlimited
- Sending too many at once may trigger spam filters at recipient companies
- Spreading sends over multiple days looks more natural

### Workflow for the full campaign

```
Day 1:  companies 1–50   (Max companies = 50)
Day 2:  companies 51–100
...
Day 10: companies 451–500
```

To resume from where you left off, filter the XLSX to skip already-processed rows, or set Max companies appropriately.

### The bulk sender script (no GUI, faster)

```bash
# Run headlessly in background
python bulk_sender.py \
  --cv /path/to/cv.pdf \
  --companies /path/to/companies.xlsx \
  --max 50 \
  --provider deepseek \
  --dry-run
```

---

## 11. Troubleshooting

### "Cannot locate username field"
ProtonMail may have changed their login UI. Run with `headless=False` to watch what happens. Update selectors in `email_sender.py → _LOGIN_USERNAME`.

### "Unable to fill email body"
The Rooster editor (ProtonMail's rich-text editor) uses iframes. Run headed mode to inspect the actual selector. Add the new selector to `email_sender.py → iframe_strategies`.

### "No results for [Company]"
DuckDuckGo returned no results. Try:
- Adding the company email manually to the XLSX
- Check if the company name in the spreadsheet is correct

### "AI error, falling back to template"
Check your API key is valid and has credits. The template fallback ensures emails are still generated.

### Log files
All activity is logged to:
- `logs/automation.log` — human-readable timestamped log
- `data/metadata/runs.jsonl` — machine-readable JSON, one record per run

---

## 12. How it was Built — Technical Log

### Language & Libraries

| Component | Technology | Why |
|-----------|-----------|-----|
| GUI | Python + PyQt6 | Cross-platform, mature, accessible |
| Browser automation | Playwright (sync API) | Most reliable for modern web apps |
| Web research | requests + BeautifulSoup + lxml | Fast, no API key needed |
| Search engine | DuckDuckGo HTML endpoint | Free, no rate limits in reasonable use |
| CV parsing | PyPDF2 | Simple, reliable for text-based PDFs |
| Company data | pandas + openpyxl | Standard for Excel files |
| AI (Claude) | anthropic SDK | Best quality, reliable API |
| AI (Mistral) | mistralai SDK | EU-based alternative |
| AI (DeepSeek) | openai SDK (compatible) | Cheapest paid option |
| AI (Ollama) | HTTP API (requests) | 100% local, free |
| Config | python-dotenv | Simple .env file |

### Architecture decisions

1. **Separation of concerns** — each file does one thing: parse, research, generate, send.
2. **AI is optional** — template fallback means the system works with zero dependencies on external AI services.
3. **Column auto-detection** — the XLSX reader tries multiple column name variants so it works with different spreadsheet formats.
4. **Multiple CSS selectors** — the ProtonMail sender tries 5+ selector strategies per UI element to survive UI updates.
5. **Worker thread** — automation runs in a QThread so the GUI stays responsive.
6. **JSONL metadata** — each run appended as one JSON line, easy to query and never overwrites.

### Playwright send flow (detailed)

```python
# 1. Launch browser
browser = p.chromium.launch(headless=False)
page = browser.new_page()

# 2. Login
page.goto("https://mail.proton.me/login")
page.fill("#username", username)
page.fill("#password", password)
page.click("button[type='submit']")
page.wait_for_selector(".sidebar")   # inbox loaded

# 3. Compose
page.click("button[data-testid='sidebar:compose']")
page.fill("input[data-testid='composer:to']", recipient)
page.fill("input[data-testid='composer:subject']", subject)

# 4. Fill rich-text body (iframe-based editor)
frame = page.frame_locator("iframe[data-testid='rooster-iframe']")
frame.locator("div[aria-label='Email body']").fill(body_text)

# 5. Attach CV
page.set_input_files("input[type='file']", cv_path)
page.wait_for_selector(".attachment-card")

# 6. Send
page.click("button[data-testid='composer:send-button']")
page.wait_for_selector("div[data-testid='composer']", state='hidden')
```

---

## 13. Reusing this System for Any Job Search

This system is **general purpose**. To reuse it:

### Change the candidate profile
Edit `email_generator.py → _TEMPLATE` and update:
- Name, contact info in the signature
- Key credentials in the body
- Speciality hook paragraph

### Change the company list
Replace the XLSX file with any spreadsheet that has a company name column. The system adapts to the column names automatically.

### Change the language
The template is in French. To use English:
- Replace `_TEMPLATE_FR` in `email_generator.py` with an English version
- Update the AI prompt language in `_build_user_prompt`

### Change the email provider
The `email_sender.py` uses ProtonMail. To use Gmail, Outlook, or any SMTP provider:
- Add an SMTP sending function using Python's built-in `smtplib`
- Or use `yagmail` for Gmail with app passwords

```python
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# Gmail example (requires App Password, not main password)
with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
    server.login("you@gmail.com", "app_password_here")
    server.sendmail(from_addr, to_addr, msg.as_string())
```

### Add to Aeon Dashboard
The job automator is imported as a module inside Aeon Dashboard. To add another tool:
1. Create a new `YourToolPage(QWidget)` class in `aeon_dashboard.py`
2. Add it to `self._pages` and add a nav button for it.

---

*Built with Python, PyQt6, Playwright, DuckDuckGo, and optional AI APIs.*
*No data is sent to any server except the AI provider you choose.*
*All credentials stay on your machine in the local `.env` file.*
