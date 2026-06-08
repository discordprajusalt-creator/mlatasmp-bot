import os
import json
import asyncio
from openai import AsyncOpenAI, APIError, RateLimitError, APITimeoutError
from typing import Dict, Any, Optional

class AIService:
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("GITHUB_TOKEN is required for GitHub Models")

        self.client = AsyncOpenAI(
            base_url="https://models.github.ai/inference",
            api_key=self.token,
        )
        self.model = "openai/gpt-4o"

    async def chat_completion(
        self,
        prompt: str,
        system_prompt: str = "You are a helpful Discord bot assistant.",
        temperature: float = 0.7,
        max_tokens: int = 1000,
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
            await asyncio.sleep(5)
            raise
        except (APITimeoutError, APIError) as e:
            raise RuntimeError(f"GitHub Models API error: {str(e)}") from e
        except Exception as e:
            raise RuntimeError(f"Unexpected AI service error: {str(e)}") from e

    async def structured_analysis(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        """For risk assessments, moderation, etc."""
        response = await self.chat_completion(
            prompt=prompt,
            system_prompt=system_prompt,
            json_mode=True,
            temperature=0.3,
        )
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"error": "Failed to parse structured response", "raw": response}

# Global instance
ai_service = AIService()
