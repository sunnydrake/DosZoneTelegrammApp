# DosZone Telegram Game Bot

Bring classic DOS browser emulation from [dos.zone](https://dos.zone) into Telegram.  
Players tap **Play** inside any Telegram chat and immediately get the game running with **mobile-friendly touch controls** — no installation required.

The first supported game is **[Dangerous Dave in the Haunted Mansion (1991)](https://dos.zone/dangerous-dave-in-the-haunted-mansion-1991/)**.

---

## How it works

```
User → /game → Bot sends game message
             → User taps Play
             → Telegram opens game web page (app.py)
             → Page loads dos.zone /mobile/ URL in a full-screen iframe
             → dos.zone touch controls are active on phones / tablets
```

The project is a **thin wrapper** around dos.zone:

| File | Purpose |
|------|---------|
| `bot.py` | Telegram bot — handles `/start`, `/game`, `/help` and Play callbacks |
| `app.py` | Flask web server — serves the game wrapper HTML page |
| `templates/game.html` | Full-screen iframe that embeds the dos.zone mobile game URL |

---

## Prerequisites

* Python 3.10+
* A Telegram Bot Token from [@BotFather](https://t.me/BotFather)
* A Telegram **Game** registered with BotFather (`/newgame`)
* A public HTTPS URL for the web server (ngrok works for local dev)

---

## Setup

### 1. Clone and install dependencies

```bash
git clone https://github.com/sunnydrake/DosZoneTelegrammApp.git
cd DosZoneTelegrammApp
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Create the Telegram Bot and Game

1. Open [@BotFather](https://t.me/BotFather) on Telegram.
2. `/newbot` — create a bot, copy the **token**.
3. `/newgame` — register a game under your bot.  
   - Set the short name to `dangerous_dave` (or anything you prefer).  
   - Set the game URL to your public server address (see step 4).

### 3. Configure environment variables

```bash
cp .env.example .env
# Edit .env and fill in BOT_TOKEN, GAME_SHORT_NAME, GAME_URL
```

### 4. Expose the web server publicly (local development)

Install [ngrok](https://ngrok.com) and run:

```bash
ngrok http 5000
```

Copy the `https://…ngrok-free.app` URL and set:

```
GAME_URL=https://<your-ngrok-id>.ngrok-free.app/game/dangerous-dave
```

Also update the game URL in BotFather (`/editgame → Game URL`).

### 5. Run

Open **two terminals**:

```bash
# Terminal 1 — web server
python app.py

# Terminal 2 — Telegram bot
python bot.py
```

---

## Mobile controls

The game page loads the dos.zone **`/mobile/`** URL, which activates
dos.zone's built-in on-screen gamepad overlay.  This makes the game
fully playable on smartphones and tablets without a physical keyboard.

Desktop users get the same URL; dos.zone detects the device and can
show or hide the overlay accordingly.

---

## Adding more games

1. Add an entry to the `GAMES` dict in `app.py`:

```python
"my-game": {
    "title": "My DOS Game (1994)",
    "slug": "my-dos-game-1994",
    "mobile_url": "https://dos.zone/mobile/my-dos-game-1994/",
    "desktop_url": "https://dos.zone/my-dos-game-1994/",
},
```

2. Add a Flask route in `app.py`:

```python
@app.route("/game/my-game")
def my_game():
    game = GAMES["my-game"]
    return render_template("game.html",
                           game_title=game["title"],
                           game_url=game["mobile_url"],
                           desktop_url=game["desktop_url"])
```

3. Register the new game with BotFather and add a `/command` handler in `bot.py`.

---

## Production deployment

Deploy `app.py` to any platform that provides HTTPS
(Render, Railway, Fly.io, Heroku, a VPS with nginx + Let's Encrypt, …).  
Set the environment variables there and update the game URL in BotFather.

The bot (`bot.py`) can run on the same server or any machine with internet access.

