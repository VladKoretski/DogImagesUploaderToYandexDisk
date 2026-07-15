import requests
import time
import logging

logger = logging.getLogger(__name__)


class DogBreedsAPI:
    """
    Клиент для работы с публичным API dog.ceo.
    Позволяет получать список пород, подпород, а также случайные изображения
    для одной или всех пород. Результаты запросов кешируются для ускорения
    повторных вызовов.
    """

    def __init__(self, timeout=10, retries=3, delay=0.2):
        """
        Инициализация объекта.
        Args:
            timeout (int, optional): максимальное время ожидания ответа от сервера. По умолчанию 10.
            retries (int, optional): сколько раз повторять запрос при ошибке. По умолчанию 3.
            delay (float, optional): задержка между попытками и между запросами (сек). По умолчанию 0.2.
        """
        self.BASE_URL = 'https://dog.ceo/api'
        self.message_key = 'message'
        self._all_breeds_data = None
        self.timeout = timeout
        self.retries = retries
        self.delay = delay

    def _request_with_retry(self, url):
        """
        Выполняет GET-запрос с автоматическими повторными попытками при таймаутах
        или проблемах с соединением.
        url (str): Адрес для запроса.
        Returns:
            requests.Response: Объект ответа от сервера.
        Raises:
            requests.exceptions.RequestException: Если все попытки исчерпаны.
        """
        for attempt in range(self.retries):
            try:
                response = requests.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                if attempt == self.retries - 1:
                    logger.error(f"Request failed after {self.retries} tries: {url}")
                    raise
                logger.warning(f"Try {attempt+1}/{self.retries} failed: {e}. Retry in {self.delay} sec.")
                time.sleep(self.delay)
        raise requests.exceptions.RequestException("Request failed")

    def _get_all_breeds_data(self):
        """
        Возвращает словарь со списком всех пород и подпород:
        dict: Полный JSON-ответ от API (содержит ключ 'message' со вложенным словарём пород).
        Данные кешируются: при первом вызове отправляется запрос к API,
        при последующих – используется сохранённый результат.
        """
        if self._all_breeds_data is None:
            url = f'{self.BASE_URL}/breeds/list/all'
            logger.info(f"All breeds request: {url}")
            response = self._request_with_retry(url)
            self._all_breeds_data = response.json()
        return self._all_breeds_data

    def get_all_breeds_json(self):
        """
        Возвращает полный JSON-ответ от API (с кешированием):
        dict: Словарь с данными о всех породах.
        """
        return self._get_all_breeds_data()

    def get_only_breeds(self):
        """
        Возвращает список названий основных пород (без подпород):
        list of str: Список строк с названиями пород.
        """
        data = self._get_all_breeds_data()
        breeds = list(data[self.message_key].keys())
        logger.info(f"Number off all breeds is {len(breeds)}")
        return breeds

    def get_all_sub_breeds(self, breed):
        """
        Возвращает список, содержащий основную породу и все её подпороды:
            list or None: Список вида [основная, подпорода1, подпорода2, ...]
                          или None, если порода не найдена.
        Аргумент breed (str): Название основной породы (на английском).
        """
        data = self._get_all_breeds_data()
        sub_breeds = data[self.message_key].get(breed)
        if sub_breeds is not None:
            return [breed] + sub_breeds
        logger.warning(f"The breed {breed} has been not found")
        return None

    def get_breed_random_image(self, breed):
        """
        Получает случайное изображение для указанной породы и всех её подпород.
        Для каждой подпороды (и для самой основной породы) формируется отдельный запрос
        к эндпоинту /breed/{breed}/images/random или /breed/{breed}/{sub}/images/random.
        Аргумент breed (str) - название основной породы на английском.
        Возвращаем dict or None: Словарь вида {название_породы_или_подпороды: URL_изображения}
                          или None, если порода не найдена или ни одно изображение не получено.
        """
        breeds_list = self.get_all_sub_breeds(breed)
        if breeds_list is None:
            return None

        breeds_images_urls = {}
        for brd in breeds_list:
            if brd == breed:
                url = f'{self.BASE_URL}/breed/{breed}/images/random'
            else:
                url = f'{self.BASE_URL}/breed/{breed}/{brd}/images/random'

            try:
                logger.debug(f"Request for a random image of breed {brd}: {url}")
                response = self._request_with_retry(url)
                image_url = response.json()['message']
                breeds_images_urls[brd] = image_url
                logger.info(f"Image for breed {brd}: {image_url} has been gotten")
            except Exception as e:
                logger.error(f"It is failure at getting an image for {brd}: {e}")
                continue

            time.sleep(self.delay)  # пауза между запросами

        return breeds_images_urls if breeds_images_urls else None

    def get_all_breeds_images(self):
        """
        Получает по одному случайному изображению для ВСЕХ основных пород и их подпород.
        Итеративно проходит по всем основным породам, для каждой вызывает
        `get_breed_random_image()` и объединяет результаты в один словарь вида
        {название_породы_или_подпороды: URL_изображения}.
        Если для какой-то породы не удалось получить изображение, она пропускается.
        """
        all_breeds = self.get_only_breeds()
        all_images = {}
        total = len(all_breeds)
        for idx, breed in enumerate(all_breeds, 1):
            logger.info(f"The breed {idx}/{total}: {breed} processing")
            breed_images = self.get_breed_random_image(breed)
            if breed_images:
                all_images.update(breed_images)
            time.sleep(self.delay)  # пауза между основными породами
        logger.info(f"There are {len(all_images)} links to images")
        return all_images