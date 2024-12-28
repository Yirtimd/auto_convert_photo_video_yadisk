import os
from dotenv import load_dotenv
import subprocess
from PIL import Image, ImageOps
import yadisk

load_dotenv()

api_key = os.getenv("API_KEY_YADISK")

# Инициализируем API-клиент
y = yadisk.YaDisk(token=api_key)


def download_folder_from_disk(disk_folder_path, local_folder_path):
    """Скачивание всех файлов и подкаталогов из указанной папки на Яндекс.Диске."""
    if not os.path.exists(local_folder_path):
        os.makedirs(local_folder_path)

    for item in y.listdir(disk_folder_path):
        if item['type'] == 'dir':
            # Рекурсивно загружаем поддиректории
            subfolder_path = os.path.join(local_folder_path, item['name'])
            download_folder_from_disk(item['path'], subfolder_path)
        else:
            # Скачиваем файл
            file_path = os.path.join(local_folder_path, item['name'])
            print(f"Скачиваем {item['name']} в {file_path}")
            y.download(item['path'], file_path)


def upload_photos_to_disk(local_resize_folder, original_disk_folder):
    """Загружает фотографии в ту же папку на Яндекс.Диске, где они находились изначально."""
    for file in os.listdir(local_resize_folder):
        file_path = os.path.join(local_resize_folder, file)
        file_ext = file.lower().split('.')[-1]

        if file_ext in ['jpg', 'jpeg', 'png']:
            disk_file_path = f"{original_disk_folder}/{file}"
            try:
                print(f"Загружаем {file_path} в {disk_file_path}")
                with open(file_path, 'rb') as f:
                    y.upload(f, disk_file_path, overwrite=True)
            except Exception as e:
                print(f"Ошибка при загрузке {file_path}: {e}")


def resize_image(image_path, output_path, target_size=(1080, 1440)):
    """Функция для изменения размера изображения с учетом ориентации EXIF."""
    with Image.open(image_path) as img:
        img = ImageOps.exif_transpose(img)
        img.thumbnail(target_size, Image.Resampling.LANCZOS)
        img.save(output_path, format='JPEG')


def convert_video_ffmpeg(input_path, output_path):
    """Конвертация видео через FFmpeg без изменения пропорций."""
    command = [
        'ffmpeg', '-i', input_path, '-vcodec', 'h264', '-acodec', 'aac', output_path
    ]
    subprocess.run(command, check=True)


def process_folder(local_folder_path, disk_folder_path):
    """Обрабатывает файлы в локальной папке и загружает их обратно на Яндекс.Диск."""
    for root, dirs, files in os.walk(local_folder_path):
        resize_folder = os.path.join(root, 'resize')
        os.makedirs(resize_folder, exist_ok=True)

        photo_count = 1  # Счетчик для фотографий

        for file in files:
            file_path = os.path.join(root, file)
            file_ext = file.lower().split('.')[-1]

            if file_ext in ['jpg', 'jpeg', 'png']:
                # Обрабатываем фото и сохраняем в папку resize
                output_photo_path = os.path.join(resize_folder, f'sj_{photo_count}.jpg')
                resize_image(file_path, output_photo_path)
                photo_count += 1

            elif file_ext == 'mov':
                # Обрабатываем видео и сохраняем в исходную папку
                output_video_path = os.path.join(root, 'sj.mp4')
                convert_video_ffmpeg(file_path, output_video_path)

        # Относительный путь для текущей директории
        relative_path = os.path.relpath(root, local_folder_path)
        original_disk_photo_folder = f"{disk_folder_path}/{relative_path}".replace("\\", "/")

        # Загружаем фото из папки resize обратно на Яндекс.Диск в ту же папку, где они были найдены
        upload_photos_to_disk(resize_folder, original_disk_photo_folder)


# Пример использования
disk_folder_path = "disk:/Monogram_Store/Miu Miu Leather Beau "  # Путь к папке на Яндекс.Диске
local_folder_path = "/Users/dmitrijvoknap/Desktop/convert"  # Локальная папка для временного хранения

# Скачиваем папку с Яндекс.Диска
download_folder_from_disk(disk_folder_path, local_folder_path)

# Обрабатываем фотографии и видео
process_folder(local_folder_path, disk_folder_path)



