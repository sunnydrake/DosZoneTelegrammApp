#!/usr/bin/env python3
"""
DosZone Game Web Server
=======================
Serves the HTML game-wrapper pages that Telegram opens when a user taps Play.

Run:
    python app.py

The server must be reachable via a public HTTPS URL (see GAME_URL in .env).
For local development, expose it with ngrok:
    ngrok http 5000
"""

import os

from dotenv import load_dotenv
from flask import Flask, redirect, render_template, url_for

load_dotenv()

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Game catalogue
# Each entry maps a route key to dos.zone metadata.
# The mobile URL uses the /mobile/ path prefix which enables dos.zone's
# built-in touch-control overlay — ideal for phone / tablet users.
# ---------------------------------------------------------------------------

DOSZONE_BASE = "https://dos.zone"

GAMES: dict[str, dict] = {
    "dangerous-dave": {
        "title": "Dangerous Dave in the Haunted Mansion (1991)",
        "slug": "dangerous-dave-in-the-haunted-mansion-1991",
        "mobile_url": f"{DOSZONE_BASE}/mobile/dangerous-dave-in-the-haunted-mansion-1991/",
        "desktop_url": f"{DOSZONE_BASE}/dangerous-dave-in-the-haunted-mansion-1991/",
    },
}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.route("/game/dangerous-dave")
def dangerous_dave():
    """Serve the mobile-optimised game wrapper for Dangerous Dave."""
    game = GAMES["dangerous-dave"]
    return render_template(
        "game.html",
        game_title=game["title"],
        game_url=game["mobile_url"],
        desktop_url=game["desktop_url"],
    )


@app.route("/")
def index():
    """Redirect the root path to the default game."""
    return redirect(url_for("dangerous_dave"))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_ENV") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug)
