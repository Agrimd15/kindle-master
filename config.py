import os
from dotenv import load_dotenv

load_dotenv()

KINDLE_EMAIL = os.getenv("KINDLE_EMAIL")       # optional — CLI only
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
BOT_TOKEN = os.getenv("BOT_TOKEN")


def validate_smtp():
    """Validate SMTP credentials (used by both CLI and bot)."""
    missing = [k for k, v in {
        "SENDER_EMAIL": SENDER_EMAIL,
        "SENDER_PASSWORD": SENDER_PASSWORD,
    }.items() if not v]
    if missing:
        raise SystemExit(
            f"Missing config: {', '.join(missing)}\n"
            "Copy .env.example to .env and fill in your details."
        )


def validate():
    """Full validation for CLI — also requires KINDLE_EMAIL."""
    validate_smtp()
    if not KINDLE_EMAIL:
        raise SystemExit(
            "Missing config: KINDLE_EMAIL\n"
            "Copy .env.example to .env and fill in your details."
        )


def validate_bot():
    """Validate bot-specific config."""
    validate_smtp()
    if not BOT_TOKEN:
        raise SystemExit(
            "Missing config: BOT_TOKEN\n"
            "Get one from @BotFather on Telegram and add it to .env."
        )
