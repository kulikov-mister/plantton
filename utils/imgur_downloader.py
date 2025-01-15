# utils/imgur_downloader.py
import os
import asyncio
import aiofiles
from imgurpython import ImgurClient
from tqdm.asyncio import tqdm

Client_ID = "6a1229976958828"
Client_secret = "4a3c33feaf367061898cddbb1c3b0e238f2f13ae"

client = ImgurClient(Client_ID, Client_secret)


def upload_image_from_url(image_url: str):
    response = client.upload_from_url(image_url, anon=True)
    return response['link']


def upload_image_from_path(path: str):
    response = client.upload_from_path(path=path, anon=True)
    return response['link']


source_image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d1/Book_designed_by_Benny_Forsberg_from_the_Noun_Project.svg/240px-Book_designed_by_Benny_Forsberg_from_the_Noun_Project.svg.png"
# image_url = upload_image(source_image_url)
# print(image_url)


async def upload_files_from_directory_to_imgur(directory):
    base_dir = os.path.dirname(os.path.abspath(__file__))

    """Асинхронно читает все файлы в указанной директории."""
    full_dir = f'{base_dir}/{directory}'
    print(full_dir)

    files = []
    for filename in tqdm(os.listdir(full_dir), desc='Uploading on Imgur'):
        filepath = os.path.join(full_dir, filename)
        if os.path.isfile(filepath):  # Проверяем, что это файл, а не директория
            async with aiofiles.open(filepath, mode='r') as f:
                link = upload_image_from_path(f'{full_dir}/{filename}')
                files.append(link)

    print(files)


# if __name__ == "__main__":
    # asyncio.run(read_files_in_directory('icons'))
