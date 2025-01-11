# libs/open_ai.py
import openai
import logging
import os


class OpenAI:
    def __init__(self, prompt: str):
        self.model = os.environ.get("OPENAI_MODEL")
        self.prompt = prompt
        self.oclient = openai.AsyncOpenAI(
            api_key=os.environ.get("OPENAI_API_KEY")
        )

    async def process_msg(self, message):
        answer = None
        OPENAI_COMPLETION_OPTIONS = {
            "temperature": 0.75,
            "max_tokens": 1000,
            "top_p": 1,
            "frequency_penalty": 0,
            "presence_penalty": 0,
        }
        while answer is None:
            try:
                response = await self.oclient.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "user", "content": self.prompt + message}
                    ],
                    **OPENAI_COMPLETION_OPTIONS
                )
                answer = response.choices[0].message.content
                n_used_tokens = response.usage.total_tokens
                print(f"Used tokens: {n_used_tokens}")
            except openai.APIConnectionError as e:
                logging.error("The server could not be reached")
                # an underlying Exception, likely raised within httpx.
                logging.error(e.__cause__)
            except openai.RateLimitError as e:
                logging.error(
                    "A 429 status code was received; we should back off a bit.")
            except openai.APIStatusError as e:
                logging.error("Another non-200-range status code was received")
                logging.error(e.status_code)
                logging.error(e.response)

        return answer


async def main():
    prompt = "The following is a conversation with an AI assistant. The assistant is helpful, creative, clever, and very friendly."
    openai = OpenAI(prompt)
    answer = await openai.process_msg("What is the meaning of life?")
    print(answer)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
