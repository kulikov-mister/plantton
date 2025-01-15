# utils/sonnet_ai.py
#
import os
import logging
import asyncio
import httpx
from anthropic import AsyncAnthropic
from typing import Optional


class SonnetAI:
    def __init__(self):
        api_key = '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'
        self.api_key = os.getenv('ANTHROPIC_API_KEY', api_key)
        self.model = "claude-3-5-sonnet-latest"
        self.client = AsyncAnthropic(
            api_key=self.api_key
        )

    async def generate_sonnet(self, content: str, max_tokens: int = 1024) -> Optional[str]:

        try:
            message = await self.client.messages.create(
                max_tokens=max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": content,
                    }
                ],
                model=self.model,
            )
            return message.content
        except Exception as e:
            err = e.response.json()
            logging.error(err.get('error').get('message'))
        return None


async def main() -> None:
    claude = SonnetAI()
    sonnet = await claude.generate_sonnet("Hello, Claude")
    if sonnet:
        print(sonnet)

# if __name__ == "__main__":
#     asyncio.run(main())
