#!/usr/bin/env python3
"""
DosZone Telegram Game Bot
=========================
Serves classic DOS games from dos.zone through the Telegram Games API.

Usage:
    1. Create a bot with @BotFather and obtain a token.
    2. Register a game with @BotFather using /newgame; note the short name.
    3. Set GAME_URL to the public URL of the web server (app.py).
    4. Copy .env.example to .env, fill in the values, and run:
           python bot.py
"""

import logging
import os

from dotenv import load_dotenv
from telegram import InlineQueryResultGame, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    InlineQueryHandler,
)

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration — loaded from environment / .env file
# ---------------------------------------------------------------------------

BOT_TOKEN: str = os.environ["BOT_TOKEN"]
GAME_SHORT_NAME: str = os.getenv("GAME_SHORT_NAME", "dangerous_dave")
GAME_URL: str = os.environ["GAME_URL"]

# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Welcome the user and explain available commands."""
    await update.message.reply_text(
        "🕹️ Welcome to DosZone Telegram Games!\n\n"
        "Play classic DOS games directly inside Telegram — "
        "powered by dos.zone with mobile-friendly touch controls.\n\n"
        "Commands:\n"
        "  /game  — Play Dangerous Dave in the Haunted Mansion (1991)\n"
        "  /help  — Show this message"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show help text."""
    await update.message.reply_text(
        "🕹️ DosZone Telegram Games\n\n"
        "Available games:\n"
        "  • Dangerous Dave in the Haunted Mansion (1991)\n\n"
        "Commands:\n"
        "  /game  — Start playing\n"
        "  /help  — Show this message\n\n"
        "Games are powered by dos.zone — a browser-based DOS emulator "
        "with built-in mobile touch controls."
    )


async def game_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the game message so the user can click Play."""
    await update.message.reply_game(GAME_SHORT_NAME)


# ---------------------------------------------------------------------------
# Callback query handler (fires when the user taps the Play button)
# ---------------------------------------------------------------------------


async def callback_query_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Answer a game callback with the URL of the game web page."""
    query = update.callback_query
    if query.game_short_name:
        # Telegram will open this URL in its built-in WebView.
        await query.answer(url=GAME_URL)
    else:
        # Not a game callback — acknowledge without a URL.
        await query.answer()


# ---------------------------------------------------------------------------
# Inline query handler (lets users share the game in any chat)
# ---------------------------------------------------------------------------


async def inline_query_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Return the game as an inline result so it can be shared anywhere."""
    results = [
        InlineQueryResultGame(
            id="dangerous_dave",
            game_short_name=GAME_SHORT_NAME,
        )
    ]
    await update.inline_query.answer(results)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Build the Application and start polling."""
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("game", game_command))
    application.add_handler(CallbackQueryHandler(callback_query_handler))
    application.add_handler(InlineQueryHandler(inline_query_handler))

    logger.info("Bot is running. Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
