""" your 
Company researcher: finds website URL, scrapes about/contact pages, extracts emails.
Uses DuckDuckGo HTML search (no API key required) with multiple fallback strategies.
"""
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, unquote, parse_qs

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    )
}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,6}"
)

CONTACT_PATHS = [
    "/contact", "/contact-us", "/nous-contacter", "/contactez-nous",
    "/recrutement", "/emploi", "/carrieres", "/careers", "/jobs",
    "/rh", "/ressources-humaines", "/a-propos", "/about", "/qui-sommes-nous",
]

JUNK_DOMAINS = {
    "linkedin.com", "facebook.com", "twitter.com", "instagram.com",
    "youtube.com", "wikipedia.org", "indeed.com", "glassdoor.com",
    "leboncoin.fr", "societe.com", "verif.com", "pappers.fr",
    "manageo.fr", "infogreffe.fr", "annuaire-entreprises.data.gouv.fr",
}

# French business directories
DIRECTORIES = [
    "https://www.pagesjaunes.fr/pagesblanches/recherche?quoiquoi={query}",
    "https://www.kompass.com/fr/search/?text={query}",
    "https://www.societe.com/recherche/{query}.html",
]


def _ddg_search(query):
    """DuckDuckGo HTML search — returns list of result URLs."""
    try:
        resp = SESSION.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            timeout=15,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        urls = []
        for a in soup.select("a.result__a"):
            href = a.get("href", "")
            parsed = urlparse(href)
            actual = parse_qs(parsed.query).get("uddg", [None])[0]
            if actual:
                actual = unquote(actual)
                domain = urlparse(actual).netloc.lower().lstrip("www.")
                if not any(j in domain for j in JUNK_DOMAINS):
                    urls.append(actual)
        return urls
    except Exception as e:
        print(f"DDG search error: {e}")
        return []


def _fetch_text(url, timeout=10):
    """Fetch a URL and return (soup, raw_text). Returns (None, None) on error."""
    try:
        resp = SESSION.get(url, timeout=timeout, allow_redirects=True)
        if resp.status_code != 200:
            return None, None
        soup = BeautifulSoup(resp.text, "lxml")
        text = soup.get_text(separator=" ", strip=True)
        return soup, text
    except Exception:
        return None, None


def _extract_emails(text):
    """Extract unique, plausible email addresses from text."""
    found = EMAIL_RE.findall(text or "")
    cleaned = set()
    for e in found:
        e = e.strip(".,;:")
        domain = e.split("@")[-1].lower()
        if any(bad in domain for bad in ["sentry", "example", "pixel", "noreply", "no-reply"]):
            continue
        cleaned.add(e.lower())
    return sorted(cleaned)


def _pick_contact_email(emails, company_name):
    """Score and rank emails: prefer hr/recrutement/contact, avoid generic."""
    if not emails:
        return None
    priority_keywords = ["recrutement", "rh", "hr", "contact", "emploi", "candidature"]
    for kw in priority_keywords:
        for e in emails:
            if kw in e:
                return e
    return emails[0]

def _search_french_directories(company_name, city):
    """Search French business directories for company information."""
    query = company_name.replace(" ", "+")
    if city:
        query += "+" + city.replace(" ", "+")

    for directory in DIRECTORIES:
        url = directory.replace("{query}", query)
        try:
            resp = SESSION.get(url, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "lxml")
                text = soup.get_text(separator=" ", strip=True)
                emails = _extract_emails(text)
                if emails:
                    print(f"  Found in directory: {emails[0]}")
                    return emails[0], url
        except Exception as e:
            print(f"  Directory search error: {e}")
        time.sleep(1)
    return None, None

def _generate_guess_emails(company_name):
    """Generate likely email addresses based on company name."""
    # Clean company name
    clean_name = re.sub(r'[^\w\s\-]', '', company_name)
    clean_name = re.sub(r'\s+', '', clean_name).lower()

    # Common domains for French companies
    domains = [
        f"{clean_name}.fr",
        f"{clean_name}.re",  # Réunion
        f"{clean_name}.com",
        f"{clean_name}.net",
        f"{clean_name}.org"
    ]

    # Common email patterns
    patterns = [
        "contact",
        "info",
        "recrutement",
        "rh",
        "direction",
        "accueil"
    ]

    guesses = []
    for domain in domains:
        for pattern in patterns:
            guesses.append(f"{pattern}@{domain}")

    return guesses[:5]  # Return top 5 guesses

def _search_with_qwant(query):
    """Qwant search (French search engine) fallback."""
    try:
        # Use Qwant search
        url = f"https://www.qwant.com/?q={query.replace(' ', '+')}"
        resp = SESSION.get(url, timeout=15)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "lxml")
            urls = []
            for a in soup.find_all("a", href=True):
                href = a.get("href", "")
                if href.startswith("https://www.qwant.com/") or "qwant.com" in href:
                    continue
                if href.startswith("http") and not any(j in href for j in JUNK_DOMAINS):
                    domain = urlparse(href).netloc.lower().lstrip("www.")
                    if not any(j in domain for j in JUNK_DOMAINS):
                        urls.append(href)
            return urls[:3]
    except Exception as e:
        print(f"  Qwant search error: {e}")
    return []

def _search_with_google_fallback(query):
    """Google search fallback when DuckDuckGo fails."""
    try:
        # Use Google search with HTML parsing
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        resp = SESSION.get(url, timeout=15)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "lxml")
            urls = []
            for a in soup.find_all("a", href=True):
                href = a.get("href", "")
                if href.startswith("/url?q="):
                    parsed = urlparse(href)
                    actual = parse_qs(parsed.query).get("q", [None])[0]
                    if actual:
                        actual = unquote(actual)
                        domain = urlparse(actual).netloc.lower().lstrip("www.")
                        if not any(j in domain for j in JUNK_DOMAINS):
                            urls.append(actual)
            return urls[:3]
    except Exception as e:
        print(f"  Google search error: {e}")
    return []


def search_company_info(company_name, city=""):
    """
    Main entry point: research a company with multiple fallback strategies.

    Returns dict with keys:
        website (str|None), about_text (str), contact_email (str|None), all_emails (list)
    """
    result = {"website": None, "about_text": "", "contact_email": None, "all_emails": []}

    # Strategy 1: French business directories
    directory_email, directory_url = _search_french_directories(company_name, city)
    if directory_email:
        result["contact_email"] = directory_email
        result["website"] = directory_url
        result["all_emails"] = [directory_email]
        print(f"  Found in French directory: {directory_email}")
        return result

    # Strategy 2: DuckDuckGo search
    query = f"{company_name} {city} site officiel".strip()
    print(f"  Searching: {query}")
    urls = _ddg_search(query)

    if not urls:
        query2 = f"{company_name} recrutement contact email"
        urls = _ddg_search(query2)

    # Strategy 3: Qwant (French search engine) fallback
    if not urls:
        print(f"  Trying Qwant search...")
        urls = _search_with_qwant(query)

    # Strategy 4: Google fallback if Qwant fails
    if not urls:
        print(f"  Trying Google search...")
        urls = _search_with_google_fallback(query)

    if not urls:
        print(f"  No website found for {company_name}")
        # Strategy 4: Generate guess emails as last resort
        guess_emails = _generate_guess_emails(company_name)
        if guess_emails:
            result["all_emails"] = guess_emails
            result["contact_email"] = guess_emails[0]
            print(f"  Generated guess emails: {guess_emails[0]}")
        return result

    website = urls[0]
    result["website"] = website
    base = f"{urlparse(website).scheme}://{urlparse(website).netloc}"
    print(f"  Website candidate: {website}")

    all_emails = []
    about_text_parts = []

    # Extract emails from homepage
    soup_home, text_home = _fetch_text(website)
    if text_home:
        all_emails.extend(_extract_emails(text_home))
        about_text_parts.append(text_home[:800])

    # Check contact pages
    for path in CONTACT_PATHS:
        url = urljoin(base, path)
        _, text = _fetch_text(url)
        if text:
            emails = _extract_emails(text)
            if emails:
                all_emails.extend(emails)
                print(f"  Found emails at {path}: {emails}")
            if "contact" in path or "recrutement" in path:
                about_text_parts.append(text[:600])
        time.sleep(0.3)  # Reduced delay for efficiency

    # Add guess emails if no real emails found
    if not all_emails:
        guess_emails = _generate_guess_emails(company_name)
        all_emails.extend(guess_emails)
        print(f"  Added guess emails: {guess_emails[:2]}")

    unique_emails = list(dict.fromkeys(all_emails))
    result["all_emails"] = unique_emails
    result["contact_email"] = _pick_contact_email(unique_emails, company_name)
    result["about_text"] = " ".join(about_text_parts)[:1500]

    if result["contact_email"]:
        print(f"  ✓ Contact email: {result['contact_email']}")
    else:
        print(f"  ✗ No email found for {company_name}")

    time.sleep(0.8)  # Reduced delay between companies
    return result


# Legacy alias used by older code
def search_company_website(company_name):
    r = search_company_info(company_name)
    return r.get("about_text") or None


if __name__ == "__main__":
    info = search_company_info("ADECCO REUNION", "LA POSSESSION")
    print("\nResult:", info)
