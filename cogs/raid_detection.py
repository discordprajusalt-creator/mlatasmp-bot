import discord
from discord.ext import commands
from utils.ai_service import ai_service
import logging
from collections import defaultdict
import datetime
import json

logger = logging.getLogger(__name__)

class RaidDetection(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.join_log = defaultdict(list)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild_id = member.guild.id
        now = datetime.datetime.utcnow()
        self.join_log[guild_id].append((member, now))

        # Keep only last 5 minutes
        cutoff = now - datetime.timedelta(minutes=5)
        self.join_log[guild_id] = [(m, t) for m, t in self.join_log[guild_id] if t > cutoff]

        if len(self.join_log[guild_id]) >= 6:  # Potential raid threshold
            await self.analyze_potential_raid(member.guild)

    async def analyze_potential_raid(self, guild: discord.Guild):
        joins = self.join_log[guild.id][-25:]
        data = {
            "join_count": len(joins),
            "time_window_minutes": 5,
            "usernames": [m.name for m, _ in joins],
            "account_ages_days": [(datetime.datetime.utcnow() - m.created_at).days for m, _ in joins],
            "has_suspicious_names": any(any(k in name.lower() for k in ["discord", "nitro", "free", "mod"]) for name in [m.name for m, _ in joins]),
        }

        prompt = f"""Perform a detailed raid risk analysis:

{json.dumps(data, indent=2)}

Respond with JSON only:
{{
  "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
  "reasoning": "detailed explanation",
  "recommended_actions": ["kick_all_new", "lock_channel", "notify_admins", ...]
}}"""

        try:
            analysis = await ai_service.structured_analysis(
                prompt,
                "You are a senior Discord security analyst. Detect raids accurately."
            )
            logger.info(f"AI Raid Analysis for {guild.name}: {analysis.get('risk_level')}")

            if analysis.get("risk_level") in ["HIGH", "CRITICAL"]:
                await self.trigger_raid_protection(guild, analysis)
        except Exception as e:
            logger.error(f"Raid analysis failed: {e}")

    async def trigger_raid_protection(self, guild: discord.Guild, analysis: dict):
        try:
            # Notify admins
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    await channel.send(
                        f"🚨 **RAID DETECTED** - Risk: {analysis.get('risk_level')}\n"
                        f"Reason: {analysis.get('reasoning', 'AI flagged suspicious activity')}"
                    )
                    break
            # TODO: Add auto-verification, slowmode, etc.
        except Exception as e:
            logger.error(f"Failed to trigger protection: {e}")


async def setup(bot):
    await bot.add_cog(RaidDetection(bot))
