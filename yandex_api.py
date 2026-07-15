import requests
import time
import logging

logger = logging.getLogger(__name__)


class YandexDisk:
    """
    Клиент для работы с REST API Яндекс.Диска.
    Позволяет создавать папки и загружать файлы на диск по публичной ссылке.
    Все запросы выполняются с авторизацией по OAuth-токену.
    Attributes:
        BASE_URL (str): Базовый URL ресурсов Яндекс.Диска.
        headers (dict): Заголовки запросов, содержащие токен.
        timeout (int): Таймаут для HTTP-запросов (сек).
        retries (int): Количество повторных попыток при сбое.
        delay (float): Задержка между попытками (сек).
    """

    BASE_URL = 'https://cloud-api.yandex.net/v1/disk/resources'

    def __init__(self, user_token, timeout=30, retries=3, delay=1.0):
        """
        Инициализация объекта.
        Args:
            user_token (str): OAuth-токен для доступа к Яндекс.Диску.
            timeout (int, optional): Таймаут для запросов (сек). По умолчанию 30.
            retries (int, optional): Количество повторных попыток. По умолчанию 3.
            delay (float, optional): Задержка между попытками (сек). По умолчанию 1.0.
        """
        self.headers = {'Authorization': f'OAuth {user_token}'}
        self.timeout = timeout
        self.retries = retries
        self.delay = delay

    def _request_with_retry(self, method, url, **kwargs):
        """
        Выполняет HTTP-запрос с повторными попытками при ошибках соединения.
        Args:
            method (str): HTTP-метод ('GET', 'POST', 'PUT' и т.д.).
            url (str): Адрес запроса.
            **kwargs: Дополнительные параметры для requests.request (params, data и т.п.).
        Returns:
            requests.Response: Успешный ответ сервера.
        Raises:
            requests.exceptions.RequestException: Если все попытки исчерпаны.
        """
        for attempt in range(self.retries):
            try:
                response = requests.request(method, url, headers=self.headers, timeout=self.timeout, **kwargs)
                response.raise_for_status()
                return response
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                if attempt == self.retries - 1:
                    logger.error(f"The request failed after {self.retries} tries: {url}")
                    raise
                logger.warning(f"The try {attempt+1}/{self.retries} failed: {e}. Retry after {self.delay} sec.")
                time.sleep(self.delay)
        raise requests.exceptions.RequestException("Request failed")

    def create_folder(self, path):
        """
        Создаёт папку на Яндекс.Диске.
        Если папка уже существует, возвращает True (код 409 обрабатывается как успех).
        Args:
            path (str): Относительный путь к папке (например, 'Images' или 'Photos/2025').
        Returns:
            bool: True, если папка создана или уже существует; False в случае других ошибок.
        """
        try:
            logger.info(f"The folder {path} creation")
            response = self._request_with_retry('PUT', self.BASE_URL, params={'path': path})
            if response.status_code in (201, 409):
                if response.status_code == 201:
                    logger.info(f"The folder {path} created")
                else:
                    logger.info(f"The folder {path} does exist")
                return True
            else:
                logger.error(f"Unexpected status {response.status_code} when the folder was creating")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Error of folder {path}: {e} creating")
            return False

    def upload_file(self, path_to_file, file_name, file_url):
        """
        Загружает файл на Яндекс.Диск по публичной ссылке.
        Файл будет сохранён в указанной папке под заданным именем.
        Args:
            path_to_file (str): Путь к папке на диске.
            file_name (str): Имя, под которым сохранить файл.
            file_url (str): Прямая ссылка на файл (должна быть доступна для скачивания).
        Returns:
            bool: True, если загрузка прошла успешно; False при ошибке.
        """
        try:
            logger.info(f"File {file_name} uploading to folder {path_to_file}")
            response = self._request_with_retry('POST', f'{self.BASE_URL}/upload', params={'path': f'{path_to_file}/{file_name}', 'url': file_url})
            if response.status_code == 202:
                logger.info(f"File {file_name} successfully uploaded")
                return True
            else:
                logger.error(f"Unexpected status {response.status_code} when file was loading")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Error {file_name}: {e} of file uploading")
            return False