# kindle-master

> Search a book → download the epub → it lands on your Kindle. One command or one Telegram message.

**Two ways to use it:**

| | Telegram Bot | CLI |
|---|---|---|
| Works on | Phone + desktop | Desktop only |
| Setup | `/setup` in chat | Edit `.env` file |
| Input | Type title, send a photo | Type title, pass image path |
| Best for | Everyday use, on the go | Power users |

---

## How it works

1. You search by book title, author, or photo of a cover
2. Picks from Anna's Archive (largest book index online)
3. Downloads the epub from Libgen mirrors
4. Emails it to your Kindle — Amazon delivers it in ~1 minute

> Anna's Archive is the search engine. Libgen hosts the actual files. This tool wires them together.

---

## Telegram Bot — Setup (recommended)

The bot is the easiest way to use this, especially from your phone. You host it once, and anyone can use it by messaging it on Telegram.

### Step 1 — Create a Telegram bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Follow the prompts — give it a name and username
4. BotFather gives you a token like `7123456789:AAF...` — copy it

### Step 2 — Get your SMTP credentials

The bot sends emails from your Gmail account to deliver books to Kindle.

**Gmail App Password** (required — regular passwords don't work):
1. Go to [myaccount.google.com](https://myaccount.google.com)
2. Click **Security** → enable **2-Step Verification** if not on
3. Search **"App Passwords"** → click it → click **Create**
4. Name it anything (e.g. `kindle-master`) → copy the 16-character password

### Step 3 — Deploy to Railway (free)

Railway runs the bot for free with no credit card required.

1. Fork this repo on GitHub
2. Go to [railway.app](https://railway.app) and sign in with GitHub
3. Click **New Project** → **Deploy from GitHub repo** → select your fork
4. Once deployed, go to your service → **Variables** tab → add these:

   | Variable | Value |
   |---|---|
   | `BOT_TOKEN` | Token from BotFather |
   | `SENDER_EMAIL` | Your Gmail address |
   | `SENDER_PASSWORD` | Your Gmail App Password |
   | `SMTP_HOST` | `smtp.gmail.com` |
   | `SMTP_PORT` | `587` |

5. Railway will restart the bot automatically — it's live

> Railway's free tier gives 500 hours/month. For a always-on worker, upgrade to the $5/month Hobby plan or use Render's free tier (see below).

**Alternative: Render (free, always-on)**
1. Go to [render.com](https://render.com) → New → Background Worker
2. Connect your GitHub repo
3. Set Build Command: `pip install -r requirements.txt`
4. Set Start Command: `python bot.py`
5. Add the same environment variables under Environment tab

### Step 4 — First-time user setup (everyone who uses the bot)

Each person who uses the bot needs to do this once:

**4a. Tell the bot your Kindle email**

Find your Kindle email:
- Go to [amazon.com](https://amazon.com) → **Account & Lists** → **Manage Your Content and Devices**
- Click **Preferences** tab → scroll to **Personal Document Settings**
- Your address is listed under **Send-to-Kindle E-Mail Settings** — looks like `yourname_abc@kindle.com`

Then message the bot:
```
/setup
```
The bot will ask for your Kindle email — paste it in.

**4b. Approve the bot's sender email on Amazon**

Amazon only delivers documents from addresses you've whitelisted.

1. Message the bot `/info` — it shows the sender email address
2. Go back to **Manage Your Content and Devices** → **Preferences** → **Personal Document Settings** → **Approved Personal Document E-mail List**
3. Click **Add a new approved e-mail address** → enter the address from `/info` → save

That's it. You're set up.

### Using the bot

```
# Search by title
Atomic Habits

# Search by author
James Clear

# Send a photo of a book cover or spine
[attach any photo]
```

The bot shows up to 5 results as buttons. Tap one — the book is downloaded and sent to your Kindle.

**Bot commands:**

| Command | What it does |
|---|---|
| `/start` | Intro and quick guide |
| `/setup` | Save your Kindle email |
| `/info` | Shows the sender email to whitelist on Amazon |
| `/help` | Usage tips |
| `/cancel` | Cancel current operation |

---

## CLI — Setup

For running locally from the terminal.

### Step 1 — Clone and install

```bash
git clone https://github.com/Agrimd15/kindle-master.git
cd kindle-master

python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

For the photo/OCR feature, also install Tesseract:

```bash
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt install tesseract-ocr

# Windows — download from: https://github.com/UB-Mannheim/tesseract/wiki
```

### Step 2 — Configure `.env`

```bash
cp .env.example .env
```

Fill in these fields:

| Field | Where to find it |
|---|---|
| `SENDER_EMAIL` | Your Gmail address |
| `SENDER_PASSWORD` | Gmail App Password (see bot setup Step 2 above) |
| `KINDLE_EMAIL` | Your `@kindle.com` address (see bot setup Step 4a above) |
| `SMTP_HOST` | `smtp.gmail.com` (default) |
| `SMTP_PORT` | `587` (default) |

**Approve your sender email on Amazon** — same as bot setup Step 4b above. Use your own `SENDER_EMAIL` as the address to whitelist.

### Step 3 — Run

```bash
source venv/bin/activate

# By title
python main.py "Atomic Habits"

# By author
python main.py "James Clear" --author

# From a photo
python main.py --image /path/to/photo.jpg

# Interactive prompt
python main.py
```

---

## Troubleshooting

**"Missing config" on startup**
→ Copy `.env.example` to `.env` and fill in all required fields.

**Gmail "Authentication failed"**
→ You need an App Password, not your regular password. See Step 2 of the bot setup.

**Book not arriving on Kindle**
→ Your sender email isn't on Amazon's approved list. Complete Step 4b above.

**No results found**
→ Try a shorter query — just the main title or the author's last name.

**OCR reads wrong text from photo**
→ Make sure Tesseract is installed (`tesseract --version`). Use a well-lit, in-focus photo.

**Railway deploy not starting**
→ Check that `BOT_TOKEN` is set in your Railway environment variables. Logs are under the Deployments tab.

---

## Project structure

```
kindle-master/
├── bot.py          # Telegram bot — entry point for hosted/mobile use
├── main.py         # CLI — entry point for local/terminal use
├── search.py       # Anna's Archive search + Libgen epub download
├── sender.py       # SMTP email delivery to Kindle
├── ocr.py          # Extract book title from photo via Tesseract
├── db.py           # SQLite store for per-user Kindle emails (bot only)
├── config.py       # Loads .env and validates required fields
├── Procfile        # Railway/Render worker process definition
├── nixpacks.toml   # Installs Tesseract on Railway automatically
├── requirements.txt
└── .env.example    # Config template — copy to .env and fill in
```

---

## SMTP providers

| Provider | `SMTP_HOST` | `SMTP_PORT` | Password type |
|---|---|---|---|
| Gmail | `smtp.gmail.com` | `587` | App Password |
| Outlook/Hotmail | `smtp.office365.com` | `587` | App Password |
| iCloud | `smtp.mail.me.com` | `587` | App-specific password |

---

## Contributing

Pull requests welcome. The two core modules are `search.py` (scraping + download) and `sender.py` (email delivery). The bot logic lives entirely in `bot.py`.

---

## Disclaimer

For personal use only. Only download books you own or that are in the public domain in your jurisdiction.
