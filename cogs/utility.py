import discord
from discord.ext import commands
from datetime import timedelta
import time

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ip(self, ctx):
        await ctx.send("Server IP: `play.bonkmc.net`")

    @commands.command(aliases=["discord"])
    async def vanity(self, ctx):
        await ctx.send("Discord URL: `discord.gg/bonknetwork`")

    @commands.command()
    async def avatar(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        embed = discord.Embed(
            title=f"{member.display_name}'s Avatar",
            color=discord.Color.blurple()
        )
        embed.set_image(url=member.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def lockdown(self, ctx):
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(embed=discord.Embed(
            description="🔒 Channel has been locked down.",
            color=discord.Color.red()
        ))

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def unlockdown(self, ctx):
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = None
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(embed=discord.Embed(
            description="🔓 Channel has been unlocked.",
            color=discord.Color.green()
        ))

    @commands.command()
    async def uptime(self, ctx):
        uptime_seconds = int(time.time() - self.bot.launch_time)
        uptime_str = str(timedelta(seconds=uptime_seconds))
        embed = discord.Embed(
            title="🟢 Bot Uptime",
            description=f"`{uptime_str}`",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Utility(bot))