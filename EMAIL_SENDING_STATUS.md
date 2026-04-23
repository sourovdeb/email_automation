# Email Sending Status - April 23, 2026

## 1) Current verified status

- Total prepared emails: 100
- First full send attempt (1-50): failed due to attachment wait logic in older sender flow
- Second-batch rerun (51-100 file): partially processed
  - completed: 18
  - success: 17
  - failed: 1
  - run completion marker: missing (`RUN_COMPLETED` not present)
- Direct report/document deliveries to sourovdeb.is@gmail.com: successful

## 2) Verified delivery runs to sourovdeb.is@gmail.com

1. run_20260423_074132_send
   - sent_count: 1
   - failed_count: 0

2. run_20260423_090729_send
   - subject: Detailed Automation Framework Report (Part 1)
   - sent_count: 1
   - failed_count: 0

3. run_20260423_090749_send
   - subject: Scratch-to-End Automation Guideline (Part 2)
   - sent_count: 1
   - failed_count: 0

## 3) Tools actually used in successful sends

Primary send stack:

- Python runner: files(5)/send_prepared_emails.py
- Node sender: files(5)/sender/protonmail_sender.js
- Browser automation engine: Playwright with Chromium

Operational flow:

1. Parse prepared email blocks from text file.
2. Build JSON payload (to, subject, body, attachment path, action).
3. Launch Node sender process for each email.
4. Open ProtonMail web, compose, attach file, send.
5. Persist run evidence under logs/batch_runs/run_<timestamp>_send/.

## 4) Regex used in parsing and verification

Saved in:

- REGEX_REFERENCE_2026-04-23.md

Core parser patterns from send_prepared_emails.py include:

- === EMAIL \d+/\d+ ===
- Company: (.+?) ===
- Recipient: (.+)
- Subject: (.+)
- Subject: .+?\n\n(.+?)(?:\n\n\n=== EMAIL|\Z)

## 5) Notes on remaining campaign state

- For emails_for_manual_sending_51-100.txt, indexes 49 and 50 (global emails 99 and 100) do not appear in the partial rerun event log.
- This means emails 99 and 100 were prepared but not reached in that specific interrupted run.

## 6) Where evidence is stored

- logs/batch_runs/run_20260422_205846_send/
- logs/batch_runs/run_20260422_221409_send/
- logs/batch_runs/run_20260423_074132_send/
- logs/batch_runs/run_20260423_090729_send/
- logs/batch_runs/run_20260423_090749_send/

## 7) Related summary documents

- AUTOMATION_FRAMEWORK_DETAILED_REPORT_2026-04-23.md
- AUTOMATION_GUIDELINE_SCRATCH_TO_END_2026-04-23.md
- INFORMATION_COLLECTION_AND_SENDING_TOOLS_2026-04-23.md
