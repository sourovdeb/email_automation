# Email Automation (Accessible GUI)

This project automates personalized job outreach emails with:
1. Python orchestration
2. Playwright + Chromium/Firefox for web automation
3. Open-source search workflow for company profiling
4. Proton Mail primary send path
5. Thunderbird fallback path (compose automation)

The GUI is accessibility-focused (large controls, high contrast, clear flow) for autistic, elderly, and handicapped users.

## What The User Must Provide

1. CV file:
   - Type: PDF
   - Example: `cv.pdf`
2. Company list file:
   - Type: XLSX
   - Must include at least one company name column (for example `NOM`)
   - Should include an email/contact column when available
3. Login options:
   - Proton email username
   - Proton password
   - Browser choice (`chromium` or `firefox`)
   - Run mode (`headless` true/false)
   - Safety mode (`dry_run` true/false)
   - Max companies per run

## Required Local Files And Folders

The app creates and uses these paths under the project root:

1. `.env`
   - Stores credentials and runtime options
2. `logs/automation.log`
   - Detailed timestamped runtime log
3. `data/metadata/runs.jsonl`
   - One JSON record per execution (local learning history)
4. `data/attachments/`
   - Optional folder for additional attachments

## .env Format

Use this format in `.env`:

```env
PROTON_USER=your_user@proton.me
PROTON_PASS=your_password
BROWSER=chromium
HEADLESS=false
DRY_RUN=true
MAX_COMPANIES=5
```

## Setup

1. Create and activate virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install Python dependencies and Playwright browsers:

```bash
pip install -r requirements.txt
playwright install chromium firefox
```

3. Run app:

```bash
python main_app.py
```

## Usage Flow

1. Select CV (PDF).
2. Select company list (XLSX).
3. Confirm or edit login options.
4. Save login options to `.env` (button or checkbox auto-save).
5. Run `Send Test Email` first.
6. Run `Start Automation`.

## Graceful Fallback Hierarchy

At each send attempt, use this order:

1. Primary: Proton Mail via Playwright
2. Fallback A: Switch browser (Chromium <-> Firefox)
3. Fallback B: Headed mode (disable headless)
4. Fallback C: Thunderbird compose automation (manual final review/send)
5. Fallback D: Dry-run export/log only (no send)

## Thunderbird Automation (Fallback)

If Proton UI selectors fail or login flow changes, compose via Thunderbird:

```bash
thunderbird -compose "to=recipient@example.com,subject='Job inquiry',body='Hello ...',attachment='file:///absolute/path/to/cv.pdf'"
```

Notes:
1. Use absolute file paths for attachments.
2. Keep final review manual before clicking Send.
3. This fallback protects continuity when web UI changes.

## Local Metadata Learning

Each run appends metadata to `data/metadata/runs.jsonl`.
Saved fields include:
1. Timestamp
2. Browser used
3. Run settings (headless/dry-run/max)
4. Per-company outcome
5. Summary stats (sent ok/failed/skipped)

Adaptive behavior:
1. On startup, the app checks previous run success by browser.
2. It preselects the browser with the best historical send success rate.
3. This improves reliability over repeated use.

## Detailed Logging

The app logs to:
1. GUI log panel (live feedback)
2. `logs/automation.log` (persistent log with timestamps)

Typical entries:
1. File selection
2. Run configuration
3. Per-company processing status
4. Send success/failure
5. Metadata save status

Security:
1. Do not log raw passwords.
2. Keep `.env` local.
3. Never commit `.env`.

## AI Role vs Python Role

Python + Playwright role:
1. Daily execution
2. Deterministic automation
3. Logging and metadata history
4. Reliability tuning via local run outcomes

AI role:
1. Architect and engineer when requested
2. Design or update workflows/templates
3. Debug broken selectors or edge cases
4. Improve system strategy on demand

This keeps normal operation reusable without AI, while AI remains optional for upgrades.

## Repository

https://github.com/sourovdeb/email_automation
