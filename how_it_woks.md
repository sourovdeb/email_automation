# how_it_woks

Date: 2026-04-21

## Objective
Execute the project safely, validate dry-test readiness, document how it works, and push updates to GitHub.

## Tooling Used
- Python (venv)
- Playwright (Chromium/Firefox)
- Open web search for company context
- Proton Mail automation (primary)
- Thunderbird compose fallback (documented)

## What Was Verified Before Testing
1. Python environment configured and executable resolved.
2. Source files compile successfully.
3. Dry-safe smoke test was prepared to avoid sending emails.

## Tests Executed

### 1) Syntax/compile validation
Command:
```bash
/home/sourov/Documents/employment/.venv/bin/python -m py_compile main_app.py email_sender.py email_generator.py data_parser.py researcher.py
```
Result: PASS

### 2) Dry-safe smoke test (real input files, no sending)
Inputs:
- CV PDF: /home/sourov/Documents/employment/rerappelrdvfrancetravailuesaaxeressourceconseilst/Formateurd_Anglais_Certifié_CELTA_Cambridge_Spécialiste_IELTS_TOEIC_Business_English.pdf
- XLSX list: /home/sourov/Documents/employment/unemploistablecestpartimisedispositiondeconse/260 Plus grosses entreprises 974 Filtre.xlsx

Checks:
- Company list loaded
- CV text extracted
- Personalized email body generated

Observed output:
- SMOKE_OK companies=500
- cv_chars=2207
- email_chars=552
- FIRST_COMPANY=UNKNOWN

Result: PASS (functional dry test)

### 3) App execution check
Command:
```bash
/home/sourov/Documents/employment/.venv/bin/python /home/sourov/Documents/employment/job_automator/main_app.py
```
Result: Executed from absolute path.

## Runtime Behavior (How It Works)
1. GUI loads credentials/options from `.env`.
2. User selects CV PDF and company XLSX.
3. App researches each company via open search.
4. App generates concise, polite personalized email content.
5. App sends through Proton via Playwright (browser selectable).
6. Fallback strategy is documented (browser switch, headed mode, Thunderbird compose, dry-run).
7. App logs details to GUI and local log file.
8. App writes per-run metadata locally for historical learning and adaptive browser default.

## Files Updated In This Cycle
- README.md
- main_app.py
- .gitignore
- how_it_woks.md

## Notes
- `.env` is ignored by git and should stay local.
- Sensitive credentials must never be committed.
- For production sending, first run a test email and keep dry_run=true until confirmed.
