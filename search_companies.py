"""
search_companies.py — Reusable company researcher script.

Reads an XLSX company list, searches each company online (DuckDuckGo),
extracts contact emails, and saves results to a JSON file.
Companies with no email found are saved separately for follow-up.

Usage:
    python search_companies.py --companies companies.xlsx --max 50 --out results.json
    python search_companies.py --companies companies.xlsx --max 50 --out results.json --directory http://www.reunion-directory.com/annuaire-des-professions.html
"""

import argparse, json, os, sys, time, re, requests
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, unquote, parse_qs
sys.path.insert(0, os.path.dirname(__file__))
from data_parser import read_company_list

HEADERS = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) Chrome/124.0 Safari/537.36'}
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,6}")
JUNK = {"linkedin.com","facebook.com","twitter.com","instagram.com","youtube.com",
        "wikipedia.org","indeed.com","glassdoor.com","leboncoin.fr","societe.com",
        "pagesjaunes.fr","verif.com","pappers.fr","infogreffe.fr"}
CONTACT_PATHS = ["/contact","/nous-contacter","/recrutement","/emploi","/carrieres","/rh"]
sess = requests.Session(); sess.headers.update(HEADERS)


def ddg_search(query, n=3):
    try:
        r = sess.get("https://html.duckduckgo.com/html/", params={"q": query}, timeout=15)
        soup = BeautifulSoup(r.text, "lxml")
        urls = []
        for a in soup.select("a.result__a"):
            href = a.get("href","")
            u = parse_qs(urlparse(href).query).get("uddg",[None])[0]
            if u:
                u = unquote(u)
                dom = urlparse(u).netloc.lower().lstrip("www.")
                if not any(j in dom for j in JUNK):
                    urls.append(u)
        return urls[:n]
    except Exception as e:
        print(f"    DDG error: {e}"); return []


def scrape_directory(url, company_name):
    """Try to find company email from a local business directory."""
    try:
        r = sess.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "lxml")
        text = soup.get_text(separator=" ")
        # Look for company name vicinity
        idx = text.lower().find(company_name.lower()[:10])
        if idx >= 0:
            chunk = text[max(0,idx-200):idx+400]
            emails = EMAIL_RE.findall(chunk)
            if emails:
                return emails[0]
    except Exception:
        pass
    return None


def extract_emails(url):
    emails = []
    try:
        r = sess.get(url, timeout=10, allow_redirects=True)
        if r.status_code != 200: return []
        soup = BeautifulSoup(r.text, "lxml")
        emails = list(set(EMAIL_RE.findall(soup.get_text())))
        base = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        for path in CONTACT_PATHS:
            try:
                r2 = sess.get(urljoin(base, path), timeout=8)
                if r2.status_code == 200:
                    emails += EMAIL_RE.findall(r2.text)
                time.sleep(0.4)
            except Exception:
                pass
    except Exception:
        pass
    # filter junk emails
    cleaned = []
    for e in set(emails):
        e = e.lower().strip(".,;:")
        d = e.split("@")[-1]
        if not any(x in d for x in ["sentry","example","pixel","noreply"]):
            cleaned.append(e)
    priority = ["recrutement","rh","hr","contact","emploi","candidature"]
    for kw in priority:
        for e in cleaned:
            if kw in e: return [e] + [x for x in cleaned if x != e]
    return cleaned


def research_one(company_name, city, directory_url=None):
    result = {"company": company_name, "city": city, "website": None,
              "email": None, "alternatives": [], "status": "not_found"}
    # 1. Try directory if provided
    if directory_url:
        email = scrape_directory(directory_url, company_name)
        if email:
            result["email"] = email; result["status"] = "found_directory"; return result

    # 2. DuckDuckGo search
    urls = ddg_search(f"{company_name} {city} recrutement contact email")
    if not urls:
        urls = ddg_search(f"{company_name} {city} site officiel")
    if urls:
        result["website"] = urls[0]
        emails = extract_emails(urls[0])
        if emails:
            result["email"] = emails[0]
            result["alternatives"] = emails[1:4]
            result["status"] = "found_web"
    time.sleep(1)
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--companies", required=True)
    ap.add_argument("--max", type=int, default=20)
    ap.add_argument("--out", default="research_results.json")
    ap.add_argument("--directory", default="", help="URL of local business directory to search first")
    ap.add_argument("--resume", action="store_true", help="Skip already-researched companies")
    args = ap.parse_args()

    r = read_company_list(args.companies)
    if not r: sys.exit(1)
    df, name_col, email_col = r

    existing = {}
    if args.resume and os.path.exists(args.out):
        with open(args.out) as f:
            for rec in json.load(f).get("results", []):
                existing[rec["company"]] = rec

    found, not_found = [], []
    for _, row in df.head(args.max).iterrows():
        name = str(row.get(name_col,"")).strip()
        city = str(row.get("Ville","")).strip()
        if not name: continue

        if name in existing:
            rec = existing[name]
        else:
            print(f"Researching: {name}")
            rec = research_one(name, city, args.directory or None)

        if rec["email"]:
            found.append(rec)
            print(f"  ✓ {rec['email']}")
        else:
            rec["alternatives"] = [
                f"Rechercher manuellement: {name} {city} recrutement",
                f"Appeler directement ou visiter leur site: {rec.get('website','?')}",
                f"Consulter: https://www.reunion-directory.com/annuaire-des-professions.html",
                f"Consulter: https://www.pagesjaunes.fr/pros/search?quoiqui={name.replace(' ','+')}",
            ]
            not_found.append(rec)
            print(f"  ✗ no email — saved for follow-up")

    output = {
        "generated_at": datetime.now().isoformat(),
        "total": len(found)+len(not_found),
        "found": len(found), "not_found": len(not_found),
        "results": found + not_found,
        "follow_up_needed": not_found,
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nDone. Found: {len(found)} | No email: {len(not_found)}")
    print(f"Results saved to: {args.out}")
    if not_found:
        print(f"Follow-up needed: {args.out} → 'follow_up_needed' key")


if __name__ == "__main__":
    main()
