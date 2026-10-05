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
    """ Генерация уникального имени папки для тестирования"""
    return f"test-folder-{uuid4()}"


@pytest.fixture
def create_and_cleanup_folder(headers, temp_folder):
    """Создаем временную папку и удаляем ее после теста"""
    folder_path = f"disk:/{temp_folder}"
    response = requests.put(ya.BASE_URL, headers=headers, params={'path': folder_path})
    assert response.status_code in [201, 409], f"Ошибка при создании: {response.text}"

    yield temp_folder

    requests.delete(
        ya.BASE_URL,
        headers=headers,
        params={'path': folder_path, 'permanently': 'true'},
    )


@pytest.fixture
def create_new_folder_and_cleanup(headers, temp_folder):
    """Создаёт гарантированно новую папку (ожидает 201) и удаляет после теста."""
    folder_path = f"disk:/{temp_folder}"
    response = requests.put(ya.BASE_URL, headers=headers, params={'path': folder_path})
    assert response.status_code == 201, (
        f"Ожидался 201 при создании, получен {response.status_code}: {response.text}"
    )

    yield temp_folder

    requests.delete(
        ya.BASE_URL,
        headers=headers,
        params={'path': folder_path, 'permanently': 'true'},
    )


# Тесты

def test_create_existing_folder(headers, create_and_cleanup_folder):
    folder = create_and_cleanup_folder
    response = requests.put(
        ya.BASE_URL,
        headers=headers,
        params={'path': f'disk:/{folder}'},
    )
    assert response.status_code == 409


def test_create_folder_invalid_path(headers):
    response = requests.put(
        ya.BASE_URL,
        headers=headers,
        params={'path': 'disk://///'},
    )
    assert response.status_code == 404


def test_create_folder_success(headers, create_new_folder_and_cleanup):
    folder = create_new_folder_and_cleanup

    list_response = requests.get(
        ya.BASE_URL,
        headers=headers,
        params={'path': 'disk:/', 'limit': 1000},
    )
    assert list_response.status_code == 200, list_response.text

    items = list_response.json()['_embedded']['items']
    names = [item['name'] for item in items]

    assert folder in names, (
        f"Папка '{folder}' не найдена в списке. Найдено: {names}"
    )