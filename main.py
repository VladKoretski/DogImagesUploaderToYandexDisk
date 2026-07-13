# from settings import TOKEN
#
# print(TOKEN)

import os
from dotenv import load_dotenv

load_dotenv() #загружает все из .env

print(os.environ.items())
token = os.getenv('YANDEX_DISK_TOKEN')
print(token)
