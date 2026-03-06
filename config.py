import os
from dotenv import load_dotenv

load_dotenv()

KINDLE_EMAIL = os.getenv("KINDLE_EMAIL")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

def validate():
    missing = [k for k, v in {
        "KINDLE_EMAIL": KINDLE_EMAIL,
        "SENDER_EMAIL": SENDER_EMAIL,
        "SENDER_PASSWORD": SENDER_PASSWORD,
    }.items() if not v]
    if missing:
        raise SystemExit(
            f"Missing config: {', '.join(missing)}\n"
            "Copy .env.example to .env and fill in your details."
        )
