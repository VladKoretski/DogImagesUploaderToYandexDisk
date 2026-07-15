import os
import json
import time
import logging
from config import YANDEX_DISK_TOKEN
from dog_api import DogBreedsAPI
from yandex_api import YandexDisk

def setup_logging():
    """
    Настраивает логирование: вывод в консоль и в файл app.log.
    """
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('app.log', encoding='utf-8')
        ]
    )

def main():

    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        choice = int(input('Upload all breeds (1) or a particular one (2)? '))
        if choice not in (1, 2):
            raise ValueError
    except ValueError:
        logger.error('Input error: input 1 or 2')
        return

    dog_api = DogBreedsAPI(timeout=10, retries=3, delay=0.2)
    yandex = YandexDisk(YANDEX_DISK_TOKEN, timeout=30, retries=3, delay=1.0)

    if choice == 1:
        logger.info("All breed mode was chosen")
        images_dict = dog_api.get_all_breeds_images()
        folder_name = "AllBreeds"
    else:
        breed = input('Input the breed in English: ').strip().lower()
        logger.info(f"Particular breed {breed} mode was chosen")
        images_dict = dog_api.get_breed_random_image(breed)
        if not images_dict:
            logger.error(f"The breed '{breed}' or any image was found")
            return
        folder_name = breed.capitalize()

    if not images_dict:
        logger.error("No one image was found.")
        return

    logger.info(f"{len(images_dict)} links to images were found.")

    if not yandex.create_folder(folder_name):
        logger.error(f"'{folder_name}' folder creation was failed. Upload unavailable.")
        return

    results = []
    total = len(images_dict)
    for idx, (breed_name, img_url) in enumerate(images_dict.items(), 1):
        original_filename = os.path.basename(img_url)
        saved_name = f"{breed_name}_{original_filename}"

        logger.info(f"[{idx}/{total}] loading {saved_name}.")
        success = yandex.upload_file(folder_name, saved_name, img_url)

        results.append({
            "breed": breed_name,
            "original_url": img_url,
            "saved_name": saved_name,
            "status": "success" if success else "error"
        })

        time.sleep(0.3)

    report_file = "results.json"
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        logger.info(f"The report was saved as a '{report_file}' file")
    except Exception as e:
        logger.error(f"The report failed to be saved: {e}")

    success_count = sum(1 for r in results if r['status'] == 'success')
    logger.info(f"Success! {success_count} number of {total} files have been loaded to folder '{folder_name}'.")

if __name__ == '__main__':
    main()