"""
organise_emails.py — Reads research_results.json + CV, generates all email
drafts, saves them to a structured JSON queue ready for sending.

Reusable: works for any candidate, any company list, any AI provider.

Usage:
    python organise_emails.py --research results.json --cv cv.pdf --provider deepseek
    python organise_emails.py --research results.json --cv cv.pdf --provider template
"""

import argparse, json, os, sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(__file__))
from data_parser import extract_cv_text, extract_motivation_letter
from email_generator import generate_email
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"), override=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--research",   required=True, help="JSON from search_companies.py")
    ap.add_argument("--cv",         required=True, help="CV PDF path")
    ap.add_argument("--letter",     default="",    help="Motivation letter PDF (optional)")
    ap.add_argument("--provider",   default=None,  help="anthropic|mistral|deepseek|ollama|template")
    ap.add_argument("--api-key",    default=None)
    ap.add_argument("--ollama-model", default="mistral")
    ap.add_argument("--ollama-url",   default="http://localhost:11434")
    ap.add_argument("--out",        default="email_queue.json")
    args = ap.parse_args()

    with open(args.research, encoding="utf-8") as f:
        research_data = json.load(f)

    cv_text = extract_cv_text(args.cv)
    if not cv_text:
        print("ERROR: cannot read CV"); sys.exit(1)

    letter = ""
    if args.letter and os.path.exists(args.letter):
        letter = extract_motivation_letter(args.letter) or ""

    profile = f"=== CV ===\n{cv_text}\n\n=== LETTRE ===\n{letter}".strip()

    queue = []
    skipped = []

    for rec in research_data.get("results", []):
        if not rec.get("email"):
            skipped.append(rec)
            continue

        company_info = {
            "company_name": rec["company"],
            "city":         rec.get("city", ""),
            "ca":           rec.get("ca", ""),
            "postal_code":  rec.get("postal_code", ""),
        }
        research = {"about_text": rec.get("about_text", ""), "website": rec.get("website")}

        print(f"Generating email for {rec['company']} → {rec['email']}")
        subject, body = generate_email(
            profile, company_info, research,
            api_key      = args.api_key or os.getenv("ANTHROPIC_API_KEY") or os.getenv("DEEPSEEK_API_KEY"),
            provider     = args.provider,
            ollama_model = args.ollama_model,
            ollama_url   = args.ollama_url,
        )
        queue.append({
            "company":   rec["company"],
            "recipient": rec["email"],
            "subject":   subject,
            "body":      body,
            "website":   rec.get("website"),
            "status":    "pending",
        })

    output = {
        "generated_at":    datetime.now().isoformat(),
        "cv_path":         args.cv,
        "provider":        args.provider or "auto",
        "total_queued":    len(queue),
        "total_skipped":   len(skipped),
        "queue":           queue,
        "skipped_no_email": skipped,
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nDone. {len(queue)} emails queued | {len(skipped)} skipped (no email).")
    print(f"Queue saved to: {args.out}")
    print("Next step: python send_emails.py --queue email_queue.json --cv cv.pdf")


if __name__ == "__main__":
    main()
