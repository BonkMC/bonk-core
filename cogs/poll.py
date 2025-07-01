import discord
from discord.ext import commands
import asyncio
import json
import os

class Polls(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "poll_data.json"
        self.poll_count = self.load_poll_count()

    def load_poll_count(self):
        if not os.path.exists(self.data_file):
            return 1
        with open(self.data_file, "r") as f:
            data = json.load(f)
            return data.get("poll_count", 1)

    def save_poll_count(self):
        with open(self.data_file, "w") as f:
            json.dump({"poll_count": self.poll_count}, f, indent=2)

    @commands.group(invoke_without_command=True)
    async def poll(self, ctx):
        await ctx.send("Use `?poll create <question> <duration>` to create a poll.")

    @poll.command()
    async def create(self, ctx, question: str, duration: str = "1m"):
        time_units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        try:
            seconds = int(duration[:-1]) * time_units[duration[-1]]
        except:
            await ctx.send("Invalid duration format. Use formats like `30s`, `10m`, `1h`, etc.")
            return

        yes_emoji = "<:yes:1388549665644875887>"
        no_emoji = "<:wrong:1388546336135184424>"

        poll_number = self.poll_count
        self.poll_count += 1
        self.save_poll_count()

        # Hidden @everyone mention
        await ctx.send("[||@everyone||]")

        embed = discord.Embed(
            title=f"📊 Poll #{poll_number}",
            description=f"**\n{question}**\n",
            color=discord.Color.blue()
        )
        embed.add_field(name=yes_emoji, value="Yes", inline=True)
        embed.add_field(name=no_emoji, value="No", inline=True)

        poll_msg = await ctx.send(embed=embed)
        await poll_msg.add_reaction(yes_emoji)
        await poll_msg.add_reaction(no_emoji)

        await asyncio.sleep(seconds)

        new_msg = await ctx.channel.fetch_message(poll_msg.id)
        yes_count = 0
        no_count = 0

        for reaction in new_msg.reactions:
            if str(reaction.emoji) == yes_emoji:
                yes_count = reaction.count - 1
            elif str(reaction.emoji) == no_emoji:
                no_count = reaction.count - 1

        if yes_count > no_count:
            result = "✅ **Yes** wins!"
        elif no_count > yes_count:
            result = "❌ **No** wins!"
        else:
            result = "⚖️ It's a **tie**!"

        result_embed = discord.Embed(
            title="⏰ Poll Ended!",
            description=f"**{question}**\n\n{result}",
            color=discord.Color.gold()
        )
        result_embed.add_field(name="📊 Final Results", value=f"Yes: `{yes_count}`\nNo: `{no_count}`")
        await ctx.send(embed=result_embed)

    @poll.command()
    async def reset(self, ctx):
        self.poll_count = 1
        self.save_poll_count()
        await ctx.send("✅ Poll counter has been reset.")

async def setup(bot):
    await bot.add_cog(Polls(bot))
