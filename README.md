# kindle-master

> Search a book → download the epub → it lands on your Kindle. One command.

```
python main.py "Atomic Habits"
```

---

## How it works

1. Searches [Anna's Archive](https://annas-archive.gl/) for the epub
2. Shows top results — you pick one
3. Downloads the epub (via Libgen mirrors)
4. Emails it to your Kindle address — Amazon delivers it automatically

---

## Features

- Search by title or author name
- Snap a photo of a book cover → it reads the title via OCR and searches automatically
- Works with any SMTP provider (Gmail, Outlook, iCloud, etc.)

---

## Requirements

- Python 3.10+
- A Kindle device or the Kindle app
- A Gmail account (or any SMTP email)
- [Tesseract](https://github.com/tesseract-ocr/tesseract) — only needed for the photo feature

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/Agrimd15/kindle-master.git
cd kindle-master
```

### 2. Create a virtual environment and install dependencies

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

For the photo/OCR feature, also install Tesseract:

```bash
# macOS
brew install tesseract

# Ubuntu / Debian
sudo apt install tesseract-ocr

# Windows — download installer from:
# https://github.com/UB-Mannheim/tesseract/wiki
```

### 3. Configure your `.env` file

```bash
cp .env.example .env
```

Open `.env` and fill in four values. Here's how to find each one:

---

#### `KINDLE_EMAIL` — your personal Kindle address

1. Go to [amazon.com](https://amazon.com) and sign in
2. Click **Account & Lists** → **Manage Your Content and Devices**
3. Click the **Preferences** tab
4. Scroll to **Personal Document Settings**
5. Your Kindle email is listed under **Send-to-Kindle E-Mail Settings** — looks like `yourname_abc@kindle.com`

---

#### `SENDER_EMAIL` — the email you'll send from

Any Gmail address works. This is the address Amazon will receive mail from.

> **Important:** Amazon only accepts files from approved addresses. After you set `SENDER_EMAIL`, you must add it to Amazon's allowlist (step 4 below).

---

#### `SENDER_PASSWORD` — Gmail App Password

Regular Gmail passwords won't work here — you need an **App Password**.

1. Go to your [Google Account](https://myaccount.google.com)
2. Click **Security** in the left sidebar
3. Under "How you sign in to Google", enable **2-Step Verification** if not already on
4. Search for **"App Passwords"** in the search bar at the top, or go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
5. Click **Create**, give it any name (e.g. `kindle-master`), click **Create**
6. Copy the 16-character password shown — paste it as `SENDER_PASSWORD`

> For Outlook/Hotmail: use `smtp.office365.com` / port `587`. For iCloud: use `smtp.mail.me.com` / port `587` with an app-specific password from Apple ID settings.

---

#### `SMTP_HOST` / `SMTP_PORT`

Leave these as-is if you're using Gmail. Only change if using a different provider:

| Provider | `SMTP_HOST` | `SMTP_PORT` |
|----------|------------|------------|
| Gmail | `smtp.gmail.com` | `587` |
| Outlook/Hotmail | `smtp.office365.com` | `587` |
| iCloud | `smtp.mail.me.com` | `587` |

---

Your final `.env` should look like this:

```env
KINDLE_EMAIL=yourname_abc123@kindle.com
SENDER_EMAIL=you@gmail.com
SENDER_PASSWORD=abcd efgh ijkl mnop
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
```

---

### 4. Approve your sender email on Amazon

Amazon only delivers documents from addresses you've explicitly allowlisted.

1. Go back to **Manage Your Content and Devices** → **Preferences** → **Personal Document Settings**
2. Scroll to **Approved Personal Document E-mail List**
3. Click **Add a new approved e-mail address**
4. Enter your `SENDER_EMAIL` and save

---

## Usage

```bash
source venv/bin/activate   # activate the venv if not already active

# Search by book title
python main.py "Atomic Habits"

# Search by author
python main.py "James Clear" --author

# From a photo of a book cover or title page
python main.py --image /path/to/photo.jpg

# No arguments — will prompt you
python main.py
```

After running, you'll see a numbered list of results. Pick one, and the epub is downloaded and emailed to your Kindle. It usually shows up within a minute or two.

---

## Notes

- The email subject is set to `convert` — this tells Amazon to optimize the format for Kindle
- Amazon has a 50MB file size limit for email delivery; most epubs are well under this
- If a book doesn't appear on your Kindle, check your Amazon Kindle library at [read.amazon.com](https://read.amazon.com)
- OCR works best with clear, well-lit photos showing the title and author prominently

---

## Troubleshooting

**"Missing config" error**
→ Make sure you copied `.env.example` to `.env` and filled in all four fields.

**"Authentication failed" from Gmail**
→ You're using your regular password. Create an App Password as described in step 3 above.

**Book not appearing on Kindle**
→ Your sender email isn't on Amazon's allowlist. Complete step 4 above.

**No results found**
→ Try a shorter query. Instead of the full subtitle, just use the main title or the author's last name.

**OCR reads wrong text from photo**
→ Make sure Tesseract is installed (`tesseract --version`). Use a clear photo with good lighting; the title and author text should be in focus.

---

## Contributing

Pull requests welcome. To add support for a new download mirror or email provider, the relevant files are `search.py` and `sender.py`.

---

## Disclaimer

This tool is for personal use only. Only download books you own or that are in the public domain in your jurisdiction.
