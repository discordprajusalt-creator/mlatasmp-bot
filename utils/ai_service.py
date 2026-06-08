"""
utils/ai_service.py
───────────────────
Centralized OpenRouter AI service for Malta SMP Bot.

Handles:
  - API calls to OpenRouter with retry + back-off
  - Per-guild rate limiting (token bucket)
  - Response caching (TTL-based, keyed by prompt hash)
  - Fallback responses when the API is unavailable
  - Structured logging for every AI interaction
"""

import asyncio
import hashlib
import json
import logging
import os
import time
from typing import Optional

import aiohttp

log = logging.getLogger("MaltaSMP.AI")

# ── Configuration from environment ───────────────────────────────────────────
AI_PROVIDER = os.getenv("AI_PROVIDER", "github").lower()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_MODEL = os.getenv("GITHUB_MODEL", "openai/gpt-4o")
GITHUB_BASE_URL = "https://models.github.ai/inference/chat/completions"

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

# ── Retry settings ────────────────────────────────────────────────────────────
MAX_RETRIES = 3
BASE_RETRY_DELAY = 1.5   # seconds, doubles each attempt

# ── Cache settings ────────────────────────────────────────────────────────────
CACHE_TTL = 300          # 5 minutes — reuse identical prompt results
MAX_CACHE_SIZE = 500     # maximum number of cached entries

# ── Rate limiting (per guild) ─────────────────────────────────────────────────
# Allow 20 requests per 60 seconds per guild
RATE_LIMIT_CALLS = 20
RATE_LIMIT_WINDOW = 60   # seconds


class _RateLimiter:
    """Simple sliding-window rate limiter keyed by guild_id."""

    def __init__(self, max_calls: int, window: float):
        self.max_calls = max_calls
        self.window = window
        # guild_id -> list of timestamps
        self._calls: dict[int, list[float]] = {}

    def is_allowed(self, guild_id: int) -> bool:
        now = time.monotonic()
        calls = self._calls.setdefault(guild_id, [])

        # Evict old entries
        self._calls[guild_id] = [t for t in calls if now - t < self.window]

        if len(self._calls[guild_id]) >= self.max_calls:
            return False

        self._calls[guild_id].append(now)
        return True

    def seconds_until_reset(self, guild_id: int) -> float:
        calls = self._calls.get(guild_id, [])
        if not calls:
            return 0.0
        oldest = min(calls)
        return max(0.0, self.window - (time.monotonic() - oldest))


class _ResponseCache:
    """TTL-based in-memory cache for AI responses."""

    def __init__(self, ttl: int, max_size: int):
        self.ttl = ttl
        self.max_size = max_size
        self._store: dict[str, tuple[str, float]] = {}  # key -> (value, expiry)

    def _key(self, prompt: str, system: str) -> str:
        raw = f"{system}|||{prompt}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def get(self, prompt: str, system: str) -> Optional[str]:
        key = self._key(prompt, system)
        entry = self._store.get(key)
        if entry and time.monotonic() < entry[1]:
            return entry[0]
        if entry:
            del self._store[key]
        return None

    def set(self, prompt: str, system: str, value: str):
        if len(self._store) >= self.max_size:
            # Evict the oldest entry
            oldest = min(self._store.items(), key=lambda x: x[1][1])
            del self._store[oldest[0]]
        key = self._key(prompt, system)
        self._store[key] = (value, time.monotonic() + self.ttl)

    @property
    def size(self) -> int:
        return len(self._store)


# Module-level singletons
_rate_limiter = _RateLimiter(RATE_LIMIT_CALLS, RATE_LIMIT_WINDOW)
_cache = _ResponseCache(CACHE_TTL, MAX_CACHE_SIZE)

# Shared aiohttp session (created lazily, reused)
_session: Optional[aiohttp.ClientSession] = None


def _get_session() -> aiohttp.ClientSession:
    global _session
    if _session is None or _session.closed:
        _session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": "https://malta-smp.discord.bot",
                "X-Title": "Malta SMP Bot",
                "Content-Type": "application/json",
            },
            timeout=aiohttp.ClientTimeout(total=30),
        )
    return _session


async def close_session():
    """Call on bot shutdown to clean up the shared session."""
    global _session
    if _session and not _session.closed:
        await _session.close()
        _session = None


# ── Fallback responses ────────────────────────────────────────────────────────
_FALLBACK_CHAT = (
    "I'm having a bit of trouble connecting right now 🙁  "
    "Please try again in a moment, or ask a staff member for help!"
)

_FALLBACK_MODERATION = None   # None means "skip AI review, use local result only"


async def chat_completion(
    messages: list[dict],
    *,
    system: str = "",
    guild_id: int = 0,
    max_tokens: int = 512,
    temperature: float = 0.7,
    use_cache: bool = True,
) -> str:
    """
    Send a chat completion request to OpenRouter.

    Parameters
    ----------
    messages    : list of {"role": ..., "content": ...} dicts
    system      : system prompt
    guild_id    : used for rate limiting (0 = global/no limit)
    max_tokens  : max response tokens
    temperature : sampling temperature
    use_cache   : whether to check/populate the response cache

    Returns the model's reply text, or a fallback string on failure.
    """
    if AI_PROVIDER == "github" and not GITHUB_TOKEN:
        log.warning("GITHUB_TOKEN not set — returning fallback response")
        return _FALLBACK_CHAT
    if AI_PROVIDER != "github" and not OPENROUTER_API_KEY:
        log.warning("OPENROUTER_API_KEY not set — returning fallback response")
        return _FALLBACK_CHAT

    # Rate limit check
    if guild_id and not _rate_limiter.is_allowed(guild_id):
        wait = _rate_limiter.seconds_until_reset(guild_id)
        log.info(f"Rate limited guild {guild_id} — resets in {wait:.1f}s")
        return f"I'm being used a lot right now! Please wait {int(wait)+1} seconds before chatting again. 🕐"

    # Cache check — only for single-turn style queries
    last_user_msg = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
    if use_cache and last_user_msg:
        cached = _cache.get(last_user_msg, system)
        if cached:
            log.debug(f"Cache hit for guild {guild_id}")
            return cached

    payload = {
        "model": GITHUB_MODEL if AI_PROVIDER == "github" else OPENROUTER_MODEL,
        "messages": [{"role": "system", "content": system}] + messages if system else messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    if AI_PROVIDER == "github":
        session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {GITHUB_TOKEN}",
                "Content-Type": "application/json",
            },
            timeout=aiohttp.ClientTimeout(total=30),
        )
        target_url = GITHUB_BASE_URL
    else:
        session = _get_session()
        target_url = OPENROUTER_BASE_URL
    delay = BASE_RETRY_DELAY

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with session.post(target_url, json=payload) as resp:
                if resp.status == 429:
                    log.warning(f"OpenRouter 429 on attempt {attempt}/{MAX_RETRIES}")
                    if attempt < MAX_RETRIES:
                        await asyncio.sleep(delay)
                        delay *= 2
                        continue
                    return _FALLBACK_CHAT

                if resp.status >= 500:
                    log.warning(f"OpenRouter {resp.status} on attempt {attempt}/{MAX_RETRIES}")
                    if attempt < MAX_RETRIES:
                        await asyncio.sleep(delay)
                        delay *= 2
                        continue
                    return _FALLBACK_CHAT

                if resp.status != 200:
                    body = await resp.text()
                    log.error(f"OpenRouter unexpected {resp.status}: {body[:200]}")
                    return _FALLBACK_CHAT

                data = await resp.json()
                reply = data["choices"][0]["message"]["content"].strip()

                if use_cache and last_user_msg:
                    _cache.set(last_user_msg, system, reply)

                log.info(
                    f"AI response: guild={guild_id} model={OPENROUTER_MODEL} "
                    f"tokens={data.get('usage', {}).get('total_tokens', '?')}"
                )
                return reply

        except asyncio.TimeoutError:
            log.warning(f"OpenRouter timeout on attempt {attempt}/{MAX_RETRIES}")
            if attempt < MAX_RETRIES:
                await asyncio.sleep(delay)
                delay *= 2
        except aiohttp.ClientError as exc:
            log.error(f"OpenRouter network error: {exc}")
            if attempt < MAX_RETRIES:
                await asyncio.sleep(delay)
                delay *= 2

    return _FALLBACK_CHAT


async def moderation_analysis(
    text: str,
    *,
    guild_id: int = 0,
) -> Optional[dict]:
    """
    Ask the AI to analyse a message for harmful content.

    Returns a dict like:
        {
            "flagged": True,
            "category": "harassment",
            "severity": "high",       # low / medium / high
            "action": "timeout",      # warn / delete / timeout / escalate
            "reason": "..."
        }
    or None if the API is unavailable.
    """
    system = (
        "You are a content moderation assistant for a Minecraft Discord server called Malta SMP. "
        "Analyse the provided message for: toxicity, harassment, hate speech, threats, spam, "
        "advertising, scam attempts, NSFW content, or mass-mention abuse. "
        "Respond ONLY with a JSON object — no prose, no markdown fences. "
        "Keys: flagged (bool), category (string), severity (low|medium|high), "
        "action (warn|delete|timeout|escalate), reason (string ≤100 chars). "
        "If the message is safe, set flagged=false and omit other keys."
    )

    messages = [{"role": "user", "content": f"Message to analyse:\n{text[:1500]}"}]

    # Moderation calls are never cached (content is always unique)
    raw = await chat_completion(
        messages,
        system=system,
        guild_id=guild_id,
        max_tokens=200,
        temperature=0.0,
        use_cache=False,
    )

    if raw == _FALLBACK_CHAT:
        return _FALLBACK_MODERATION  # None — caller should fall back to local rules

    # Strip possible markdown fences
    raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()

    try:
        result = json.loads(raw)
        return result if isinstance(result, dict) else None
    except json.JSONDecodeError:
        log.warning(f"AI moderation returned non-JSON: {raw[:200]}")
        return None


async def phishing_analysis(
    text: str,
    urls: list[str],
    *,
    guild_id: int = 0,
) -> Optional[dict]:
    """
    Analyse text + URLs for phishing / scam content.

    Returns dict:
        { "malicious": bool, "type": str, "confidence": low|medium|high, "reason": str }
    or None on failure.
    """
    system = (
        "You are a security analyst for a Minecraft Discord server. "
        "Determine if the provided message or URLs are a phishing/scam attempt "
        "(Nitro scam, fake giveaway, crypto scam, token grabber, fake Steam/Minecraft login, "
        "URL shortener abuse, fake login page). "
        "Respond ONLY with JSON. Keys: malicious (bool), type (string), "
        "confidence (low|medium|high), reason (string ≤100 chars). "
        "If safe, set malicious=false."
    )

    content = f"Message:\n{text[:800]}\n\nURLs found:\n" + "\n".join(urls[:10])
    messages = [{"role": "user", "content": content}]

    raw = await chat_completion(
        messages,
        system=system,
        guild_id=guild_id,
        max_tokens=200,
        temperature=0.0,
        use_cache=False,
    )

    if raw == _FALLBACK_CHAT:
        return None

    raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
    try:
        result = json.loads(raw)
        return result if isinstance(result, dict) else None
    except json.JSONDecodeError:
        log.warning(f"Phishing AI returned non-JSON: {raw[:200]}")
        return None


def cache_stats() -> dict:
    """Return current cache statistics."""
    return {
        "cache_size": _cache.size,
        "cache_max": MAX_CACHE_SIZE,
        "cache_ttl": CACHE_TTL,
        "rate_limit_calls": RATE_LIMIT_CALLS,
        "rate_limit_window": RATE_LIMIT_WINDOW,
        "model": OPENROUTER_MODEL,
    }
