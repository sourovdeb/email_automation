"""
France Travail (Pôle Emploi) API Client
APIs: Offres d'emploi v2 + Accès à l'emploi des demandeurs d'emploi v1

Usage:
    client = FranceTravailClient(client_id=..., client_secret=...)
    jobs = client.search_jobs(keywords="formateur anglais", department="974")
    for job in jobs:
        print(job['intitule'], job.get('contact', {}).get('courriel'))
"""
import os
import time
import requests
from datetime import datetime, timedelta

# ── Configuration ────────────────────────────────────────────────────────────

TOKEN_URL   = "https://entreprise.pole-emploi.fr/connexion/oauth2/access_token"
JOBS_URL    = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"
JOB_URL     = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/{id}"
DEMANDEUR_URL = "https://api.francetravail.io/partenaire/accesdemandeuremploi/v1"

SCOPE_JOBS   = "api_offresdemploiv2 o2dsoffre"
SCOPE_ACCESS = "api_accesdemandeuremploi"


class FranceTravailClient:
    """
    OAuth2 client_credentials client for the France Travail partner APIs.

    Handles token acquisition, caching, and automatic renewal.
    """

    def __init__(self, client_id: str = None, client_secret: str = None):
        self.client_id     = client_id     or os.getenv("FT_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("FT_CLIENT_SECRET", "")
        self._token_jobs:   str | None = None
        self._token_access: str | None = None
        self._token_jobs_exp   = datetime.min
        self._token_access_exp = datetime.min
        self._session = requests.Session()
        self._session.headers["Accept"] = "application/json"

    # ── Token management ────────────────────────────────────────────────────

    def _get_token(self, scope: str) -> str:
        data = {
            "grant_type":    "client_credentials",
            "client_id":     self.client_id,
            "client_secret": self.client_secret,
            "scope":         scope,
        }
        resp = requests.post(
            TOKEN_URL,
            data=data,
            params={"realm": "/partenaire"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15,
        )
        resp.raise_for_status()
        payload = resp.json()
        expires_in = int(payload.get("expires_in", 1490))
        token = payload["access_token"]
        return token, datetime.utcnow() + timedelta(seconds=expires_in - 30)

    def _jobs_token(self) -> str:
        if datetime.utcnow() >= self._token_jobs_exp:
            self._token_jobs, self._token_jobs_exp = self._get_token(SCOPE_JOBS)
        return self._token_jobs

    def _access_token(self) -> str:
        if datetime.utcnow() >= self._token_access_exp:
            self._token_access, self._token_access_exp = self._get_token(SCOPE_ACCESS)
        return self._token_access

    # ── Job offers API ───────────────────────────────────────────────────────

    def search_jobs(
        self,
        keywords:    str  = "formateur anglais",
        department:  str  = "974",       # 974 = La Réunion
        contract:    str  = None,         # CDI, CDD, MIS, SAI, LIB …
        distance:    int  = None,         # km around commune
        commune:     str  = None,         # INSEE commune code
        experience:  str  = None,         # 1 = < 1 yr, 2 = 1-3 yrs, 3 = > 3 yrs
        max_results: int  = 50,
    ) -> list[dict]:
        """
        Search job offers on France Travail.

        Returns a list of job offer dicts with keys:
            id, intitule, entreprise, lieuTravail, typeContrat,
            dateCreation, contact (courriel, url), description …
        """
        params = {"range": f"0-{max_results - 1}"}
        if keywords:   params["motsCles"]      = keywords
        if department: params["departement"]   = department
        if contract:   params["typeContrat"]   = contract
        if distance:   params["distance"]      = distance
        if commune:    params["commune"]        = commune
        if experience: params["experience"]    = experience

        resp = self._session.get(
            JOBS_URL,
            params=params,
            headers={"Authorization": f"Bearer {self._jobs_token()}"},
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("resultats", [])

    def get_job(self, job_id: str) -> dict:
        """Fetch full details for one job offer."""
        resp = self._session.get(
            JOB_URL.format(id=job_id),
            headers={"Authorization": f"Bearer {self._jobs_token()}"},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

    def search_training_jobs(
        self,
        department: str = "974",
        max_results: int = 100,
    ) -> list[dict]:
        """
        Convenience: search for formateur / formation anglais jobs in a department.
        Tries multiple keyword combinations and deduplicates.
        """
        all_jobs: dict[str, dict] = {}
        queries = [
            "formateur anglais",
            "formation anglais",
            "professeur anglais",
            "enseignant anglais",
            "CELTA",
            "IELTS formateur",
            "TOEIC formateur",
            "english trainer",
            "english teacher",
        ]
        for q in queries:
            try:
                results = self.search_jobs(keywords=q, department=department, max_results=20)
                for job in results:
                    all_jobs[job["id"]] = job
                time.sleep(0.5)
            except Exception as e:
                print(f"  Query '{q}' error: {e}")
        return list(all_jobs.values())[:max_results]

    def extract_contact_info(self, job: dict) -> dict:
        """
        Extract contact email + URL from a job offer.
        Returns dict with keys: email, url, phone, name
        """
        contact = job.get("contact", {})
        entreprise = job.get("entreprise", {})
        return {
            "email":   contact.get("courriel") or "",
            "url":     contact.get("urlPostulation") or job.get("urlOrigine") or "",
            "phone":   contact.get("telephone") or "",
            "name":    contact.get("nom") or "",
            "company": entreprise.get("nom") or "",
            "job_id":  job.get("id") or "",
            "title":   job.get("intitule") or "",
            "city":    job.get("lieuTravail", {}).get("libelle") or "",
            "contract":job.get("typeContratLibelle") or "",
            "description": job.get("description") or "",
        }

    def get_jobs_with_email(
        self,
        department: str = "974",
        max_results: int = 200,
    ) -> list[dict]:
        """
        Return only job offers that have a direct email contact.
        Ideal for auto-apply via Gmail.
        """
        jobs = self.search_training_jobs(department=department, max_results=max_results)
        with_email = []
        for job in jobs:
            info = self.extract_contact_info(job)
            if info["email"]:
                with_email.append(info)
        print(f"Found {len(with_email)} jobs with direct email out of {len(jobs)} total")
        return with_email

    def save_to_csv(self, jobs: list[dict], path: str = "france_travail_jobs.csv") -> None:
        """Save job list to CSV for use with the email automation pipeline."""
        import csv
        if not jobs:
            print("No jobs to save.")
            return
        fieldnames = ["company", "email", "url", "title", "city", "contract", "job_id", "phone", "name", "description"]
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(jobs)
        print(f"Saved {len(jobs)} jobs to {path}")


# ── CLI demo ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    CLIENT_ID     = os.getenv("FT_CLIENT_ID",     "PAR_automationderecherech_72d2b44113ac287b9c4cb540958e31ff2b95695fabec41ce3580d057a753c346")
    CLIENT_SECRET = os.getenv("FT_CLIENT_SECRET", "159c4ab554143db7f6d45638628c8a47bcbf9f52ac2efb9beedd3815c4b472ca")

    client = FranceTravailClient(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)

    print("Searching for formateur anglais jobs in La Réunion (974)...")
    jobs = client.get_jobs_with_email(department="974")

    print(f"\nJobs with direct email contact: {len(jobs)}")
    for j in jobs[:10]:
        print(f"  [{j['company']}] {j['title']} — {j['city']} — {j['email']}")

    client.save_to_csv(jobs, "france_travail_jobs_974.csv")
    print("\nSaved to france_travail_jobs_974.csv")
    print("Now run: python main_app.py and load this CSV as the company list.")
