import discord
from discord.ext import commands
from utils.ai_service import ai_service
import logging

logger = logging.getLogger(__name__)

class AIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="chat", aliases=["ai", "ask"])
    async def chat(self, ctx: commands.Context, *, message: str):
        """Chat with GPT-4o via GitHub Models"""
        async with ctx.typing():
            try:
                response = await ai_service.chat_completion(
                    prompt=message,
                    system_prompt="You are a friendly, witty Discord assistant.",
                    temperature=0.8,
                )
                await ctx.reply(response[:1900], mention_author=True)
            except Exception as e:
                logger.error(f"Chat error: {e}")
                await ctx.reply("❌ Sorry, I'm having trouble connecting to the AI right now.")

    @commands.command(name="summarize")
    async def summarize(self, ctx: commands.Context, *, text: str):
        """Summarize long text"""
        async with ctx.typing():
            prompt = f"Summarize the following in a concise, clear way:\n\n{text}"
            response = await ai_service.chat_completion(prompt, max_tokens=600)
            await ctx.reply(response)


async def setup(bot):
    await bot.add_cog(AIChat(bot))
