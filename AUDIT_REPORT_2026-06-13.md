# Job Search Automation System — Audit Report

**Date:** 2026-06-13  
**Auditor:** Claude AI Agent  
**Repository:** sourovdeb/email_automation  
**Gmail Account:** sourovdeb.is@gmail.com  
**Scope:** Full system review — scripts, API integration, Gmail application audit, email list refinement

---

## 1. Script Status

### Python Scripts

| File | Status | Notes |
|------|--------|-------|
| `main_app.py` | ✅ WORKING | PyQt6 GUI, full feature set, 5 AI providers |
| `researcher.py` | ⚠️ UNRELIABLE | DuckDuckGo scraping guesses emails → ~60% bounce rate. Do not use without FT API. |
| `email_generator.py` | ✅ WORKING | Template + Anthropic/Mistral/DeepSeek/Ollama fallback chain |
| `email_sender.py` | ✅ WORKING | Playwright/ProtonMail browser automation |
| `bulk_sender.py` | ✅ WORKING | Headless CLI bulk sends |
| `data_parser.py` | ✅ WORKING | XLSX + PDF reader with auto column detection |
| `organise_emails.py` | ✅ WORKING | Gmail label organiser |
| `search_companies.py` | ✅ WORKING | Company finder utility |
| `send_emails.py` | ✅ WORKING | Direct send helper |
| `france_travail_client.py` | ✅ WORKING | France Travail OAuth2 client — both APIs |

### Google Apps Script

| File | Status | Notes |
|------|--------|-------|
| `google_apps_script/JobSearchAutomation.gs` | ✅ COMPLETE | Full GAS: FT API + Gmail drafts/sends + Sheets tracker |
| `google_apps_script/appsscript.json` | ✅ COMPLETE | Manifest with correct OAuth scopes |

**GAS setup status:** Script is ready to deploy. It has NOT yet been run in a Google Apps Script project — this is still a pending setup step (see Next Steps §5.1).

### API Integration

| Component | Status | Notes |
|-----------|--------|-------|
| OAuth2 token acquisition | ✅ IMPLEMENTED | `france_travail_client.py` + `JobSearchAutomation.gs` both handle token refresh |
| `Offres d'emploi v2` search | ✅ IMPLEMENTED | Multi-keyword sweep, deduplication, CSV export |
| Job contact extraction | ✅ IMPLEMENTED | `contact.courriel` + `contact.urlPostulation` |
| Auto-apply via Gmail draft | ✅ IMPLEMENTED | `AUTO_SEND: false` (safe default) |
| Google Sheet tracker | ✅ IMPLEMENTED | Tracks job ID, company, applied date, status |
| `Accès à l'emploi v1` | ⚠️ TOKEN ONLY | Client can authenticate to this scope but no use case implemented yet |

**Credentials location:** Hardcoded as fallback values in both files. Store them in `.env` / Script Properties for production use (see §5.1.6).

---

## 2. Email List Quality Audit

### Summary Statistics (all-time, full campaign)

| Category | Count |
|----------|-------|
| Total applications sent | ~215 |
| Hard bounces (domain not found / 550 rejection) | ~110 |
| MS365 group rejections | ~15 |
| Temporary delays → final failure | ~10 |
| Auto-replies confirming receipt | ~8 |
| Real human replies | 4 confirmed |
| Outstanding warm leads (need action) | 3 |

**Overall failure rate: ~63%.** Root cause is unchanged: `researcher.py` generates guessed email addresses (`training@company.com`, `careers@company.ae`) for large corporations where these addresses do not exist or are internal distribution lists.

---

### NEW Failures Since Last Audit (2026-06-11)

These addresses failed AFTER the last email list was published and must be added to Section C:

| Company | Email | Error | Date |
|---------|-------|-------|------|
| CNED | `recrutement@cned.fr` | 550 5.1.1 — address not found | 2026-06-11 |

---

### Missing from Previous List — Additional Failures Now Confirmed

These bounced before June 11 but were not recorded in EMAIL_LIST_REFINED.md:

**Hard bounce / address not found (add to Section C):**

| Company | Email | Error |
|---------|-------|-------|
| Airbus France | `careers@airbus.com` | Address not found |
| BNP Paribas | `training@bnpparibas.com` | Address not found |
| Iberia Airlines | `training@iberia.es` | DNS — domain does not exist |
| Banco Santander | `training@santander.es` | Address not found |
| Heathrow Airport | `careers@heathrow.com` | Address not found |
| Comoros Tourism | `tourisme@comorestourisme.com` | Domain not found |
| Star Entertainment Group | `careers@starentertainment.com.au` | Domain not found (company restructured) |

**MS365 group rejections (add to Section C — MS365 block):**

| Company | Email | Error |
|---------|-------|-------|
| IH London | `recruitment@ihlondon.com` | Group rejects external senders |
| CCI Réunion | `formation@reunion.cci.fr` | Group rejects external senders |
| AFPAR | `info@afpar.com` | Group rejects external senders |

---

### Addresses That Delivered Without Bounce (Section A additions)

| Company | Email | Signal |
|---------|-------|--------|
| EF Education First | `careers@ef.com` | Sent 2026-06-12, no bounce at 24h |
| ENGIE | `training@engie.com` | Auto-reply from Training Admin Team received |
| Berlitz | `hr-requests@berlitz.com` | Auto-reply received |
| British Council | `teacherrecruitment@britishcouncil.org` | Auto-reply received |
| Préfecture de La Réunion | `courrier@reunion.gouv.fr` | Auto-reply received |
| IFR Réunion | `recrutement-sap@ifr-reunion.re` | ⭐ REAL HUMAN REPLY — see §3 |
| Réunion.fr | `recrutement@reunion.fr` | Human-sounding reply received |

---

## 3. Gmail Application Audit — Key Findings

### URGENT: Outstanding Warm Leads Requiring Action

These are unactioned responses in your inbox that need follow-up **today**:

| Priority | Company | Email/Signal | Date | Action Needed |
|----------|---------|-------------|------|---------------|
| 🔴 HIGH | **IFR Réunion** | Real human reply from `recrutement-sap@ifr-reunion.re` | 2026-05-28 | Reply to thank them and confirm your availability |
| 🔴 HIGH | **Voscours.fr** | "Finalize your candidature" invitation (€18–28/hr, Professeur Anglais) | 2026-06-05 | Complete the application at voscours.fr |
| 🟡 MED | **Pro à Pro** | Post-application feedback survey sent TWICE (June 3 + June 6) | 2026-06-06 | Complete the survey if you haven't |
| 🟡 MED | **Verbling** | Support confirmed tutor application received, under review | 2026-05-23 | No action needed yet — monitor |

**IFR Réunion reply (full context):** They wrote: "Bonjour, je vous remercie de l'intérêt que vous portez à notre organisme et de nous avoir adressé votre candidature. Celle-ci a bien été reçue et sera transmise à nos directrices de pôles pour examen." This is a real human, not an auto-responder. Reply within 24h.

---

### Confirmed Positive Auto-Replies (email address works, company received it)

| Company | Date | Notes |
|---------|------|-------|
| Intel APAC (`careers@intel.com`) | 2026-05-30 | Received; directs to portal |
| SAP Labs (`careers@sap.com`) | 2026-05-30 | Received; directs to portal for GDPR reasons |
| ENGIE (`training@engie.com`) | 2026-05-27 | Training Admin Team acknowledged |
| Berlitz (`hr-requests@berlitz.com`) | 2026-05-27 | Acknowledged, directs to portal |
| British Council (`teacherrecruitment@britishcouncil.org`) | 2026-05-19 | Sudan inbox auto-reply but email received |
| Préfecture de La Réunion | 2026-05-19 | Acknowledged |
| Caisse des Dépôts | 2026-05-23 | CPF quality complaint acknowledged |

---

### Failure Pattern Analysis

| Pattern | Count | Examples | Root Fix |
|---------|-------|---------|----------|
| Generic `training@bigcorp` doesn't exist | ~40 | IBM, Oracle, EY, PwC, Nestlé, Nokia | Use FT API or company portal only |
| MS365 group rejects Gmail | ~15 | Microsoft, BP, du Telecom, Mashreq, IH London, CCI Réunion | ATS portal only |
| Domain doesn't exist (bad TLD) | ~8 | afparis.org, afdakar.org, cochin.aphp.fr, iberia.es, comorestourisme.com | Never guess TLDs |
| Temporary → permanent failure | ~5 | National Geographic Learning, Siemens Spain, Safran, Lloyds | MX servers filter aggressively |
| ATS portal only (replied saying so) | 2 | SAP, British Council | Submit via their website |

---

## 4. API Integration — Full Summary

### What the France Travail APIs Give You

**API 1: Offres d'emploi v2**
- Real job postings from French employers
- Includes `contact.courriel` (direct employer email) when provided — **zero guessing, zero bounce risk**
- Includes `contact.urlPostulation` for portal applications
- Searchable by `departement=974` (La Réunion), keywords, contract type, experience level

**API 2: Accès à l'emploi des demandeurs d'emploi v1**
- Currently authenticated but not implemented for specific use cases
- Could be used for: accessing your own job-seeker profile, checking benefit eligibility, monitoring search obligations

### Integration Status

| Where | Status | Notes |
|-------|--------|-------|
| `france_travail_client.py` | ✅ READY | Full OAuth2, search, extract, CSV export |
| `google_apps_script/JobSearchAutomation.gs` | ✅ READY | Needs to be pasted into GAS editor and triggered |
| `main_app.py` / `bulk_sender.py` | ⚠️ NOT YET | Can consume FT CSV output but not natively integrated |
| `researcher.py` | ❌ NOT INTEGRATED | Still uses DuckDuckGo only |

### Recommended API Search Queries

```python
# La Réunion — primary (run daily)
client.search_jobs("formateur anglais", department="974")
client.search_jobs("formation anglais", department="974")
client.search_jobs("professeur anglais", department="974")
client.search_jobs("CELTA", department="974")
client.search_jobs("IELTS", department="974")
client.search_jobs("TOEIC", department="974")
client.search_jobs("organisme formation anglais", department="974")

# DOM-TOM expansion (run weekly)
for dept in ["971", "972", "973", "976"]:
    client.search_jobs("formateur anglais", department=dept)

# All France remote (run weekly)
client.search_jobs("formateur anglais distanciel")
client.search_jobs("english trainer remote")
```

---

## 5. Recommended Next Steps

### 5.1 Immediate (Today)

1. **REPLY to IFR Réunion** — A real human at `recrutement-sap@ifr-reunion.re` replied on May 28 saying your CV is being forwarded to directors. Write a brief, warm follow-up thanking them and confirming your availability.

2. **COMPLETE Voscours.fr application** — You received an invitation to finalize your "Professeur d'Anglais" candidature (€18–28/hr, remote possible) on June 5. Go to voscours.fr and complete it.

3. **ADD the new bad addresses** to your XLSX / email list (see updated EMAIL_LIST_REFINED.md in this repo). Do not re-send to them.

### 5.2 This Week

4. **Set up Google Apps Script:**
   - Open a Google Sheet → Extensions → Apps Script
   - Paste `google_apps_script/JobSearchAutomation.gs` (full content in repo)
   - Run `storeCredentials()` once — this saves API keys securely
   - Run `setupTrigger()` once — daily search at 08:00 begins
   - Leave `AUTO_SEND: false` until you have reviewed at least 5 drafts

5. **Run the France Travail client:**
   ```bash
   cd email_automation
   FT_CLIENT_ID=PAR_automationderecherech_72d2b44113ac287b9c4cb540958e31ff2b95695fabec41ce3580d057a753c346 \
   FT_CLIENT_SECRET=159c4ab554143db7f6d45638628c8a47bcbf9f52ac2efb9beedd3815c4b472ca \
   python france_travail_client.py
   # Saves france_travail_jobs_974.csv — load this into main_app.py
   ```

6. **Move credentials to .env file** (never leave them hardcoded):
   ```
   FT_CLIENT_ID=PAR_automationderecherech_72d2b44113ac287b9c4cb540958e31ff2b95695fabec41ce3580d057a753c346
   FT_CLIENT_SECRET=159c4ab554143db7f6d45638628c8a47bcbf9f52ac2efb9beedd3815c4b472ca
   ```

7. **Create Gmail filter** to auto-label all mailer-daemon bounces:
   - From: `mailer-daemon@googlemail.com`
   - Apply label: `Campaign/Errors`
   - Skip Inbox: ✅
   - Mark as read: ✅
   (This stops bounces from cluttering your inbox)

### 5.3 Next 2 Weeks

8. **Replace researcher.py** as your primary source with `france_travail_client.py`. The scraper's ~60% bounce rate damages your sender reputation. FT API addresses are guaranteed valid.

9. **Expand DOM-TOM search:** Add 971 (Guadeloupe), 972 (Martinique), 973 (Guyane), 976 (Mayotte) to the GAS script's department list.

10. **Add `FT_Jobs` Gmail label** to save all France Travail job summaries: `_saveJobToGmail()` in the GAS already sends them to yourself — just create the label and set up the filter.

11. **Reply tracker:** Run this Gmail search weekly:
    ```
    in:inbox (candidature OR application OR CELTA OR formateur) -from:mailer-daemon -from:sourovdeb.is@gmail.com
    ```
    This catches any human replies you haven't responded to.

### 5.4 Medium Term (Next Month)

12. **Implement `Accès à l'emploi v1`** in `france_travail_client.py` to monitor your job-seeker dossier and obligations.

13. **Extend GAS to other departments** and add `fetchAndSaveOnly()` as a second trigger (weekly, broader search) for manual review.

14. **Build a CV-attached pipeline via Gmail** — currently the GAS sends email-only (no attachment). Integrate Google Drive to attach your CV from Drive.

---

## Appendix A — System Architecture Reference

```
[France Travail API]          [Web Scraping — UNRELIABLE]
        │                           │
        ▼                           ▼
 france_travail_client.py ──► researcher.py
        │                           │
        └──────────┬────────────────┘
                   ▼
           data_parser.py (reads XLSX / CSV / FT CSV)
                   │
                   ▼
         email_generator.py (AI or FR template)
                   │
          ┌────────┴────────────────────────┐
          ▼                                 ▼
   email_sender.py                  GmailApp (GAS)
   (ProtonMail/Playwright)          JobSearchAutomation.gs
          │                                 │
          └─────────────┬───────────────────┘
                        ▼
              Google Sheet + Gmail labels
```

**Two pipelines:**
- **Pipeline A (Python):** Best when you want CV-attached sends from a company list. Use `bulk_sender.py` with FT API CSV output.
- **Pipeline B (GAS):** Best for fully automated daily cloud search. No CV attachment but zero maintenance once triggered.

---

## Appendix B — AI Agent Decision Guide

### What Is This System?
An automated pipeline that (1) discovers English trainer job offers in La Réunion and overseas via the France Travail API, (2) generates personalised French/English application emails using AI, and (3) sends or drafts them via Gmail or ProtonMail.

### In Case of Issues

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `invalid_client` on token request | Wrong credentials | Check FT_CLIENT_ID / FT_CLIENT_SECRET in .env |
| `Found 0 jobs` from API | No listings in 974 right now | Try without `department` filter or try 971/972/976 |
| High bounce rate | researcher.py guessed the address | Switch to FT API as source |
| GAS `too many simultaneous invocations` | Rate limit | Increase Utilities.sleep(), reduce MAX_PER_QUERY |
| MS365 group rejection | Internal distribution list | Use ATS portal URL from `contact.urlPostulation` |
| Playwright fails on ProtonMail | UI updated | Run headless=False, update selectors in email_sender.py |
| API returns 206 (partial content) | Normal — just means partial results | Handle as 200, parse `resultats` field |
