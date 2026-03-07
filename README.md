# kindle-master

> See a book. Want it on your Kindle. Done in 30 seconds.

Send a book title — or a photo of the cover — to a Telegram bot. It finds the epub, downloads it, and delivers it to your Kindle automatically.

```
You: "Atomic Habits"
Bot: [shows 3 results as buttons]
You: [tap first result]
Bot: "Atomic Habits is on its way to your Kindle."
```

Works on your phone. No terminal required.

---

## How it works

```
Your message → Anna's Archive (search) → Libgen (download) → your Kindle email → Kindle
```

Anna's Archive is the largest book index online. Libgen hosts the actual files. This tool connects them and emails the result straight to your Kindle.

---

## Roles

There are two roles:

- **Deployer** — the person who hosts the bot (you, if you're reading this). Done once.
- **User** — anyone who messages the bot on Telegram, including yourself. Each user does a 2-minute setup the first time.

If you just want to use someone else's already-deployed bot, skip to [User setup](#user-setup).

---

## Deployer Setup

You're setting up the bot so you (and optionally others) can use it from Telegram. Do this once.

### 1. Create a Telegram bot

1. Open Telegram on your phone or desktop
2. Search for **@BotFather** (blue checkmark, official)
3. Tap **Start** or send `/start`
4. Send `/newbot`
5. It asks for a **name** — this is the display name, e.g. `Kindle Master`
6. It asks for a **username** — must end in `bot`, e.g. `kindlemaster_bot`
7. BotFather replies with your token:
   ```
   Use this token to access the HTTP API:
   7123456789:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
   Copy and save this token — you'll need it in Step 4.

---

### 2. Create a Gmail App Password

The bot sends emails from your Gmail to deliver books to Kindle. Gmail requires an App Password (your regular password won't work).

1. Go to [myaccount.google.com](https://myaccount.google.com) and sign in
2. Click **Security** in the left sidebar
3. Under "How you sign in to Google", click **2-Step Verification** and turn it on if it isn't already
4. In the search bar at the top of your Google Account page, type **App Passwords** and click it
   - Direct link: [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
5. Under "App name", type anything — e.g. `kindle-master`
6. Click **Create**
7. Google shows a 16-character password like `abcd efgh ijkl mnop` — **copy it now**, it won't be shown again

---

### 3. Fork this repo

1. Click **Fork** at the top-right of this GitHub page
2. Leave all settings as default and click **Create fork**

You now have your own copy at `github.com/YOUR_USERNAME/kindle-master`.

---

### 4. Deploy to Railway

Railway runs the bot in the cloud for free.

1. Go to [railway.app](https://railway.app) and click **Login** → **Login with GitHub**
2. Authorize Railway to access your GitHub
3. Click **New Project**
4. Click **Deploy from GitHub repo**
5. Find and select your forked `kindle-master` repo
6. Railway starts deploying — wait for it to finish (usually under a minute)
7. Click on the service that was created, then click the **Variables** tab
8. Add each of these variables by clicking **New Variable**:

   | Variable | Value | Notes |
   |---|---|---|
   | `BOT_TOKEN` | `7123456789:AAFxxx...` | From BotFather in Step 1 |
   | `SENDER_EMAIL` | `you@gmail.com` | The Gmail you created the App Password for |
   | `SENDER_PASSWORD` | `abcd efgh ijkl mnop` | The 16-character App Password from Step 2 |
   | `SMTP_HOST` | `smtp.gmail.com` | Leave as-is for Gmail |
   | `SMTP_PORT` | `587` | Leave as-is |

9. After adding all variables, Railway automatically redeploys the bot
10. Click the **Deployments** tab → click the latest deployment → you should see logs ending in `Bot running...`

Your bot is live. Open Telegram, search for your bot's username, and send `/start` to confirm it responds.

> **Railway free tier note:** Railway's free tier includes 500 hours/month, which isn't enough for an always-on bot. To run 24/7 for free, use **Render** instead (see [Alternative: Render](#alternative-render-free-always-on) below), or upgrade to Railway's $5/month Hobby plan.

---

### Alternative: Render (free, always-on)

Render's free Background Worker tier runs continuously at no cost.

1. Go to [render.com](https://render.com) and sign up / log in with GitHub
2. Click **New** → **Background Worker**
3. Select your forked `kindle-master` repo → click **Connect**
4. Fill in the service settings:
   - **Name:** `kindle-master` (or anything)
   - **Region:** pick the one closest to you
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
5. Scroll down to **Environment Variables** and add the same 5 variables from the Railway table above
6. Click **Create Background Worker**
7. Render builds and starts the bot — check the **Logs** tab for `Bot running...`

---

## User Setup

Do this once before you start sending books. Takes about 2 minutes.

### Step 1 — Find your Kindle email

Every Kindle has a unique `@kindle.com` email address. Amazon delivers documents to your device when you email them to this address.

1. Go to [amazon.com](https://www.amazon.com) and sign in
2. Click **Account & Lists** (top right) → **Manage Your Content and Devices**
   - Or go directly: [amazon.com/hz/mycd/myx](https://www.amazon.com/hz/mycd/myx)
3. Click the **Preferences** tab
4. Scroll down to **Personal Document Settings**
5. Under **Send-to-Kindle E-Mail Settings**, find your device and note the address — it looks like:
   ```
   yourname_abc123@kindle.com
   ```

---

### Step 2 — Tell the bot your Kindle email

Open your Telegram bot and send:

```
/setup
```

The bot will ask for your Kindle email address. Paste it in and send. The bot confirms when it's saved.

---

### Step 3 — Approve the sender email on Amazon

Amazon only delivers documents from email addresses you've explicitly approved. You need to add the bot's sending address to your allowlist.

1. In Telegram, send the bot:
   ```
   /info
   ```
   The bot replies with the sender email address, e.g. `youremail@gmail.com`

2. Copy that address

3. Go back to Amazon → **Manage Your Content and Devices** → **Preferences** → **Personal Document Settings** → scroll to **Approved Personal Document E-mail List**
   - Direct link: [amazon.com/hz/mycd/myx#/page/settings/pdoc](https://www.amazon.com/hz/mycd/myx#/page/settings/pdoc)

4. Click **Add a new approved e-mail address**

5. Paste the sender email and click **Add**

That's it. You're ready.

---

## Using the Bot

Open your Telegram bot and just type or send a photo.

**Search by title:**
```
Atomic Habits
```

**Search by author:**
```
James Clear
```

**Photo of a book cover or spine:**
Just attach and send any photo — the bot reads the text automatically.

The bot replies with up to 3 results as tap-able buttons. Tap one and the book is sent to your Kindle. It usually appears within 1–2 minutes.

**All commands:**

| Command | What it does |
|---|---|
| `/start` | Welcome message and quick guide |
| `/setup` | Save or update your Kindle email |
| `/info` | Shows the sender email to add to your Amazon approved list |
| `/help` | Usage tips and setup checklist |
| `/clear` | Delete recent bot messages to clean up the chat |
| `/cancel` | Cancel the current operation |

---

## CLI Setup (optional — desktop only)

If you prefer running the tool from a terminal instead of Telegram.

### Install

```bash
git clone https://github.com/Agrimd15/kindle-master.git
cd kindle-master

python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

For the `--image` feature, install Tesseract:

```bash
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt install tesseract-ocr

# Windows: https://github.com/UB-Mannheim/tesseract/wiki
```

### Configure

```bash
cp .env.example .env
```

Open `.env` and fill in:

```env
SENDER_EMAIL=you@gmail.com
SENDER_PASSWORD=abcd efgh ijkl mnop   # Gmail App Password
KINDLE_EMAIL=yourname_abc@kindle.com  # Your @kindle.com address
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
```

Then add `SENDER_EMAIL` to your Amazon approved senders list (same as User Setup Step 3).

### Run

```bash
source venv/bin/activate

python main.py "Atomic Habits"
python main.py "James Clear" --author
python main.py --image /path/to/photo.jpg
python main.py   # interactive prompt
```

---

## Troubleshooting

**Bot doesn't respond to messages**
→ Check Railway/Render logs for errors. Make sure `BOT_TOKEN` is set correctly — no extra spaces, copied in full from BotFather.

**`Bot running...` appears in logs but /start does nothing**
→ Your `BOT_TOKEN` is wrong or belongs to a different bot. Regenerate it with BotFather (`/mybots` → select your bot → API Token → Revoke and generate new token) and update the variable.

**"You haven't set your Kindle email yet"**
→ Send `/setup` to the bot and paste your `@kindle.com` address.

**Book not arriving on Kindle**
→ The sender email isn't on your Amazon approved list. Send `/info` to get the address, then add it at: Manage Content & Devices → Preferences → Personal Document Settings → Approved Personal Document E-mail List.

**"Authentication failed" error in logs**
→ Your `SENDER_PASSWORD` is your regular Gmail password. It must be an App Password. Create one at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).

**"No results found"**
→ Shorten the query. Try just the main title without the subtitle, or just the author's last name.

**OCR returns wrong text from photo**
→ Use a well-lit photo where the title is clearly visible. Tesseract works best on horizontal text with good contrast.

**Railway bot goes offline after ~20 days**
→ Railway's free tier has a 500 hour/month limit. Either switch to Render (free, no limit) or upgrade to Railway Hobby ($5/month).

---

## Project Structure

```
kindle-master/
├── bot.py            # Telegram bot — for hosted/mobile use
├── main.py           # CLI — for local terminal use
├── search.py         # Anna's Archive search + Libgen epub download
├── sender.py         # SMTP email delivery to Kindle
├── ocr.py            # Extract text from photo via Tesseract
├── db.py             # SQLite store for per-user Kindle emails
├── config.py         # Loads .env, validates required fields
├── Procfile          # Tells Railway/Render to run bot.py as a worker
├── nixpacks.toml     # Installs Tesseract automatically on Railway
├── requirements.txt
└── .env.example      # Config template — copy to .env and fill in
```

---

## Other SMTP Providers

| Provider | `SMTP_HOST` | `SMTP_PORT` | Password |
|---|---|---|---|
| Gmail | `smtp.gmail.com` | `587` | App Password |
| Outlook / Hotmail | `smtp.office365.com` | `587` | App Password |
| iCloud | `smtp.mail.me.com` | `587` | App-specific password |

---

## Disclaimer

For personal use only. Only download books you own or that are in the public domain in your jurisdiction.
