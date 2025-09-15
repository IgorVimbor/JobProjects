"""
Общие пути для всех аналитических модулей
Аналог paths_home.py из десктопного приложения
"""

import os
from datetime import date

# ==================== БАЗОВЫЕ НАСТРОЙКИ ====================
# Каталог для сохранения справок, отчетов, таблиц и др.
BASE_REPORTS_DIR = r"\\Server\otk\АНАЛИТИЧЕСКАЯ_СИСТЕМА_УК"
# BASE_REPORTS_DIR = r"D:\АНАЛИТИЧЕСКАЯ_СИСТЕМА_УК"

# Текущая дата и год для имен файлов
date_today = date.today().strftime("%d-%m-%Y")
year_now = date.today().year

# ==================== ENQUIRY PERIOD ====================
ENQUIRY_PERIOD_TXT_DIR = os.path.join(BASE_REPORTS_DIR, "ENQUIRY_PERIOD_txt")

# Создаем папку для справок TXT
os.makedirs(ENQUIRY_PERIOD_TXT_DIR, exist_ok=True)


def get_enquiry_period_txt_path(sequence_number):
    """TXT архив - уникальное имя для каждого отчета"""
    return os.path.join(
        ENQUIRY_PERIOD_TXT_DIR,
        f"Справка по рекламациям за период-{sequence_number}_{date_today}.txt",
    )


def get_enquiry_period_excel_path(sequence_number):
    """Excel файл - фиксированное имя, перезаписывается"""
    return os.path.join(BASE_REPORTS_DIR, "Справка по рекламациям за период.xlsx")


# ==================== ACCEPT DEFECT ====================
ACCEPT_DEFECT_DIR = os.path.join(BASE_REPORTS_DIR, "Кол-во_признанных-непризнанных_txt")

# Создаем папку для справок TXT
os.makedirs(ACCEPT_DEFECT_DIR, exist_ok=True)


def get_accept_defect_txt_path(sequence_number):
    return os.path.join(
        ACCEPT_DEFECT_DIR,
        f"Справка по количеству признанных-непризнанных_{date_today}.txt",
    )


# # ==================== LENGTH STUDY ====================
# LENGTH_STUDY_DIR = os.path.join(BASE_REPORTS_DIR, "length_study")


# def get_length_study_excel_path(sequence_number):
#     return os.path.join(
#         LENGTH_STUDY_DIR, f"length_study_{sequence_number}_{date_today}.xlsx"
#     )


# # ==================== NOT ACTS ====================
# NOT_ACTS_DIR = os.path.join(BASE_REPORTS_DIR, "not_acts")

# # ==================== PRETENCE ====================
# PRETENCE_DIR = os.path.join(BASE_REPORTS_DIR, "pretence")

# # ==================== DB SEARCH ====================
# DB_SEARCH_DIR = os.path.join(BASE_REPORTS_DIR, "db_search")

# # ==================== СОЗДАНИЕ ПАПОК ====================
# # Создаем все необходимые папки
# for directory in [
#     ENQUIRY_PERIOD_DIR,
#     ACCEPT_DEFECT_DIR,
#     LENGTH_STUDY_DIR,
#     NOT_ACTS_DIR,
#     PRETENCE_DIR,
#     DB_SEARCH_DIR,
# ]:
#     os.makedirs(directory, exist_ok=True)
