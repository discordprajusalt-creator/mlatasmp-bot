import discord
from discord.ext import commands
import os
import logging
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Bot Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.moderation = True

# Initialize Bot
bot = commands.Bot(
    command_prefix=os.getenv("COMMAND_PREFIX", "!"),
    intents=intents,
    help_command=None  # Disable default help
)

@bot.event
async def on_ready():
    logger.info(f"✅ Bot is online as {bot.user}")
    logger.info(f"Connected to {len(bot.guilds)} servers")
    logger.info("🤖 AI Service: GitHub Models (GPT-4o) - Ready")
    
    # Optional: Change bot status
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name="/chat"
        )
    )

# ====================== OWNER SYNC COMMAND ======================
@bot.tree.command(name="sync", description="Sync slash commands (Owner only)")
async def sync(interaction: discord.Interaction):
    """Sync slash commands"""
    if not await bot.is_owner(interaction.user):
        return await interaction.response.send_message("❌ Only the bot owner can use this command.", ephemeral=True)
    
    await interaction.response.defer()
    try:
        await bot.tree.sync()
        await interaction.followup.send("✅ Slash commands synced successfully!")
        logger.info("Slash commands synced globally")
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        await interaction.followup.send("❌ Failed to sync commands.")

# ====================== LOAD ALL COGS ======================
async def load_cogs():
    cogs = [
        "cogs.ai_chat",
        "cogs.ai_moderation",
        "cogs.spam_detection",
        "cogs.phishing",
        "cogs.raid_detection",
    ]
    
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            logger.info(f"✅ Loaded cog: {cog}")
        except Exception as e:
            logger.error(f"❌ Failed to load {cog}: {e}")

# ====================== MAIN START FUNCTION ======================
async def main():
    # Check required tokens
    if not os.getenv("DISCORD_TOKEN"):
        logger.critical("❌ DISCORD_TOKEN is missing in .env file!")
        return
    
    if not os.getenv("GITHUB_TOKEN"):
        logger.warning("⚠️ GITHUB_TOKEN is missing! AI features will not work.")

    try:
        await load_cogs()
        await bot.start(os.getenv("DISCORD_TOKEN"))
    except discord.LoginFailure:
        logger.critical("❌ Invalid DISCORD_TOKEN. Please check your .env file.")
    except Exception as e:
        logger.critical(f"❌ Failed to start bot: {e}")

if __name__ == "__main__":
    asyncio.run(main())
