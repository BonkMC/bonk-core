import discord
from discord.ext import commands
import random
import json
import aiohttp

ALLOWED_CHANNEL = 1310626256760475659

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def ensure_channel(self, ctx):
        return ctx.channel.id == ALLOWED_CHANNEL or ctx.author.guild_permissions.administrator

    @commands.command()
    async def meme(self, ctx):
        if not await self.ensure_channel(ctx): return
        async with aiohttp.ClientSession() as session:
            async with session.get("https://meme-api.com/gimme") as r:
                if r.status == 200:
                    data = await r.json()
                    embed = discord.Embed(title=data["title"], url=data["postLink"], color=discord.Color.random())
                    embed.set_image(url=data["url"])
                    await ctx.send(embed=embed)

    @commands.command()
    async def dadjoke(self, ctx):
        if not await self.ensure_channel(ctx): return
        async with aiohttp.ClientSession() as session:
            async with session.get("https://icanhazdadjoke.com/", headers={"Accept": "application/json"}) as r:
                data = await r.json()
                embed = discord.Embed(title="Dad Joke", description=data["joke"], color=discord.Color.orange())
                await ctx.send(embed=embed)

    @commands.command()
    async def roast(self, ctx):
        if not await self.ensure_channel(ctx): return
        with open("roasts.json") as f:
            roasts = json.load(f)
        roast = random.choice(roasts)
        embed = discord.Embed(description=roast, color=discord.Color.red())
        await ctx.send(embed=embed)

    @commands.command()
    async def howgay(self, ctx, member: discord.Member = None):
        if not await self.ensure_channel(ctx): return
        member = member or ctx.author
        percent = random.randint(0, 100)
        embed = discord.Embed(description=f"🌈 {member.mention} is **{percent}%** gay!", color=discord.Color.purple())
        await ctx.send(embed=embed)

    @commands.command()
    async def ship(self, ctx, user1: discord.Member, user2: discord.Member):
        if not await self.ensure_channel(ctx): return
        percent = random.randint(0, 100)
        bar = "█" * (percent // 10) + "░" * (10 - percent // 10)
        embed = discord.Embed(
            title="💘 Ship Result",
            description=f"{user1.mention} ❤️ {user2.mention}\nCompatibility: `{percent}%`\n[{bar}]",
            color=discord.Color.magenta()
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def define(self, ctx, *, word):
        if not await self.ensure_channel(ctx): return
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}") as r:
                if r.status != 200:
                    embed = discord.Embed(description=f"No definition found for `{word}`", color=discord.Color.red())
                    await ctx.send(embed=embed)
                    return
                data = await r.json()
                meaning = data[0]['meanings'][0]
                definition = meaning['definitions'][0]['definition']
                part = meaning['partOfSpeech']
                embed = discord.Embed(
                    title=f"📖 Definition of {word}",
                    description=f"**{part}**: {definition}",
                    color=discord.Color.blue()
                )
                await ctx.send(embed=embed)

    @commands.command()
    async def hug(self, ctx, member: discord.Member):
        if not await self.ensure_channel(ctx): return
        embed = discord.Embed(description=f"🤗 {ctx.author.mention} hugged {member.mention}!", color=discord.Color.green())
        await ctx.send(embed=embed)

    @commands.command()
    async def slap(self, ctx, member: discord.Member):
        if not await self.ensure_channel(ctx): return
        embed = discord.Embed(description=f"👋 {ctx.author.mention} slapped {member.mention}!", color=discord.Color.red())
        await ctx.send(embed=embed)

    @commands.command()
    async def pat(self, ctx, member: discord.Member):
        if not await self.ensure_channel(ctx): return
        embed = discord.Embed(description=f"✨ {ctx.author.mention} patted {member.mention}!", color=discord.Color.blurple())
        await ctx.send(embed=embed)

    @commands.command(name="8ball")
    async def _8ball(self, ctx, *, question: str):
        if not await self.ensure_channel(ctx): return
        responses = [
            "Yes.", "No.", "Maybe.", "Absolutely!", "Definitely not.", "Try again later.",
            "It is certain.", "Very doubtful.", "Without a doubt.", "Ask again tomorrow."
        ]
        answer = random.choice(responses)
        embed = discord.Embed(
            title="🎱 The Magic 8-Ball Says...",
            description=f"**Q:** {question}\n**A:** {answer}",
            color=discord.Color.dark_teal()
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Fun(bot))
