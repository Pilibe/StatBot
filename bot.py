import discord
from discord.ext import commands
import aiohttp
import urllib.parse
import json

# Setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

API_KEY = "bbd2283628cbc7e2fbd38f16af136389"
BASE_URL = "https://skanderbeg.pm/api.php"

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong!")

def extract_stats(stats):
    if isinstance(stats, dict):
        return stats
    if isinstance(stats, list) and stats:
        if isinstance(stats[0], dict):
            return stats[0]
    return {}

@bot.command()
async def k(ctx, url: str):
    await ctx.send("📊 Fetching and analyzing data...")

    try:
        parsed = urllib.parse.urlparse(url)
        query = urllib.parse.parse_qs(parsed.query)
        save_id = query["id"][0] if "id" in query else parsed.path.split("/")[-1]
    except Exception:
        await ctx.send("❌ Invalid URL format.")
        return

    values = "monthly_income;max_manpower;manpower_recovery;adjustedEffectiveDisci"
    params = {
        "key": API_KEY,
        "scope": "getCountryData",
        "save": save_id,
        "value": values,
        "format": "json"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(BASE_URL, params=params) as resp:
            text = await resp.text()
            try:
                data = json.loads(text)
            except Exception as e:
                print(f"Error parsing JSON:\n{text}\nException: {e}")
                await ctx.send(f"❌ Failed to parse JSON: `{e}`")
                return

    if not isinstance(data, dict) or not data:
        await ctx.send("⚠️ No data found in the save.")
        return

    # First pass: find max values
    max_income = max_manpower = max_recovery = max_discipline = 0
    for tag, stats_raw in data.items():
        stats = extract_stats(stats_raw)
        income = float(stats.get("monthly_income", 0))
        manpower = float(stats.get("max_manpower", 0))
        recovery = float(stats.get("manpower_recovery", 0))
        discipline = float(stats.get("adjustedEffectiveDisci", 0))

        max_income = max(max_income, income)
        max_manpower = max(max_manpower, manpower)
        max_recovery = max(max_recovery, recovery)
        max_discipline = max(max_discipline, discipline)

    # Calculate combined military scores and track max combined military score
    military_raw_scores = {}
    max_combined_military = 0
    for tag, stats_raw in data.items():
        stats = extract_stats(stats_raw)
        manpower = float(stats.get("max_manpower", 0))
        recovery = float(stats.get("manpower_recovery", 0))
        discipline = float(stats.get("adjustedEffectiveDisci", 0))

        # Quantity score out of 100 (average of manpower and recovery ratios)
        quantity_score = 0
        if max_manpower > 0 and max_recovery > 0:
            quantity_score = ((manpower / max_manpower) + (recovery / max_recovery)) / 2 * 100

        # Quality score out of 100
        quality_score = (discipline / max_discipline) * 100 if max_discipline > 0 else 0

        combined = quantity_score + quality_score  # max possible 200
        military_raw_scores[tag] = combined
        max_combined_military = max(max_combined_military, combined)

    # Now compute final scores
    scores = []
    for tag, stats_raw in data.items():
        stats = extract_stats(stats_raw)
        income = float(stats.get("monthly_income", 0))
        economic_score = (income / max_income) * 30 if max_income else 0

        combined = military_raw_scores.get(tag, 0)
        # Scale military to max 70 points
        military_score = (combined / max_combined_military) * 70 if max_combined_military else 0

        total_score = economic_score + military_score
        scores.append((tag, total_score, economic_score, military_score))

    # Sort and send results
    scores.sort(key=lambda x: x[1], reverse=True)
    lines = ["Kocur Score (Eco + Mil)\n"]
    for rank, (tag, total, eco, mil) in enumerate(scores[:20], 1):
        lines.append(f"{rank:2}. {tag} – {total:.2f} pts (Eco: {eco:.2f}, Mil: {mil:.2f})")

    await ctx.send("```\n" + "\n".join(lines) + "\n```")
@bot.command(name='devranking')
async def dc(ctx):
    # Sort the data by dev_total in descending order
    sorted_data = sorted(data.items(), key=lambda x: x[1].get("dev_total", 0), reverse=True)

    # Create the ranking message
    ranking_message = "**🏆 Developer Ranking (by dev_total)**\n\n"
    for rank, (user_id, stats) in enumerate(sorted_data, start=1):
        dev_total = stats.get("dev_total", 0)
        ranking_message += f"{rank}. <@{user_id}> — {dev_total} dev points\n"

    await ctx.send(ranking_message)

import os
TOKEN = os.getenv("DISCORD_TOKEN")

bot.run(TOKEN)

