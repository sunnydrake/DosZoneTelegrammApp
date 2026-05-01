#!/usr/bin/env python3
"""
DosZone Telegram Game Bot
=========================
Serves classic DOS games from dos.zone through the Telegram Games API.

Usage:
    1. Create a bot with @BotFather and obtain a token.
    2. Register a game with @BotFather using /newgame; note the short name.
    3. Set GAME_URL to the GitHub Pages game URL (see .env.example).
    4. Copy .env.example to .env, fill in the values, and run:
           python bot.py
"""

import json
import logging
import os
import urllib.parse
import urllib.request

from dotenv import load_dotenv
from telegram import InlineQueryResultArticle, InputTextMessageContent, InlineQueryResultGame, Update
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
GAMES_JSON_HOST: str = os.getenv(
    "GAMES_JSON_HOST", "https://sunnydrake.github.io/DosZoneTelegrammApp/"
)

# Base URL of the game page (everything before the ?slug= query string).
# Used to build links for games other than the BotFather-registered one.
_parsed = urllib.parse.urlparse(GAME_URL)
GAME_PAGE_BASE_URL: str = urllib.parse.urlunparse(
    _parsed._replace(query="", fragment="")
)

# ---------------------------------------------------------------------------
# Games catalog — fetched from GAMES_JSON_HOST/games.json
# ---------------------------------------------------------------------------

_GAMES_JSON_URL: str = GAMES_JSON_HOST.rstrip("/") + "/games.json"


def _load_games() -> list[dict]:
    try:
        with urllib.request.urlopen(_GAMES_JSON_URL, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        logger.warning("Could not fetch games.json from %s (%s); falling back to empty list.", _GAMES_JSON_URL, exc)
        return []


GAMES: list[dict] = _load_games()


def _game_url(slug: str) -> str:
    """Return the GitHub Pages URL for a given game slug."""
    return f"{GAME_PAGE_BASE_URL}?slug={urllib.parse.quote(slug)}"


def _find_games(query: str) -> list[dict]:
    """Return games whose title, slug, or genre contains *query* (case-insensitive)."""
    q = query.strip().lower()
    if not q:
        return GAMES
    return [
        g for g in GAMES
        if q in g["title"].lower()
        or q in g["slug"].lower()
        or q in g.get("genre", "").lower()
    ]


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
        f"  /game  — Play the featured game ({GAME_SHORT_NAME})\n"
        "  /games — Browse all available games\n"
        "  /game <name> — Search for a specific game\n"
        "  /help  — Show this message"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show help text."""
    await update.message.reply_text(
        "🕹️ DosZone Telegram Games\n\n"
        f"There are {len(GAMES)} classic DOS games available.\n\n"
        "Commands:\n"
        f"  /game         — Play the featured game ({GAME_SHORT_NAME})\n"
        "  /game <name>  — Search and play a specific game\n"
        "  /games        — Show the full game list\n"
        "  /help         — Show this message\n\n"
        "Games are powered by dos.zone — a browser-based DOS emulator "
        "with built-in mobile touch controls.\n\n"
        "You can also use me inline: type @your_bot_name in any chat to share a game."
    )


async def game_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the registered game, or search for a game by name."""
    query_text = " ".join(context.args) if context.args else ""

    if not query_text:
        # No argument — send the BotFather-registered game via the Games API.
        await update.message.reply_game(GAME_SHORT_NAME)
        return

    matches = _find_games(query_text)
    if not matches:
        await update.message.reply_text(
            f'❌ No games found for "{query_text}".\n\n'
            "Use /games to see the full list."
        )
        return

    if len(matches) == 1:
        game = matches[0]
        url = _game_url(game["slug"])
        await update.message.reply_text(
            f"{game.get('icon', '🎮')} *{game['title']}* ({game['year']})\n"
            f"Genre: {game.get('genre', '—').capitalize()}\n\n"
            f"[▶ Play Now]({url})",
            parse_mode="Markdown",
        )
    else:
        lines = [f'🔍 Found {len(matches)} games for "{query_text}":\n']
        for game in matches[:10]:
            url = _game_url(game["slug"])
            lines.append(
                f"{game.get('icon', '🎮')} [{game['title']} ({game['year']})]({url})"
            )
        if len(matches) > 10:
            lines.append(f"\n_…and {len(matches) - 10} more. Narrow your search._")
        await update.message.reply_text(
            "\n".join(lines),
            parse_mode="Markdown",
            disable_web_page_preview=True,
        )


async def games_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all available games grouped by genre."""
    if not GAMES:
        await update.message.reply_text("No games available yet.")
        return

    # Group by genre
    by_genre: dict[str, list[dict]] = {}
    for game in GAMES:
        genre = game.get("genre", "other").capitalize()
        by_genre.setdefault(genre, []).append(game)

    lines = [f"🕹️ *{len(GAMES)} DOS games available* — tap to play:\n"]
    for genre, game_list in sorted(by_genre.items()):
        lines.append(f"*{genre}*")
        for game in game_list:
            url = _game_url(game["slug"])
            lines.append(
                f"  {game.get('icon', '🎮')} [{game['title']} ({game['year']})]({url})"
            )
        lines.append("")

    lines.append("_Tip: use /game followed by a title or genre to search\\._")

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="MarkdownV2",
        disable_web_page_preview=True,
    )


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
# Inline query handler (lets users share any game in any chat)
# ---------------------------------------------------------------------------


async def inline_query_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Return matching games as inline results so they can be shared anywhere."""
    query_text = update.inline_query.query or ""
    matches = _find_games(query_text)[:20]  # Telegram caps inline results at 50; 20 is readable

    results = []
    for game in matches:
        url = _game_url(game["slug"])
        title = f"{game.get('icon', '🎮')} {game['title']} ({game['year']})"
        description = f"{game.get('genre', '').capitalize()} · dos.zone"
        results.append(
            InlineQueryResultArticle(
                id=game["slug"],
                title=title,
                description=description,
                input_message_content=InputTextMessageContent(
                    message_text=(
                        f"{game.get('icon', '🎮')} *{game['title']}* ({game['year']})\n"
                        f"Genre: {game.get('genre', '—').capitalize()}\n\n"
                        f"[▶ Play Now]({url})"
                    ),
                    parse_mode="Markdown",
                ),
                url=url,
            )
        )

    # If the query is empty and the registered game is in the catalog,
    # also prepend the native Games API result so the Play button works in chats.
    if not query_text:
        registered = next(
            (g for g in GAMES if g.get("short_name") == GAME_SHORT_NAME), None
        )
        if registered:
            results.insert(
                0,
                InlineQueryResultGame(
                    id=f"game_{GAME_SHORT_NAME}",
                    game_short_name=GAME_SHORT_NAME,
                ),
            )

    await update.inline_query.answer(results, cache_time=300)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Build the Application and start polling."""
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("game", game_command))
    application.add_handler(CommandHandler("games", games_command))
    application.add_handler(CallbackQueryHandler(callback_query_handler))
    application.add_handler(InlineQueryHandler(inline_query_handler))

    logger.info("Bot is running. Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
