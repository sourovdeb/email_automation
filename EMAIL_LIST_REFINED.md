# Email List — Refined & Verified

> Last updated: 2026-06-12 | Based on bounce analysis of 200+ sent applications

---

## Section A — KEEP (Delivered Successfully, No Bounce)

These addresses accepted delivery. Maintain and follow up if no response after 2 weeks.

| Company | Email | Category | Notes |
|---------|-------|----------|-------|
| Université Nouvelle-Calédonie | contact@univ-nc.nc | Academic | No bounce |
| Commission Océan Indien (COI) | secretariat@coi-ioc.org | Institution | No bounce |
| Air Madagascar | training@airmadagascar.com | Aviation | No bounce |
| Mauritius Tourism Board | info@tourismauthority.mu | Tourism | No bounce |
| Bank of Mauritius | careers@bom.intnet.mu | Finance | No bounce |
| ANZ Bank | training@anz.com | Finance | No bounce |
| Qantas Airways | training@qantas.com.au | Aviation | No bounce |
| Sydney Opera House | training@sydneyoperahouse.com | Culture | No bounce |
| Macmillan Education | jobs@macmillaneducation.com | Education | No bounce |
| Cambridge University Press ELT | elt.recruitment@cambridge.org | Education | No bounce |
| DBS Bank | careers@dbs.com | Finance | No bounce |
| flydubai | training@flydubai.com | Aviation | No bounce |
| ADNOC | training@adnoc.ae | Energy | No bounce |
| Saudi Aramco | training@aramco.com | Energy | No bounce |
| Intel APAC | careers@intel.com | Tech | Auto-reply confirms receipt |
| SAP Labs | careers@sap.com | Tech | Auto-reply confirms receipt |
| Hilton Hotels | recruitment@hilton.com | Hospitality | No bounce |
| Shell | careers@shell.com | Energy | No bounce |
| Unilever | training@unilever.com | FMCG | No bounce |
| Air Mauritius Training (verify) | (resend after fixing address) | Aviation | Old address bounced |

---

## Section B — CORRECTED (Bad address → Good replacement)

Old addresses bounced. Use these verified replacements.

| Company | Old (bounced) | Corrected Email | How to Verify |
|---------|---------------|-----------------|---------------|
| Alliance Française Paris | formation@afparis.org | contact@alliancefrancaiseparis.com | Visit alliancefrancaiseparis.com |
| Alliance Française Dakar | direction@afdakar.org | contact@alliancefrancaise.sn | Visit alliancefrancaise.sn |
| Université des Mascareignes | contact@univ-mascareignes.org | contact@univ-mascareignes.re | Correct TLD: .re |
| AP-HP (all hospitals) | formation@cochin.aphp.fr | formation@aphp.fr | AP-HP central formation |
| AP-HP Saint-Louis | formation@hsl.aphp.fr | formation@aphp.fr | Same parent domain |
| Thai Airways | training@thaiairways.co.th | careers@thaiairways.com | Correct domain |
| IH Prague | prague@ihlondon.com | info@ihprague.cz | IH Prague is independent |

---

## Section C — REMOVE (Confirmed Undeliverable — Hard Bounce)

These addresses permanently failed. Remove from all lists immediately.

### Domain does not exist
```
formation@afparis.org
direction@afdakar.org
tourisme@comorestourisme.com
careers@starentertainment.com.au
training@thaiairways.co.th
formation@cochin.aphp.fr
```

### Address rejected (550/554 permanent failure)
```
careers@oracle.com
training@ibm.com
careers@cisco.com
training@ey.com
careers@hsbc.co.uk
training@lloydsbankinggroup.com
formacion@bbva.es
careers@kpmg.fr
formation@societegenerale.com
training@novartis.com
formation@hsl.aphp.fr
training@skoda-auto.cz
careers@pragueairport.cz
eltjobs@oup.com
jobs@pearsonelt.com
careers@aucegypt.edu
careers@emaar.com
careers@melia.com
rh@michelin.com
formation@edf.fr
training@iberdrola.com
careers@bangkokbank.com
training@airbus.es
training@siemens.es
careers@ngl.cengage.com
training@pwc.co.uk
formation@safran-group.com
careers@nokia.com
careers@google.co.th
careers@google.ae
training@cba.com.au
training@nestle.com
formacion@telefonica.es
training@singaporeair.com
prague@ihlondon.com
training@emiratesnbd.com
careers@heathrow.com
recrutement@cned.fr          ← bounced 2026-06-11 (550 5.1.1 — address not found)
```

### MS365 group — rejects external senders
```
training@du.ae
training@mashreqbank.com
training@microsoft.com
training@bp.com
training@otpbank.hu
training@cathaypacific.com
```

---

## Section D — PORTALS ONLY (use URL, not email)

These companies only accept applications through their ATS portal. Do not email directly.

| Company | Portal URL |
|---------|------------|
| Oxford University Press | jobs.oup.com |
| Pearson | careers.pearson.com |
| IBM | ibm.com/employment |
| Oracle | oracle.com/corporate/careers |
| Cisco | jobs.cisco.com |
| Microsoft | careers.microsoft.com |
| SAP | sap.com/careers |
| Siemens | siemens.com/careers |
| Airbus | jobs.airbus.com |
| EDF | jobs.edf.com |
| Total/TotalEnergies | totalenergies.com/careers |
| PwC | pwc.com/gx/en/careers |
| EY | ey.com/en_gl/careers |
| KPMG | home.kpmg/careers |
| Société Générale | careers.societegenerale.com |
| Michelin | jobs.michelin.com |
| CNED | cned.fr (use contact form — recrutement@cned.fr address does not exist) |

---

## Section E — HIGH-QUALITY TARGETS (France Travail API)

These categories consistently have real job postings with contact emails on France Travail. Use `france_travail_client.py` to fetch current listings.

### La Réunion (974) — Priority targets
- Language schools (`école de langues`)
- OPCO-funded training centres (`organisme de formation`)
- Hotels and resorts (5-star: Club Med, IHG, Marriott)
- Hospitals and clinics (CHU Réunion, polycliniques)
- Local government / collectivités
- Alliance Française Réunion: `info@alliancefrancaise-reunion.com`
- Chambre de Commerce et d'Industrie (CCI) Réunion

### Indian Ocean region
- Alliance Française: Madagascar, Comoros, Seychelles, Mauritius
- Air Austral (Réunion airline): `rh@air-austral.com`
- Groupe Bourbon: `rh@bourbon.com`
- Océinde: regional education network

### France métropolitaine (remote/hybrid)
- EF Education First: `jobs@ef.com`
- Wall Street English: national network
- Berlitz France: `recrutement@berlitz.fr`
- Inlingua France: regional schools
- Gymglish / Babbel for Business: `jobs@gymglish.com`

---

## Section F — France Travail API Recommended Search Parameters

Use `france_travail_client.py` with these parameters:

```python
# La Réunion — priority
client.search_jobs(keywords="formateur anglais",  department="974")
client.search_jobs(keywords="formation anglais",   department="974")
client.search_jobs(keywords="professeur anglais",  department="974")
client.search_jobs(keywords="organisme formation", department="974")
client.search_jobs(keywords="CELTA",               department="974")
client.search_jobs(keywords="IELTS",               department="974")
client.search_jobs(keywords="TOEIC formateur",     department="974")

# Nearby departments
client.search_jobs(keywords="formateur anglais",   department="976")  # Mayotte
client.search_jobs(keywords="formateur anglais",   department="972")  # Martinique
client.search_jobs(keywords="formateur anglais",   department="971")  # Guadeloupe

# All France (remote roles)
client.search_jobs(keywords="formateur anglais distanciel")
client.search_jobs(keywords="english trainer remote France")
```
