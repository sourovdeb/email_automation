# Email Automation (Accessible GUI)

A Python desktop app that helps prepare and send concise, personalized job emails using:
- CV parsing (PDF)
- Company list parsing (XLSX)
- Company research via open web search
- Playwright browser automation with Proton Mail (Chromium or Firefox)

## Accessibility goals

The GUI is designed for easier use by autistic, elderly, and handicapped users:
- Large text and controls
- High-contrast colors
- Clear labels and focused flow
- Keyboard-friendly input order
- Live log panel with simple messages
- Safety toggle (dry-run)

## Project files

- `main_app.py`: GUI and orchestration
- `data_parser.py`: reads CV and company list
- `researcher.py`: collects company context from web search
- `email_generator.py`: generates concise personalized email body
- `email_sender.py`: sends email through Proton Mail web UI via Playwright

## Setup

1. Create and activate virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
playwright install
```

3. Run app:

```bash
python main_app.py
```

## Usage

1. Select CV PDF.
2. Select company list XLSX.
3. Enter Proton credentials.
4. Choose browser (`chromium` or `firefox`).
5. Set options:
   - headless mode
   - dry run
   - max companies
6. Run test email first.
7. Start automation.

## Important notes

- Always run a test email to your own address before a full run.
- Use dry-run to verify generated flow before sending.
- Proton web UI selectors can change over time; update `email_sender.py` if needed.
- Never commit passwords.

## GitHub

This project is intended for:
- https://github.com/sourovdeb/email_automation
