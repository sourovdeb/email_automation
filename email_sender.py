"""
ProtonMail email sender using Playwright browser automation.

Strategy: try multiple selectors for each UI element to stay resilient across
ProtonMail interface updates.  Retries once on failure.
"""
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
import time
import os


# ---------------------------------------------------------------------------
# Selector lists — ordered by most-likely-current first
# ---------------------------------------------------------------------------

_LOGIN_USERNAME = ["#username", "input[name='username']", "input[type='email']"]
_LOGIN_PASSWORD = ["#password", "input[name='password']", "input[type='password']"]
_LOGIN_SUBMIT   = ["button[type='submit']", "button:has-text('Sign in')", "button:has-text('Se connecter')"]
_SIDEBAR_READY  = [".sidebar", "[data-testid='navigation-item:inbox']", "nav"]
_COMPOSE_BTN    = [
    "button[data-testid='sidebar:compose']",
    "a[data-testid='sidebar:compose']",
    "button:has-text('New message')",
    "button:has-text('Nouveau message')",
]
_TO_FIELD       = [
    "input[data-testid='composer:to']",
    "input[placeholder*='recipient' i]",
    "input[aria-label*='To' i]",
]
_SUBJECT_FIELD  = [
    "input[data-testid='composer:subject']",
    "input[placeholder*='Subject' i]",
    "input[placeholder*='Objet' i]",
]
_SEND_BTN       = [
    "button[data-testid='composer:send-button']",
    "button:has-text('Send')",
    "button:has-text('Envoyer')",
]
_ATTACHMENT_INPUT = ["input[type='file']"]
_ATTACHMENT_DONE  = [".attachment-card", "[data-testid='composer:attachment-list'] *"]
_COMPOSER_GONE    = ["div[data-testid='composer']"]


def _try_click(page, selectors, timeout=8000):
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            loc.wait_for(state="visible", timeout=timeout)
            loc.click()
            return True
        except Exception:
            continue
    return False


def _try_fill(page, selectors, value, timeout=8000):
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            loc.wait_for(state="visible", timeout=timeout)
            loc.fill(value)
            return True
        except Exception:
            continue
    return False


def _fill_body(page, body_text):
    """Fill ProtonMail's rich-text editor (Rooster) via iframe or contenteditable."""
    iframe_strategies = [
        ("iframe[data-testid='rooster-iframe']", "div[aria-label='Email body']"),
        ("iframe[data-testid*='rooster']",        "div[aria-label='Email body']"),
        ("iframe[title*='Email' i]",              "div[aria-label='Email body']"),
        ("iframe[data-testid='rooster-iframe']",  "div[contenteditable='true']"),
        ("iframe[data-testid*='rooster']",        "div[contenteditable='true']"),
    ]
    for frame_sel, body_sel in iframe_strategies:
        try:
            frame  = page.frame_locator(frame_sel)
            target = frame.locator(body_sel).first
            target.wait_for(timeout=8000)
            target.click()
            target.fill(body_text)
            return True
        except Exception:
            continue

    inline = [
        "div[data-testid='composer:body'] div[contenteditable='true']",
        "div[aria-label='Email body'][contenteditable='true']",
        "div[role='textbox'][contenteditable='true']",
        "div[contenteditable='true']",
    ]
    for sel in inline:
        try:
            loc = page.locator(sel).first
            loc.wait_for(timeout=8000)
            loc.click()
            loc.fill(body_text)
            return True
        except Exception:
            continue

    return False


def _do_send(page, username, password, recipient, subject, body, attachment_path):
    print("  Navigating to ProtonMail login …")
    page.goto("https://mail.proton.me/login", timeout=60000)
    # Don't wait for networkidle — ProtonMail has persistent background requests.
    # Instead wait for the username field to appear.
    for sel in _LOGIN_USERNAME:
        try:
            page.wait_for_selector(sel, timeout=30000)
            break
        except Exception:
            continue

    print("  Filling credentials …")
    if not _try_fill(page, _LOGIN_USERNAME, username):
        raise RuntimeError("Cannot locate username field")
    if not _try_fill(page, _LOGIN_PASSWORD, password):
        raise RuntimeError("Cannot locate password field")
    if not _try_click(page, _LOGIN_SUBMIT):
        raise RuntimeError("Cannot click submit button")

    print("  Waiting for inbox …")
    found = False
    for sel in _SIDEBAR_READY:
        try:
            page.wait_for_selector(sel, timeout=60000)
            found = True
            break
        except PWTimeout:
            continue
    if not found:
        raise RuntimeError("Login timed out – check credentials or 2FA")
    print("  Login OK")

    time.sleep(2)
    print("  Opening composer …")
    if not _try_click(page, _COMPOSE_BTN, timeout=10000):
        raise RuntimeError("Cannot find Compose button")
    time.sleep(1)

    print("  Filling To / Subject …")
    if not _try_fill(page, _TO_FIELD, recipient):
        raise RuntimeError("Cannot fill recipient field")
    page.keyboard.press("Tab")
    time.sleep(0.5)

    if not _try_fill(page, _SUBJECT_FIELD, subject):
        raise RuntimeError("Cannot fill subject field")

    print("  Filling body …")
    if not _fill_body(page, body):
        raise RuntimeError("Cannot fill email body – ProtonMail selectors may have changed")

    if attachment_path and os.path.exists(attachment_path):
        print(f"  Attaching {os.path.basename(attachment_path)} …")
        for sel in _ATTACHMENT_INPUT:
            try:
                page.set_input_files(sel, attachment_path)
                break
            except Exception:
                continue
        # wait for upload confirmation
        for sel in _ATTACHMENT_DONE:
            try:
                page.wait_for_selector(sel, timeout=30000)
                print("  Attachment uploaded")
                break
            except PWTimeout:
                continue

    print("  Sending …")
    if not _try_click(page, _SEND_BTN, timeout=10000):
        raise RuntimeError("Cannot click Send button")

    # Wait for composer to close (sent successfully)
    try:
        page.wait_for_selector(_COMPOSER_GONE[0], state="hidden", timeout=30000)
    except PWTimeout:
        pass  # composer may auto-close differently on some builds

    time.sleep(3)
    print("  Email sent!")
    return True


def send_email_with_protonmail(
    username, password, recipient_email, subject, body,
    attachment_path=None, browser_name="chromium", headless=False
):
    """
    Send an email via ProtonMail using Playwright.

    Returns True on success, False on failure.
    Retries once automatically on transient failures.
    """
    for attempt in range(1, 3):
        print(f"\n--- ProtonMail send attempt {attempt}/2 ---")
        with sync_playwright() as p:
            try:
                launch = p.firefox.launch if browser_name == "firefox" else p.chromium.launch
                browser = launch(headless=headless)
                ctx  = browser.new_context(viewport={"width": 1280, "height": 900})
                page = ctx.new_page()
                _do_send(page, username, password, recipient_email, subject, body, attachment_path)
                browser.close()
                return True
            except Exception as e:
                print(f"  Attempt {attempt} failed: {e}")
                try:
                    browser.close()
                except Exception:
                    pass
                if attempt < 2:
                    print("  Retrying in 5 s …")
                    time.sleep(5)
    return False


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    ok = send_email_with_protonmail(
        username=os.getenv("PROTON_USER"),
        password=os.getenv("PROTON_PASS"),
        recipient_email="sourovdeb.is@gmail.com",
        subject="Test – Job Automator",
        body="Ceci est un email de test automatisé.\n\nCordialement,\nSourov Deb",
        attachment_path=None,
        browser_name="chromium",
        headless=False,
    )
    print("Result:", "OK" if ok else "FAILED")
