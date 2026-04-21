"""
Email generator — supports multiple AI providers:
  - Anthropic Claude (claude-haiku-4-5-20251001)
  - Mistral AI (mistral-small-latest)
  - DeepSeek (deepseek-chat via OpenAI-compatible API)
  - Ollama (local, e.g. mistral, llama3, gemma3)
  - Template (no AI, high-quality French template — always available)

Provider is selected via PROVIDER env var or passed explicitly.
"""
import os, re

# ─── Optional provider imports ───────────────────────────────────────────────
try:
    import anthropic as _anthropic_mod
    _HAS_ANTHROPIC = True
except ImportError:
    _HAS_ANTHROPIC = False

try:
    from mistralai import Mistral as _MistralClient
    _HAS_MISTRAL = True
except ImportError:
    _HAS_MISTRAL = False

try:
    import openai as _openai_mod   # used for DeepSeek (OpenAI-compatible)
    _HAS_OPENAI = True
except ImportError:
    _HAS_OPENAI = False

try:
    import requests as _requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False


# ─── System prompt ────────────────────────────────────────────────────────────
_SYSTEM = (
    "Tu es un expert en candidature professionnelle en France (DOM-TOM).\n"
    "Rédige des lettres courtes (max 200 mots), professionnelles et personnalisées en français.\n"
    "Première ligne : 'OBJET: <sujet de l'email>'\n"
    "Ensuite le corps de la lettre, texte brut uniquement.\n"
    "Signature : Sourov Deb | Formateur d'Anglais CELTA | 06 93 84 61 68 | sourovdeb.is@gmail.com | Saint-Pierre La Réunion 97410"
)


def _build_user_prompt(cv_text, company_info, research):
    cname  = company_info.get("company_name", "l'entreprise")
    city   = company_info.get("city", "")
    about  = (research or {}).get("about_text", "")[:600]
    return (
        f"CANDIDAT:\n{cv_text[:1000]}\n\n"
        f"ENTREPRISE:\n- Nom: {cname}\n- Ville: {city}\n"
        f"- Infos: {about or '(aucune information disponible)'}"
    )


def _parse_response(text, company_name):
    text = text.strip()
    m = re.match(r"^OBJET\s*:\s*(.+)$", text, re.MULTILINE | re.IGNORECASE)
    if m:
        subject = m.group(1).strip()
        body    = re.sub(r"^OBJET\s*:.+\n?", "", text, flags=re.MULTILINE | re.IGNORECASE).strip()
    else:
        subject = f"Candidature Formateur d'Anglais CELTA – {company_name}"
        body    = text
    return subject, body


# ─── Template (no AI) ────────────────────────────────────────────────────────
_TEMPLATE = """\
Madame, Monsieur,

Je me permets de vous adresser ma candidature spontanée pour un poste de formateur d'anglais professionnel au sein de {company_name}.

Certifié CELTA (Cambridge, 2026) et spécialisé en préparation IELTS et TOEIC, je dispose de 18 ans d'expérience en management international dans des environnements 100 % anglophones (Australie, France). Cette double expertise — académique et terrain — me permet de former des équipes opérationnelles aux exigences réelles du monde professionnel.

{hook}

Je serais ravi(e) d'échanger sur la façon dont mes compétences peuvent servir vos objectifs. Je reste disponible pour un entretien à votre convenance.

Veuillez trouver ci-joint mon CV.

Cordialement,
Sourov Deb
Formateur d'Anglais Certifié CELTA | Spécialiste IELTS · TOEIC
📱 06 93 84 61 68 | ✉ sourovdeb.is@gmail.com
Saint-Pierre, La Réunion (97410)
"""


def _template(cv_text, company_info, research):
    cname = company_info.get("company_name", "votre organisation")
    city  = company_info.get("city", "La Réunion")
    about = (research or {}).get("about_text", "")

    if about and len(about) > 80:
        parts = [s.strip() for s in re.split(r"[.!?]", about) if len(s.strip()) > 30]
        if parts:
            hook = (
                f"Votre organisation retient particulièrement mon attention : "
                f"{parts[0][:200].lower()}. "
                f"C'est précisément dans ce type d'environnement que ma maîtrise de l'anglais "
                f"professionnel apporte une valeur ajoutée immédiate."
            )
        else:
            hook = _generic_hook(city)
    else:
        hook = _generic_hook(city)

    subject = f"Candidature Formateur d'Anglais CELTA – {cname}"
    body    = _TEMPLATE.format(company_name=cname, hook=hook).strip()
    return subject, body


def _generic_hook(city):
    return (
        f"Implanté(e) à {city or 'La Réunion'}, votre structure opère dans un contexte "
        f"où la maîtrise de l'anglais est un avantage compétitif réel — export, tourisme, "
        f"échanges intra-océan Indien. Je propose une formation sur-mesure, immédiatement opérationnelle."
    )


# ─── Provider: Anthropic Claude ──────────────────────────────────────────────
def _claude(cv_text, company_info, research, api_key):
    if not _HAS_ANTHROPIC:
        raise RuntimeError("anthropic package not installed")
    client = _anthropic_mod.Anthropic(api_key=api_key)
    resp   = client.messages.create(
        model      = "claude-haiku-4-5-20251001",
        max_tokens = 600,
        system     = _SYSTEM,
        messages   = [{"role": "user", "content": _build_user_prompt(cv_text, company_info, research)}],
    )
    return _parse_response(resp.content[0].text, company_info.get("company_name", ""))


# ─── Provider: Mistral ───────────────────────────────────────────────────────
def _mistral(cv_text, company_info, research, api_key):
    if not _HAS_MISTRAL:
        raise RuntimeError("mistralai package not installed — run: pip install mistralai")
    client = _MistralClient(api_key=api_key)
    resp   = client.chat.complete(
        model    = "mistral-small-latest",
        messages = [
            {"role": "system",  "content": _SYSTEM},
            {"role": "user",    "content": _build_user_prompt(cv_text, company_info, research)},
        ],
    )
    return _parse_response(resp.choices[0].message.content, company_info.get("company_name", ""))


# ─── Provider: DeepSeek (OpenAI-compatible) ──────────────────────────────────
def _deepseek(cv_text, company_info, research, api_key):
    if not _HAS_OPENAI:
        raise RuntimeError("openai package not installed — run: pip install openai")
    client = _openai_mod.OpenAI(
        api_key  = api_key,
        base_url = "https://api.deepseek.com/v1",
    )
    resp = client.chat.completions.create(
        model    = "deepseek-chat",
        messages = [
            {"role": "system",  "content": _SYSTEM},
            {"role": "user",    "content": _build_user_prompt(cv_text, company_info, research)},
        ],
        max_tokens = 600,
    )
    return _parse_response(resp.choices[0].message.content, company_info.get("company_name", ""))


# ─── Provider: Ollama (local) ────────────────────────────────────────────────
def _ollama(cv_text, company_info, research, model="mistral", base_url="http://localhost:11434"):
    if not _HAS_REQUESTS:
        raise RuntimeError("requests package not installed")
    payload = {
        "model":  model,
        "stream": False,
        "messages": [
            {"role": "system",  "content": _SYSTEM},
            {"role": "user",    "content": _build_user_prompt(cv_text, company_info, research)},
        ],
    }
    resp = _requests.post(f"{base_url}/api/chat", json=payload, timeout=120)
    resp.raise_for_status()
    text = resp.json()["message"]["content"]
    return _parse_response(text, company_info.get("company_name", ""))


# ─── Public API ──────────────────────────────────────────────────────────────
PROVIDERS = ["anthropic", "mistral", "deepseek", "ollama", "template"]


def generate_email(cv_text, company_info, research,
                   api_key=None, provider=None, ollama_model="mistral",
                   ollama_url="http://localhost:11434"):
    """
    Generate a personalized email (subject, body) for a job application.

    Args:
        cv_text (str):        Full CV text.
        company_info (dict):  Keys: company_name, city, ca, postal_code.
        research (dict):      Output from researcher.search_company_info().
        api_key (str|None):   API key for the chosen provider.
        provider (str|None):  One of 'anthropic', 'mistral', 'deepseek', 'ollama', 'template'.
                              Defaults to PROVIDER env var, then auto-detects from available keys.
        ollama_model (str):   Ollama model name (default: 'mistral').
        ollama_url (str):     Ollama server URL.

    Returns:
        tuple[str, str]: (subject, body)
    """
    if provider is None:
        provider = os.getenv("PROVIDER", "").lower() or _auto_detect_provider(api_key)

    cname = company_info.get("company_name", "")
    try:
        if provider == "anthropic":
            key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
            if not key:
                raise RuntimeError("ANTHROPIC_API_KEY not set")
            return _claude(cv_text, company_info, research, key)

        elif provider == "mistral":
            key = api_key or os.getenv("MISTRAL_API_KEY", "")
            if not key:
                raise RuntimeError("MISTRAL_API_KEY not set")
            return _mistral(cv_text, company_info, research, key)

        elif provider == "deepseek":
            key = api_key or os.getenv("DEEPSEEK_API_KEY", "")
            if not key:
                raise RuntimeError("DEEPSEEK_API_KEY not set")
            return _deepseek(cv_text, company_info, research, key)

        elif provider == "ollama":
            model = ollama_model or os.getenv("OLLAMA_MODEL", "mistral")
            url   = ollama_url   or os.getenv("OLLAMA_URL", "http://localhost:11434")
            return _ollama(cv_text, company_info, research, model, url)

        else:
            return _template(cv_text, company_info, research)

    except Exception as e:
        print(f"  AI provider '{provider}' error: {e} — falling back to template")
        return _template(cv_text, company_info, research)


def _auto_detect_provider(explicit_key):
    """Pick best available provider based on env vars."""
    if explicit_key or os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.getenv("MISTRAL_API_KEY"):
        return "mistral"
    if os.getenv("DEEPSEEK_API_KEY"):
        return "deepseek"
    if os.getenv("OLLAMA_URL") or _ollama_running():
        return "ollama"
    return "template"


def _ollama_running():
    try:
        _requests.get("http://localhost:11434/api/tags", timeout=2)
        return True
    except Exception:
        return False


# Legacy compatibility
def generate_email_body(cv_text, company_row, company_research):
    if hasattr(company_row, "to_dict"):
        row_dict = company_row.to_dict()
    else:
        row_dict = dict(company_row)
    company_info = {
        "company_name": row_dict.get("Raison sociale") or row_dict.get("NOM", ""),
        "city":         row_dict.get("Ville", ""),
        "ca":           row_dict.get("C.A.", ""),
        "postal_code":  row_dict.get("CP", ""),
    }
    research = {"about_text": company_research or ""}
    _, body = generate_email(cv_text, company_info, research)
    return body


if __name__ == "__main__":
    mock_cv = "Sourov Deb – Formateur CELTA, 18 ans Australie, IELTS TOEIC Business English."
    info    = {"company_name": "ADECCO REUNION", "city": "LA POSSESSION", "ca": "17 154 661 €"}
    res     = {"about_text": "Adecco est un leader mondial des ressources humaines et du recrutement."}
    subj, body = generate_email(mock_cv, info, res)
    print("SUBJECT:", subj)
    print("---\n", body)
