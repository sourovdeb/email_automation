"""
send_emails.py — Sends all emails from a JSON queue via ProtonMail + Playwright.
Logs in ONCE, sends all, marks each as sent/failed in the queue file.

Reusable for any campaign: just provide a different queue JSON.

Usage:
    python send_emails.py --queue email_queue.json --cv cv.pdf [--dry-run] [--max 10]
"""

import argparse, json, os, sys, time
from datetime import datetime
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"), override=True)
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
from email_sender import (
    _try_click, _try_fill, _fill_body,
    _LOGIN_USERNAME, _LOGIN_PASSWORD, _LOGIN_SUBMIT,
    _SIDEBAR_READY, _COMPOSE_BTN, _TO_FIELD, _SUBJECT_FIELD,
    _SEND_BTN, _ATTACHMENT_INPUT, _ATTACHMENT_DONE, _COMPOSER_GONE,
)

LOG_FILE = os.path.join(os.path.dirname(__file__), "logs", "send_emails.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)


def log(msg):
    ts = datetime.now().isoformat(timespec="seconds")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def login(page, user, pw):
    page.goto("https://mail.proton.me/login", timeout=60000)
    for sel in _LOGIN_USERNAME:
        try: page.wait_for_selector(sel, timeout=25000); break
        except Exception: continue
    if not _try_fill(page, _LOGIN_USERNAME, user):
        raise RuntimeError("Cannot fill username")
    if not _try_fill(page, _LOGIN_PASSWORD, pw):
        raise RuntimeError("Cannot fill password")
    if not _try_click(page, _LOGIN_SUBMIT):
        raise RuntimeError("Cannot click submit")
    for sel in _SIDEBAR_READY:
        try: page.wait_for_selector(sel, timeout=60000); log("Login OK"); return
        except PWTimeout: continue
    raise RuntimeError("Login timed out")


def send_one(page, recipient, subject, body, attachment=None):
    if not _try_click(page, _COMPOSE_BTN, timeout=10000):
        raise RuntimeError("No compose button")
    time.sleep(1)
    if not _try_fill(page, _TO_FIELD, recipient): raise RuntimeError("No To field")
    page.keyboard.press("Tab"); time.sleep(0.3)
    if not _try_fill(page, _SUBJECT_FIELD, subject): raise RuntimeError("No Subject field")
    if not _fill_body(page, body): raise RuntimeError("Cannot fill body")
    if attachment and os.path.exists(attachment):
        for sel in _ATTACHMENT_INPUT:
            try: page.set_input_files(sel, attachment); break
            except Exception: pass
        for sel in _ATTACHMENT_DONE:
            try: page.wait_for_selector(sel, timeout=25000); break
            except PWTimeout: pass
    if not _try_click(page, _SEND_BTN, timeout=10000):
        raise RuntimeError("No Send button")
    try: page.wait_for_selector(_COMPOSER_GONE[0], state="hidden", timeout=25000)
    except PWTimeout: pass
    time.sleep(2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--queue",    required=True, help="JSON queue from organise_emails.py")
    ap.add_argument("--cv",       required=True, help="CV PDF to attach")
    ap.add_argument("--dry-run",  action="store_true", default=os.getenv("DRY_RUN","true").lower()=="true")
    ap.add_argument("--max",      type=int, default=None, help="Max emails to send this run")
    ap.add_argument("--browser",  default=os.getenv("BROWSER","chromium"))
    ap.add_argument("--headless", action="store_true", default=os.getenv("HEADLESS","false").lower()=="true")
    args = ap.parse_args()

    user = os.getenv("PROTON_USER",""); pw = os.getenv("PROTON_PASS","")
    if not user or not pw:
        print("ERROR: set PROTON_USER and PROTON_PASS in .env"); sys.exit(1)

    with open(args.queue, encoding="utf-8") as f:
        data = json.load(f)

    pending = [e for e in data["queue"] if e["status"] == "pending"]
    if args.max:
        pending = pending[:args.max]

    log(f"Queue: {len(pending)} pending | dry_run={args.dry_run}")

    if args.dry_run:
        for e in pending:
            log(f"[DRY RUN] {e['company']} → {e['recipient']} | {e['subject'][:60]}")
        print(f"\nDry run complete. {len(pending)} emails previewed. Remove --dry-run to send.")
        return

    sent = failed = 0
    with sync_playwright() as p:
        launch = p.firefox.launch if args.browser == "firefox" else p.chromium.launch
        browser = launch(headless=args.headless)
        page = browser.new_context(viewport={"width":1280,"height":900}).new_page()

        try:
            login(page, user, pw)
        except Exception as e:
            log(f"LOGIN FAILED: {e}"); browser.close(); sys.exit(1)

        for entry in pending:
            log(f"Sending → {entry['company']} <{entry['recipient']}>")
            try:
                send_one(page, entry["recipient"], entry["subject"], entry["body"], args.cv)
                entry["status"] = "sent"
                entry["sent_at"] = datetime.now().isoformat(timespec="seconds")
                log(f"  OK")
                sent += 1
            except Exception as e:
                entry["status"] = "failed"
                entry["error"] = str(e)
                log(f"  FAILED: {e}")
                failed += 1
                time.sleep(3)

        browser.close()

    # Save updated queue with sent/failed status
    with open(args.queue, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    log(f"=== Done: sent={sent} failed={failed} ===")
    print(f"\nUpdated queue saved to {args.queue}")


if __name__ == "__main__":
    main()
