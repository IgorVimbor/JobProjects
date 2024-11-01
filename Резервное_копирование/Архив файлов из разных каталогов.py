# Для создания архива из файлов, расположенных в разных каталогах, можно использовать модуль shutil в Python,
# который предоставляет удобные функции для работы с файлами и директориями.
# В частности, функция shutil.make_archive позволяет создавать архивы.
#     Вот пример, как это можно сделать:
# 1. Соберите список файлов, которые нужно добавить в архив.
# 2. Создайте временный каталог.
# 3. Скопируйте файлы в временный каталог.
# 4. Создайте архив из временного каталога.
# 5. Удалите временный каталог.

import os
import shutil


# Список файлов, которые нужно добавить в архив
files_to_archive = [
    "D:/PDF files/Баланс семьи.xls",
    "D:/PDF files/Банковские платежи/Оплата ДС-19_январь21.pdf",
    "D:/ЗАГРУЗКИ/calendar.csv",
    "D:/Изображения/1-6-1.png",
]

# Путь к временному каталогу
temp_dir = "D:/АРХИВ резервных копий файлов_2024-11-01/temp_archive_dir"

# Создаем временный каталог
os.makedirs(temp_dir, exist_ok=True)

# Копируем файлы во временный каталог
for file in files_to_archive:
    file_name = os.path.basename(file)
    shutil.copy(file, os.path.join(temp_dir, file_name))

# Путь к создаваемому архиву (без расширения)
archive_name = "D:/АРХИВ резервных копий файлов_2024-11-01/my_archive"
archive_format = "zip"  # Можно использовать 'zip', 'tar', 'gztar', 'bztar', 'xztar'

# Создаем архив
shutil.make_archive(archive_name, archive_format, temp_dir)

# Удаляем временный каталог
shutil.rmtree(temp_dir)

print(f"Архив {archive_name}.{archive_format} успешно создан.")
