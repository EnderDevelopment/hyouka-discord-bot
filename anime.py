from __future__ import annotations

import asyncio
import random
from datetime import datetime, timezone
from typing import Any

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

PURPLE = discord.Color.from_rgb(155, 126, 222)
BASE_URL = "https://api.jikan.moe/v4"
FOOTER = "Hyouka Anime System ⛩️"
QUOTES = [
    ("Houtarou Oreki", "If I don't have to do something, I won't do it. If I have to do it, I'll do it quickly."),
    ("Edward Elric", "A lesson without pain is meaningless."),
    ("Kakashi Hatake", "Those who abandon their friends are worse than scum."),
    ("Rintarou Okabe", "The world is not kind. Therefore, it must be."),
]


class JikanError(Exception):
    pass


class JikanClient:
    def __init__(self) -> None:
        self.session: aiohttp.ClientSession | None = None

    async def start(self) -> None:
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=12),
            headers={"User-Agent": "HyoukaBot/1.0"},
        )

    async def close(self) -> None:
        if self.session and not self.session.closed:
            await self.session.close()

    async def get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if self.session is None:
            raise JikanError("API client is not ready.")
        for attempt in range(3):
            try:
                async with self.session.get(f"{BASE_URL}/{endpoint.lstrip('/')}", params=params) as response:
                    if response.status == 429:
                        if attempt < 2:
                            await asyncio.sleep(2 ** attempt)
                            continue
                        raise JikanError("Jikan is rate limiting requests. Please try again shortly.")
                    if response.status >= 500:
                        raise JikanError("Jikan is temporarily unavailable.")
                    if response.status == 404:
                        raise JikanError("No matching result was found.")
                    if response.status != 200:
                        raise JikanError("Jikan returned an unexpected response.")
                    return await response.json()
            except asyncio.TimeoutError as error:
                if attempt == 2:
                    raise JikanError("Jikan took too long to respond.") from error
                await asyncio.sleep(1)
            except aiohttp.ClientError as error:
                raise JikanError("Unable to connect to Jikan right now.") from error
        raise JikanError("Jikan request failed.")


def shorten(text: str | None, limit: int = 700) -> str:
    value = (text or "No synopsis available.").replace("[Written by MAL]", "").strip()
    return value if len(value) <= limit else value[: limit - 3].rstrip() + "..."


def embed(title: str, description: str = "") -> discord.Embed:
    result = discord.Embed(
        title=title,
        description=description,
        colour=PURPLE,
        timestamp=datetime.now(timezone.utc),
    )
    result.set_footer(text=FOOTER)
    return result


def anime_embed(item: dict[str, Any]) -> discord.Embed:
    title = item.get("title") or item.get("title_english") or "Unknown anime"
    result = embed(title, shorten(item.get("synopsis")))
    result.add_field(name="Rating", value=str(item.get("score") or "Not rated"), inline=True)
    result.add_field(name="Episodes", value=str(item.get("episodes") or "Unknown"), inline=True)
    genres = ", ".join(g["name"] for g in item.get("genres", [])) or "Unknown"
    result.add_field(name="Genres", value=genres[:1024], inline=False)
    result.add_field(name="Type", value=str(item.get("type") or "Unknown"), inline=True)
    result.add_field(name="Status", value=str(item.get("status") or "Unknown"), inline=True)
    images = item.get("images") or {}
    jpg = images.get("jpg") or {}
    image = jpg.get("large_image_url") or jpg.get("image_url")
    if image:
        result.set_image(url=image)
    if item.get("url"):
        result.url = item["url"]
    return result


class AnimeView(discord.ui.View):
    def __init__(self, item: dict[str, Any], timeout: float = 180) -> None:
        super().__init__(timeout=timeout)
        if item.get("url"):
            self.add_item(discord.ui.Button(label="View on MyAnimeList", url=item["url"], emoji="🔗"))


class Anime(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.api = JikanClient()

    async def cog_load(self) -> None:
        await self.api.start()

    async def cog_unload(self) -> None:
        await self.api.close()

    async def send_error(self, interaction: discord.Interaction, error: Exception) -> None:
        message = str(error) if isinstance(error, JikanError) else "The anime service is unavailable right now."
        result = embed("Anime system unavailable", message)
        if interaction.response.is_done():
            await interaction.followup.send(embed=result, ephemeral=True)
        else:
            await interaction.response.send_message(embed=result, ephemeral=True)

    async def send_anime(self, interaction: discord.Interaction, item: dict[str, Any]) -> None:
        await interaction.followup.send(embed=anime_embed(item), view=AnimeView(item))

    @app_commands.command(name="anime", description="Show detailed information about an anime")
    @app_commands.describe(name="Anime title")
    async def anime(self, interaction: discord.Interaction, name: str) -> None:
        await interaction.response.defer()
        try:
            data = await self.api.get("anime", {"q": name, "limit": 1, "sfw": "true"})
            if not data.get("data"):
                raise JikanError("No anime matched that title.")
            await self.send_anime(interaction, data["data"][0])
        except Exception as error:
            await self.send_error(interaction, error)

    @app_commands.command(name="animesearch", description="Search for anime titles")
    @app_commands.describe(name="Search terms")
    async def animesearch(self, interaction: discord.Interaction, name: str) -> None:
        await interaction.response.defer()
        try:
            data = await self.api.get("anime", {"q": name, "limit": 5, "sfw": "true"})
            results = data.get("data", [])
            if not results:
                raise JikanError("No anime matched that search.")
            result = embed(f"Anime search: {name}")
            for index, item in enumerate(results, 1):
                result.add_field(
                    name=f"{index}. {item.get('title', 'Unknown')}",
                    value=(
                        f"Score: {item.get('score') or 'N/A'} • Episodes: {item.get('episodes') or 'N/A'}\n"
                        f"{shorten(item.get('synopsis'), 180)}"
                    ),
                    inline=False,
                )
            first_image = (((results[0].get("images") or {}).get("jpg") or {}).get("large_image_url"))
            if first_image:
                result.set_image(url=first_image)
            await interaction.followup.send(embed=result, view=AnimeView(results[0]))
        except Exception as error:
            await self.send_error(interaction, error)

    @app_commands.command(name="randomanime", description="Get a random anime recommendation")
    async def randomanime(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        try:
            data = await self.api.get("random/anime")
            await self.send_anime(interaction, data["data"])
        except Exception as error:
            await self.send_error(interaction, error)

    @app_commands.command(name="topanime", description="Show the current top anime")
    @app_commands.describe(page="Top list page, from 1 to 10")
    async def topanime(self, interaction: discord.Interaction, page: app_commands.Range[int, 1, 10] = 1) -> None:
        await interaction.response.defer()
        try:
            data = await self.api.get("top/anime", {"page": page, "limit": 10, "sfw": "true"})
            result = embed(f"Top anime · page {page}")
            for item in data.get("data", []):
                result.add_field(
                    name=f"#{item.get('rank', '?')} · {item.get('title', 'Unknown')}",
                    value=f"Score: {item.get('score') or 'N/A'} • {item.get('episodes') or '?'} episodes",
                    inline=False,
                )
            await interaction.followup.send(embed=result)
        except Exception as error:
            await self.send_error(interaction, error)

    @app_commands.command(name="character", description="Find an anime character")
    @app_commands.describe(name="Character name")
    async def character(self, interaction: discord.Interaction, name: str) -> None:
        await interaction.response.defer()
        try:
            data = await self.api.get("characters", {"q": name, "limit": 1})
            if not data.get("data"):
                raise JikanError("No character matched that name.")
            item = data["data"][0]
            result = embed(item.get("name", "Unknown character"), shorten(item.get("about")))
            image = (((item.get("images") or {}).get("jpg") or {}).get("image_url"))
            if image:
                result.set_image(url=image)
            result.add_field(name="Favorites", value=str(item.get("favorites", 0)), inline=True)
            if item.get("url"):
                result.url = item["url"]
            await interaction.followup.send(embed=result, view=AnimeView(item))
        except Exception as error:
            await self.send_error(interaction, error)

    @app_commands.command(name="waifu", description="Find a popular anime character")
    async def waifu(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        try:
            data = await self.api.get("characters", {"order_by": "favorites", "sort": "desc", "limit": 25})
            characters = data.get("data", [])
            if not characters:
                raise JikanError("No characters are available right now.")
            item = random.choice(characters)
            result = embed(f"Waifu pick · {item.get('name', 'Unknown')}", shorten(item.get("about")))
            image = (((item.get("images") or {}).get("jpg") or {}).get("image_url"))
            if image:
                result.set_image(url=image)
            await interaction.followup.send(embed=result, view=AnimeView(item))
        except Exception as error:
            await self.send_error(interaction, error)

    @app_commands.command(name="animequote", description="Get a random anime quote")
    async def animequote(self, interaction: discord.Interaction) -> None:
        speaker, quote = random.choice(QUOTES)
        await interaction.response.send_message(embed=embed("Anime quote", f"> {quote}\n\n— **{speaker}**"))

    @app_commands.command(name="animefact", description="Get a random anime fact")
    async def animefact(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        try:
            data = await self.api.get("random/anime")
            item = data["data"]
            fact = (
                f"**{item.get('title', 'This anime')}** premiered in **{item.get('year') or 'an unknown year'}** "
                f"and has a MyAnimeList score of **{item.get('score') or 'not yet rated'}**."
            )
            await interaction.followup.send(embed=embed("Anime fact", fact))
        except Exception as error:
            await self.send_error(interaction, error)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Anime(bot))
