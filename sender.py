import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
import config


def send_to_kindle(epub_path: str, book_title: str = "Book", kindle_email: str | None = None) -> None:
    """Email the epub/pdf file to a Kindle address."""
    config.validate_smtp()

    to = kindle_email or config.KINDLE_EMAIL
    if not to:
        raise ValueError("No Kindle email address provided.")

    ext = os.path.splitext(epub_path)[1].lower()
    if ext not in {".epub", ".pdf"}:
        raise ValueError(f"Unsupported format: {ext}")

    msg = MIMEMultipart()
    msg["From"] = config.SENDER_EMAIL
    msg["To"] = to
    msg["Subject"] = "convert"

    msg.attach(MIMEText(f"Sending: {book_title}", "plain"))

    filename = os.path.basename(epub_path)
    with open(epub_path, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
    msg.attach(part)

    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.login(config.SENDER_EMAIL, config.SENDER_PASSWORD)
        server.sendmail(config.SENDER_EMAIL, to, msg.as_string())
