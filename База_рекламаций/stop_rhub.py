import os
import subprocess
import logging
import sys
import psutil
from datetime import datetime
import time


# ---------------------------- Настройка логирования --------------------------------
# Файл для записи логов
log_file = f"reclamationhub_log/rhub_shutdown_{datetime.now().strftime('%Y%m%d')}.log"

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


def find_django_process():
    """Поиск процесса Django сервера"""
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            cmdline = proc.info["cmdline"]
            # Ищем процесс, в командной строке которого есть одновременно 'manage.py' и 'runserver'
            if cmdline and "manage.py" in cmdline and "runserver" in cmdline:
                logging.info(f"Найден процесс Django: PID={proc.pid}")
                return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    logging.info("Процесс Django не найден")
    return None


def stop_django_server(process, timeout=5):
    """Останавливает сервер Django с таймаутом"""
    try:
        # Сначала пробуем вежливо остановить
        logging.info("Отправка сигнала terminate...")
        process.terminate()

        # Ждем завершения процесса с таймаутом
        logging.info(f"Ожидание завершения процесса (таймаут {timeout} сек)...")
        process.wait(timeout=timeout)

        logging.info("Процесс успешно остановлен")
        return True

    except psutil.TimeoutExpired:
        # Если процесс не завершился за timeout секунд, убиваем его
        logging.warning("Процесс не завершился вовремя, применяем kill...")
        process.kill()
        process.wait()  # ждем завершения после kill
        logging.info("Процесс принудительно остановлен")
        return True

    except Exception as e:
        logging.error(f"Ошибка при остановке процесса: {e}")
        return False


def run_command(command, description, capture_output=True):
    try:
        logging.info(f"Выполняется: {description}")
        if capture_output:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            logging.info(f"Успешно: {description}")
            # logging.info(f"Вывод команды: {result.stdout}")
        else:
            subprocess.run(command, check=True)
            logging.info(f"Успешно: {description}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Ошибка в {description}: {e}")
        return False


# def setup_git_encoding():
#     """Настройка Git для корректного отображения Unicode"""
#     subprocess.run(["git", "config", "core.quotepath", "false"])
#     subprocess.run(["git", "config", "i18n.commitencoding", "utf-8"])
#     subprocess.run(["git", "config", "i18n.logoutputencoding", "utf-8"])


def main():
    # Пути
    PROJECT_PATH = r"D:/MyRepositories/JobProjects/База_рекламаций"
    VENV_PATH = os.path.join(PROJECT_PATH, "rhub_venv")
    PYTHON_PATH = os.path.join(VENV_PATH, "Scripts", "python.exe")

    logging.info("Начало выполнения скрипта остановки сервера")

    try:
        # 1. Остановка сервера
        django_process = find_django_process()
        if django_process:
            if not stop_django_server(django_process):
                logging.error("Не удалось остановить сервер")
                return

        # Переход в папку проекта
        os.chdir(PROJECT_PATH)
        logging.info(f"Текущая директория: {os.getcwd()}")

        # Переход в папку reclamationhub
        os.chdir("reclamationhub")
        logging.info(f"Переход в директорию проекта: {os.getcwd()}")

        # 2. Создание фикстуры
        if not run_command(
            [
                PYTHON_PATH,
                "-Xutf8",
                "manage.py",
                "dumpdata",
                "--indent=2",
                "--output=fixtures/db.json",
                "--exclude=auth.permission",
                "--exclude=contenttypes",
            ],
            "Создание фикстуры",
        ):
            return

        # 3. Git операции
        # setup_git_encoding()  # Настройка Git

        # Переход в корневую папку проекта для git операций
        os.chdir(PROJECT_PATH)

        # Добавление изменений
        if not run_command(
            ["git", "add", "reclamationhub/fixtures/db.json"], "Git add"
        ):
            return

        # Создание коммита
        commit_message = (
            f"Обновление базы данных {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        if not run_command(["git", "commit", "-m", commit_message], "Git commit"):
            return

        # Push изменений
        if not run_command(["git", "push"], "Git push"):
            return

    except Exception as e:
        logging.error(f"Неожиданная ошибка: {str(e)}")

    logging.info("Завершение скрипта остановки сервера")


if __name__ == "__main__":
    main()
