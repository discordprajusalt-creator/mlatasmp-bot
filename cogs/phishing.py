import discord
from discord.ext import commands
from utils.ai_service import ai_service
import re
import logging

logger = logging.getLogger(__name__)

class PhishingDetection(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.content:
            return

        urls = re.findall(r'(https?://\S+)', message.content)
        if not urls:
            return

        prompt = f"""Check these URLs for phishing/scam risk:
{urls}

Return JSON: is_phishing (bool), risk_level (LOW/MEDIUM/HIGH), explanation"""

        analysis = await ai_service.structured_analysis(
            prompt,
            "You are a cybersecurity expert specialized in Discord phishing detection."
        )

        if analysis.get("is_phishing") or analysis.get("risk_level") in ["HIGH", "MEDIUM"]:
            await message.delete()
            await message.channel.send(
                f"🚫 Potential phishing link removed from {message.author.mention}",
                delete_after=15
            )


async def setup(bot):
    await bot.add_cog(PhishingDetection(bot))
