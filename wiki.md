# Job Application Automator — Wiki & User Manual

> Version 2.1 | Updated: 2026-04-21 | Language: EN/FR

---

## Table of Contents

1. [What this does](#1-what-this-does)
2. [Quick Start (5 minutes)](#2-quick-start)
3. [File & Folder Structure](#3-file--folder-structure)
4. [Three-Script Workflow (CLI — recommended for bulk)](#4-three-script-workflow)
5. [GUI Tab-by-Tab Guide](#5-gui-tab-by-tab-guide)
6. [AI Providers — choosing one](#6-ai-providers)
7. [Sending without AI (Template Mode)](#7-sending-without-ai)
8. [Email & Attachment Guidelines](#8-email--attachment-guidelines)
9. [Company Spreadsheet Format](#9-company-spreadsheet-format)
10. [How company research works](#10-how-company-research-works)
11. [ProtonMail & Playwright — how it works](#11-protonmail--playwright)
12. [Bulk sending strategy & daily limits](#12-bulk-sending-strategy)
13. [Troubleshooting](#13-troubleshooting)
14. [How it was built — technical log](#14-how-it-was-built)
15. [Reusing for any job search](#15-reusing-for-any-job-search)
16. [Aeon Dashboard integration](#16-aeon-dashboard)

---

## 1. What this does

Reads your **CV** + a **company list** (Excel), then for each company:

1. Searches the web (DuckDuckGo — no API key) for the company's website
2. Also checks a local business directory if you provide one (e.g. reunion-directory.com)
3. Scrapes the site to find a **contact / HR email address**
4. Saves companies with **no email found** separately with follow-up recommendations
5. Generates a **personalised French email** (AI or high-quality template)
6. Logs into **ProtonMail** via browser automation (Playwright)
7. Sends the email with your **CV attached**
8. Logs every result — sent, skipped, failed — to a local JSON file

**Works 100% without AI** — template mode generates quality emails in French with zero external services.

---

## 2. Quick Start

```bash
# Install dependencies
pip install -r requirements.txt
playwright install chromium firefox

# Fill in .env with your credentials
cp .env.example .env   # edit with your ProtonMail login + optional AI key

# Run GUI
python main_app.py

# Or run Aeon Dashboard (includes job automator)
python ../aeon_dashboard/aeon_dashboard.py
```

---

## 3. File & Folder Structure

```
job_automator/
├── main_app.py           # GUI — all-in-one tabbed interface
├── bulk_sender.py        # Programmatic bulk sender (GUI backend + CLI)
│
├── search_companies.py   # SCRIPT 1: research companies → research_results.json
├── organise_emails.py    # SCRIPT 2: generate email drafts → email_queue.json
├── send_emails.py        # SCRIPT 3: send queue via ProtonMail → marks sent/failed
│
├── data_parser.py        # reads XLSX + PDF (shared library)
├── researcher.py         # web search + email extraction (shared library)
├── email_generator.py    # AI or template email generation (shared library)
├── email_sender.py       # ProtonMail Playwright automation (shared library)
│
├── requirements.txt
├── .env                  # credentials & settings — NEVER commit this
├── wiki.md               # this file
│
├── logs/
│   ├── automation.log    # GUI run log
│   ├── bulk_sender.log   # bulk_sender.py log
│   └── send_emails.log   # send_emails.py log
└── data/
    ├── metadata/
    │   └── runs.jsonl    # JSON record of every run
    └── attachments/      # optional extra files to attach
```

---

## 4. Three-Script Workflow

This is the **recommended approach for bulk campaigns** — faster, more transparent, and resumable.

### Step 1 — Research companies

```bash
python search_companies.py \
  --companies "path/to/companies.xlsx" \
  --max 50 \
  --out research_results.json \
  --directory "http://www.reunion-directory.com/annuaire-des-professions.html"
```

**What it does:**
- Reads XLSX, auto-detects company name column
- For each company: tries the local directory URL first, then DuckDuckGo
- Extracts emails from `/contact`, `/recrutement`, `/emploi`, `/carrieres` pages
- Saves results to `research_results.json`
- Companies with no email → saved in `"follow_up_needed"` key with recommendations

**Options:**
| Flag | Default | Meaning |
|------|---------|---------|
| `--companies` | required | Path to XLSX |
| `--max` | 20 | Max companies to process |
| `--out` | research_results.json | Output file |
| `--directory` | (none) | Business directory URL to try first |
| `--resume` | off | Skip companies already in the output file |

### Step 2 — Generate email drafts

```bash
python organise_emails.py \
  --research research_results.json \
  --cv "path/to/cv.pdf" \
  --letter "path/to/lettre_motivation.pdf" \
  --provider deepseek \
  --out email_queue.json
```

**What it does:**
- Reads `research_results.json`
- Extracts CV text (and optional motivation letter)
- Generates a personalised email for each company with a found email
- Saves all drafts to `email_queue.json` with status `"pending"`
- Companies with no email are listed separately in `"skipped_no_email"`

**Options:**
| Flag | Default | Meaning |
|------|---------|---------|
| `--research` | required | Output from Step 1 |
| `--cv` | required | CV PDF path |
| `--letter` | (none) | Motivation letter PDF (optional, improves AI quality) |
| `--provider` | auto | anthropic / mistral / deepseek / ollama / template |
| `--api-key` | from .env | Override API key |
| `--out` | email_queue.json | Output queue file |

### Step 3 — Send emails

```bash
# First: preview (no sending)
python send_emails.py \
  --queue email_queue.json \
  --cv "path/to/cv.pdf" \
  --dry-run

# Then: send for real
python send_emails.py \
  --queue email_queue.json \
  --cv "path/to/cv.pdf" \
  --max 20
```

**What it does:**
- Reads `email_queue.json`
- Logs into ProtonMail **once**
- Sends all `"pending"` emails in the same browser session
- Updates each entry to `"sent"` or `"failed"` in the queue file
- Logs everything to `logs/send_emails.log`

**Options:**
| Flag | Default | Meaning |
|------|---------|---------|
| `--queue` | required | JSON from Step 2 |
| `--cv` | required | CV PDF to attach |
| `--dry-run` | from .env | Preview only, no sending |
| `--max` | all | Limit how many to send this run |
| `--browser` | from .env | chromium or firefox |
| `--headless` | from .env | Run browser invisibly |

### Resume / re-run

The queue file tracks status per email. To resume after a failure or send the next batch:

```bash
# Only pending emails are sent — already-sent ones are skipped automatically
python send_emails.py --queue email_queue.json --cv cv.pdf --max 20
```

---

## 5. GUI Tab-by-Tab Guide

Launch with `python main_app.py`.

### ⚙ Configuration
| Field | Action |
|-------|--------|
| CV (PDF) | Click to select your CV |
| Liste entreprises (XLSX) | Click to select company list |
| Lettre motivation (PDF) | Optional — improves AI personalisation |
| Email / Mot de passe | Your ProtonMail login |
| Mémoriser dans .env | Saves credentials locally |
| Email de test | Sends one email to verify setup before bulk run |

### ▶ Lancement
- Click **Lancer** to start; progress bar fills per company
- Live log shows each research + send step in real time
- **Arrêter** stops cleanly after the current company

### 📧 Aperçu
Select any company from the dropdown to preview the exact subject and body generated. Use this in Dry Run mode before sending.

### 🔧 Paramètres
| Setting | Meaning |
|---------|---------|
| Navigateur | chromium (recommended) or firefox |
| Mode invisible | headless = browser hidden; off = you can watch |
| Dry run | Generate + log but do NOT send |
| Max entreprises | Companies to process per run |
| Fournisseur IA | Select AI provider or Template |
| Clé API | Paste your key here |
| Modèle Ollama | e.g. mistral, llama3, gemma3 |
| URL Ollama | Default: http://localhost:11434 |

### 📋 Historique
Each run's stats saved automatically. Shows timestamp, dry/live, sent/skipped/failed counts.

---

## 6. AI Providers

All providers fall back to **Template** automatically if they fail.

### Template (always works — no internet, no key)
```
Paramètres → Fournisseur IA → "template (sans IA)"
```
High-quality French email. Personalised with company name, city, and website content if found. **Recommended starting point.**

### Anthropic Claude Haiku
Best quality. Fast. ~$0.001 per email.
```bash
# 1. https://console.anthropic.com → API Keys → New key (sk-ant-…)
# 2. Paste in Paramètres → Clé API  OR  add to .env:
PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### Mistral AI
Good quality. EU-based. Cheaper than Claude.
```bash
pip install mistralai
# Key from: https://console.mistral.ai
PROVIDER=mistral
MISTRAL_API_KEY=your-key-here
```

### DeepSeek
Cheapest paid option. OpenAI-compatible.
```bash
pip install openai
# Key from: https://platform.deepseek.com
PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-your-key-here
```
Model: `deepseek-chat`

### Ollama (local — free forever)
Runs entirely on your computer. No account. No cost. Privacy-first.
```bash
# 1. Install: https://ollama.com
# 2. Pull a model:
ollama pull mistral        # good for French
ollama pull llama3         # alternative
ollama pull mistral-nemo   # best for French tasks
# 3. Set in .env:
PROVIDER=ollama
OLLAMA_MODEL=mistral
OLLAMA_URL=http://localhost:11434
```

**Auto-detection order (if PROVIDER not set):** Anthropic → Mistral → DeepSeek → Ollama → Template

---

## 7. Sending without AI

Template mode requires **nothing** — no account, no key, no internet for email generation.

The template:
1. Addresses "Madame, Monsieur" (appropriate for unsolicited French applications)
2. States CELTA certification + 18 years international experience upfront
3. Inserts a company-specific paragraph if website content was found
4. Closes with a clear call to action

**To adapt the template for a different candidate** — edit `email_generator.py → _TEMPLATE`:
```python
_TEMPLATE = """\
Madame, Monsieur,
Je me permets ...
Cordialement,
[Your Name]
"""
```

---

## 8. Email & Attachment Guidelines

### Subject line
```
Candidature Formateur d'Anglais CELTA – [Company Name]
```
Keep under 60 characters. No symbols. No ALL CAPS.

### Body rules
| Rule | Why |
|------|-----|
| French language | DOM-TOM companies expect French |
| Max 200 words | Hiring managers skim — be concise |
| Plain text only (no HTML) | Better deliverability, avoids spam filters |
| One clear call to action | "Disponible pour un entretien à votre convenance" |
| Professional tone — not overly formal | French DOM-TOM culture is warm but professional |

### Attachment rules
| Rule | Why |
|------|-----|
| CV must be **PDF** | Universal — works on all devices |
| Filename: `Prenom_Nom_CV_2026.pdf` | HR can file it correctly |
| Max **5 MB** total attachments | ProtonMail limit |
| Attach CV only (not motivation letter) | Letter goes in the email body |

### Spam avoidance
- Space sends 30–50 per day maximum
- Never send the same email twice to the same address
- The queue file tracks `"sent"` status — re-running skips already-sent
- Vary send times (not all at 9:00 AM)

---

## 9. Company Spreadsheet Format

### Required
At minimum one column with company names. Auto-detected column names:

| Column | Auto-detected as |
|--------|-----------------|
| `Raison sociale`, `NOM`, `Company`, `Entreprise`, `Société` | Company name |
| `Email`, `email`, `Mail`, `Courriel`, `E-mail` | Email (skips web search if present) |
| `Ville`, `City` | City (used in search + personalisation) |
| `CP` | Postal code |
| `C.A.` | Revenue |

### If the spreadsheet has no email column
The researcher automatically searches the web for each company. Companies where no email is found are saved to the `"follow_up_needed"` key in `research_results.json` with these alternatives:
- Manual search query (Google/DuckDuckGo)
- Direct link to local business directory
- Pages Jaunes link

### Adding emails manually
If you find an email manually, add an `Email` column to the XLSX. The system will use it directly and skip the web search for that row.

---

## 10. How Company Research Works

```
Company name
  → Check local directory URL (if provided)
  → DuckDuckGo: "[name] [city] recrutement contact email"
  → DuckDuckGo: "[name] [city] site officiel"
  → Visit top result (filter out LinkedIn, Facebook, societe.com etc.)
  → Try paths: /contact /recrutement /emploi /carrieres /rh /nous-contacter
  → Extract emails with regex
  → Rank: recrutement@ > rh@ > hr@ > contact@ > generic
  → If found: add to queue
  → If not found: save to follow_up_needed with recommendations
```

**Rate limiting:** 1–2 second pause between companies. Respects robots.

**Why DuckDuckGo?** Free, no API key, no rate limits for reasonable use, returns real results.

**Why not Google?** Google's search API costs money and requires account setup. DuckDuckGo HTML endpoint works without any credentials.

---

## 11. ProtonMail & Playwright — How it Works

Playwright controls a real browser (Chromium or Firefox) exactly like a human would.

### Login once, send many
```
Launch browser → Navigate to ProtonMail login →
Fill username + password → Click Sign In →
Wait for inbox selector → [LOGIN SESSION ACTIVE]

For each email in queue:
  Click "New Message" →
  Fill To: → Fill Subject: → Fill body (Rooster iframe editor) →
  Attach CV → Click Send → Wait for composer to close → next email
```

### Why this is better than SMTP for ProtonMail
- ProtonMail free accounts don't support SMTP without Bridge (desktop app)
- Bridge requires a paid plan
- Playwright works with any plan using your regular password

### Selector resilience
The sender tries **5+ CSS selector strategies** per UI element. If ProtonMail updates their UI, the system tries the next selector. This means the code survives minor redesigns without manual fixes.

### Troubleshooting a broken send
Run with `--headless` NOT set (or `HEADLESS=false`) — you'll see the browser and can watch where it gets stuck.

---

## 12. Bulk Sending Strategy

### Recommended batch sizes
| Situation | Batch size | Frequency |
|-----------|-----------|-----------|
| First test | 1 (dry run first) | Once |
| First live send | 5 | Once |
| Daily production | 30–50 | Daily |
| Full 500 campaign | 50/day | 10 days |

### Running batches

```bash
# Day 1: first 50
python search_companies.py --companies companies.xlsx --max 50 --out research_batch1.json
python organise_emails.py --research research_batch1.json --cv cv.pdf --out queue_batch1.json
python send_emails.py --queue queue_batch1.json --cv cv.pdf --max 50

# Day 2: next 50 (use --resume to avoid re-researching)
python search_companies.py --companies companies.xlsx --max 100 --out research_batch2.json --resume
# ... etc
```

### The queue file is your audit trail
Every email in `email_queue.json` has:
```json
{
  "company": "ROYAL BOURBON INDUSTRIES",
  "recipient": "rbi@royalbourbon.com",
  "subject": "Candidature Formateur d'Anglais CELTA – Royal Bourbon Industries",
  "body": "Madame, Monsieur, ...",
  "status": "sent",
  "sent_at": "2026-04-21T23:13:39"
}
```

---

## 13. Troubleshooting

### "Cannot locate username field"
ProtonMail may have updated their login page. Run headed (`HEADLESS=false`) to watch. Check selectors in `email_sender.py → _LOGIN_USERNAME`.

### "Cannot fill email body"
The Rooster editor uses iframes. Run headed to inspect. Add new selector to `email_sender.py → iframe_strategies`.

### Login timeout
Usually a slow internet connection. The code already waits for the username field to appear instead of `networkidle` (ProtonMail keeps background requests open forever). If still timing out, increase the timeout values in `email_sender.py`.

### "No results for [Company]"
DuckDuckGo returned no results for that query. Try:
1. Add email manually to the XLSX
2. Provide `--directory` flag with a local business directory URL
3. Check the company name — sometimes very long names match poorly

### "AI error, falling back to template"
- Check API key has credits
- Check `PROVIDER=` is set correctly in `.env`
- Template will be used as fallback — emails still get generated and sent

### Check logs
```bash
tail -f logs/automation.log        # GUI runs
tail -f logs/bulk_sender.log       # bulk_sender.py
tail -f logs/send_emails.log       # send_emails.py
cat data/metadata/runs.jsonl       # JSON run history
```

---

## 14. How it was Built — Technical Log

### Language & Libraries

| Component | Technology | Why chosen |
|-----------|-----------|-----------|
| GUI | Python + PyQt6 | Cross-platform, accessible, no web server needed |
| Browser automation | Playwright (sync) | Most reliable for modern SPAs like ProtonMail |
| Web search | DuckDuckGo HTML | Free, no API key, usable by anyone |
| Local directory | requests + BeautifulSoup | Flexible scraping of any HTML page |
| CV parsing | PyPDF2 | Simple, reliable for text-layer PDFs |
| Company data | pandas + openpyxl | Industry standard for Excel |
| AI (Claude) | anthropic SDK (claude-haiku-4-5) | Best quality, Anthropic's fastest/cheapest model |
| AI (Mistral) | mistralai SDK | EU-based, good French language quality |
| AI (DeepSeek) | openai SDK (compatible) | Cheapest paid, OpenAI-compatible API |
| AI (Ollama) | HTTP (requests) | 100% local, free, privacy-preserving |
| Config | python-dotenv | Simple, portable .env pattern |
| Accessible UI | PyQt6 | Same framework, custom stylesheet |

### Architecture decisions

1. **Three separate scripts** — search / organise / send — means each step is inspectable, resumable, and replaceable independently.
2. **AI is always optional** — template fallback means the system works with zero external dependencies beyond Playwright.
3. **Login-once session** — `send_emails.py` and `bulk_sender.py` log into ProtonMail once and send all emails in that session. 10× faster than per-email login.
4. **Column auto-detection** — handles `Raison sociale`, `NOM`, `Company` etc. Works with most French/English spreadsheets.
5. **Multi-selector resilience** — 5+ CSS strategies per ProtonMail UI element. Survives minor redesigns.
6. **Queue file as audit trail** — `email_queue.json` tracks `"pending"` / `"sent"` / `"failed"` per email. Re-running skips already-sent.
7. **Follow-up saving** — companies with no email found are not silently dropped; they go into `"follow_up_needed"` with actionable recommendations.

### Playwright send flow (annotated)

```python
# Login — wait for field, not networkidle (ProtonMail has permanent background requests)
page.goto("https://mail.proton.me/login")
page.wait_for_selector("#username", timeout=25000)
page.fill("#username", user)
page.fill("#password", pw)
page.click("button[type='submit']")
page.wait_for_selector(".sidebar", timeout=60000)  # inbox ready

# Compose
page.click("button[data-testid='sidebar:compose']")
page.fill("input[data-testid='composer:to']", recipient)
page.fill("input[data-testid='composer:subject']", subject)

# Body — Rooster rich-text editor is inside an iframe
frame = page.frame_locator("iframe[data-testid='rooster-iframe']")
frame.locator("div[aria-label='Email body']").fill(body_text)

# Attach
page.set_input_files("input[type='file']", cv_path)
page.wait_for_selector(".attachment-card")  # upload confirmed

# Send
page.click("button[data-testid='composer:send-button']")
page.wait_for_selector("div[data-testid='composer']", state="hidden")
```

---

## 15. Reusing for Any Job Search

### Change the candidate
Edit `email_generator.py → _TEMPLATE`:
- Update name, phone, email, location in the signature
- Update key credentials in the body
- Update the speciality hook paragraph

### Change the company list
Any XLSX with a company name column works. The system auto-detects column names. Add an `Email` column to skip web research for companies where you already know the address.

### Change the language
The template is in French. For English:
```python
# In email_generator.py, replace _TEMPLATE with English text
_TEMPLATE = """\
Dear Hiring Manager,
I am writing to express my interest in ...
"""
# Also update _SYSTEM prompt in _build_user_prompt() to request English output
```

### Change the email provider
Replace `email_sender.py` with an SMTP-based sender for any provider:

```python
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# Gmail (needs App Password from myaccount.google.com/apppasswords)
with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
    server.login("you@gmail.com", "app_password")
    server.sendmail(from_addr, to_addr, msg.as_string())

# Outlook / Hotmail
with smtplib.SMTP("smtp.live.com", 587) as server:
    server.starttls()
    server.login("you@hotmail.com", "password")
    server.sendmail(...)

# ProtonMail Bridge (paid plan + Bridge app running)
with smtplib.SMTP("127.0.0.1", 1025) as server:
    server.login("you@proton.me", "bridge_password")
    server.sendmail(...)
```

---

## 16. Aeon Dashboard

The Aeon Dashboard (`../aeon_dashboard/aeon_dashboard.py`) is an accessible hub that wraps the job automator with a calm, inclusive interface.

### Design principles
- **Autism-friendly:** predictable layout, no sudden UI changes, clear labels, every destructive action confirmed, muted green palette
- **Alzheimer-friendly:** large text (14–28px), clock always visible, "What am I doing here?" button on every page, persistent reminders, one task visible at a time
- **Universal:** works for any user — the job automator is just one module inside a broader personal assistant

### Pages
| Page | What it does |
|------|-------------|
| 🏠 Accueil | Clock, date, today's reminders, quick-action buttons |
| 📧 Candidatures | Full job automator embedded as a tab |
| ⏰ Rappels | Add/delete reminders with dates; overdue reminders shown in red |
| 📝 Notes | Free-text notepad with manual save |
| ❓ Aide | Full help guide; also accessible via "Qu'est-ce que je fais ici?" button |

### Adding new modules
```python
# In aeon_dashboard.py, create a new page class:
class MyNewToolPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # ... build your UI

# Add to self._pages list and add nav button:
self._pages.append(MyNewToolPage())
nav_items.append(("🔧  Mon outil", 5))
```

### Running
```bash
python aeon_dashboard/aeon_dashboard.py
```
The job automator is embedded. If it can't load (import error), a "Launch in separate window" button appears instead.

---

*All credentials stay on your machine in `.env`. Nothing is sent to any server except the AI provider you choose and ProtonMail (your own account).*

*Built with Python · PyQt6 · Playwright · DuckDuckGo · DeepSeek / Anthropic / Mistral / Ollama*
