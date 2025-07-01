import discord
from discord.ext import commands
from discord.ui import Button, View
import asyncio
import time
import random
import config as c

AppConfig_obj = c.AppConfig()
giveaway_banner = AppConfig_obj.get_giveaway_banner()

class Giveaways(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_giveaway = None

    def parse_duration(self, duration):
        units = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
        try:
            return int(duration[:-1]) * units[duration[-1]]
        except:
            return None

    @commands.group(invoke_without_command=True)
    @commands.has_permissions(manage_messages=True)
    async def giveaway(self, ctx):
        await ctx.send("Use `*giveaway create`, `*giveaway reroll`, or `*giveaway cancel`")

    @giveaway.command()
    @commands.has_permissions(manage_messages=True)
    async def create(self, ctx, duration: str, winners: int, *, prize: str):
        if self.active_giveaway:
            await ctx.send("A giveaway is already running.")
            return

        seconds = self.parse_duration(duration)
        if not seconds:
            await ctx.send("Invalid duration. Use formats like `1m`, `2h`, `1d`.")
            return

        end_time = int(time.time()) + seconds
        banner_url = giveaway_banner
        entries = []

        embed = discord.Embed(
            title=f"🎉 Giveaway: {prize} 🎉",
            description="Press the button below to join the giveaway!\n\n🔔 Everyone is invited!",
            color=discord.Color.blurple()
        )
        embed.add_field(name="🎁 Prize:", value=f"`{prize}`", inline=False)
        embed.add_field(name="🏆 Winners:", value=str(winners), inline=True)
        embed.add_field(name="⏳ Ends:", value=f"<t:{end_time}:R>", inline=True)
        if banner_url:
            embed.set_image(url=banner_url)
        embed.set_footer(text=f"Hosted by: {ctx.author} • {discord.utils.utcnow():%H:%M}")

        view = View(timeout=None)

        async def update_buttons():
            view.clear_items()

            # Join Button
            join_button = Button(label="Enter", style=discord.ButtonStyle.green)

            async def join_callback(interaction: discord.Interaction):
                if interaction.user.id in entries:
                    await interaction.response.send_message("You’ve already entered!", ephemeral=True)
                else:
                    entries.append(interaction.user.id)
                    await interaction.response.send_message("You joined the giveaway!", ephemeral=True)
                    await update_buttons()
                    await message.edit(view=view)

            join_button.callback = join_callback
            view.add_item(join_button)

            # Entries Button (disabled)
            entries_button = Button(label=f"Entries: {len(entries)}", style=discord.ButtonStyle.grey, disabled=True)
            view.add_item(entries_button)

        await update_buttons()
        message = await ctx.send(embed=embed, view=view)

        self.active_giveaway = {
            "message_id": message.id,
            "channel_id": ctx.channel.id,
            "prize": prize,
            "winners": winners,
            "end": end_time,
            "entries": entries,
            "view": view,
            "message": message
        }

        await asyncio.sleep(seconds)
        await self.end_giveaway()

    async def end_giveaway(self):
        giveaway = self.active_giveaway
        if not giveaway:
            return

        channel = self.bot.get_channel(giveaway["channel_id"])
        entries = giveaway["entries"]
        winners = giveaway["winners"]
        prize = giveaway["prize"]

        if not entries:
            await channel.send("🎉 Giveaway ended! Nobody entered.")
        else:
            selected = random.sample(entries, min(winners, len(entries)))
            mentions = ", ".join(f"<@{uid}>" for uid in selected)

            embed = discord.Embed(
                title="🎉 Giveaway Ended!",
                description=(
                    f"Congratulations to {mentions}!\n\n"
                    f"🎁 **Prize:** {prize}\n"
                    f"📝 Create a ticket in <#1224177644699123765> to claim your reward within **24 hours**.\n"
                    f"⏱️ If not claimed in time, it will be rerolled."
                ),
                color=discord.Color.gold()
            )
            await channel.send(embed=embed)

        giveaway["view"].stop()
        self.active_giveaway = None

    @giveaway.command()
    @commands.has_permissions(manage_messages=True)
    async def reroll(self, ctx):
        if not self.active_giveaway:
            await ctx.send("No active giveaway to reroll.")
            return
        entries = self.active_giveaway["entries"]
        winners = self.active_giveaway["winners"]
        prize = self.active_giveaway["prize"]
        if not entries:
            await ctx.send("No entries to choose from.")
            return
        selected = random.sample(entries, min(winners, len(entries)))
        mentions = ", ".join(f"<@{uid}>" for uid in selected)
        await ctx.send(f"🔁 Rerolled winners: {mentions}\nPrize: **{prize}**")

    @giveaway.command()
    @commands.has_permissions(manage_messages=True)
    async def cancel(self, ctx):
        if not self.active_giveaway:
            await ctx.send("No active giveaway to cancel.")
            return
        self.active_giveaway["view"].stop()
        self.active_giveaway = None
        await ctx.send("The giveaway has been cancelled.")


async def setup(bot):
    await bot.add_cog(Giveaways(bot))
