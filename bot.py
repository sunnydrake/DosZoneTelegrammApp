sunnydrake@tr1:/bulk_pool/Dev/tgDosZone/tgDosZone$ cat bot.py
#!/usr/bin/env python3
import json
import logging
import os
import sys
import urllib.parse
import urllib.request
import socket
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from dotenv import load_dotenv
from telegram import (
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineQueryResultGame,
    Update
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    InlineQueryHandler,
    MessageHandler,
    filters,
)
from telegram.request import HTTPXRequest

# 1. Clean Logging (Info level hides the raw network handshakes)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BOT_TOKEN: str = os.environ.get("BOT_TOKEN", "").strip()
GAME_SHORT_NAME: str = os.getenv("GAME_SHORT_NAME", "dangerous_dave")
GAME_URL: str = os.environ.get("GAME_URL", "").strip()
GAMES_JSON_HOST: str = os.getenv(
    "GAMES_JSON_HOST", "https://sunnydrake.github.io/DosZoneTelegrammApp/"
)

# Parse base URL for games
GAME_PAGE_BASE_URL = ""
if GAME_URL:
    _p = urllib.parse.urlparse(GAME_URL)
    GAME_PAGE_BASE_URL = urllib.parse.urlunparse(_p._replace(query="", fragment=""))

_GAMES_JSON_URL: str = GAMES_JSON_HOST.rstrip("/") + "/games.json"

# ---------------------------------------------------------------------------
# HF Health Check (Port 7860)
# ---------------------------------------------------------------------------
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is active.")
    def log_message(self, format, *args): return

def run_health_check():
    try:
        server = HTTPServer(('0.0.0.0', 7860), HealthCheckHandler)
        server.serve_forever()
    except Exception as e:
        logger.error(f"Health check server error: {e}")

# ---------------------------------------------------------------------------
# Game Data Logic
# ---------------------------------------------------------------------------
def _load_games() -> list[dict]:
    try:
        # Increased timeout for catalog fetch
        with urllib.request.urlopen(_GAMES_JSON_URL, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        logger.error(f"Could not fetch games.json: {exc}")
        return []

GAMES: list[dict] = _load_games()

def _game_url(slug: str) -> str:
    return f"{GAME_PAGE_BASE_URL}?slug={urllib.parse.quote(slug)}"

def _find_games(query: str) -> list[dict]:
    q = query.strip().lower()
    if not q: return GAMES
    return [g for g in GAMES if q in g["title"].lower() or q in g["slug"].lower() or q in g.get("genre", "").lower()]

# ---------------------------------------------------------------------------
# Command Handlers
# ---------------------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🕹️ *Welcome to DosZone Telegram Games!*\n\n"
        "Play classic DOS games with mobile touch controls.\n\n"
        f"  /game  — Play featured ({GAME_SHORT_NAME})\n"
        "  /games — List all available games\n"
        "  /help  — Show instructions",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🕹️ *DosZone Help*\n\nCatalog size: {len(GAMES)} games.\n\n"
        "Commands:\n"
        "• `/game <name>` — Search for a game\n"
        "• `/games` — List by genre\n\n"
        "You can also use me inline: type `@bot_username` in any chat.",
        parse_mode="Markdown"
    )

async def games_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not GAMES:
        await update.message.reply_text("Catalog currently empty.")
        return
    by_genre = {}
    for g in GAMES:
        gen = g.get("genre", "other").capitalize()
        by_genre.setdefault(gen, []).append(g)

    lines = ["🕹️ *DOS Game Catalog:*\n"]
    for genre, g_list in sorted(by_genre.items()):
        lines.append(f"*{genre}*")
        for g in g_list:
            url = _game_url(g["slug"])
            lines.append(f"  {g.get('icon', '🎮')} [{g['title']} ({g['year']})]({url})")
        lines.append("")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown", disable_web_page_preview=True)

async def game_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_game(GAME_SHORT_NAME)
        return
    matches = _find_games(query)
    if not matches:
        await update.message.reply_text("❌ No games found.")
        return
    g = matches[0]
    url = _game_url(g["slug"])
    await update.message.reply_text(f"{g.get('icon', '🎮')} *{g['title']}* ({g['year']})\n[▶ Play Now]({url})", parse_mode="Markdown")

async def inline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.inline_query.query or ""
    matches = _find_games(q)[:20]
    results = [InlineQueryResultArticle(
        id=g["slug"], title=f"{g.get('icon', '🎮')} {g['title']}",
        input_message_content=InputTextMessageContent(f"🎮 *{g['title']}*\n\n[▶ Play Now]({_game_url(g['slug'])})", parse_mode="Markdown")
    ) for g in matches]
    await update.inline_query.answer(results, cache_time=300)

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q.game_short_name: await q.answer(url=GAME_URL)
    else: await q.answer()

async def traffic_logger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Silent log to verify message arrival without leaking token or data."""
    logger.info(f"Incoming update type: {update.update_id}")

# ---------------------------------------------------------------------------
# Main Execution
# ---------------------------------------------------------------------------
def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is missing. Check HF Secrets.")
        return

    # Start HF Health Server
    threading.Thread(target=run_health_check, daemon=True).start()

    # Setup Application with high-stability timeouts
    t_req = HTTPXRequest(
        connect_timeout=45.0,
        read_timeout=45.0,
        write_timeout=45.0,
        pool_timeout=45.0
    )
    application = Application.builder().token(BOT_TOKEN).request(t_req).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("game", game_command))
    application.add_handler(CommandHandler("games", games_command))
    application.add_handler(InlineQueryHandler(inline_handler))
    application.add_handler(CallbackQueryHandler(callback_handler))
    application.add_handler(MessageHandler(filters.ALL, traffic_logger), group=1)

    logger.info("🚀 Starting polling. Token is hidden.")

    try:
        # bypass_clean=True equivalent (drop_pending_updates=False)
        # to avoid the deleteWebhook TLS hang
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=False,
            close_loop=False
        )
    except Exception as e:
        logger.error(f"Critical error during polling: {e}")

if __name__ == "__main__":
    main()
