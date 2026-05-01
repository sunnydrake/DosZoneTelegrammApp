# DosZone Telegram Game Bot

Bring classic DOS browser emulation from [dos.zone](https://dos.zone) into Telegram.  
Players tap **Play** inside any Telegram chat and immediately get the game running with **mobile-friendly touch controls** — no installation required.

The game pages are **static HTML hosted on GitHub Pages** — no web server needed.  
The only process you need to run is `bot.py`.

---

## How it works

```
User → /game → Bot sends game message (Telegram Games API)
             → User taps Play
             → Telegram sends callback_query to bot
             → Bot answers with game.html?slug=<slug>  (GitHub Pages URL)
             → game.html reads ?slug= and does window.location.replace()
             → Telegram WebView navigates directly to dos.zone/mobile/<slug>/
             → dos.zone touch controls are active on phones / tablets
```

> **Why the redirect instead of an iframe?**  
> dos.zone sets `X-Frame-Options` / CSP headers that block it from loading
> inside a nested `<iframe>`.  By redirecting at the top-level navigation
> the Telegram WebView *becomes* the dos.zone page — no iframe involved —
> so the headers don't apply and the game loads correctly.

| File | Purpose |
|------|---------|
| `bot.py` | Telegram bot — handles `/start`, `/game`, `/help` and Play callbacks |
| `docs/games.json` | **Catalog of all games** — add an entry here to add a new game |
| `docs/game.html` | Redirect page — reads `?slug=` and navigates to dos.zone |
| `docs/index.html` | Game list page — fetches `games.json` and renders links dynamically |

---

## Prerequisites

* Python 3.10+
* A Telegram Bot Token from [@BotFather](https://t.me/BotFather)
* A Telegram **Game** registered with BotFather (`/newgame`)
* The `docs/` folder published via GitHub Pages (free, built-in)

---

## Setup

### 1. Enable GitHub Pages

Go to **Settings → Pages** in this repository and set:

* Source: **Deploy from a branch**
* Branch: `main`, folder: `/docs`

Your game pages will be live at:  
`https://sunnydrake.github.io/DosZoneTelegrammApp/`

### 2. Clone and install dependencies

```bash
git clone https://github.com/sunnydrake/DosZoneTelegrammApp.git
cd DosZoneTelegrammApp
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Create the Telegram Bot and Game

1. Open [@BotFather](https://t.me/BotFather) on Telegram.
2. `/newbot` — create a bot, copy the **token**.
3. `/newgame` — register a game under your bot.  
   BotFather will ask for:
   - **Short name** (the `game=` identifier, e.g. `dangerous_dave`) — this is what goes into share links like `t.me/tgDosZone_bot?game=dangerous_dave`
   - A title, description, cover photo, and optionally a GIF

   > **BotFather does not ask for a game URL.**  The URL that Telegram opens when
   > a user taps **Play** is provided dynamically by the bot in its
   > `answer_callback_query` response — that's what `GAME_URL` in `.env` controls.
   > You only need **one** game registration; the bot appends `?slug=<game>` per
   > game in the Play callback, and `game.html` redirects the user to the correct
   > dos.zone page.

### 4. Configure environment variables

```bash
cp .env.example .env
# Edit .env and fill in BOT_TOKEN, GAME_SHORT_NAME, GAME_URL
```

`GAME_URL` is the base URL the bot sends to Telegram when answering a Play
callback (BotFather never stores this).  It should point to the GitHub Pages
`game.html` page **without** a `?slug=` param — the bot appends the slug per game:

```
GAME_URL=https://sunnydrake.github.io/DosZoneTelegrammApp/game.html
```

### 5. Run the bot

```bash
python bot.py
```

That's it — no web server process needed.

---

## Mobile controls

The game page loads the dos.zone **`/mobile/`** URL, which activates
dos.zone's built-in on-screen gamepad overlay.  This makes the game
fully playable on smartphones and tablets without a physical keyboard.

Desktop users get the same URL; dos.zone detects the device and can
show or hide the overlay accordingly.

---

## Adding more games

Adding a game only requires **two changes** — no new HTML files:

### 1. Add an entry to `docs/games.json`

```json
[
  ...,
  {
    "slug": "my-dos-game-1994",
    "title": "My DOS Game",
    "year": 1994,
    "icon": "🎮",
    "short_name": "my_dos_game"
  }
]
```

The `slug` must match the path used on dos.zone (visible in the game's URL).  
The `short_name` should match what you register with BotFather.

### 2. No BotFather changes needed

`/game <name>` works for every game already in the catalog — no additional
BotFather registrations are required.  When the user taps **Play** the bot
passes the correct `?slug=` URL to Telegram at callback time.

The game list on `index.html` updates automatically — it always reads from `games.json`.

---

## Production deployment for the bot

Deploy `bot.py` to any platform that provides a persistent Python process:

* [Render](https://render.com) (free tier, sleeps after inactivity)
* [Railway](https://railway.app) ($5/mo free credit)
* [Fly.io](https://fly.io) (free shared VMs)
* Any VPS

Set `BOT_TOKEN`, `GAME_SHORT_NAME`, and `GAME_URL` as environment variables on your host.

