"""
Company researcher — finds website URL + contact email.

Strategy (in order):
  1. Mailto: links scraped from the company website (most reliable)
  2. Email regex in page text + contact/recrutement sub-pages
  3. Domain-guessing: try common prefixes (recrutement@, rh@, contact@, info@)
     and verify with SMTP RCPT probe (optional)
  4. Targeted DDG search: "[company] recrutement email @"
  5. Alternative directories (Pages Jaunes, local directory)

Uses DuckDuckGo HTML — no API key required.
"""

import re, time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, unquote, parse_qs

UA = ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')
SESS = requests.Session()
SESS.headers.update({'User-Agent': UA})

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,6}")
MAILTO_RE = re.compile(r'href=["\']mailto:([^"\'?\s]+)', re.IGNORECASE)

JUNK_DOMAINS = {
    "linkedin.com","facebook.com","twitter.com","instagram.com","youtube.com",
    "wikipedia.org","indeed.com","glassdoor.com","leboncoin.fr","societe.com",
    "pagesjaunes.fr","verif.com","pappers.fr","infogreffe.fr","kompass.com",
    "manageo.fr","annuaire-entreprises.data.gouv.fr","infobel.fr",
    "africabizinfo.com","shipping-data.com","ma.kompass.com",
}
JUNK_EMAIL_PARTS = {"noreply","no-reply","sentry","example","pixel","webmaster",
                    "bounce","unsubscribe","mailer","postmaster","abuse"}
PRIORITY_PREFIXES = ["recrutement","rh","hr","emploi","candidature","jobs","career"]
COMMON_PREFIXES   = ["contact","info","direction","accueil","hello","administration"]
CONTACT_PATHS = [
    "/contact","/nous-contacter","/contactez-nous","/contact-us",
    "/recrutement","/emploi","/carrieres","/careers","/jobs",
    "/rh","/ressources-humaines","/nous-rejoindre","/join-us",
]


# ── helpers ──────────────────────────────────────────────────────────────────

def _clean(email: str) -> str | None:
    e = email.lower().strip(".,;:\"' ")
    local, _, domain = e.partition("@")
    if not domain or "." not in domain:
        return None
    if any(p in local for p in JUNK_EMAIL_PARTS):
        return None
    if len(e) < 6 or len(e) > 80:
        return None
    return e


def _score(email: str) -> int:
    local = email.split("@")[0]
    for i, p in enumerate(PRIORITY_PREFIXES):
        if p in local:
            return 100 - i
    for i, p in enumerate(COMMON_PREFIXES):
        if p in local:
            return 50 - i
    return 10


def _rank(emails: list[str]) -> list[str]:
    unique = list(dict.fromkeys(e for e in emails if e))
    return sorted(unique, key=_score, reverse=True)


def _fetch(url: str, timeout: int = 10):
    """Return (soup, html_text) or (None, None)."""
    try:
        r = SESS.get(url, timeout=timeout, allow_redirects=True)
        if r.status_code != 200:
            return None, None
        return BeautifulSoup(r.text, "lxml"), r.text
    except Exception:
        return None, None


def _extract_emails_from_html(html: str) -> list[str]:
    """Extract from mailto: links first (most explicit), then regex in text."""
    found = []
    # mailto: links are the clearest signal
    for m in MAILTO_RE.findall(html):
        c = _clean(m)
        if c:
            found.append(c)
    # regex in full text (catches obfuscated and plain text)
    for m in EMAIL_RE.findall(html):
        c = _clean(m)
        if c:
            found.append(c)
    return found


def _ddg(query: str, n: int = 5) -> list[str]:
    """DuckDuckGo HTML search → list of result URLs."""
    for attempt in range(2):
        try:
            r = SESS.get("https://html.duckduckgo.com/html/",
                         params={"q": query}, timeout=20)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "lxml")
            urls = []
            for a in soup.select("a.result__a"):
                href = a.get("href", "")
                u = parse_qs(urlparse(href).query).get("uddg", [None])[0]
                if u:
                    u = unquote(u)
                    dom = urlparse(u).netloc.lower().lstrip("www.")
                    if not any(j in dom for j in JUNK_DOMAINS):
                        urls.append(u)
            return urls[:n]
        except Exception:
            if attempt == 0:
                time.sleep(3)
    return []


def _guess_emails(domain: str) -> list[str]:
    """Construct plausible email addresses from the company domain."""
    guesses = []
    for prefix in PRIORITY_PREFIXES + COMMON_PREFIXES:
        guesses.append(f"{prefix}@{domain}")
    return guesses


# ── main entry point ─────────────────────────────────────────────────────────

def search_company_info(company_name: str, city: str = "") -> dict:
    """
    Research a company. Returns:
        website (str|None), about_text (str),
        contact_email (str|None), all_emails (list[str])
    """
    result = {"website": None, "about_text": "", "contact_email": None, "all_emails": []}
    all_emails: list[str] = []

    # ── 1. Find the website ──────────────────────────────────────────────────
    queries = [
        f"{company_name} {city} site officiel recrutement",
        f"{company_name} {city} contact email emploi",
    ]
    website = None
    for q in queries:
        urls = _ddg(q)
        if urls:
            website = urls[0]
            break
        time.sleep(0.5)

    if not website:
        print(f"    No website found for {company_name}")
        return result

    result["website"] = website
    base = f"{urlparse(website).scheme}://{urlparse(website).netloc}"
    print(f"    Website: {website}")

    # ── 2. Scrape homepage ───────────────────────────────────────────────────
    soup_home, html_home = _fetch(website)
    if html_home:
        found = _extract_emails_from_html(html_home)
        all_emails.extend(found)
        if soup_home:
            result["about_text"] = soup_home.get_text(" ", strip=True)[:1000]

    # ── 3. Scrape contact/recrutement sub-pages ───────────────────────────────
    for path in CONTACT_PATHS:
        url = urljoin(base, path)
        _, html = _fetch(url)
        if html:
            found = _extract_emails_from_html(html)
            if found:
                print(f"    Found at {path}: {found[:2]}")
            all_emails.extend(found)
        time.sleep(0.3)

    # ── 4. Targeted DDG email search ─────────────────────────────────────────
    if not all_emails:
        q = f'"{company_name}" recrutement OR emploi OR "rh@" OR "contact@" email site:{urlparse(base).netloc}'
        email_urls = _ddg(q, n=3)
        for u in email_urls:
            _, html = _fetch(u)
            if html:
                all_emails.extend(_extract_emails_from_html(html))
        time.sleep(0.5)

    # ── 5. Domain-guess as last resort ───────────────────────────────────────
    domain = urlparse(base).netloc.lstrip("www.")
    if not all_emails and domain:
        guesses = _guess_emails(domain)
        # We don't verify (no SMTP probe by default) — just flag as guessed
        result["guessed_emails"] = guesses
        print(f"    No email found — guesses: {guesses[:3]}")

    ranked = _rank(all_emails)
    result["all_emails"] = ranked
    result["contact_email"] = ranked[0] if ranked else None

    if result["contact_email"]:
        print(f"    Email: {result['contact_email']}")
    else:
        print(f"    No confirmed email for {company_name}")

    time.sleep(1)
    return result


# Legacy alias
def search_company_website(company_name: str) -> str | None:
    r = search_company_info(company_name)
    return r.get("about_text") or None


if __name__ == "__main__":
    for name, city in [("ADECCO REUNION", "LA POSSESSION"), ("J. ANZEMBERG", "LA POSSESSION")]:
        print(f"\n=== {name} ===")
        info = search_company_info(name, city)
        print("Email:", info["contact_email"])
        print("All:", info["all_emails"])
