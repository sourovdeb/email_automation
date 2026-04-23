# Job Automation Guideline: From Scratch to End (2026-04-23)

This is a practical, reproducible runbook for building and operating the full workflow in this workspace:

- search jobs and company contacts,
- generate personalized emails,
- send through Proton web automation,
- verify and report outcomes.

---

## 0) Prerequisites

## 0.1 System tools

Install required system packages (Linux):

```bash
sudo apt update
sudo apt install -y python3 python3-pip nodejs npm poppler-utils
```

`poppler-utils` provides `pdftotext`, used by document extraction.

## 0.2 Workspace and repository

Work in repository:

- `job_automator`

If needed:

```bash
git clone https://github.com/sourovdeb/email_automation.git
cd email_automation
```

## 0.3 Python dependencies

If using a dedicated environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 0.4 Node dependencies for sender

Inside `files(5)`:

```bash
cd files\(5\)
npm install
```

(Use shell escaping for parentheses as shown.)

---

## 1) Prepare configuration and input assets

## 1.1 Core config

Edit:

- `files(5)/config.json`

Set at minimum:

- AI backend (`ai_backend`)
- job titles and locations (`search.job_titles`, `search.locations`)
- Proton sender address (`protonmail_email`)
- sending behavior (`sending.max_per_run`, delays, dry-run)

## 1.2 Candidate documents

Place candidate files in:

- `documents/` (or configured `documents_folder`)

Recommended files:

- CV (PDF or DOCX)
- optional cover letter
- optional advice/strategy text

Document parsing is handled by `files(5)/document_reader.py`.

## 1.3 Company source data (batch campaigns)

For a campaign like 100 companies:

- keep company list in source sheet or generated text,
- ensure one recipient email per entry (researched or guessed where needed).

---

## 2) Run job search/scraping layer

## 2.1 Free API scraper route

From `files(5)`:

```bash
python3 job_scraper_free_apis.py
```

Optional DB save:

```bash
python3 job_scraper_free_apis.py --save-to data/jobs.db
```

This script queries:

- Arbeitnow,
- Findwork (if API key configured),
- Jooble (if API key configured),
- GraphQL Jobs.

## 2.2 Full orchestrator route

```bash
python3 main.py --scrape-only
```

This uses configured boards and persists jobs for later application/send phases.

---

## 3) Generate personalized emails

## 3.1 AI processing path

Personalization flow:

1. Read and classify documents (`document_reader.py`).
2. Select backend via `modules/ai_router.py`.
3. Generate email subject/body via:
   - cloud: `modules/ai_personalizer.py`
   - local Ollama: `modules/local_lm.py`
4. Apply fallback templates if AI/provider output is invalid.

## 3.2 Save generated results

For large campaigns, save into auditable files such as:

- `generated_emails.txt`
- `emails_for_manual_sending.txt`
- `generated_emails_51-100.txt`
- `emails_for_manual_sending_51-100.txt`

Use block structure:

- `=== EMAIL x/y ===`
- `Company:`
- `Recipient:`
- `Subject:`
- `Body:`

This is the format expected by `send_prepared_emails.py`.

---

## 4) Execute sending phase

## 4.1 Send mode vs draft mode

`send_prepared_emails.py` supports both:

- `send` (actual send)
- `draft` (save draft only)

Set environment before run:

```bash
export EMAILS_FILE="../emails_for_manual_sending_51-100.txt"
export EMAIL_ACTION="send"
python3 send_prepared_emails.py
```

Run from `files(5)` folder so relative defaults stay consistent.

## 4.2 Sender internals

`sender/protonmail_sender.js` (Node + Playwright) performs:

1. open Proton web app,
2. wait for inbox-ready selector,
3. open compose,
4. fill recipient/subject/body,
5. upload CV,
6. verify attachment count,
7. send or save draft,
8. emit structured JSON success/failure.

---

## 5) Logging, evidence, and verification

Each batch run creates a folder:

- `logs/batch_runs/run_<timestamp>_<action>/`

Key artifacts:

- `events.jsonl` (per-event truth source)
- `summary.json` (totals)
- `report.md` (human-readable summary)

Verification checklist:

1. confirm `RUN_STARTED` and `EMAIL_COMPLETED` events,
2. compare completed count vs expected input count,
3. verify `RUN_COMPLETED` exists,
4. inspect failures by `error` field,
5. confirm at least one external mailbox receipt for end-to-end proof.

---

## 6) Handling failures and retries

## 6.1 Known issue pattern

Historical common failure:

- waiting for attachment thumbnail visibility.

Mitigation in current sender:

- attachment-count-based waiting (`waitForComposerAttachmentCount`).

## 6.2 If run is interrupted mid-batch

1. read `events.jsonl` and identify last completed index,
2. compute remaining entries,
3. resume by creating a remainder input file, or rerun with controlled slicing,
4. avoid duplicate sends by checking sent recipients in logs.

## 6.3 If Proton web flow becomes unstable

1. reduce throughput (one email per browser session if needed),
2. keep snapshots enabled,
3. review stderr and HTML snapshots in run folders,
4. retest with a pilot recipient before bulk continuation.

---

## 7) Worked example for final two entries (99 and 100)

From `emails_for_manual_sending_51-100.txt`:

- Email 99 -> `recrutement@ubipharmguyane.fr`
- Email 100 -> `recrutement@brasserielorraine.fr`

During the observed rerun (`run_20260422_221409_send`), processing stopped at index 18, so these two were not reached.

If continuing safely:

1. extract remaining unsent block(s),
2. run in `send` mode,
3. verify entries 49 and 50 in `events.jsonl`,
4. confirm mailbox-level delivery evidence.

---

## 8) End-of-run reporting and archival

After each campaign:

1. summarize totals (processed/sent/failed/pending),
2. include key failure signatures and fixes,
3. keep run folder IDs in the report,
4. commit markdown reports and runbook updates,
5. push to GitHub,
6. email report(s) to archival mailbox.

Suggested report files:

- campaign technical report,
- scratch-to-end runbook (this file),
- status snapshot for sent/failed/pending indexes.

---

## 9) Minimal command sequence (quick start)

```bash
# 1) go to repo
cd /home/sourov/Documents/employment/job_automator/files\(5\)

# 2) scrape only (optional)
python3 main.py --scrape-only

# 3) send prepared batch
export EMAILS_FILE="../emails_for_manual_sending_51-100.txt"
export EMAIL_ACTION="send"
python3 send_prepared_emails.py

# 4) inspect latest run folder
cd ..
ls -1 logs/batch_runs | tail -n 5
```

This gives a complete path from setup to verifiable output.
