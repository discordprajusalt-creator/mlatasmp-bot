import discord
from discord.ext import commands
from utils.ai_service import ai_service
import logging

logger = logging.getLogger(__name__)

class AIModeration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def moderate_message(self, message: discord.Message) -> dict:
        prompt = f"""Analyze this Discord message for toxicity, spam, or rule violations:

Message: "{message.content}"
Author: {message.author} ({message.author.id})
Channel: {message.channel.name}

Return JSON only."""
        
        try:
            result = await ai_service.structured_analysis(
                prompt,
                "You are a strict but fair Discord moderator. Flag harmful content."
            )
            return result
        except Exception as e:
            logger.error(f"Moderation failed: {e}")
            return {"flagged": False, "reason": "AI service error"}

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        analysis = await self.moderate_message(message)
        if analysis.get("flagged", False):
            await message.delete()
            await message.channel.send(
                f"⚠️ Message from {message.author.mention} was removed: {analysis.get('reason', 'Policy violation')}",
                delete_after=10
            )


async def setup(bot):
    await bot.add_cog(AIModeration(bot))
