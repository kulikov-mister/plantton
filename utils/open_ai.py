# libs/open_ai.py
import asyncio
import openai
import logging
import os


class OpenAI:
    def __init__(self, api_key: str = None, prompt: str = None):
        self.model = os.environ.get("OPENAI_MODEL")
        self.prompt = prompt
        api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.oclient = openai.AsyncOpenAI(
            api_key=api_key,
        )
        if api_key is None:
            return None, "OpenAI API key is not set"

    async def generate_text(self, message):
        max_retries = 3  # Максимальное количество попыток
        retry_delay = 5  # Время ожидания между попытками в секундах

        OPENAI_COMPLETION_OPTIONS = {
            "temperature": 0.75,
            "max_tokens": 1000,
            "top_p": 1,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "store": False
        }
        for attempt in range(max_retries):
            try:
                content = message if not self.prompt else self.prompt + message
                response = await self.oclient.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "user", "content": content}
                    ],
                    **OPENAI_COMPLETION_OPTIONS
                )
                n_used_tokens = response.usage.total_tokens
                print(f"Used tokens: {n_used_tokens}")

                # Форматируем вывод в JSON-строку
                raw_content = response.choices[0].message.content.strip()
                return True, raw_content

            except openai.APIConnectionError as e:
                logging.error("The server could not be reached")
                # an underlying Exception, likely raised within httpx.
                logging.error(e.__cause__)
                return None, e.message
            except openai.RateLimitError as e:
                logging.error(
                    "A 429 status code was received; we should back off a bit.")
                if attempt < max_retries:
                    await asyncio.sleep(retry_delay or 1)
                    continue
                else:
                    return None, e.message
            except openai.APIStatusError as e:
                logging.error(e.status_code)
                return None, e.message


async def main():
    from telegra_ph import create_page_without_token

    qt_topics = 10
    query_topics = "мобильное образование в telegram"
    prompt = prompt = f"""
Напиши список из {qt_topics} глав для книги на тему: {query_topics}.
Используй тот язык, на котором написана тема: {query_topics}
Используй list схему:
[ "название 1й главы", "название 2й главы", ..., "название {qt_topics}й главы"]
Верни чистый список без форматирования и лишних символов - [...]
"""
    openai = OpenAI(prompt=prompt)
    r, answer = await openai.generate_text("What is the meaning of life?")
    if r:
        page = await create_page_without_token("test", query_topics, html_content=answer)
        print(page)
        ...

# if __name__ == "__main__":
#     asyncio.run(main())
