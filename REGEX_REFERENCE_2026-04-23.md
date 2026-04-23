# Regex Reference Used In This Workflow (2026-04-23)

This file saves the exact regex patterns used to parse prepared emails and verify run logs.

## 1) Parsing prepared email blocks

Source implementation:
- files(5)/send_prepared_emails.py

Patterns:
- Split email sections:
  - `=== EMAIL \d+/\d+ ===`
- Extract company line:
  - `Company: (.+?) ===`
- Extract recipient line:
  - `Recipient: (.+)`
- Extract subject line:
  - `Subject: (.+)`
- Extract body block:
  - `Subject: .+?\n\n(.+?)(?:\n\n\n=== EMAIL|\Z)`

## 2) Run-log verification patterns

Patterns used during evidence checks on events.jsonl:
- Completed events:
  - `"event": "EMAIL_COMPLETED"`
- Successful completion events:
  - `"event": "EMAIL_COMPLETED".*"success": true`
- Failed completion events:
  - `"event": "EMAIL_COMPLETED".*"success": false`
- Run completion marker:
  - `"event": "RUN_COMPLETED"`
- Check whether global email 99/100 were reached in 51-100 run:
  - `"index": 49|"index": 50`

## 3) Why these matter

- The parsing regex powers conversion from manual text blocks into sender payloads.
- The verification regex gives auditable counts for sent/failed/incomplete runs.
- Together they provide deterministic traceability from prepared content to run outcomes.
