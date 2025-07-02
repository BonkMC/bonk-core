import discord
from discord.ext import commands, tasks
import json
import asyncio
from datetime import datetime, timedelta
import config as c
import os

AppConfig_obj = c.AppConfig()
modlog_channel = int(AppConfig_obj.get_modlog_channel())
WARNS_FILE = os.path.join(os.path.dirname(__file__), "warns.json")

class Moderation(commands.Cog):
    def save_warns(self):
        with open(WARNS_FILE, "w") as f:
            json.dump(self.warn_data, f, indent=2)

    def load_warns(self):
        try:
            with open(WARNS_FILE) as f:
                self.warn_data = json.load(f)
        except FileNotFoundError:
            self.warn_data = {}

    def _expire_user_warns(self, uid: str):
        now = datetime.utcnow()
        kept = []
        for w in self.warn_data.get(uid, []):
            exp = w.get("expires_at")
            if exp is None or datetime.fromisoformat(exp) > now:
                kept.append(w)
        if kept:
            self.warn_data[uid] = kept
        else:
            self.warn_data.pop(uid, None)

    @tasks.loop(minutes=1)
    async def expire_warns(self):
        now = datetime.utcnow()
        changed = False
        for uid in list(self.warn_data.keys()):
            original = len(self.warn_data[uid])
            self.warn_data[uid] = [
                w for w in self.warn_data[uid]
                if (w.get("expires_at") is None)
                   or (datetime.fromisoformat(w["expires_at"]) > now)
            ]
            if not self.warn_data[uid]:
                del self.warn_data[uid]
            if len(self.warn_data.get(uid, [])) != original:
                changed = True
        if changed:
            self.save_warns()

    async def send_modlog(self, ctx, action, target, reason, duration=None):
        channel = self.bot.get_channel(modlog_channel)
        if not channel:
            return
        embed = discord.Embed(title="Moderation Action", color=discord.Color.red())
        embed.add_field(name="Action", value=action, inline=False)
        embed.add_field(name="User", value=str(target), inline=False)
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
        if duration:
            embed.add_field(name="Duration", value=duration, inline=False)
        embed.add_field(name="Reason", value=reason or "Unspecified", inline=False)
        await channel.send(embed=embed)

    async def send_dm(self, member, action, duration, reason):
        try:
            embed = discord.Embed(title="You have been punished", color=discord.Color.red())
            embed.add_field(name="Server", value=member.guild.name, inline=False)
            embed.add_field(name="Action", value=action, inline=False)
            embed.add_field(name="Duration", value=duration or "Permanent", inline=False)
            embed.add_field(name="Reason", value=reason or "Unspecified", inline=False)
            await member.send(embed=embed)
        except:
            pass

    def parse_duration(self, duration_str):
        units = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
        try:
            return int(duration_str[:-1]) * units[duration_str[-1].lower()]
        except:
            return None

    async def send_confirmation(self, ctx, action, member, reason, duration=None):
        embed = discord.Embed(title="✅ Action Successful", color=discord.Color.green())
        embed.add_field(name="Action", value=action, inline=True)
        embed.add_field(name="User", value=member.mention, inline=True)
        if duration:
            embed.add_field(name="Duration", value=duration, inline=True)
        embed.add_field(name="Reason", value=reason or "Unspecified", inline=False)
        msg = await ctx.reply(embed=embed, mention_author=False)
        await asyncio.sleep(60)
        try:
            await msg.delete()
            await ctx.message.delete()
        except:
            pass

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, duration: str = None, *, reason: str = "Unspecified"):
        await self.send_dm(member, "Ban", duration, reason)
        await member.ban(reason=reason, delete_message_days=0)
        await self.send_modlog(ctx, "Ban", member, reason, duration)
        await self.send_confirmation(ctx, "Ban", member, reason, duration)

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = "Unspecified"):
        await self.send_dm(member, "Kick", None, reason)
        await member.kick(reason=reason)
        await self.send_modlog(ctx, "Kick", member, reason)
        await self.send_confirmation(ctx, "Kick", member, reason)

    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def mute(self, ctx, member: discord.Member, duration: str = None, *, reason: str = "Unspecified"):
        seconds = self.parse_duration(duration) if duration else None
        if duration and seconds is None:
            await ctx.send("❌ Invalid duration. Use `10s`, `5m`, `2h`, `1d`, etc.")
            return
        until = discord.utils.utcnow() + timedelta(seconds=seconds) if seconds else None
        try:
            await member.timeout(until, reason=reason)
        except Exception as e:
            await ctx.send(f"❌ Failed to mute: `{e}`")
            return
        await self.send_dm(member, "Mute", duration, reason)
        await self.send_modlog(ctx, "Mute", member, reason, duration)
        await self.send_confirmation(ctx, "Mute", member, reason, duration)

    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def unmute(self, ctx, member: discord.Member):
        await member.timeout(None)
        await self.send_modlog(ctx, "Unmute", member, "Manual unmute")
        await self.send_confirmation(ctx, "Unmute", member, "Manual unmute")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, *, name_tag):
        banned = await ctx.guild.bans()
        for entry in banned:
            user = entry.user
            if str(user) == name_tag:
                await ctx.guild.unban(user)
                await self.send_modlog(ctx, "Unban", user, "Manual unban")
                await self.send_confirmation(ctx, "Unban", user, "Manual unban")
                return
        await ctx.send("User not found in bans.")

    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def warn(self, ctx, member: discord.Member, duration: str = None, *, reason: str = "Unspecified"):
        uid = str(member.id)
        now = datetime.utcnow()

        self._expire_user_warns(uid)

        entry = {
            "reason": reason,
            "timestamp": now.isoformat(),
            "expires_at": None
        }
        if duration:
            secs = self.parse_duration(duration)
            if secs is None:
                return await ctx.send("❌ Invalid duration. Use `10s`, `5m`, `2h`, `1d`, etc.")
            expires = now + timedelta(seconds=secs)
            entry["expires_at"] = expires.isoformat()

        self.warn_data.setdefault(uid, []).append(entry)
        self.save_warns()

        total = len(self.warn_data[uid])
        if total % 3 == 0:
            self._expire_user_warns(uid)
            total = len(self.warn_data.get(uid, []))

            sets = total // 3
            duration_str = f"{sets}d"
            self.warn_data.pop(uid, None)
            self.save_warns()

            return await ctx.invoke(
                self.bot.get_command("mute"),
                member=member,
                duration=duration_str,
                reason="Warns limit reached"
            )

        await self.send_modlog(ctx, "Warn", member, reason)
        await self.send_dm(member, "Warn", None, reason)
        await self.send_confirmation(ctx, "Warn", member, reason)

    @commands.command()
    @commands.has_permissions(view_audit_log=True)
    async def modlogs(self, ctx, member: discord.Member, filter_type=None, page: int = 1):
        uid = str(member.id)
        logs = self.warn_data.get(uid, [])
        if filter_type:
            logs = [w for w in logs if w["reason"].lower().startswith(filter_type.lower())]

        if not logs:
            await ctx.send("No modlogs found.")
            return

        per_page = 10
        start = (page - 1) * per_page
        end = start + per_page
        page_logs = logs[start:end]

        embed = discord.Embed(title=f"Modlogs for {member}", color=discord.Color.orange())
        for i, log in enumerate(page_logs, start=1):
            embed.add_field(
                name=f"#{start + i}",
                value=f"Reason: {log['reason']}\nDate: <t:{int(datetime.fromisoformat(log['timestamp']).timestamp())}:R>",
                inline=False
            )

        if len(logs) > per_page:
            embed.set_footer(text=f"Page {page} • Use ?modlogs {member.mention} {page + 1} for more")

        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, count: int, member: discord.Member = None):
        if count <= 0 or count > 100:
            await ctx.send("Please provide a message count between 1 and 100.")
            return

        def check(m):
            if m.id == ctx.message.id:
                return False
            if member:
                return m.author == member
            return True

        deleted = await ctx.channel.purge(limit=count + 1, check=check)

        if not deleted or len(deleted) <= 1:
            await ctx.send("No matching messages found.")
            return

        user_counts = {}
        for msg in deleted:
            user_counts[msg.author.display_name] = user_counts.get(msg.author.display_name, 0) + 1

        embed = discord.Embed(
            title="🧹 Purge Complete",
            description=f"Deleted `{len(deleted) - 1}` messages.",
            color=discord.Color.green()
        )

        for user, num in user_counts.items():
            embed.add_field(name=user, value=f"{num} messages", inline=False)

        msg = await ctx.send(embed=embed)
        await asyncio.sleep(60)
        try:
            await msg.delete()
            await ctx.message.delete()
        except:
            pass

async def setup(bot):
    await bot.add_cog(Moderation(bot))
