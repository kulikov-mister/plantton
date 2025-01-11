# Description: This file contains the SonnetAI class which is used to generate sonnets using the GPT-2 model.
import logging
import os
import httpx
from typing import Optional


class SonnetAI:
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.endpoint = "https://api.openai.com/v1/engines/gpt-3.5/completions"

    async def generate_sonnet(self, prompt: str, max_tokens: int = 100) -> Optional[str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model,
            "prompt": prompt,
            "max_tokens": max_tokens
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.endpoint, headers=headers, json=data)
                response.raise_for_status()
                return response.json()["choices"][0]["text"]
        except httpx.HTTPStatusError as e:
            logging.error(f"Error generating sonnet: {e}")
        except Exception as e:
            logging.error(f"Error generating sonnet: {e}")
        return None


# Usage:
async def main():
    # Create an instance of SonnetAI
    sonnet_ai = SonnetAI(api_key=os.getenv("OPENAI_API_KEY"),
                         model=os.getenv("OPENAI_MODEL"))
    # Generate a sonnet from a prompt
    sonnet = await sonnet_ai.generate_sonnet("Shall I compare thee to a summer's day?")
    print(sonnet)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
