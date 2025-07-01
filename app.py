import discord
from discord.ext import commands
import json
import os
import asyncio
import time

# Load config
with open("config.json") as f:
    config = json.load(f)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=config["prefix"], intents=intents)

# Track bot uptime
bot.launch_time = time.time()

# Error handler: Only show errors in DM to the command invoker
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandInvokeError) or isinstance(error, commands.MissingRequiredArgument):
        try:
            await ctx.author.send(embed=discord.Embed(
                description=f"❌ {str(error)}",
                color=discord.Color.red()
            ))
        except discord.Forbidden:
            pass

# Cog loader
async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")

@bot.event
async def on_ready():
    print(f"Bot is ready: {bot.user}")

# Main startup
async def main():
    await load_cogs()
    await bot.start(config["token"])

if __name__ == "__main__":
    asyncio.run(main())