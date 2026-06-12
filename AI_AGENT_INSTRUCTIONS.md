# AI Agent Instructions — Job Search Automation System

> Version 1.1 | Updated: 2026-06-12 | For: Sourov Deb, Formateur Anglais CELTA

---

## What This System Is

This is an **automated job application pipeline** for Sourov Deb, a Cambridge CELTA-certified English trainer based in Saint-Pierre, La Réunion. The system:

1. **Finds jobs** via the France Travail (Pôle Emploi) API (primary) and web scraping (legacy)
2. **Generates personalised application emails** using AI or a French template
3. **Sends emails** via ProtonMail (Playwright browser automation) or Gmail (Google Apps Script)
4. **Tracks** all applications in a log and a Google Sheet

---

## System Architecture

```
[France Travail API]          [Web Scraping — legacy]
        │                           │
        ▼                           ▼
 france_travail_client.py ──► researcher.py (deprecated)
        │                           │
        └──────────┬────────────────┘
                   ▼
           data_parser.py (reads XLSX / CSV company list)
                   │
                   ▼
         email_generator.py (AI or template)
                   │
          ┌────────┴────────┐
          ▼                 ▼
   email_sender.py    GmailApp (Google Apps Script)
   (ProtonMail)       (google_apps_script/JobSearchAutomation.gs)
          │                 │
          └────────┬────────┘
                   ▼
         Google Sheet + Gmail labels
```

---

## The Two Pipelines

### Pipeline A — Python + ProtonMail (existing)

| Component | File | Status |
|-----------|------|--------|
| GUI launcher | `main_app.py` | ✅ Working |
| Job discovery | `france_travail_client.py` | ✅ Use this (API) |
| Company research (legacy) | `researcher.py` | ⚠️ High bounce rate — replace with API |
| Email generator | `email_generator.py` | ✅ Working (5 AI providers + template) |
| Email sender | `email_sender.py` | ✅ Working (Playwright/ProtonMail) |
| Bulk CLI | `bulk_sender.py` | ✅ Working |

**When to use:** When you want to apply to companies found via France Travail API or an XLSX list, attaching your CV.

**Run it:**
```bash
# Step 1: fetch live jobs from France Travail API
python france_travail_client.py
# Output: france_travail_jobs_974.csv

# Step 2: load the CSV into the GUI
python main_app.py
# Configuration → load france_travail_jobs_974.csv

# Or headless bulk:
python bulk_sender.py --cv /path/to/cv.pdf --companies france_travail_jobs_974.csv --max 50
```

### Pipeline B — Google Apps Script + Gmail (cloud, no computer needed)

| Component | File | Status |
|-----------|------|--------|
| Job search + apply | `google_apps_script/JobSearchAutomation.gs` | ✅ Code complete — deploy once |
| Config | `google_apps_script/appsscript.json` | ✅ Correct |

**When to use:** For fully automated daily job discovery and application without your computer being on.

**One-time setup:**
1. Open a Google Sheet → Extensions → Apps Script
2. Paste the `.gs` file content and `appsscript.json`
3. Run `storeCredentials()` — stores API keys in Script Properties
4. Set `AUTO_SEND: false` in CONFIG (safe default)
5. Run `fetchAndSaveOnly()` first — review jobs without sending
6. When satisfied, run `setupTrigger()` — daily automation starts at 08:00
7. To enable automatic sending: change `AUTO_SEND: true`

---

## AI Provider Decision Tree

```
Do you have an API key?
  ├─ Anthropic key → use 'anthropic' (Claude Haiku — best quality)
  ├─ Mistral key   → use 'mistral' (good quality, EU-based)
  ├─ DeepSeek key  → use 'deepseek' (cheapest)
  └─ No key:
       ├─ Ollama running locally? → use 'ollama' (free, private)
       └─ Nothing → use 'template' (always works, no cost)
```

Set in `.env`:
```
PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
FT_CLIENT_ID=PAR_automationderecherech_...
FT_CLIENT_SECRET=159c4ab554...
```

---

## France Travail API — How It Works

**API Name:** Offres d'emploi v2 + Accès à l'emploi des demandeurs d'emploi v1  
**Auth:** OAuth2 client_credentials  
**Token URL:** `https://entreprise.pole-emploi.fr/connexion/oauth2/access_token`  
**Jobs URL:** `https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search`

**Key search parameters:**
- `motsCles` — keywords (e.g., `formateur anglais`)
- `departement` — department code (974 = La Réunion)
- `typeContrat` — CDI, CDD, MIS, SAI, LIB
- `range` — pagination (e.g., `0-49` for 50 results)

**What comes back per job:**
- `id` — unique job ID
- `intitule` — job title
- `entreprise.nom` — company name
- `lieuTravail.libelle` — city
- `typeContratLibelle` — contract type
- `contact.courriel` — direct email (present on ~20–40% of listings)
- `contact.urlPostulation` — application URL
- `description` — full job description

**To use from Python:**
```python
from france_travail_client import FranceTravailClient
client = FranceTravailClient()  # reads from env vars
jobs = client.get_jobs_with_email(department="974")
client.save_to_csv(jobs, "ft_jobs.csv")
# Load ft_jobs.csv into main_app.py
```

---

## Warm Leads — Current Status (2026-06-12)

| Company | Type | Date | Action |
|---------|------|------|--------|
| **Voscours.fr** | Human invitation to complete application (Professeur d'Anglais, €18–28/hr) | 2026-06-05 | **⚠️ URGENT — complete application at voscours.fr** |
| Intel APAC | Auto-reply, email confirmed | 2026-05-30 | Submit via intel.com/jobs |
| SAP Labs | Auto-reply, email confirmed | 2026-05-30 | Submit via sap.com/careers |
| Pro à Pro | Satisfaction survey (automated) | 2026-06-03, 2026-06-06 | No action required |

---

## In Case of Difficulty

### Token / Authentication Error
**Symptom:** `Token error: {"error":"invalid_client"}`  
**Fix:** Verify credentials in `.env` or GAS Script Properties. Token expires every ~25 min — the client auto-renews.

### High Email Bounce Rate
**Symptom:** Many `Delivery Status Notification (Failure)` in inbox  
**Cause:** Addresses generated by `researcher.py` are guessed and often wrong  
**Fix:** Use `france_travail_client.py` — addresses come directly from official job postings. Remove Section C addresses from your XLSX immediately.

### ProtonMail Playwright Failure
**Symptom:** `Cannot locate username field` or browser fails to compose  
**Fix:** ProtonMail may have updated their UI. Run with `headless=False` to debug. Common selectors:
- Login: `#username`, `#password`
- Compose: `button[data-testid='sidebar:compose']`
- To field: `input[data-testid='composer:to']`
- Body: `iframe[data-testid='rooster-iframe']`

### Google Apps Script Quota Exceeded
**Symptom:** `Service using too many simultaneous invocations`  
**Fix:** Reduce `MAX_PER_QUERY` to 15, add `Utilities.sleep(1000)` between keyword queries, or split the search across two triggers (morning + evening).

**Also:** If `_saveJobToGmail` sends too many self-emails (>100/day), switch to creating drafts instead:
```javascript
// Replace GmailApp.sendEmail(CONFIG.YOUR_EMAIL, ...) with:
GmailApp.createDraft(CONFIG.YOUR_EMAIL, subject, body);
```

### MS365 Group Rejection
**Symptom:** `Your message to the Microsoft 365 group training@... couldn't be delivered`  
**Cause:** Internal distribution list — rejects all external senders  
**Fix:** Remove ALL `training@[bigcorp].com` addresses. Use Section D portal URLs.

### Domain Not Found Bounce
**Symptom:** `because the domain X couldn't be found`  
**Cause:** Address guessed from non-existent or misspelled domain  
**Fix:** Delete from email list immediately. Only use addresses from France Travail API or verified from the company's own website.

### No Jobs Returned from France Travail API
**Symptom:** `Found 0 unique job offers`  
**Fix:** La Réunion (974) may have limited listings. Try:
- Remove the `departement` filter to search all of France
- Try nearby: `971` (Guadeloupe), `972` (Martinique), `973` (Guyane), `976` (Mayotte)
- Try broader keywords: `"anglais"`, `"formateur"`, `"FLE"`, `"langue"`

---

## Email Address Quality Rules

Before adding any email to your campaign list:

| Check | How |
|-------|-----|
| Domain exists | `nslookup domain.com` or browser visit |
| MX record present | `nslookup -type=MX domain.com` |
| Not a distribution group | Avoid `training@bigcorp.com` — use portal |
| Not no-reply | Avoid `noreply@`, `donotreply@` |
| Source is trusted | France Travail API or company `/recrutement` page |

**Reliable sources:**
- France Travail API (`contact.courriel`) ✅
- Company's own `/recrutement` or `/careers` page ✅
- A real human job posting ✅

**Unreliable sources:**
- `training@[largecorp].com` — almost always a distribution group ❌
- `rh@[company]` generated by scraper ❌
- `careers@[country-specific domain]` at multinationals ❌
- Any address with a guessed TLD ❌

---

## Gmail Labels Reference

| Label | ID | Meaning |
|-------|----|--------|
| Campaign/Sent-OK | Label_14 | Sent, no bounce |
| Campaign/Errors | Label_15 | Bounce or failure received |
| Org_CareerApplication | Label_31 | Career application (organised) |
| Org_Letter | Label_28 | Candidature letters (organised) |
| Org_Done | Label_26 | Fully processed |
| Personal/pole emploi | Label_7399566805105625860 | Pôle Emploi messages |
| FT_Jobs (to create) | — | France Travail job saves |

---

## Recommended Daily Workflow

```
08:00  Google Apps Script runs automatically (once deployed)
         → fetches new France Travail jobs for La Réunion
         → logs to Google Sheet (JobTracker)
         → saves each job to Gmail inbox
         → creates Gmail drafts for offers with direct email

09:00  Review Gmail drafts
         → approve / edit / delete before sending
         → check JobTracker sheet for portal-only jobs → apply manually

Weekly  Run france_travail_client.py
         → export to CSV
         → load into main_app.py for CV-attached sends
         → 30–50 companies per session, Section A addresses only
```

---

*Candidate profile: Sourov Deb | Cambridge CELTA 2026 | IELTS/TOEIC Specialist | 18 years in Australia | Saint-Pierre, La Réunion 97410 | 06 93 84 61 68*
