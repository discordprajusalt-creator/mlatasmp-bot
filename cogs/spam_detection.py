import discord
from discord.ext import commands
from utils.ai_service import ai_service
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class SpamDetection(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.message_log = defaultdict(list)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        self.message_log[message.author.id].append(message.content)
        if len(self.message_log[message.author.id]) > 10:
            await self.analyze_spam(message)

    async def analyze_spam(self, message: discord.Message):
        recent = self.message_log[message.author.id][-8:]
        prompt = f"""Analyze for spam:
Messages: {recent}
User: {message.author}

Return JSON with: is_spam (bool), confidence (0-1), reason"""
        
        analysis = await ai_service.structured_analysis(
            prompt,
            "You are an expert spam detection system for Discord."
        )
        if analysis.get("is_spam", False) and analysis.get("confidence", 0) > 0.7:
            await message.delete()
            logger.warning(f"Spam detected from {message.author}")


async def setup(bot):
    await bot.add_cog(SpamDetection(bot))
