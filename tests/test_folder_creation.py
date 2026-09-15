from uuid import uuid4

import pytest
import requests

import os
from dotenv import load_dotenv
import yandex_api as ya

load_dotenv()

YANDEX_DISK_TOKEN = os.getenv('YANDEX_DISK_TOKEN')

@pytest.fixture
def token():
    token = YANDEX_DISK_TOKEN
    if not token:
        pytest.fail("YANDEX_TOKEN не установлен в переменных окружения")
    return token

@pytest.fixture
def headers(token):
    return {
        'Authorization': f'OAuth {token}'
    }

@pytest.fixture
def temp_folder():
    """Генерирует уникальное имя папки"""
    return f"test-folder-{uuid4()}"

@pytest.fixture
def create_and_cleanup_folder(headers, temp_folder):
    """Создаёт папку и удаляет её после теста"""
    folder_path = f"disk:/{temp_folder}"
    # Создание
    response = requests.put(ya.BASE_URL, headers=headers, params={'path': folder_path})
    assert response.status_code in [201, 409], f"Ошибка при создании: {response.text}"

    yield temp_folder  # передаём управление в тест

    # Удаление после теста
    requests.delete(ya.BASE_URL, headers=headers, params={'path': folder_path, 'permanently': 'true'})

def test_create_folder_success(headers, temp_folder):
    response = requests.put(ya.BASE_URL, headers=headers, params={'path': f'disk:/{temp_folder}'})
    assert response.status_code in [201, 409]


def test_create_existing_folder(headers, create_and_cleanup_folder):
    folder = create_and_cleanup_folder
    response = requests.put(ya.BASE_URL, headers=headers, params={'path': f'disk:/{folder}'})
    assert response.status_code == 409


def test_create_folder_invalid_path(headers):
    response = requests.put(ya.BASE_URL, headers=headers, params={'path': 'disk://///'})
    assert response.status_code == 404