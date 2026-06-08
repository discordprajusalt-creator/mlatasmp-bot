import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix=os.getenv("COMMAND_PREFIX", "!"), intents=intents)

@bot.event
async def on_ready():
    logger.info(f"✅ Bot is online as {bot.user}")
    logger.info("AI Service: GitHub Models (GPT-4o)")

# Load all cogs
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

@bot.command()
@commands.is_owner()
async def sync(ctx):
    """Sync slash commands"""
    await bot.tree.sync()
    await ctx.send("✅ Commands synced.")

async def main():
    try:
        # Verify GitHub Token
        if not os.getenv("GITHUB_TOKEN"):
            logger.critical("❌ GITHUB_TOKEN is missing! AI features will not work.")
            return

        await load_cogs()
        await bot.start(os.getenv("DISCORD_TOKEN"))
    except Exception as e:
        logger.critical(f"Failed to start bot: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
