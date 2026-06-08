import discord
from discord.ext import commands
from utils.ai_service import ai_service
import logging
from collections import defaultdict
import datetime

class RaidDetection(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.join_log = defaultdict(list)
        self.logger = logging.getLogger(__name__)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild_id = member.guild.id
        now = datetime.datetime.utcnow()
        self.join_log[guild_id].append((member, now))

        # Clean old entries
        self.join_log[guild_id] = [(m, t) for m, t in self.join_log[guild_id] if (now - t).total_seconds() < 300]

        if len(self.join_log[guild_id]) >= 8:  # Flood threshold
            await self.analyze_potential_raid(member.guild)

    async def analyze_potential_raid(self, guild: discord.Guild):
        recent_joins = self.join_log[guild.id][-20:]  # Last 20
        data = {
            "join_count": len(recent_joins),
            "time_window_minutes": 5,
            "usernames": [m.name for m, _ in recent_joins],
            "account_ages_days": [(datetime.datetime.utcnow() - m.created_at).days for m, _ in recent_joins],
            "suspicious_patterns": any("discord" in name.lower() or name.isdigit() for name in [m.name for m, _ in recent_joins]),
        }

        prompt = f"""Analyze this potential Discord raid. Return JSON only:
{json.dumps(data, indent=2)}

Return structure:
{{
  "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
  "reasoning": "detailed explanation",
  "recommended_actions": ["kick", "ban", "verify", ...]
}}"""

        try:
            analysis = await ai_service.structured_analysis(
                prompt,
                "You are an expert Discord security analyst specializing in raid detection."
            )
            self.logger.info(f"AI Raid Analysis: {analysis}")

            if analysis.get("risk_level") in ["HIGH", "CRITICAL"]:
                await self.trigger_protection(guild, analysis)
        except Exception as e:
            self.logger.error(f"Raid analysis failed: {e}")

    async def trigger_protection(self, guild, analysis):
        # Example: Lockdown, notify admins, etc.
        await guild.text_channels[0].send(f"🚨 **HIGH RISK RAID DETECTED** - {analysis['reasoning']}")
        # Implement auto-kick/ban/verification as needed
