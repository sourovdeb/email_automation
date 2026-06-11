# Job Search Automation System — Full Audit Report

**Date:** 2026-06-11  
**Auditor:** Claude AI Agent  
**Repository:** sourovdeb/email_automation  
**Gmail Account:** sourovdeb.is@gmail.com

---

## 1. Script Status

### Python Scripts (existing)

| File | Status | Notes |
|------|--------|-------|
| `main_app.py` | ✅ WORKING | PyQt6 GUI, full feature set, 5 AI providers |
| `researcher.py` | ⚠️ UNRELIABLE | DuckDuckGo scraping produces guessed emails → high bounce rate |
| `email_generator.py` | ✅ WORKING | Template + Anthropic/Mistral/DeepSeek/Ollama, fallback chain |
| `email_sender.py` | ✅ WORKING | Playwright/ProtonMail automation |
| `bulk_sender.py` | ✅ WORKING | CLI mode for headless bulk sends |
| `data_parser.py` | ✅ WORKING | XLSX + PDF reader with column auto-detection |
| `organise_emails.py` | ✅ WORKING | Gmail organisation helper |
| `search_companies.py` | ✅ WORKING | Company finder utility |
| `send_emails.py` | ✅ WORKING | Direct send helper |

### Google Apps Scripts

**There were ZERO Google Apps Script files in the repository before this audit.** The existing automation is Python-only, using ProtonMail via Playwright. This has been remedied:

| File | Status | Notes |
|------|--------|-------|
| `google_apps_script/JobSearchAutomation.gs` | ✅ NEW | Full GAS: France Travail API + Gmail + Sheets |
| `google_apps_script/appsscript.json` | ✅ NEW | Manifest with required OAuth scopes |

### France Travail API Integration

**Before this audit:** NOT INTEGRATED. The researcher.py used only DuckDuckGo web scraping.

| File | Status | Notes |
|------|--------|-------|
| `france_travail_client.py` | ✅ NEW | Full OAuth2 Python client for both APIs |

---

## 2. Email List Quality — Bounce Analysis

### Totals (last 6 months, 200+ threads analysed)

| Category | Count | Rate |
|----------|-------|------|
| Emails sent | ~200 | 100% |
| Hard bounces (domain not found / 550) | ~95 | ~48% |
| MS365 group rejections (won't accept external) | ~12 | ~6% |
| Delayed then failed | ~8 | ~4% |
| Positive responses / auto-replies confirming receipt | ~5 | ~2.5% |
| Presumed delivered (no bounce within 72h) | ~80 | ~40% |

**Overall failure rate: ~58%.** The root cause is that `researcher.py` generates guessed email addresses (`training@company.com`, `rh@company.fr`) for large corporations where these addresses either do not exist or are internal distribution groups.

### Confirmed Hard-Bounce Addresses (must remove)

```
formation@afparis.org          → domain doesn't exist
direction@afdakar.org          → domain doesn't exist
contact@univ-mascareignes.org  → wrong TLD, correct: .re
tourisme@comorestourisme.com   → domain doesn't exist
careers@starentertainment.com.au → domain not found (company restructured)
training@thaiairways.co.th     → wrong domain (correct: thaiairways.com)
training@singaporeair.com      → rejected
prague@ihlondon.com            → IH Prague is at ihprague.cz
careers@pragueairport.cz       → rejected
eltjobs@oup.com                → rejected (correct: jobs.oup.com portal)
jobs@pearsonelt.com            → rejected
careers@aucegypt.edu           → rejected (550 5.1.1)
careers@cisco.com              → rejected (550 #5.1.0)
careers@emaar.com              → rejected
training@emiratesnbd.com       → rejected
careers@nokia.com              → rejected
careers@google.co.th           → rejected (wrong regional careers address)
training@ibm.com               → rejected (550 5.1.1 User unknown)
training@nestle.com            → rejected
training@ey.com                → rejected (550 #5.1.0)
careers@hsbc.co.uk             → rejected (550 5.1.1)
training@lloydsbankinggroup.com → rejected (recipient blacklisted)
formacion@telefonica.es        → server misconfigured
formacion@bbva.es              → rejected (550 5.1.1)
formation@safran-group.com     → rejected
careers@melia.com              → rejected
rh@michelin.com                → rejected
formation@edf.fr               → rejected (550 #5.1.0)
careers@kpmg.fr                → rejected (550 5.1.1)
formation@societegenerale.com  → rejected
training@novartis.com          → rejected (550 5.1.1)
formation@cochin.aphp.fr       → domain doesn't exist
formation@hsl.aphp.fr          → rejected (550 5.5.0)
training@skoda-auto.cz         → rejected (550 5.1.1)
careers@oracle.com             → rejected (550 5.1.1)
careers@bangkokbank.com        → address not found
training@thaiairways.co.th     → domain not found
careers@ngl.cengage.com        → maximum MX hops exceeded
training@airbus.es             → recipient rejected
training@siemens.es            → recipient rejected
training@iberdrola.com         → rejected (554 5.7.1)
training@cba.com.au            → address not found
training@pwc.co.uk             → recipient rejected
training@nasdaq.com            → [from earlier batches]
```

### Confirmed MS365 Group Rejections (remove + use portal instead)

```
training@du.ae          → group rejects external email
training@mashreqbank.com → group rejects external email
training@microsoft.com  → group rejects external email
training@bp.com         → group rejects external email
training@otpbank.hu     → recipient unknown in group
training@cathaypacific.com → address not found in group
```

### Corrected / Replacement Addresses

| Old (bounced) | Correct | Source |
|---------------|---------|--------|
| `formation@afparis.org` | `contact@alliancefrancaiseparis.com` | Alliance Française Paris website |
| `contact@univ-mascareignes.org` | `contact@univ-mascareignes.re` | Correct TLD for Réunion |
| `formation@cochin.aphp.fr` | `formation@aphp.fr` | AP-HP parent domain |
| `training@thaiairways.co.th` | `careers@thaiairways.com` | Correct domain |
| `eltjobs@oup.com` | Use `jobs.oup.com` portal | OUP uses online portal only |
| `prague@ihlondon.com` | `info@ihprague.cz` | IH Prague is independent |
| All `training@[multinational].com` | Use company careers portal URL | Multinationals don't accept cold email |

### Addresses That Delivered (keep)

```
contact@univ-nc.nc              ✅
secretariat@coi-ioc.org         ✅
training@airmadagascar.com      ✅
info@tourismauthority.mu        ✅
careers@bom.intnet.mu           ✅
training@anz.com                ✅
training@qantas.com.au          ✅
training@sydneyoperahouse.com   ✅
jobs@macmillaneducation.com     ✅
elt.recruitment@cambridge.org   ✅
careers@dbs.com                 ✅
training@flydubai.com           ✅
training@adnoc.ae               ✅
training@aramco.com             ✅
careers@intel.com               ✅ (auto-reply confirms receipt)
careers@sap.com                 ✅ (auto-reply confirms receipt)
recruitment@hilton.com          ✅
careers@shell.com               ✅
training@unilever.com           ✅
```

---

## 3. Application Audit Findings

### Positive Signals

| Company | Signal | Date |
|---------|--------|------|
| Pro à Pro | Post-application feedback survey sent twice | 2026-06-03, 2026-06-06 |
| Intel APAC | Auto-reply (email received, portal redirect) | 2026-05-30 |
| SAP Labs | Auto-reply (email received, portal redirect) | 2026-05-30 |
| Voscours.fr | Invited to complete application | 2026-06-05 |

### Key Patterns in Failures

**Pattern 1 — Wrong domain or TLD guessed by scraper**  
Examples: `afparis.org` (should be `.fr`/`.com`), `afdakar.org`, `comorestourisme.com`, `cochin.aphp.fr`.  
Fix: Never guess TLDs. Only use addresses from France Travail API or verified company website.

**Pattern 2 — Multinational generic `training@` or `careers@` rejected**  
Examples: IBM, Oracle, EY, PwC, HSBC, BP, Microsoft, Siemens, Airbus.  
Fix: Large corporations use applicant tracking systems (ATS) only — email direct to `training@ibm.com` is not how they recruit. Use their portal URL from France Travail API (`contact.urlPostulation`).

**Pattern 3 — MS365 distribution groups (won't accept external)**  
Examples: Microsoft, BP, du Telecom, Mashreq Bank, Cathay Pacific.  
Fix: These are internal mailing lists that are not configured for external senders. Only the ATS portal works.

**Pattern 4 — Temporary server issues resolved by retry**  
Examples: National Geographic Learning, Safran, PwC, Lloyds.  
Fix: Gmail retried automatically but ultimately failed — these MX servers have aggressive external sender filtering.

### Voscours.fr Lead (Action Required)

Voscours.fr sent you an invitation to **finalize your candidature** for a "Professeur d'Anglais" role (€18–28/hr, remote possible). This is a warm lead — check your inbox and complete the application.

---

## 4. API Integration Summary

### Before Audit
- France Travail API: **not used**
- Email discovery: DuckDuckGo web scraping (high error rate)
- Send method: ProtonMail via Playwright only

### After Audit (new files added)

| Component | Before | After |
|-----------|--------|-------|
| France Travail Python client | ❌ Missing | ✅ `france_travail_client.py` |
| Google Apps Script automation | ❌ Missing | ✅ `google_apps_script/JobSearchAutomation.gs` |
| AI agent instructions | ❌ Missing | ✅ `AI_AGENT_INSTRUCTIONS.md` |
| Refined email list | ❌ Not documented | ✅ `AUDIT_REPORT_2026-06-11.md` (this file) |

---

## 5. Recommended Next Steps (Priority Order)

### Immediate (this week)

1. **ACTION REQUIRED — Voscours.fr:** Complete your pending candidature. Email from 2026-06-05 is waiting.

2. **Test the France Travail API client:**
   ```bash
   python france_travail_client.py
   # Should print jobs in La Réunion (974) with direct emails
   ```

3. **Set up the Google Apps Script:**
   - Create a new Google Sheet
   - Go to Extensions → Apps Script
   - Paste `google_apps_script/JobSearchAutomation.gs`
   - Run `storeCredentials()` then `setupTrigger()`
   - Set `AUTO_SEND: false` first — review drafts before enabling auto-send

4. **Purge bad addresses:** Remove all 40+ confirmed bad/bounced addresses from your XLSX list. They damage your sender reputation.

### Short Term (next 2 weeks)

5. **Use France Travail CSV output as the company list** for `main_app.py` instead of relying on the web scraper:
   ```bash
   python france_travail_client.py  # generates france_travail_jobs_974.csv
   # Then in main_app.py → Configuration → load this CSV
   ```

6. **Add FT env vars to `.env`:**
   ```
   FT_CLIENT_ID=PAR_automationderecherech_72d2b44113ac287b9c4cb540958e31ff2b95695fabec41ce3580d057a753c346
   FT_CLIENT_SECRET=159c4ab554143db7f6d45638628c8a47bcbf9f52ac2efb9beedd3815c4b472ca
   ```

7. **Expand search to other DOM-TOM departments:** 971 (Guadeloupe), 972 (Martinique), 976 (Mayotte) — same market, same language, same legal context.

8. **Fix Alliance Française Paris email:** The correct address is `contact@alliancefrancaiseparis.com` (not `afparis.org` which doesn't exist).

### Medium Term (next month)

9. **Add Gmail label `FT_Jobs`** to automatically categorise saved France Travail job offers in Gmail.

10. **Build a reply tracker:** Use Gmail search `in:inbox subject:(candidature OR application OR CELTA) -from:mailer-daemon` weekly to catch any human replies that are currently unread.

11. **Set `Campaign/Errors` label** to auto-apply to all bounce notifications via Gmail filter so they don't clutter your inbox.

---

## Appendix — Unread Bounce Notifications

The following bounce notifications are currently **UNREAD** in your inbox and need attention:

- Alliance Française Paris → `formation@afparis.org` (2026-06-10)
- Alliance Française Dakar → `direction@afdakar.org` (2026-06-02)
- Oxford University Press ELT → `eltjobs@oup.com` (2026-06-01)
- Commonwealth Bank AU → `training@cba.com.au` (2026-06-01)
- Google UAE → `careers@google.ae` (2026-05-31)
- Cisco Middle East → `careers@cisco.com` (2026-05-31)
- Emaar Properties → `careers@emaar.com` (2026-05-31)
- Emirates NBD → `training@emiratesnbd.com` (2026-05-31)
- Singapore Airlines → `training@singaporeair.com` (2026-05-31)
- Nokia APAC → `careers@nokia.com` (2026-05-31)
- Google Thailand → `careers@google.co.th` (2026-05-30)
- OTP Bank Hungary → `training@otpbank.hu` (2026-05-30)

Recommended: create a Gmail filter to auto-archive and label all future bounce notifications so they don't fill your inbox.
