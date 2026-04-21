"""
bulk_sender.py — Session-based bulk email sender via ProtonMail + Playwright.

Logs into ProtonMail ONCE, then sends all queued emails in the same browser
session. Much faster than logging in per email.

Usage (CLI):
    python bulk_sender.py \\
        --cv /path/cv.pdf \\
        --companies /path/companies.xlsx \\
        --max 50 \\
        --provider deepseek \\
        [--dry-run]

Usage (from code):
    from bulk_sender import run_bulk_campaign
    run_bulk_campaign(config)
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

from data_parser import read_company_list, extract_cv_text, extract_motivation_letter
from researcher import search_company_info
from email_generator import generate_email
from email_sender import (
    _try_click, _try_fill, _fill_body,
    _LOGIN_USERNAME, _LOGIN_PASSWORD, _LOGIN_SUBMIT,
    _SIDEBAR_READY, _COMPOSE_BTN, _TO_FIELD, _SUBJECT_FIELD, _SEND_BTN,
    _ATTACHMENT_INPUT, _ATTACHMENT_DONE, _COMPOSER_GONE,
)


LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
META_DIR = os.path.join(os.path.dirname(__file__), "data", "metadata")
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(META_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "bulk_sender.log")
META_FILE = os.path.join(META_DIR, "runs.jsonl")


def log(msg, log_path=LOG_FILE):
    ts = datetime.now().isoformat(timespec="seconds")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def _login_protonmail(page, username, password):
    log("  Navigating to ProtonMail …")
    page.goto("https://mail.proton.me/login", timeout=60000)
    for sel in _LOGIN_USERNAME:
        try:
            page.wait_for_selector(sel, timeout=30000)
            break
        except Exception:
            continue
    if not _try_fill(page, _LOGIN_USERNAME, username):
        raise RuntimeError("Cannot find username field")
    if not _try_fill(page, _LOGIN_PASSWORD, password):
        raise RuntimeError("Cannot find password field")
    if not _try_click(page, _LOGIN_SUBMIT):
        raise RuntimeError("Cannot click submit")
    for sel in _SIDEBAR_READY:
        try:
            page.wait_for_selector(sel, timeout=60000)
            log("  Login OK")
            return
        except PWTimeout:
            continue
    raise RuntimeError("Login timed out — check credentials or 2FA setting")


def _send_one(page, recipient, subject, body, attachment_path=None):
    """Send a single email in an already-authenticated ProtonMail session."""
    if not _try_click(page, _COMPOSE_BTN, timeout=10000):
        raise RuntimeError("Cannot find Compose button")
    time.sleep(1)

    if not _try_fill(page, _TO_FIELD, recipient):
        raise RuntimeError("Cannot fill To: field")
    page.keyboard.press("Tab")
    time.sleep(0.3)

    if not _try_fill(page, _SUBJECT_FIELD, subject):
        raise RuntimeError("Cannot fill Subject field")

    if not _fill_body(page, body):
        raise RuntimeError("Cannot fill email body")

    if attachment_path and os.path.exists(attachment_path):
        for sel in _ATTACHMENT_INPUT:
            try:
                page.set_input_files(sel, attachment_path)
                break
            except Exception:
                continue
        for sel in _ATTACHMENT_DONE:
            try:
                page.wait_for_selector(sel, timeout=30000)
                break
            except PWTimeout:
                pass

    if not _try_click(page, _SEND_BTN, timeout=10000):
        raise RuntimeError("Cannot click Send")

    try:
        page.wait_for_selector(_COMPOSER_GONE[0], state="hidden", timeout=25000)
    except PWTimeout:
        pass
    time.sleep(2)


def run_bulk_campaign(config: dict) -> dict:
    """
    Main entry point for bulk sending.

    config keys:
        cv_path, company_path, letter_path (opt),
        proton_user, proton_pass,
        browser (chromium|firefox), headless (bool),
        dry_run (bool), max_companies (int),
        provider, api_key, ollama_model, ollama_url
    """
    stats = {"processed": 0, "sent": 0, "skipped": 0, "failed": 0}
    run_log = []

    log("=== Bulk Campaign Starting ===")

    result = read_company_list(config["company_path"])
    if result is None:
        log("ERROR: cannot read company list"); return stats
    df, name_col, email_col = result

    cv_text = extract_cv_text(config["cv_path"])
    if not cv_text:
        log("ERROR: cannot read CV"); return stats

    letter_text = ""
    if config.get("letter_path"):
        letter_text = extract_motivation_letter(config["letter_path"]) or ""
    combined_profile = f"=== CV ===\n{cv_text}\n\n=== LETTRE ===\n{letter_text}".strip()

    limit   = config.get("max_companies", 10)
    subset  = df.head(limit)
    dry_run = config.get("dry_run", True)

    log(f"Processing {len(subset)} companies | dry_run={dry_run} | provider={config.get('provider','template')}")

    # ── Phase 1: Research & email generation ─────────────────────────────────
    queue = []   # list of (company_name, recipient_email, subject, body)

    for _, row in subset.iterrows():
        company_name = str(row.get(name_col, "")).strip()
        city         = str(row.get("Ville", "")).strip()
        ca           = str(row.get("C.A.", "")).strip()
        postal_code  = str(row.get("CP", "")).strip()

        if not company_name:
            stats["skipped"] += 1
            continue

        log(f"\n[research] {company_name} – {city}")
        stats["processed"] += 1

        contact_email = None
        if email_col:
            val = row.get(email_col)
            if val and "@" in str(val):
                contact_email = str(val).strip()
                research = {"about_text": "", "contact_email": contact_email}

        if not contact_email:
            research = search_company_info(company_name, city)
            contact_email = research.get("contact_email")

        if not contact_email:
            log(f"  Skipped — no email found")
            stats["skipped"] += 1
            run_log.append({"company": company_name, "status": "skipped", "reason": "no email"})
            continue

        company_info = {
            "company_name": company_name,
            "city":         city,
            "ca":           ca,
            "postal_code":  postal_code,
        }
        subject, body = generate_email(
            combined_profile, company_info, research,
            api_key      = config.get("api_key"),
            provider     = config.get("provider", "template"),
            ollama_model = config.get("ollama_model", "mistral"),
            ollama_url   = config.get("ollama_url", "http://localhost:11434"),
        )
        log(f"  Email ready → {contact_email}")
        queue.append((company_name, contact_email, subject, body))

    log(f"\n=== Research done: {len(queue)} emails ready | {stats['skipped']} skipped ===")

    if dry_run:
        log("DRY RUN — saving previews, not sending.")
        for company_name, email, subject, body in queue:
            run_log.append({"company": company_name, "email": email, "status": "dry_run",
                            "subject": subject, "body_preview": body[:200]})
        stats["sent"] = 0
        stats["run_log"] = run_log
        _save_meta(config, stats)
        return stats

    # ── Phase 2: Send all emails in one browser session ───────────────────────
    if not queue:
        log("Nothing to send.")
        stats["run_log"] = run_log
        _save_meta(config, stats)
        return stats

    browser_name = config.get("browser", "chromium")
    headless     = config.get("headless", False)

    with sync_playwright() as p:
        launch = p.firefox.launch if browser_name == "firefox" else p.chromium.launch
        browser = launch(headless=headless)
        ctx  = browser.new_context(viewport={"width": 1280, "height": 900})
        page = ctx.new_page()

        try:
            _login_protonmail(page, config["proton_user"], config["proton_pass"])
        except Exception as e:
            log(f"LOGIN FAILED: {e}")
            browser.close()
            stats["run_log"] = run_log
            _save_meta(config, stats)
            return stats

        for company_name, recipient, subject, body in queue:
            log(f"\n[send] {company_name} → {recipient}")
            try:
                _send_one(page, recipient, subject, body, config.get("cv_path"))
                log(f"  Sent OK")
                stats["sent"] += 1
                run_log.append({"company": company_name, "email": recipient, "status": "sent"})
            except Exception as e:
                log(f"  FAILED: {e}")
                stats["failed"] += 1
                run_log.append({"company": company_name, "email": recipient, "status": "failed", "error": str(e)})
                # Brief pause before next attempt
                time.sleep(3)

        browser.close()

    log(f"\n=== Done | Sent:{stats['sent']} Skipped:{stats['skipped']} Failed:{stats['failed']} ===")
    stats["run_log"] = run_log
    _save_meta(config, stats)
    return stats


def _save_meta(config, stats):
    record = {
        "timestamp":  datetime.now().isoformat(timespec="seconds"),
        "browser":    config.get("browser", "chromium"),
        "dry_run":    config.get("dry_run", True),
        "provider":   config.get("provider", "template"),
        "stats":      {k: v for k, v in stats.items() if k != "run_log"},
        "log":        stats.get("run_log", []),
    }
    try:
        with open(META_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:
        log(f"Warning: could not save metadata ({e})")


# ─────────────────────────────────────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────────────────────────────────────
def _cli():
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"), override=True)

    parser = argparse.ArgumentParser(description="Bulk job application email sender")
    parser.add_argument("--cv",         required=True,  help="Path to CV PDF")
    parser.add_argument("--companies",  required=True,  help="Path to company XLSX")
    parser.add_argument("--letter",     default="",     help="Path to motivation letter PDF (optional)")
    parser.add_argument("--max",        type=int, default=10, help="Max companies to process")
    parser.add_argument("--provider",   default=None,   help="AI provider: anthropic|mistral|deepseek|ollama|template")
    parser.add_argument("--api-key",    default=None,   help="API key (overrides env var)")
    parser.add_argument("--browser",    default=os.getenv("BROWSER", "chromium"))
    parser.add_argument("--headless",   action="store_true", default=os.getenv("HEADLESS","false").lower()=="true")
    parser.add_argument("--dry-run",    action="store_true", default=os.getenv("DRY_RUN","true").lower()=="true")
    args = parser.parse_args()

    config = {
        "cv_path":       args.cv,
        "company_path":  args.companies,
        "letter_path":   args.letter,
        "proton_user":   os.getenv("PROTON_USER", ""),
        "proton_pass":   os.getenv("PROTON_PASS", ""),
        "browser":       args.browser,
        "headless":      args.headless,
        "dry_run":       args.dry_run,
        "max_companies": args.max,
        "provider":      args.provider,
        "api_key":       args.api_key,
        "ollama_model":  os.getenv("OLLAMA_MODEL", "mistral"),
        "ollama_url":    os.getenv("OLLAMA_URL", "http://localhost:11434"),
    }

    run_bulk_campaign(config)


if __name__ == "__main__":
    _cli()
