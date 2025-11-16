import os
import sys
import subprocess
import logging
from datetime import datetime


# ---------------------------- Настройка логирования --------------------------------
# Файл для записи логов
log_file = f"D:/Reclamationhub_log/rhub_backup_{datetime.now().strftime('%Y%m%d')}.log"

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


def run_command(command, description):
    """Выполняет команду и логирует результат."""
    try:
        logging.info(f"Выполняется: {description} (команда: {' '.join(command)})")
        # Мы используем -Xutf8, поэтому text=True можно не указывать, но для надежности оставим
        result = subprocess.run(
            command, capture_output=True, text=True, check=True, encoding="utf-8"
        )
        logging.info(f"Успешно: {description}")
        if result.stdout:
            logging.info(f"Вывод: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"ОШИБКА в {description}: {e}")
        return False


def main():
    logging.info("--- Начало скрипта бэкапа и коммита ---")

    # PROJECT_PATH = r"D:/MyRepositories/JobProjects/База_рекламаций"
    # VENV_PATH = os.path.join(PROJECT_PATH, "rhub_venv")
    # PYTHON_PATH = os.path.join(VENV_PATH, "Scripts", "python.exe")

    try:
        # 1. Создание фикстуры
        if not run_command(
            [
                "python",
                "-Xutf8",  # флаг для Windows, чтобы было на русском (UTF-8)
                "manage.py",
                "dumpdata",
                "--indent=2",
                "--output=fixtures/db.json",
                "--exclude=auth.permission",
                "--exclude=contenttypes",
                "--exclude=admin.logentry",
                "--exclude=sessions.session",
            ],
            "Создание фикстуры базы данных",
        ):
            return  # Прерываем выполнение в случае ошибки

        # 2. Git операции
        # # Настройка Git для UTF-8 (полезно выполнить один раз, но пусть будет)
        # run_command(
        #     ["git", "config", "core.quotepath", "false"], "Настройка Git (quotepath)"
        # )

        # Добавление изменений
        if not run_command(
            ["git", "add", "reclamationhub/fixtures/db.json"],
            f"Добавление фикстуры БД в Git",
        ):
            return

        # Создание коммита с датой
        commit_message = f"Auto: Обновление фикстуры БД от {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        if not run_command(["git", "commit", "-m", commit_message], "Создание коммита"):
            # Если коммитить нечего, git вернет ошибку.
            # Если команда commit не удалась, возможно, изменений не было.
            logging.info("Возможно, не было изменений для коммита.")
            return

        # Push изменений
        if not run_command(["git", "push"], "Отправка изменений на Git"):
            return

    except Exception as e:
        logging.error(f"Неожиданная ошибка: {str(e)}")

    logging.info("--- Скрипт бэкапа и коммита завершен ---")


if __name__ == "__main__":
    main()
