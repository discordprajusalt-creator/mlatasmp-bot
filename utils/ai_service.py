import os
import json
import asyncio
import logging
from openai import AsyncOpenAI, APIError, RateLimitError, APITimeoutError
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        if not self.token:
            logger.critical("GITHUB_TOKEN environment variable is missing!")
            raise ValueError("GITHUB_TOKEN is required for GitHub Models")

        self.client = AsyncOpenAI(
            base_url="https://models.github.ai/inference",
            api_key=self.token,
        )
        self.model = "openai/gpt-4o"
        logger.info("✅ AI Service initialized with GitHub Models (GPT-4o)")

    async def chat_completion(
        self,
        prompt: str,
        system_prompt: str = "You are a helpful Discord bot assistant.",
        temperature: float = 0.7,
        max_tokens: int = 1200,
        json_mode: bool = False,
    ) -> str:
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ]

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"} if json_mode else None,
            )
            return response.choices[0].message.content.strip()

        except RateLimitError:
            logger.warning("Rate limit hit. Retrying in 8 seconds...")
            await asyncio.sleep(8)
            raise
        except (APITimeoutError, APIError) as e:
            logger.error(f"GitHub Models API error: {e}")
            raise RuntimeError(f"GitHub Models API error: {str(e)}") from e
        except Exception as e:
            logger.exception("Unexpected error in AI service")
            raise RuntimeError(f"AI service error: {str(e)}") from e

    async def structured_analysis(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        response_text = await self.chat_completion(
            prompt=prompt,
            system_prompt=system_prompt,
            json_mode=True,
            temperature=0.2,
            max_tokens=800,
        )
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse failed: {response_text[:300]}")
            return {"error": "Failed to parse JSON response", "raw": response_text}


# Global singleton
ai_service: AIService = AIService()
