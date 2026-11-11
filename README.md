# HyoukaBot Discord Bot

HyoukaBot is an anime-focused Discord bot built with discord.py, offering anime search, recommendations, character lookups, and anime information through Discord slash commands, plus configurable-prefix text commands.

## Install

1. Install Python and create a Discord application and bot in the Discord Developer Portal.
2. Invite the bot to your server with the `bot` and `applications.commands` scopes. Grant it permission to send messages and embed links.
3. Download the project files and install dependencies:
   `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and set `DISCORD_TOKEN` to your bot token. Optionally change `COMMAND_PREFIX`, which defaults to `!`.
5. In the Developer Portal, enable the Message Content Intent for the bot.
6. Start the bot with:
   `python main.py`

## Use

Use these slash commands in your server:

- `/anime name` to show information about an anime.
- `/animesearch name` to search for up to five anime titles.
- `/randomanime` to get a random anime.
- `/topanime page` to view a page of the top anime list, from 1 to 10.
- `/character name` to find an anime character.
- `/waifu` to pick a popular character.
- `/animequote` to get a quote from the bot’s built-in selection.
- `/animefact` to get a fact based on a random anime.

The bot also provides `!ping`, `!about`, and `!help`. Replace `!` with your configured command prefix if you changed it.

---

More Discord bot projects by EnderDevelopment: https://github.com/EnderDevelopment

Project page: https://dash.enderdevelopment.com/community/ac993dbd-7cd2-4f39-9785-fd11a7fc64d8?utm_source=github&utm_medium=readme&utm_campaign=auto_publish&utm_content=ac993dbd-7cd2-4f39-9785-fd11a7fc64d8
