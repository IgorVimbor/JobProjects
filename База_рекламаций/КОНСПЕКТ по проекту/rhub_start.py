import os
import subprocess
import logging
import sys
from datetime import datetime

# -------------------- Настройка логирования --------------------------
# Файл для записи логов
log_file = f"reclamationhub_log/rhub_startup_{datetime.now().strftime('%Y%m%d')}.log"

# Создаем форматтер для единого формата вывода
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

# Настраиваем корневой логгер
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Хендлер для файла логов
file_handler = logging.FileHandler(log_file, encoding="utf-8")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Хендлер для консоли
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


def run_command(command, description, capture_output=True):
    try:
        logging.info(f"Выполняется: {description}")
        if capture_output:
            # Для вывода в лог-файл (capture_output=True)
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            logging.info(f"Успешно: {description}")
            logging.info(f"Вывод команды: {result.stdout}")
        else:
            # Для вывода в консоль (capture_output=False)
            subprocess.run(command, check=True)
            logging.info(f"Успешно: {description}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Ошибка в {description}: {e}")
        return False


def main():
    # Пути
    PROJECT_PATH = r"E:/MyRepositories/JobProjects/База_рекламаций"
    VENV_PATH = os.path.join(PROJECT_PATH, "r-hub_venv")
    PYTHON_PATH = os.path.join(VENV_PATH, "Scripts", "python.exe")

    logging.info("Начало выполнения скрипта запуска сервера")

    try:
        # Переход в папку проекта
        os.chdir(PROJECT_PATH)
        logging.info(f"Текущая директория: {os.getcwd()}")

        # Git pull
        if not run_command(["git", "pull"], "Git pull"):
            return

        # Переход в папку reclamationhub
        os.chdir("reclamationhub")
        logging.info(f"Переход в директорию проекта: {os.getcwd()}")

        # Обновление БД
        if not run_command(
            [PYTHON_PATH, "manage.py", "loaddata", "fixtures/db.json"],
            "Обновление базы данных",
        ):
            return

        # Запуск сервера без capture_output, чтобы видеть вывод Django
        run_command(
            [
                PYTHON_PATH,
                "manage.py",
                "runserver",
                "--settings=reclamationhub.settings.production",
            ],
            "Запуск сервера",
            capture_output=False,  # обычный вывод Django в консоли
            # перенаправляется в лог-файл если capture_output=True
        )

    except KeyboardInterrupt:
        logging.info("Получен сигнал остановки (Ctrl+C)")
    except Exception as e:
        logging.error(f"Неожиданная ошибка: {str(e)}")

    logging.info("Завершение скрипта запуска сервера")


if __name__ == "__main__":
    main()
