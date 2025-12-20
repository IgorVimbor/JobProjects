"""Python-скрипт для логирования и отправки письма после запуска серверов"""

import smtplib
import os
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import logging
from datetime import datetime


# ---------------------------- Настройка логирования --------------------------------

today = datetime.now()

# Файл для записи логов
log_file = f"D:/Reclamationhub_log/rhub_backup_{today.strftime('%Y-%m-%d')}.log"

# Создаем форматтер для единого формата вывода
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

# Настраиваем корневой логгер
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Хендлер для файла логов
file_handler = logging.FileHandler(log_file, encoding="utf-8")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Загрузка переменных из файла .env.production
env_prod_file_path = r".env.production"
load_dotenv(dotenv_path=env_prod_file_path)


def send_email_mailru_start():
    logging.info("--- Начало скрипта отправки письма после запуска серверов ---")
    # -------------- 1. ЗАГРУЗКА И ПРОВЕРКА ПЕРЕМЕННЫХ ----------------
    # Получение данных из переменных окружения
    sender_email = os.getenv("MAIL_USERNAME")
    sender_password = os.getenv("MAIL_PASSWORD")
    receiver_email = os.getenv("RECIPIENT_EMAIL")
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT"))

    # Проверка, что все переменные загружены
    if not all([sender_email, sender_password, receiver_email]):
        print("ОШИБКА: не все переменные окружения установлены")
        logging.info("ОШИБКА: не все переменные окружения установлены")
        return False

    # -------------- 2. СОЗДАНИЕ КОНТЕЙНЕРА ПИСЬМА ---------------------
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = "Отчет АСУР БЗА"

    # -------------- 3. ПРИКРЕПЛЕНИЕ ТЕКСТОВОГО ТЕЛА -------------------
    # Текст письма (поддерживает русский язык)
    body = f"""
    Привет!

    Это автоматическое письмо от АСУР БЗА.

    Серверы Django и Nginx успешно запущены {today.strftime("%Y-%m-%d %H:%M")} и работают в штатном режиме.
    """

    message.attach(MIMEText(body, "plain", "utf-8"))

    # --------------- 4. ОТПРАВКА ПИСЬМА ------------------------------
    try:
        print(f"Подключение к {smtp_server}:{smtp_port}...")
        logging.info(f"Подключение к {smtp_server}:{smtp_port}...")
        # Подключение к серверу Mail.ru через SMTP
        server = smtplib.SMTP(smtp_server, smtp_port)
        # # Используем SMTP_SSL вместо SMTP
        # server = smtplib.SMTP_SSL(smtp_server, smtp_port)

        server.starttls()  # Включение TLS шифрования
        server.login(sender_email, sender_password)

        # Отправка
        text = message.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()

        # print("Письмо с вложением успешно отправлено с Mail.ru на Gmail!")
        logging.info("Письмо о запуске серверов успешно отправлено!")

    except Exception as e:
        print(f"ОШИБКА: При отправке письма о запуске серверов возникла ошибка: {e}")
        logging.info(
            f"ОШИБКА: При отправке письма о запуске серверов возникла ошибка: {e}"
        )

    logging.info("--- OK! Завершен скрипт отправки письма после запуска серверов ---")


if __name__ == "__main__":
    # Тест отправки
    send_email_mailru_start()
