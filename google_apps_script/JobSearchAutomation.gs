/**
 * Job Search Automation — Google Apps Script
 * ============================================
 * Uses the France Travail (Pôle Emploi) API to:
 *  1. Fetch fresh job offers matching your profile
 *  2. Log them to a Google Sheet (tracker)
 *  3. Create Gmail drafts (or send immediately) for each new offer
 *  4. Mark applied jobs so they are never duplicated
 *
 * SETUP (one-time):
 *  1. Open Google Sheets → Extensions → Apps Script
 *  2. Paste this entire file
 *  3. Set the CONFIG constants below
 *  4. Run setupTrigger() once to schedule daily search
 *  5. Authorise the required scopes when prompted
 *
 * SCOPES REQUIRED (add in appsscript.json):
 *   https://www.googleapis.com/auth/spreadsheets
 *   https://www.googleapis.com/auth/gmail.compose
 *   https://www.googleapis.com/auth/gmail.send
 *   https://www.googleapis.com/auth/script.external_request
 */

// ── CONFIG — edit these ──────────────────────────────────────────────────────

const CONFIG = {
  // France Travail API credentials
  FT_CLIENT_ID:     PropertiesService.getScriptProperties().getProperty('FT_CLIENT_ID') || '',
  FT_CLIENT_SECRET: PropertiesService.getScriptProperties().getProperty('FT_CLIENT_SECRET') || '',

  // Search parameters
  DEPARTMENT:    '974',       // 974 = La Réunion
  KEYWORDS:      ['formateur anglais', 'professeur anglais', 'formation anglais', 'CELTA', 'TOEIC', 'IELTS'],
  MAX_PER_QUERY: 30,

  // Your profile
  YOUR_NAME:   'Sourov Deb',
  YOUR_EMAIL:  'sourovdeb.is@gmail.com',
  YOUR_PHONE:  '06 93 84 61 68',
  YOUR_CITY:   'Saint-Pierre, La Réunion 97410',

  // Behaviour
  AUTO_SEND:   false,  // false = create drafts for review; true = send immediately
  SHEET_NAME:  'JobTracker',
};

// ── Token cache (per execution) ───────────────────────────────────────────────
let _cachedToken = null;
let _tokenExpiry = 0;

function _getToken() {
  const now = Date.now() / 1000;
  if (_cachedToken && now < _tokenExpiry) return _cachedToken;

  const resp = UrlFetchApp.fetch(
    'https://entreprise.pole-emploi.fr/connexion/oauth2/access_token?realm=%2Fpartenaire',
    {
      method:  'post',
      payload: {
        grant_type:    'client_credentials',
        client_id:     CONFIG.FT_CLIENT_ID,
        client_secret: CONFIG.FT_CLIENT_SECRET,
        scope:         'api_offresdemploiv2 o2dsoffre',
      },
      muteHttpExceptions: true,
    }
  );

  if (resp.getResponseCode() !== 200) {
    throw new Error('Token error: ' + resp.getContentText());
  }
  const data = JSON.parse(resp.getContentText());
  _cachedToken = data.access_token;
  _tokenExpiry = now + data.expires_in - 30;
  return _cachedToken;
}

// ── France Travail API ────────────────────────────────────────────────────────

function searchJobs_(keywords, department, maxResults) {
  const token = _getToken();
  const params = new URLSearchParams({
    motsCles:    keywords,
    departement: department,
    range:       `0-${maxResults - 1}`,
  });
  const url  = 'https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search?' + params.toString();
  const resp = UrlFetchApp.fetch(url, {
    headers: { Authorization: 'Bearer ' + token },
    muteHttpExceptions: true,
  });

  if (resp.getResponseCode() === 206 || resp.getResponseCode() === 200) {
    const data = JSON.parse(resp.getContentText());
    return data.resultats || [];
  }
  console.warn('Search error ' + resp.getResponseCode() + ' for: ' + keywords);
  return [];
}

function getAllJobs_() {
  const seen = {};
  CONFIG.KEYWORDS.forEach(kw => {
    const results = searchJobs_(kw, CONFIG.DEPARTMENT, CONFIG.MAX_PER_QUERY);
    results.forEach(j => { seen[j.id] = j; });
    Utilities.sleep(500);
  });
  return Object.values(seen);
}

// ── Google Sheet tracker ──────────────────────────────────────────────────────

function _getOrCreateSheet() {
  const ss    = SpreadsheetApp.getActiveSpreadsheet();
  let   sheet = ss.getSheetByName(CONFIG.SHEET_NAME);
  if (!sheet) {
    sheet = ss.insertSheet(CONFIG.SHEET_NAME);
    const headers = [
      'JobID', 'Date Found', 'Company', 'Title', 'City', 'Contract',
      'Email', 'URL', 'Phone', 'Status', 'Applied Date', 'Notes'
    ];
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]).setFontWeight('bold');
    sheet.setFrozenRows(1);
  }
  return sheet;
}

function _getAppliedIds(sheet) {
  const data = sheet.getDataRange().getValues();
  const ids  = new Set();
  for (let i = 1; i < data.length; i++) {
    if (data[i][0]) ids.add(String(data[i][0]));
  }
  return ids;
}

function _appendJob(sheet, job, contactInfo) {
  sheet.appendRow([
    job.id,
    new Date().toISOString().slice(0, 10),
    contactInfo.company,
    contactInfo.title,
    contactInfo.city,
    contactInfo.contract,
    contactInfo.email,
    contactInfo.url,
    contactInfo.phone,
    'New',
    '',
    '',
  ]);
}

function _markApplied(sheet, jobId) {
  const data = sheet.getDataRange().getValues();
  for (let i = 1; i < data.length; i++) {
    if (String(data[i][0]) === String(jobId)) {
      sheet.getRange(i + 1, 10).setValue('Applied');
      sheet.getRange(i + 1, 11).setValue(new Date().toISOString().slice(0, 10));
      break;
    }
  }
}

// ── Extract contact info from job ─────────────────────────────────────────────

function _extractContact(job) {
  const contact    = job.contact    || {};
  const entreprise = job.entreprise || {};
  return {
    company:  entreprise.nom                   || '(entreprise non renseignée)',
    title:    job.intitule                     || '',
    city:     (job.lieuTravail || {}).libelle  || '',
    contract: job.typeContratLibelle           || '',
    email:    contact.courriel                 || '',
    url:      contact.urlPostulation           || job.urlOrigine || '',
    phone:    contact.telephone                || '',
    name:     contact.nom                      || '',
    desc:    (job.description || '').slice(0, 500),
  };
}

// ── Email generation ──────────────────────────────────────────────────────────

function _buildEmailBody(contact) {
  const company = contact.company;
  const title   = contact.title;
  const city    = contact.city || 'La Réunion';
  const hook    = contact.desc
    ? `Votre offre pour le poste « ${title} » retient particulièrement mon attention.`
    : `Implanté(e) à ${city}, votre structure offre un environnement où la maîtrise de l'anglais professionnel est un atout différenciant.`;

  return `Madame, Monsieur,

${hook}

Certifié Cambridge CELTA (2026), spécialiste IELTS et TOEIC, j'ai 18 ans d'expérience en milieu 100 % anglophone (Australie). Je propose des formations sur-mesure finançables via OPCO : Business English, Anglais Médical, Aviation, Hôtellerie de luxe.

Je vous transmets mon CV en pièce jointe et reste disponible pour un entretien à votre convenance.

Cordialement,
${CONFIG.YOUR_NAME}
Formateur d'Anglais Certifié CELTA | Spécialiste IELTS · TOEIC
${CONFIG.YOUR_PHONE} | ${CONFIG.YOUR_EMAIL}
${CONFIG.YOUR_CITY}`;
}

function _buildSubject(contact) {
  return `Candidature Formateur Anglais Cambridge CELTA — ${contact.company}`;
}

// ── Gmail draft / send ────────────────────────────────────────────────────────

function _sendOrDraft(to, subject, body) {
  if (CONFIG.AUTO_SEND) {
    GmailApp.sendEmail(to, subject, body, {
      name: CONFIG.YOUR_NAME,
    });
    return 'sent';
  } else {
    GmailApp.createDraft(to, subject, body, {
      name: CONFIG.YOUR_NAME,
    });
    return 'drafted';
  }
}

// ── Save job to Gmail label ───────────────────────────────────────────────────

function _saveJobToGmail(contact) {
  const subject = `[JOB SAVED] ${contact.title} — ${contact.company} (${contact.city})`;
  const body = [
    `JOB OFFER SAVED — ${new Date().toLocaleDateString()}`,
    '',
    `Titre:      ${contact.title}`,
    `Entreprise: ${contact.company}`,
    `Ville:      ${contact.city}`,
    `Contrat:    ${contact.contract}`,
    `Email:      ${contact.email}`,
    `URL:        ${contact.url}`,
    `Téléphone:  ${contact.phone}`,
    '',
    'Description:',
    contact.desc,
  ].join('\n');

  GmailApp.sendEmail(CONFIG.YOUR_EMAIL, subject, body);
}

// ── Main entry point ──────────────────────────────────────────────────────────

/**
 * Run this function manually or via trigger.
 * It fetches new jobs, logs them to the sheet, and creates drafts/sends emails.
 */
function runJobSearch() {
  console.log('Starting France Travail job search...');
  const sheet      = _getOrCreateSheet();
  const appliedIds = _getAppliedIds(sheet);
  const jobs       = getAllJobs_();

  console.log(`Found ${jobs.length} unique job offers`);

  let newCount   = 0;
  let skipCount  = 0;
  let emailCount = 0;

  jobs.forEach(job => {
    // Skip already processed
    if (appliedIds.has(String(job.id))) {
      skipCount++;
      return;
    }

    const contact = _extractContact(job);
    _appendJob(sheet, job, contact);
    newCount++;

    // Save job to Gmail for offline review
    _saveJobToGmail(contact);

    // If the offer has a direct email, apply
    if (contact.email) {
      const subject = _buildSubject(contact);
      const body    = _buildEmailBody(contact);
      const action  = _sendOrDraft(contact.email, subject, body);
      _markApplied(sheet, job.id);
      emailCount++;
      console.log(`${action}: ${contact.company} → ${contact.email}`);
    }

    Utilities.sleep(300); // polite rate limiting
  });

  const summary = [
    `Job search complete.`,
    `Total found: ${jobs.length}`,
    `New (not seen before): ${newCount}`,
    `Already processed: ${skipCount}`,
    `Emails ${CONFIG.AUTO_SEND ? 'sent' : 'drafted'}: ${emailCount}`,
  ].join('\n');

  console.log(summary);

  // Email yourself a summary
  GmailApp.sendEmail(
    CONFIG.YOUR_EMAIL,
    `[JobSearch] Daily Report — ${new Date().toLocaleDateString()}`,
    summary
  );
}

// ── Trigger setup ─────────────────────────────────────────────────────────────

/**
 * Run this ONCE to schedule the daily job search at 08:00.
 */
function setupTrigger() {
  // Remove existing triggers to avoid duplicates
  ScriptApp.getProjectTriggers().forEach(t => ScriptApp.deleteTrigger(t));

  ScriptApp.newTrigger('runJobSearch')
    .timeBased()
    .everyDays(1)
    .atHour(8)
    .create();

  console.log('Daily trigger set: runJobSearch will run every day at 08:00.');
}

/**
 * Store API credentials securely in Script Properties (recommended over hardcoding).
 * Run this once, then remove the keys from CONFIG.
 */
function storeCredentials() {
  const props = PropertiesService.getScriptProperties();
  props.setProperty('FT_CLIENT_ID',     'PAR_automationderecherech_72d2b44113ac287b9c4cb540958e31ff2b95695fabec41ce3580d057a753c346');
  props.setProperty('FT_CLIENT_SECRET', '159c4ab554143db7f6d45638628c8a47bcbf9f52ac2efb9beedd3815c4b472ca');
  console.log('Credentials stored in Script Properties.');
}

/**
 * One-shot: fetch all current offers and save them to Gmail without applying.
 * Useful for reviewing what is available before committing to auto-apply.
 */
function fetchAndSaveOnly() {
  console.log('Fetching jobs for review only (no applications sent)...');
  const sheet      = _getOrCreateSheet();
  const appliedIds = _getAppliedIds(sheet);
  const jobs       = getAllJobs_();
  let newCount = 0;

  jobs.forEach(job => {
    if (appliedIds.has(String(job.id))) return;
    const contact = _extractContact(job);
    _appendJob(sheet, job, contact);
    _saveJobToGmail(contact);
    newCount++;
    Utilities.sleep(300);
  });

  console.log(`Saved ${newCount} new job offers to Gmail and Sheet.`);
}
