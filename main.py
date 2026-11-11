import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

import anime

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = os.getenv("COMMAND_PREFIX", "!")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing. Set it in your .env file.")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)


@bot.event
async def setup_hook() -> None:
    await anime.setup(bot)
    await bot.tree.sync()


@bot.event
async def on_ready() -> None:
    await bot.change_presence(activity=discord.Game(name="HyoukaBot | /anime"))
    print(f"HyoukaBot is online as {bot.user} (ID: {bot.user.id})")


@bot.command(name="ping")
async def ping(ctx: commands.Context) -> None:
    latency_ms = round(bot.latency * 1000)
    await ctx.reply(f"Pong! {latency_ms} ms")


@bot.command(name="about")
async def about(ctx: commands.Context) -> None:
    await ctx.reply("I'm HyoukaBot, a Discord bot built with discord.py.")


@bot.command(name="help")
async def help_command(ctx: commands.Context) -> None:
    await ctx.reply(f"Commands: `{PREFIX}ping`, `{PREFIX}about`, `{PREFIX}help`, and the anime slash commands.")


bot.run(TOKEN)
