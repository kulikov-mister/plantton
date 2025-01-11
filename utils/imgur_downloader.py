# utils/imgur_downloader.py
from imgurpython import ImgurClient

Client_ID= "6a1229976958828"
Client_secret= "4a3c33feaf367061898cddbb1c3b0e238f2f13ae"

client = ImgurClient(Client_ID, Client_secret)

def upload_image(image_url):
    """
    Загружает изображение на Imgur и возвращает прямую ссылку на него.
    """
    response = client.upload_from_url(image_url, anon=True)
    return response['link']

# source_image_url = "https://dayhub.ru/upload/000/u1/1/7/zhorzh-dare-photo-normal.png"
# image_url = upload_image(source_image_url)
# print(image_url)