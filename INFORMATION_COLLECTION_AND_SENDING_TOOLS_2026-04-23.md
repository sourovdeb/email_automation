# Information Collection And Sending Tools (2026-04-23)

This file records what was kept, what was removed, and which tools were used to send emails (including sends to sourovdeb.is@gmail.com).

## 1) Kept files used to collect and preserve information

Core evidence and process docs:
- AUTOMATION_FRAMEWORK_DETAILED_REPORT_2026-04-23.md
- AUTOMATION_GUIDELINE_SCRATCH_TO_END_2026-04-23.md
- COMPLETE_ACTION_LOG.md
- HISTORY_UP_TO_FIRST_25.md
- ISSUES_AND_RECOMMENDATIONS.md
- wiki.md

Primary run evidence folders:
- logs/batch_runs/run_20260422_205846_send/
- logs/batch_runs/run_20260422_221409_send/
- logs/batch_runs/run_20260423_074132_send/
- logs/batch_runs/run_20260423_090729_send/
- logs/batch_runs/run_20260423_090749_send/

Collection and orchestration scripts retained:
- files(5)/job_scraper_free_apis.py
- files(5)/main.py
- files(5)/document_reader.py
- files(5)/modules/ai_router.py
- files(5)/modules/ai_personalizer.py
- files(5)/modules/local_lm.py
- files(5)/send_prepared_emails.py
- files(5)/sender/protonmail_sender.js

## 2) Tools used to send emails (including sourovdeb.is@gmail.com)

Execution stack:
- Python batch runner: files(5)/send_prepared_emails.py
- Node sender: files(5)/sender/protonmail_sender.js
- Browser automation library: Playwright (Chromium)

Configuration used in successful delivery runs:
- EMAIL_ACTION=send
- EMAILS_FILE=doc_delivery_email_part1.txt and doc_delivery_email_part2.txt
- CV_PATH set to target attached markdown file path

Verified delivery runs to sourovdeb.is@gmail.com:
- run_20260423_074132_send (framework report delivery)
- run_20260423_090729_send (detailed report delivery)
- run_20260423_090749_send (scratch-to-end guideline delivery)

## 3) Cleanup done for accumulated temporary files

Removed temporary delivery and legacy helper files:
- doc_delivery_email_part1.txt
- doc_delivery_email_part2.txt
- report_delivery_email.txt
- proton_webview_sender.py
- send_emails_playwright.py
- send_emails_selenium.py
- send_from_session.py
- send_proton_selenium.py

Reason for cleanup:
- They were one-off helper artifacts not required for ongoing collection/sending pipeline.
- Durable evidence is preserved in markdown reports and logs/batch_runs run artifacts.
