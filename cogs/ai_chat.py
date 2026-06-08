import discord
from discord import app_commands
from discord.ext import commands
from utils.ai_service import ai_service
import logging

logger = logging.getLogger(__name__)

class AIChat(commands.Cog):
    """AI Chat with Dedicated Channel Support"""

    def __init__(self, bot):
        self.bot = bot
        self.ai_channel_id = None  # Will be loaded from config later if needed

    # ====================== ADMIN COMMAND ======================
    @app_commands.command(name="set_aichannel", description="Set the dedicated AI chat channel")
    @app_commands.describe(channel="The channel where users can chat with AI")
    @commands.has_permissions(administrator=True)
    async def set_ai_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        self.ai_channel_id = channel.id
        await interaction.response.send_message(
            f"✅ **AI Chat Channel Set!**\n"
            f"Channel: {channel.mention}\n"
            f"Users can now chat directly with GPT-4o by sending normal messages here.",
            ephemeral=True
        )
        logger.info(f"AI Chat Channel set to #{channel.name} by {interaction.user}")

    # ====================== AUTO AI CHAT IN CHANNEL ======================
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        # Check if message is in the AI dedicated channel
        if message.channel.id == self.ai_channel_id:
            # Ignore messages starting with / (slash commands)
            if message.content.startswith('/'):
                return

            async with message.channel.typing():
                try:
                    response = await ai_service.chat_completion(
                        prompt=message.content,
                        system_prompt="You are a friendly, helpful, and witty Discord assistant. Keep responses concise and engaging.",
                        temperature=0.85,
                        max_tokens=1000,
                    )
                    await message.reply(response[:1900], mention_author=True)
                except Exception as e:
                    logger.error(f"Auto AI response error: {e}")
                    await message.reply("❌ Sorry, I'm having trouble thinking right now. Try again later.")

    # ====================== SLASH COMMANDS (Still Available) ======================

    @app_commands.command(name="chat", description="Chat with GPT-4o")
    @app_commands.describe(message="What do you want to ask?")
    async def chat(self, interaction: discord.Interaction, message: str):
        await interaction.response.defer()
        try:
            response = await ai_service.chat_completion(
                prompt=message,
                system_prompt="You are a friendly, helpful, and witty Discord assistant.",
                temperature=0.85,
            )
            await interaction.followup.send(response[:1900])
        except Exception as e:
            logger.error(f"Chat error: {e}")
            await interaction.followup.send("❌ AI service is temporarily unavailable.")

    @app_commands.command(name="summarize", description="Summarize any text")
    @app_commands.describe(text="The text you want summarized")
    async def summarize(self, interaction: discord.Interaction, text: str):
        await interaction.response.defer()
        prompt = f"Summarize the following text clearly and concisely:\n\n{text}"
        response = await ai_service.chat_completion(prompt, max_tokens=800)
        await interaction.followup.send(response[:1900])

    @app_commands.command(name="explain", description="Explain any topic")
    @app_commands.describe(topic="What do you want explained?")
    async def explain(self, interaction: discord.Interaction, topic: str):
        await interaction.response.defer()
        prompt = f"Explain {topic} in a simple and easy way."
        response = await ai_service.chat_completion(prompt, temperature=0.7)
        await interaction.followup.send(response)

    @app_commands.command(name="joke", description="Get a random joke")
    async def joke(self, interaction: discord.Interaction):
        await interaction.response.defer()
        response = await ai_service.chat_completion("Tell me one funny joke.", temperature=1.0)
        await interaction.followup.send(response)


async def setup(bot):
    await bot.add_cog(AIChat(bot))
    logger.info("✅ AI Chat Cog loaded with Dedicated Channel support")
