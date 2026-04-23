# Automation Framework Detailed Report (2026-04-23)

## 1) Scope and objective

This report documents the full framework used in this workspace to:

1. scrape/search job opportunities and company contacts,
2. generate personalized application emails,
3. save generated outputs to local files,
4. send emails through ProtonMail automation,
5. log evidence and troubleshoot failures.

It also includes:

- an explicit process breakdown for email 99 and email 100,
- obstacles/errors encountered,
- what caused them,
- how they were mitigated or solved.

---

## 2) What was done for job scraping and search

## 2.1 Inputs required

The search layer needs:

- target job titles,
- target locations,
- optional keywords,
- candidate profile context,
- a source list of companies (for batch campaigns).

Primary search configuration was maintained in:

- `files(5)/config.json`

Key configured values included:

- `search.job_titles`
- `search.locations`
- `search.keywords_extra`
- `search.job_boards`

## 2.2 Tools, languages, and scripts used

### Language/runtime

- Python 3

### Core scripts

- `files(5)/job_scraper_free_apis.py`
  - Free API aggregation layer
  - Sources implemented:
    - Arbeitnow (`https://api.arbeitnow.com/api/v2/job_search`)
    - Findwork (`https://findwork.dev/api/v1/jobs/`) when API key is configured
    - Jooble (`https://jooble.org/api/<key>`) when API key is configured
    - GraphQL Jobs (`https://graphql.jobs/api`)
  - Uses `requests`, `asyncio`, `hashlib`, `sqlite3` (optional save path)

- `files(5)/main.py`
  - End-to-end orchestrator for scrape -> personalize -> send
  - Imports:
    - `modules/job_scraper`
    - `modules/document_reader`
    - `modules/ai_personalizer`
    - `modules/database`
    - `modules/learner`

### Supporting search/research evolution

- `CHANGES.md` records upgrades to `researcher.py`:
  - French directory-first strategy (Pages Jaunes, Kompass, Societe.com)
  - DuckDuckGo fallback handling
  - Google fallback attempt
  - email pattern guessing fallback

## 2.3 Information extracted/produced

From scraping and company research, the framework aimed to build records containing:

- company name,
- job title,
- location,
- URL/job URL,
- description/snippet,
- source,
- potential contact email.

These were designed to be persisted in SQLite (`jobs.db`) and used by downstream personalization and sending.

---

## 3) What was done to write personalized emails and save outputs

## 3.1 Inputs for personalization

Personalization combined:

- candidate documents (CV, cover letter, advice docs),
- job/company context,
- configured profile and language preferences,
- AI backend selection.

### Document ingestion script

- `files(5)/document_reader.py`
  - Reads PDF/DOCX/TXT/MD/RST
  - PDF extraction stack:
    - `pdftotext` (poppler-utils) first
    - PyMuPDF fallback (`fitz`)
    - `pdfplumber` fallback
  - Classifies documents into:
    - `cv`
    - `cover_letter`
    - `advice`

## 3.2 AI engines and routing

### Router

- `files(5)/modules/ai_router.py`
  - routes by `config["ai_backend"]`
  - cloud path -> `ai_personalizer.py`
  - local path -> `local_lm.py`

### Cloud personalization

- `files(5)/modules/ai_personalizer.py`
  - personalized subject/body generation
  - JSON-structured output expected
  - fallback template when parse/API fails

### Local personalization

- `files(5)/modules/local_lm.py`
  - Ollama integration (`/api/generate`)
  - model configurable (mistral/llama/gemma/qwen family)
  - fallback template if model or parsing fails

## 3.3 Output files and storage format

For the two 50-email campaign groups, outputs were saved in local text files:

- `generated_emails.txt`
- `emails_for_manual_sending.txt`
- `generated_emails_51-100.txt`
- `emails_for_manual_sending_51-100.txt`

`COMPLETE_ACTION_LOG.md` records this generation milestone and output files.

The manual sending files use segmented blocks (`=== EMAIL x/y ===`) with:

- company,
- recipient,
- subject,
- body.

---

## 4) What was done to send emails (tools/scripts/languages/how)

## 4.1 Runtime stack

### Languages

- Python (batch orchestrator)
- JavaScript/Node.js (browser sender)

### Sending scripts

- `files(5)/send_prepared_emails.py`
  - Reads prepared email file blocks
  - Supports selecting input file via `EMAILS_FILE`
  - Supports action normalization (`send`/`draft`) via `EMAIL_ACTION`
  - Calls Node sender for each email
  - Creates durable run artifacts:
    - `events.jsonl`
    - `summary.json`
    - `report.md`

- `files(5)/sender/protonmail_sender.js`
  - Playwright automation for ProtonMail web UI
  - Compose flow: To -> Subject -> Body -> attachments -> send/draft
  - snapshot function: `saveHtmlSnapshot(...)`
  - attachment stabilization:
    - `getComposerAttachmentCount(...)`
    - `waitForComposerAttachmentCount(...)`

## 4.2 How each email is processed

For each prepared entry:

1. Parse company/recipient/subject/body from text file.
2. Build sender payload with `to`, `subject`, `body`, attachment path(s), action.
3. Launch Node sender for this payload.
4. Wait for Proton inbox readiness.
5. Compose and fill content.
6. Attach CV (and optional second attachment if provided by payload).
7. Send (or save draft if action is `draft`).
8. Log per-email result in JSONL + aggregate summary/report.

## 4.3 Evidence-first run logging

Durable run directories:

- `logs/batch_runs/run_20260422_205846_send/`
- `logs/batch_runs/run_20260422_221409_send/`
- `logs/batch_runs/run_20260423_074132_send/`

Each directory captures machine-verifiable process state and outcomes.

---

## 5) Example breakdown: email 99 and email 100

## 5.1 Source records (prepared campaign file)

From `emails_for_manual_sending_51-100.txt`:

- Email 99/100
  - Company: `UBIPHARM GUYANE`
  - Recipient: `recrutement@ubipharmguyane.fr`
  - Subject: `Candidature Formateur d'Anglais CELTA – UBIPHARM GUYANE`
  - Body personalization highlights:
    - opening names `UBIPHARM GUYANE` directly in first paragraph,
    - localized context line references `CAYENNE`,
    - same applicant profile block (CELTA 2026, IELTS/TOEIC, 18 years, Anglo environments).

- Email 100/100
  - Company: `BRASSERIE LORRAINE`
  - Recipient: `recrutement@brasserielorraine.fr`
  - Subject: `Candidature Formateur d'Anglais CELTA – BRASSERIE LORRAINE`
  - Body personalization highlights:
    - opening names `BRASSERIE LORRAINE` directly in first paragraph,
    - localized context line references `LE LAMENTIN`,
    - same applicant profile block (CELTA 2026, IELTS/TOEIC, 18 years, Anglo environments).

## 5.2 Technical process path for these two emails

If the 51-100 file is executed fully, each of these two entries follows:

1. `send_prepared_emails.py` parses the block.
2. It constructs per-email payload + artifact prefix.
3. `protonmail_sender.js` opens Proton and fills compose fields.
4. Attachment count check confirms file upload.
5. Action branch:
   - `send` -> click send and wait for sent confirmation.
   - `draft` -> close composer and save draft.
6. Result is appended to `events.jsonl` and included in `summary.json`/`report.md`.

## 5.3 Actual observed status in this workspace (as of this report)

The second-batch run in:

- `logs/batch_runs/run_20260422_221409_send/events.jsonl`

contains:

- 18 completed email events,
- 17 success,
- 1 failure,
- no `RUN_COMPLETED` event.

There are no events for batch indexes 49 and 50 in this run log, which means global emails 99 and 100 were not reached in that run.

Mapping note:

- In `emails_for_manual_sending_51-100.txt`,
  - global email 99 corresponds to batch index 49,
  - global email 100 corresponds to batch index 50.

---

## 6) Obstacles, difficulties, and error handling

## 6.1 Problem: first 50-email send run fully failed

### What

Run `run_20260422_205846_send` ended with:

- `sent_count: 0`
- `failed_count: 50`

### Why

Primary error in summary:

- timeout waiting for attachment thumbnail visibility (`attachment-thumbnail`).

### How it was solved

Sender logic was updated to attachment-count-based verification:

- `getComposerAttachmentCount(...)`
- `waitForComposerAttachmentCount(...)`

This removed reliance on thumbnail visibility and improved robustness.

---

## 6.2 Problem: intermittent long stall in second batch rerun

### What

In `run_20260422_221409_send/events.jsonl`, index 14 failed with:

- `Timed out waiting for attachment count 1`
- very long duration (`32327.34` seconds)

### Why

Likely UI/session or upload-state stall in Proton web automation path.

### How it was handled

- failure was recorded with full stderr/snapshot evidence,
- run continued for later entries,
- event logging preserved exact point-of-failure.

---

## 6.3 Problem: run stopped before completing all 50 entries in second file

### What

Second-batch run processed only up to index 18 and ended without final `RUN_COMPLETED` event.

### Why

Execution did not continue to file end (manual stop, environment interruption, or process termination).

### How it was handled

- forensic status derived from `events.jsonl` instead of assumptions,
- unsent tail segment (including 99/100) identified explicitly.

---

## 6.4 Problem: search reliability varied by source

### What

Historical notes in `CHANGES.md` mention connectivity and scraping reliability issues (DuckDuckGo and search variability).

### Why

External providers can rate-limit, timeout, or change output structures.

### How it was solved/mitigated

- introduced multi-strategy company research:
  - French directories first,
  - search fallback,
  - email guessing fallback.

---

## 7) Current factual status snapshot

As of this report:

1. First 50 run (`run_20260422_205846_send`):
   - 50 processed,
   - 0 sent,
   - 50 failed.

2. Second-file rerun (`run_20260422_221409_send`):
   - 18 processed,
   - 17 sent,
   - 1 failed,
   - not fully completed.

3. Report delivery confirmation run (`run_20260423_074132_send`):
   - 1 processed,
   - 1 sent to `sourovdeb.is@gmail.com`,
   - 0 failed,
   - externally confirmed received in Gmail.

---

## 8) Deliverables created by this documentation task

This report was produced as one of two requested local Markdown deliverables:

1. `AUTOMATION_FRAMEWORK_DETAILED_REPORT_2026-04-23.md` (this file)
2. `AUTOMATION_GUIDELINE_SCRATCH_TO_END_2026-04-23.md` (operational guide)

Both are intended to be committed and pushed in repository `sourovdeb/email_automation` (`main` branch), then sent by email for archival.
