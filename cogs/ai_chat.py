import discord
from discord import app_commands
from discord.ext import commands
from utils.ai_service import ai_service
import logging

logger = logging.getLogger(__name__)

class AIChat(commands.Cog):
    """AI Chat Cog - Only Slash Commands"""

    def __init__(self, bot):
        self.bot = bot

    # ====================== SLASH COMMANDS ======================

    @app_commands.command(name="chat", description="Chat with GPT-4o (GitHub Models)")
    @app_commands.describe(message="What do you want to ask the AI?")
    async def chat(self, interaction: discord.Interaction, message: str):
        """Main chat command"""
        await interaction.response.defer()
        try:
            response = await ai_service.chat_completion(
                prompt=message,
                system_prompt="You are a friendly, helpful, and witty Discord assistant.",
                temperature=0.85,
                max_tokens=1200,
            )
            await interaction.followup.send(response[:1900])
        except Exception as e:
            logger.error(f"Chat error: {e}")
            await interaction.followup.send("❌ AI service is temporarily unavailable. Please try again later.")

    @app_commands.command(name="summarize", description="Summarize any text")
    @app_commands.describe(text="The text you want summarized")
    async def summarize(self, interaction: discord.Interaction, text: str):
        await interaction.response.defer()
        prompt = f"Summarize the following text clearly and concisely:\n\n{text}"
        response = await ai_service.chat_completion(prompt, max_tokens=800)
        await interaction.followup.send(response[:1900])

    @app_commands.command(name="explain", description="Explain any topic in simple terms")
    @app_commands.describe(topic="What do you want explained?")
    async def explain(self, interaction: discord.Interaction, topic: str):
        await interaction.response.defer()
        prompt = f"Explain {topic} in a simple, easy-to-understand way."
        response = await ai_service.chat_completion(prompt, temperature=0.7)
        await interaction.followup.send(response)

    @app_commands.command(name="joke", description="Get a random funny joke")
    async def joke(self, interaction: discord.Interaction):
        await interaction.response.defer()
        response = await ai_service.chat_completion("Tell me one funny joke.", temperature=1.0)
        await interaction.followup.send(response)


async def setup(bot):
    await bot.add_cog(AIChat(bot))
    logger.info("✅ AI Chat Cog loaded (Slash Commands only)")
