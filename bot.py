"""
kindle-master Telegram bot

Commands:
  /start  — intro + quick guide
  /setup  — save your Kindle email
  /info   — show the sender email you need to whitelist on Amazon
  /help   — usage tips
  /clear  — delete recent bot messages from the chat
  /cancel — cancel current operation

Messages:
  Text    — search for a book by title or author
  Photo   — OCR the image and search automatically
"""

import logging
import os
import re
import tempfile

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

import config
from db import get_kindle_email, set_kindle_email
from search import search_books, get_download_urls_for_book, download_book
from sender import send_to_kindle

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s", level=logging.INFO
)
log = logging.getLogger(__name__)

AWAITING_EMAIL = 1

# In-memory cache of search results per user: {user_id: [result_dicts]}
_results_cache: dict[int, list[dict]] = {}

# Track bot message IDs per user so /clear can delete them
_tracked_msgs: dict[int, list[int]] = {}


def _track(user_id: int, msg) -> None:
    """Store a bot message ID for later deletion via /clear."""
    _tracked_msgs.setdefault(user_id, []).append(msg.message_id)


# ── Commands ────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "📚 *kindle-master*\n\n"
        "Send me a book title or author and I'll find the epub and deliver it to your Kindle.\n\n"
        "You can also send a *photo* of a book cover — I'll read it automatically.\n\n"
        "*First time?* Run /setup to save your Kindle email address.",
        parse_mode="Markdown",
    )


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "*How to use*\n\n"
        "• Type a book title or author name → pick from results → sent to Kindle\n"
        "• Send a photo of a book cover → same flow automatically\n\n"
        "*Setup checklist*\n"
        "1. Run /setup and enter your Kindle email\n"
        "2. Run /info to see the sender email\n"
        "3. Add that sender email to your Amazon approved list:\n"
        "   amazon.com → Account → Manage Content & Devices → Preferences → "
        "Personal Document Settings → Approved Personal Document E-mail List\n\n"
        "After that, books land on your Kindle within a minute or two.",
        parse_mode="Markdown",
    )


async def cmd_info(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"The bot sends emails from:\n\n`{config.SENDER_EMAIL}`\n\n"
        "Add this address to your Amazon approved senders list so your Kindle accepts the books:\n\n"
        "amazon.com → Account → Manage Content & Devices → Preferences → "
        "Personal Document Settings → Approved Personal Document E-mail List",
        parse_mode="Markdown",
    )


# ── /clear ────────────────────────────────────────────────────────────────────

async def cmd_clear(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    clear_id = update.message.message_id

    # Attempt to delete the last 200 messages by ID range.
    # Bot messages succeed; user messages fail silently (Telegram restricts that).
    ids = list(range(max(1, clear_id - 199), clear_id + 1))

    # deleteMessages accepts up to 100 IDs at once (Bot API 6.0)
    for i in range(0, len(ids), 100):
        try:
            await ctx.bot.delete_messages(chat_id, ids[i:i + 100])
        except Exception:
            for msg_id in ids[i:i + 100]:
                try:
                    await ctx.bot.delete_message(chat_id, msg_id)
                except Exception:
                    pass

    _tracked_msgs.pop(update.effective_user.id, None)


# ── /setup conversation ──────────────────────────────────────────────────────

async def cmd_setup(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    existing = get_kindle_email(update.effective_user.id)
    hint = f"\n\nYour current address: `{existing}`" if existing else ""
    await update.message.reply_text(
        f"What's your Kindle email address?{hint}\n\n"
        "_(Find it at: amazon.com → Manage Content & Devices → Preferences → "
        "Personal Document Settings)_",
        parse_mode="Markdown",
    )
    return AWAITING_EMAIL


async def save_email(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    email = update.message.text.strip()
    if "@" not in email or "." not in email:
        await update.message.reply_text(
            "That doesn't look like a valid email. Try again, or /cancel."
        )
        return AWAITING_EMAIL

    set_kindle_email(update.effective_user.id, email)
    await update.message.reply_text(
        f"Saved! Sending to: `{email}`\n\n"
        "Make sure you've added the bot's sender address to your Amazon approved list. "
        "Run /info to see what address to add.",
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def cmd_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END


# ── Book search ──────────────────────────────────────────────────────────────

async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.message.text.strip()
    await _search_and_show(update, query)


async def handle_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    msg = await update.message.reply_text("Reading photo...")
    _track(update.effective_user.id, msg)

    photo_file = await update.message.photo[-1].get_file()
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        await photo_file.download_to_drive(tmp.name)
        tmp_path = tmp.name

    try:
        from ocr import extract_text_from_image
        query = extract_text_from_image(tmp_path)
    except Exception as e:
        await msg.edit_text(f"Could not read the photo: {e}")
        return
    finally:
        os.remove(tmp_path)

    if not query.strip():
        await msg.edit_text(
            "Couldn't read any text from that photo. Just type the title instead."
        )
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f'Search "{query[:40]}"', callback_data="ocr:confirm")],
        [InlineKeyboardButton("Type it manually instead", callback_data="ocr:manual")],
    ])
    ctx.user_data["ocr_query"] = query
    await msg.edit_text(
        f"Detected:\n*{query[:80]}*\n\nDoes that look right?",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


async def _search_and_show(update: Update, query: str) -> None:
    user_id = update.effective_user.id

    if not get_kindle_email(user_id):
        await update.message.reply_text(
            "You haven't set your Kindle email yet. Run /setup first."
        )
        return

    status = await update.message.reply_text(f'Searching for "{query}"...')
    _track(user_id, status)

    try:
        import asyncio
        results = await asyncio.to_thread(search_books, query, limit=8)
    except Exception as e:
        await status.edit_text(f"Search failed: {e}")
        return

    if not results:
        await status.edit_text(
            "No epub results found. Try a shorter title or just the author's last name."
        )
        return

    _results_cache[user_id] = results  # cache all 8 for fallback during download

    display = results[:3]  # show top 3 to user
    lines = []
    for i, r in enumerate(display, 1):
        short_title = re.split(r"[:\u2014]", r["title"])[0].strip()
        lines.append(f"{i}. *{short_title}*\n    {r['author']}")

    list_text = "\n\n".join(lines) + "\n\nTap a number to send it to your Kindle:"

    number_buttons = [
        InlineKeyboardButton(str(i + 1), callback_data=f"pick:{i}")
        for i in range(len(display))
    ]
    keyboard = [number_buttons, [InlineKeyboardButton("✕ Cancel", callback_data="pick:cancel")]]

    await status.edit_text(
        list_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


# ── Book selection callback ──────────────────────────────────────────────────

async def handle_pick(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "pick:cancel":
        await query.edit_message_text("Cancelled.")
        return

    user_id = query.from_user.id
    idx = int(query.data.split(":")[1])
    results = _results_cache.get(user_id)

    if not results or idx >= len(results):
        await query.edit_message_text("Session expired. Search again.")
        return

    kindle_email = get_kindle_email(user_id)

    # Try picked result first, then fall through remaining results silently
    candidates = [results[idx]] + [r for i, r in enumerate(results) if i != idx]

    await query.edit_message_text(f'Downloading "{candidates[0]["title"]}"...')

    import asyncio

    # Collect all download URLs from all candidates in parallel
    url_lists = await asyncio.gather(
        *[asyncio.to_thread(get_download_urls_for_book, book) for book in candidates]
    )

    # Flatten to a single ordered list: picked book's URLs first, then fallbacks
    all_urls = [
        (dl_url, book)
        for book, urls in zip(candidates, url_lists)
        for dl_url in urls
    ]

    for dl_url, book in all_urls:
        try:
            safe_title = "".join(c for c in book["title"] if c.isalnum() or c in " _-")[:50]
            dest = os.path.join(tempfile.gettempdir(), f"{user_id}_{safe_title}.epub")
            dest = await asyncio.to_thread(download_book, dl_url, dest)
            size_kb = os.path.getsize(dest) // 1024

            await query.edit_message_text(f"Downloaded {size_kb} KB. Sending to Kindle...")

            send_to_kindle(dest, book["title"], kindle_email=kindle_email)
            os.remove(dest)

            await query.edit_message_text(
                f'"{book["title"]}" is on its way to your Kindle.\n\n'
                f"_Usually arrives within 1–2 minutes._",
                parse_mode="Markdown",
            )
            return

        except Exception as e:
            log.warning("Failed %s | %s: %s", book["title"][:30], dl_url[:50], e)

    await query.edit_message_text(
        "Couldn't download any of the results. Try searching again with a different title."
    )


# ── OCR confirm / manual correction ─────────────────────────────────────────

async def handle_ocr_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "ocr:confirm":
        search_query = ctx.user_data.get("ocr_query", "")
        if not search_query:
            await query.edit_message_text("Session expired. Send the photo again.")
            return
        await query.edit_message_text(
            f'Searching for "*{search_query[:60]}*"...', parse_mode="Markdown"
        )
        await _search_and_show(update, search_query)

    elif query.data == "ocr:manual":
        await query.edit_message_text("Type the book title and I'll search for it:")
        ctx.user_data["awaiting_manual"] = True


async def handle_manual_query(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not ctx.user_data.get("awaiting_manual"):
        await handle_text(update, ctx)
        return
    ctx.user_data.pop("awaiting_manual")
    await _search_and_show(update, update.message.text.strip())


# ── App setup ────────────────────────────────────────────────────────────────

def main() -> None:
    import asyncio
    asyncio.set_event_loop(asyncio.new_event_loop())

    config.validate_bot()

    app = Application.builder().token(config.BOT_TOKEN).build()

    setup_conv = ConversationHandler(
        entry_points=[CommandHandler("setup", cmd_setup)],
        states={AWAITING_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_email)]},
        fallbacks=[CommandHandler("cancel", cmd_cancel)],
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("info", cmd_info))
    app.add_handler(CommandHandler("clear", cmd_clear))
    app.add_handler(setup_conv)
    app.add_handler(CallbackQueryHandler(handle_pick, pattern=r"^pick:"))
    app.add_handler(CallbackQueryHandler(handle_ocr_callback, pattern=r"^ocr:"))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_manual_query))

    log.info("Bot running...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
