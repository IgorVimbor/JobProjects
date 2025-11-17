import smtplib
import os
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from datetime import date


# Загрузка переменных из файла .env.production
env_prod_file_path = r".env.production"
load_dotenv(dotenv_path=env_prod_file_path)


def send_email_mailru():
    # -------------- 1. ЗАГРУЗКА И ПРОВЕРКА ПЕРЕМЕННЫХ ----------------
    # Получение данных из переменных окружения
    sender_email = os.getenv("MAIL_USERNAME")
    sender_password = os.getenv("MAIL_PASSWORD")
    receiver_email = os.getenv("RECIPIENT_EMAIL")
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT"))

    # Проверка, что все переменные загружены
    if not all([sender_email, sender_password, receiver_email]):
        print("❌ Ошибка: не все переменные окружения установлены")
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

    Это автоматическое письмо отправлено с Mail.ru на Gmail.
    Во вложении фикстура базы данных db.json по состоянию на {date.today().strftime("%d-%m-%Y")}.

    С уважением,
    Автоматическая система рекламаций БЗА
    """

    message.attach(MIMEText(body, "plain", "utf-8"))

    # -------------- 4. ПРИКРЕПЛЕНИЕ ФАЙЛА ------------------------------
    # Автоматически получаем имя файла из пути к файлу
    filepath = "fixtures/db.json"
    filename = os.path.basename(filepath)

    try:
        # Открываем файл в режиме бинарного чтения
        with open(filepath, "rb") as attachment:
            # Создаем "обертку" для файла
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())

        # Кодируем файл в Base64
        encoders.encode_base64(part)

        # Добавляем заголовок, который определяет файл как вложение
        part.add_header(
            "Content-Disposition",
            f"attachment; filename= {filename}",
        )

        # Прикрепляем файл к письму
        message.attach(part)
        print(f"✅ Файл '{filename}' успешно прикреплен.")

    except FileNotFoundError:
        print(f"❌ ОШИБКА: Файл для вложения не найден по пути: {filepath}")
        return  # Прерываем отправку, если файл не найден

    # --------------- 5. ОТПРАВКА ПИСЬМА ------------------------------
    try:
        print(f"Подключаюсь к {smtp_server}:{smtp_port}...")
        # Подключение к серверу Mail.ru
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Включение TLS шифрования
        server.login(sender_email, sender_password)

        # Отправка
        text = message.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()

        print("✅ Письмо с вложением успешно отправлено с Mail.ru на Gmail!")

    except Exception as e:
        print(f"❌ Ошибка во время отправки: {e}")


if __name__ == "__main__":
    # Тест отправки
    send_email_mailru()
