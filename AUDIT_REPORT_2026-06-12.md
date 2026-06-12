# Job Search Automation System — Full Audit Report

**Date:** 2026-06-12  
**Auditor:** Claude AI Agent  
**Repository:** sourovdeb/email_automation  
**Gmail Account:** sourovdeb.is@gmail.com  
**Previous audit:** AUDIT_REPORT_2026-06-11.md

---

## Executive Summary

The system is **operational and significantly improved** since the previous audit (2026-06-11). Both the France Travail API client (`france_travail_client.py`) and the Google Apps Script (`JobSearchAutomation.gs`) are complete in the codebase but have not yet been deployed/run in production. The Python pipeline is working. The main outstanding item is: **a warm lead from Voscours.fr (2026-06-05) requires immediate action.**

One new bounce was detected since the last audit: `recrutement@cned.fr` (550 5.1.1, 2026-06-11). The email list has been updated accordingly.

---

## 1. Script Status

### Python Scripts

| File | Status | Notes |
|------|--------|-------|
| `main_app.py` | ✅ WORKING | PyQt6 GUI, full pipeline, 5 AI providers |
| `france_travail_client.py` | ✅ READY | France Travail OAuth2 client — not yet run, needs `.env` setup |
| `researcher.py` | ⚠️ UNRELIABLE | DuckDuckGo scraping produces guessed emails — 58% bounce rate — replace with API |
| `email_generator.py` | ✅ WORKING | Template + Anthropic/Mistral/DeepSeek/Ollama fallback chain |
| `email_sender.py` | ✅ WORKING | Playwright/ProtonMail automation |
| `bulk_sender.py` | ✅ WORKING | Headless CLI bulk send |
| `data_parser.py` | ✅ WORKING | XLSX + CSV reader with auto-detection |
| `organise_emails.py` | ✅ WORKING | Gmail organisation utility |
| `search_companies.py` | ✅ WORKING | Company finder utility |
| `send_emails.py` | ✅ WORKING | Direct send helper |

**Root issue with researcher.py:** It guesses email patterns like `training@company.com` or `rh@company.fr` for large corporations. These addresses are almost always rejected (distribution groups, internal-only, or simply non-existent). Replace with `france_travail_client.py` which delivers real addresses from official job postings.

### Google Apps Script

| File | Status | Notes |
|------|--------|-------|
| `google_apps_script/JobSearchAutomation.gs` | ✅ CODE COMPLETE — NOT YET DEPLOYED | Created 2026-06-11. Full GAS: France Travail API + Google Sheets + Gmail |
| `google_apps_script/appsscript.json` | ✅ CORRECT | Timezone: Indian/Reunion, all required OAuth scopes present |

**Deployment status:** The script is code-complete and ready. It has never been run. No triggers are active. No previous GAS existed before 2026-06-11 — this is the first Google Apps Script in the project.

**What it does once deployed:**
1. Runs daily at 08:00 (Réunion time)
2. Fetches jobs from France Travail API using 6 keyword queries
3. Logs all new jobs to a Google Sheet (JobTracker tab)
4. Saves each job offer to your Gmail inbox as a labelled email
5. Creates Gmail drafts (or sends directly if `AUTO_SEND: true`) for offers that have a direct contact email
6. Marks applied jobs in the sheet to prevent duplicates
7. Sends you a daily summary email

**Security note:** API credentials are stored as hardcoded fallbacks in `CONFIG`. Run `storeCredentials()` once and then clear the fallback strings from the script. Credentials should live in Script Properties only.

**Known limitation:** The `_saveJobToGmail` function sends a self-email per job, which consumes your Gmail daily sending quota (500/day free tier). If >50 jobs are found per run, consider changing it to create a draft or use a Google Doc instead.

### France Travail API Integration

| Component | Status |
|-----------|--------|
| Python client (`france_travail_client.py`) | ✅ Complete — authenticate, search, extract, save to CSV |
| GAS client (inside `JobSearchAutomation.gs`) | ✅ Complete — same capability, runs in cloud |
| API used in production | ❌ Not yet run |
| Credentials in `.env` | ❌ Not confirmed — add `FT_CLIENT_ID` and `FT_CLIENT_SECRET` |
| Credentials in GAS Script Properties | ❌ Not confirmed — run `storeCredentials()` |

**API details:**
- Endpoint: `https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search`
- Auth: `https://entreprise.pole-emploi.fr/connexion/oauth2/access_token`
- Credentials: see `.env` or AI_AGENT_INSTRUCTIONS.md
- Token expiry: 1490 seconds (~25 min) — auto-renewed by both clients

---

## 2. Email List Quality

### Overall Statistics (as of 2026-06-12)

| Category | Count |
|----------|-------|
| Section A — Keep (verified delivery) | 19 |
| Section B — Corrected addresses | 7 |
| Section C — Remove (hard bounce / rejected) | 45 |
| Section D — Portal only (no email) | 17 |
| Section E — API targets (La Réunion + Indian Ocean) | ~30 |

### New Bounce Since Last Audit (2026-06-11)

| Address | Company | Error | Date | Action |
|---------|---------|-------|------|--------|
| `recrutement@cned.fr` | CNED (Centre National d'Enseignement à Distance) | 550 5.1.1 Address not found | 2026-06-11 | Removed — use cned.fr contact form |

### Bounce Pattern Analysis

**Pattern 1 — Non-existent domain (guessed TLD)**  
Affects: `afparis.org`, `afdakar.org`, `comorestourisme.com`, `cochin.aphp.fr`, `starentertainment.com.au`  
Cause: `researcher.py` guesses `.org` or `.fr` instead of verifying the actual domain  
Fix: Always source emails from France Travail API or the company's own website

**Pattern 2 — Corporate generic addresses (rejected by mail server)**  
Affects: IBM, Oracle, Cisco, EY, HSBC, Michelin, Nokia, BBVA, Siemens, Airbus, PwC, Lloyds, Société Générale, etc.  
Cause: Major corporations route ALL recruitment through ATS portals — `training@ibm.com` and `careers@cisco.com` do not exist  
Fix: Use the portal URLs from Section D — or find the France Travail listing which contains `contact.urlPostulation`

**Pattern 3 — MS365 distribution groups (external sender blocked)**  
Affects: Microsoft, BP, du Telecom UAE, Mashreq Bank, OTP Bank, Cathay Pacific  
Cause: These are internal mailing lists with `AllowExternalSenders: false` in Exchange Online  
Fix: Cannot be fixed. Use portal only.

**Pattern 4 — Temporary server issue → eventual permanent failure**  
Affects: National Geographic Learning (`careers@ngl.cengage.com`), PwC (`training@pwc.co.uk`), Lloyds, Siemens ES, Airbus ES, Safran  
Cause: Some MX servers are misconfigured or have greylisting that eventually rejects  
Fix: If you receive a delay notification, wait 72h. If still failing, treat as hard bounce.

**Pattern 5 — Address exists but company requires portal**  
Affects: SAP (`careers@sap.com`) — delivered but auto-reply redirects to portal  
Fix: Treat as portal-only. Your email was received but will likely be ignored. Use the portal.

### Addresses That Work (Section A)
The 19 kept addresses span: Indian Ocean universities and institutions, aviation (ANZ, Qantas, flydubai, ADNOC, Saudi Aramco), education publishers (Macmillan, Cambridge ELT), tech with open inboxes (Intel, SAP), and hospitality (Hilton, Shell, Unilever).

---

## 3. Application Audit Findings (Gmail)

### Volume Overview (last 6 months)

| Metric | Count | Notes |
|--------|-------|-------|
| Applications sent | ~210 | Confirmed via SENT folder |
| Hard bounces (550/554) | ~43 | All logged above |
| MS365 rejections | 6 | Separate error type |
| Delay → failure (72h retry) | ~8 | PwC, Lloyds, Siemens, Airbus, Safran, NGL |
| Auto-replies confirming receipt | 3 | Intel, SAP, CNED (but CNED bounced on 2nd send) |
| Human/warm responses | 2 | Pro à Pro (survey x2), Voscours.fr |
| Pending warm leads | 1 | Voscours.fr — ACTION REQUIRED |

### Warm Leads — Status

| Company | Signal | Date | Status |
|---------|--------|------|--------|
| **Voscours.fr** | Invitation to finalize candidature (Professeur d'Anglais, €18–28/hr, remote possible) | 2026-06-05 | ⚠️ ACTION REQUIRED — check inbox and complete application |
| Pro à Pro | Post-application satisfaction survey sent twice | 2026-06-03, 2026-06-06 | Neutral — automated survey, not a human reply |
| Intel APAC | Auto-reply: email received, apply via portal | 2026-05-30 | Noted — submit via intel.com/jobs |
| SAP Labs | Auto-reply: email received, apply via portal | 2026-05-30 | Noted — submit via sap.com/careers |

### Unread Bounce Notifications (inbox clutter)

The following bounce notifications are currently **UNREAD** in your inbox. They require no action (addresses already in Section C) but should be archived:

- Université des Mascareignes → `contact@univ-mascareignes.org`
- Commonwealth Bank AU → `training@cba.com.au`
- Oxford University Press → `eltjobs@oup.com`
- Google UAE → `careers@google.ae`
- Cisco Middle East → `careers@cisco.com`
- Emaar Properties → `careers@emaar.com`
- Emirates NBD → `training@emiratesnbd.com`
- Singapore Airlines → `training@singaporeair.com`
- Nokia APAC → `careers@nokia.com`
- Google Thailand → `careers@google.co.th`
- OTP Bank Hungary → `training@otpbank.hu`
- Heathrow Airport → `careers@heathrow.com`
- CNED → `recrutement@cned.fr` ← NEW (2026-06-11)

**Recommended Gmail filter** to auto-archive future bounces:
```
From: (mailer-daemon@googlemail.com OR mailer-daemon)
Subject: (Delivery Status Notification OR Undeliverable)
→ Skip Inbox, Apply label: Campaign/Errors
```

---

## 4. API Integration Summary

### Current State

| Component | Status | Gap |
|-----------|--------|-----|
| `france_travail_client.py` | ✅ Code complete | Needs `.env` with credentials |
| `JobSearchAutomation.gs` | ✅ Code complete | Needs GAS deployment + `storeCredentials()` + `setupTrigger()` |
| `researcher.py` | ⚠️ Active but unreliable | Should be replaced by API for job discovery |
| Production API calls | ❌ Zero | Neither client has been run yet |

### What the France Travail API Returns

For each job offer:
- `id` — unique offer ID (used for deduplication)
- `intitule` — job title
- `entreprise.nom` — company name  
- `lieuTravail.libelle` — city/location
- `typeContratLibelle` — CDI / CDD / interim / etc.
- `contact.courriel` — **direct email** (present on ~20–40% of listings)
- `contact.urlPostulation` — application portal URL
- `contact.telephone` — phone number
- `description` — full job description (up to 4000 chars)

Only ~20–40% of La Réunion listings include a direct email. The rest have portal URLs. The GAS script handles both: email → draft/send; portal URL → saved in the Sheet for manual application.

### Test Command (Python)

```bash
# Create .env first:
echo "FT_CLIENT_ID=PAR_automationderecherech_72d2b44113ac287b9c4cb540958e31ff2b95695fabec41ce3580d057a753c346" >> .env
echo "FT_CLIENT_SECRET=159c4ab554143db7f6d45638628c8a47bcbf9f52ac2efb9beedd3815c4b472ca" >> .env

# Run the client:
python france_travail_client.py
# Expected output: list of formateur anglais jobs in La Réunion with direct emails
# Saves: france_travail_jobs_974.csv
```

---

## 5. Recommended Next Steps (Priority Order)

### URGENT (today)

**1. Voscours.fr warm lead — complete your application**
Check your inbox for the email from `info@voscours.fr` dated 2026-06-05 subject "Sourov, finalicez votre candidature". This is a real human invitation, not automated. Complete it now.

### This week

**2. First run of the France Travail API (Python)**
```bash
python france_travail_client.py
```
This will show you what actual jobs with real emails are available in La Réunion right now. Load the output CSV into `main_app.py` and send your next batch from real addresses only.

**3. Deploy the Google Apps Script**
- Open a Google Sheet
- Extensions → Apps Script → paste `JobSearchAutomation.gs` + `appsscript.json`
- Run `storeCredentials()` once
- Set `AUTO_SEND: false`
- Run `fetchAndSaveOnly()` first to review jobs without sending
- Once satisfied, run `setupTrigger()` for daily automation at 08:00

**4. Purge Section C addresses from your XLSX**
Remove all 45 hard-bounce addresses. They damage your Gmail sender reputation (spam score). Use only Section A + Section B (corrected) + addresses from France Travail API.

**5. Set up Gmail bounce filter**
```
From: mailer-daemon@googlemail.com  
→ Skip Inbox, Apply label: Campaign/Errors, Mark as read
```
This stops bounce notifications cluttering your inbox.

### Next two weeks

**6. Expand France Travail search to other DOM-TOM**
Add departments: `971` (Guadeloupe), `972` (Martinique), `973` (Guyane), `976` (Mayotte) — same legal context, same OPCO funding rules, French language market.

**7. Add follow-up for Section A addresses**
For the 19 delivered-but-no-reply addresses, send a polite follow-up after 2 weeks:
```
Subject: Suivi — Candidature Formateur Anglais CELTA — [Company]
Body: Brief 3-line reminder. No attachments.
```

**8. Fix AP-HP address**
Resend to `formation@aphp.fr` (corrected from `formation@cochin.aphp.fr` which bounced). AP-HP is a high-value target for medical English training.

### Medium term

**9. Add `FT_Jobs` Gmail label** to auto-categorise saved France Travail offers.

**10. Disable `researcher.py` as the primary job discovery tool.** Only use it for manual lookup when you have a specific company in mind and want to verify their email. Use the France Travail API as the primary source.

**11. Consider adding CV attachment to GAS emails.** Currently `JobSearchAutomation.gs` sends text-only emails. GmailApp supports `attachments` via `DriveApp.getFileById()`. Store your CV PDF in Google Drive and pass its ID to the send function for a more complete application.

---

## Appendix — Script File Index

| File | Purpose | Pipeline |
|------|---------|----------|
| `main_app.py` | PyQt6 GUI launcher | A |
| `france_travail_client.py` | France Travail API job fetcher | A + B |
| `researcher.py` | Web scraper (legacy) | A (deprecated) |
| `email_generator.py` | AI email writer | A |
| `email_sender.py` | ProtonMail sender | A |
| `bulk_sender.py` | Headless bulk send CLI | A |
| `data_parser.py` | XLSX/CSV reader | A |
| `organise_emails.py` | Gmail organisation | A |
| `search_companies.py` | Company finder | A |
| `send_emails.py` | Direct send utility | A |
| `google_apps_script/JobSearchAutomation.gs` | GAS: API + Sheets + Gmail | B |
| `google_apps_script/appsscript.json` | GAS manifest | B |
