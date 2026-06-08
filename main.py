import discord
from discord.ext import commands
import asyncio
import logging
import os
import json
from dotenv import load_dotenv
from utils.database import DatabaseManager

load_dotenv()

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("MaltaSMP")

# ── Config ────────────────────────────────────────────────────────────────────
def load_config() -> dict:
    config_path = os.path.join("config", "config.json")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return json.load(f)
    return {}

# ── Bot ───────────────────────────────────────────────────────────────────────
class MaltaSMP(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None,
            case_insensitive=True,
        )
        self.config = load_config()
        self.db: DatabaseManager = None

    async def setup_hook(self):
        # Init database
        self.db = DatabaseManager()
        await self.db.initialize()
        await self.db.migrate_v2()   # add AI/security tables
        log.info("Database initialised.")

        # Load cogs
        cogs = [
            "cogs.admin",
            "cogs.tickets",
            "cogs.moderation",
            "cogs.logs",
            "cogs.invites",
            "cogs.welcome",
            "cogs.automod",
            "cogs.security",
            # ── New AI & security cogs ──────────────────────────────────────
            "cogs.ai_chat",           # AI chatbot (OpenRouter)
            "cogs.ai_moderation",     # AI-powered content moderation
            "cogs.spam_detection",    # Enhanced hybrid spam detection
            "cogs.phishing",          # Phishing / scam link detection
            "cogs.raid_detection",    # Multi-level raid detection
            "cogs.announcements",     # Announcement system with scheduling & templates
            "cogs.help",              # Interactive /help command
        ]
        for cog in cogs:
            try:
                await self.load_extension(cog)
                log.info(f"Loaded cog: {cog}")
            except Exception as e:
                log.error(f"Failed to load cog {cog}: {e}", exc_info=True)

        # Sync slash commands
        try:
            synced = await self.tree.sync()
            log.info(f"Synced {len(synced)} slash commands globally.")
        except Exception as e:
            log.error(f"Failed to sync commands: {e}", exc_info=True)

    async def on_ready(self):
        log.info(f"Logged in as {self.user} (ID: {self.user.id})")
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="Malta SMP",
            )
        )

    async def on_command_error(self, ctx, error):
        log.error(f"Command error: {error}", exc_info=True)

    async def on_error(self, event, *args, **kwargs):
        log.error(f"Unhandled event error in {event}", exc_info=True)

    async def close(self):
        # Clean up the AI service shared aiohttp session
        from utils.ai_service import close_session
        await close_session()
        await super().close()


async def main():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        log.critical("DISCORD_TOKEN environment variable not set!")
        return

    bot = MaltaSMP()
    async with bot:
        await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
