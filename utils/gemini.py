# tools/gemini.py
import httpx
import asyncio
import json


# api_key = 'AIzaSyDU81JJpqxtevD0EFYhX1UQhu9MeUqpqeE'


class GeminiClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.model = "gemini-1.5-flash"
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{
            self.model}:"

    #  генерирует текст
    async def generate_text(self, prompt: str):
        max_retries = 3  # Максимальное количество попыток
        retry_delay = 5  # Время ожидания между попытками в секундах

        for attempt in range(max_retries):
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.post(
                        f"{self.base_url}generateContent?key={self.api_key}",
                        headers={"Content-Type": "application/json"},
                        json={"contents": [{"parts": [{"text": prompt}]}]},
                        timeout=240.0,
                    )
                    response.raise_for_status()
                    result = response.json()
                    return True, result['candidates'][0]['content']['parts'][0]['text']

                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 429:  # Too Many Requests
                        if attempt < max_retries - 1:
                            retry_after = int(e.response.headers.get(
                                "Retry-After", retry_delay))
                            print(
                                f"Rate limited. Retrying after {retry_after} seconds...")
                            await asyncio.sleep(retry_after)
                            continue  # Переходим к следующей попытке
                        else:
                            print(f"Rate limited after multiple retries. Giving up.")
                            return None, 'Rate limited after multiple retries. Giving up.'
                    else:
                        print(f"HTTP error occurred: {e}")
                        if e.response.content:
                            details = e.response.json()
                            print(details)
                        return None, details

                except httpx.RequestError as e:
                    print(f"An error occurred during the request: {e}")
                    return None, e
                except KeyError as e:
                    print(
                        # added check for response existence
                        f"Unexpected response format: Missing key {e}. Response: {response.text if response else 'No response'}")
                    return None, e
                except Exception as e:
                    print(f"An unexpected error occurred: {e}")
                    return None, e

    # закрывает клиент
    async def close(self):
        ...
#


async def main():
    prompt = "Напиши статью про мобильное образование в telegram"
    client = GeminiClient('AIzaSyDU81JJpqxtevD0EFYhX1UQhu9MeUqpqeE')
    r, generated_text = await client.generate_text(prompt)
    if r:
        print(generated_text)


# if __name__ == "__main__":
#     asyncio.run(main())
