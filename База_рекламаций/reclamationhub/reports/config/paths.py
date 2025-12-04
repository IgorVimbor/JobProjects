"""
Общие пути до каталогов и файлов для всех аналитических модулей
"""

import os
from datetime import date
from dateutil.relativedelta import relativedelta


# ==================== БАЗОВЫЕ НАСТРОЙКИ ====================
# Каталог для сохранения справок, отчетов, таблиц и др.
BASE_REPORTS_DIR = r"\\Server\otk\АНАЛИТИЧЕСКАЯ_СИСТЕМА_УК"
# BASE_REPORTS_DIR = r"D:\АНАЛИТИЧЕСКАЯ_СИСТЕМА_УК"

# Текущая дата и год для имен файлов
today = date.today()
date_today = today.strftime("%d-%m-%Y")
year_now = today.year

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
ACCEPT_DEFECT_DIR = os.path.join(BASE_REPORTS_DIR, "ACCEPT_DEFECT_txt")

# Создаем папку для справок TXT
os.makedirs(ACCEPT_DEFECT_DIR, exist_ok=True)


def get_accept_defect_txt_path(sequence_number):
    return os.path.join(
        ACCEPT_DEFECT_DIR,
        f"Справка по количеству признанных-непризнанных_{date_today}.txt",
    )


# ======================= DB SEARCH ======================
# DB_SEARCH_DIR = os.path.join(BASE_REPORTS_DIR, "db_search")


def get_db_search_txt_path():
    """Путь к TXT файлу отчета поиска"""
    filename = f"Результаты поиска по базе.txt"
    return os.path.join(BASE_REPORTS_DIR, filename)


# ====================== LENGTH STUDY =====================
# LENGTH_STUDY_DIR = os.path.join(BASE_REPORTS_DIR, "length_study")


def get_length_study_txt_path():
    """Путь к TXT файлу отчета по длительности исследований"""
    filename = f"Длительность исследований_справка_{date_today}.txt"
    return os.path.join(BASE_REPORTS_DIR, filename)


def get_length_study_png_path():
    """Путь к png файлу графиков по длительности исследований"""
    filename = f"Длительность исследований_график_{date_today}.png"
    return os.path.join(BASE_REPORTS_DIR, filename)


# ======================= CULPRITS DEFECT ========================
# Названия месяцев
MONTH_NAMES = {
    1: "январь",
    2: "февраль",
    3: "март",
    4: "апрель",
    5: "май",
    6: "июнь",
    7: "июль",
    8: "август",
    9: "сентябрь",
    10: "октябрь",
    11: "ноябрь",
    12: "декабрь",
}
# Определяем отчетный (предыдущий) месяц и год по этому месяцу
prev_month = today - relativedelta(months=1)
analysis_year = prev_month.year
month_name = MONTH_NAMES[prev_month.month]

# Папка для сохранения справок по виновникам дефектов и базы данных json
CULPRITS_DEFECT_DIR = os.path.join(BASE_REPORTS_DIR, "СПРАВКИ_по_виновникам")
# Создаем папку для справок если не существует
os.makedirs(CULPRITS_DEFECT_DIR, exist_ok=True)

# файл базы данных справок по виновникам - номер месяца и последнего акта исследования
culprits_defect_json_db = f"{CULPRITS_DEFECT_DIR}/CULPRITS_DEFECT_база_данных.txt"


def get_culprits_defect_excel_path():
    """Excel файл для сохранения справок по виновникам дефектов"""
    return os.path.join(
        CULPRITS_DEFECT_DIR,
        f"Справка по виновникам за {month_name} {analysis_year}.xlsx",
    )


# ====================== MILEAGE CHART ======================


def get_mileage_chart_txt_path():
    """Путь к TXT файлу анализа по пробегу изделия"""
    filename = f"Анализ по пробегу_справка_{date_today}.txt"
    return os.path.join(BASE_REPORTS_DIR, filename)


def get_mileage_chart_png_path():
    """Путь к png файлу графика анализа по пробегу изделия"""
    filename = f"Анализ по пробегу_график_{date_today}.png"
    return os.path.join(BASE_REPORTS_DIR, filename)


# ====================== COMBINED CHART ======================


def get_defect_chart_product_path():
    """Путь к png файлу графика по обозначению изделия"""
    filename = f"Анализ по обозначению изделия_график_{date_today}.png"
    return os.path.join(BASE_REPORTS_DIR, filename)


def get_defect_chart_manufacture_path():
    """Путь к png файлу графика по дате изготовления изделия"""
    filename = f"Анализ по дате изготовления изделия_график_{date_today}.png"
    return os.path.join(BASE_REPORTS_DIR, filename)


def get_defect_chart_message_path():
    """Путь к png файлу графика по дате сообщения"""
    filename = f"Анализ по дате сообщения_график_{date_today}.png"
    return os.path.join(BASE_REPORTS_DIR, filename)


def get_defect_chart_combined_path():
    """Путь к png файлу сводного графика по дате изготовления изделия и сообщения"""
    filename = f"Анализ по дате изготовления + сообщения_график_{date_today}.png"
    return os.path.join(BASE_REPORTS_DIR, filename)


# ===================== EXCEL EXPORTER ======================


def get_excel_exporter_path(year):
    """Excel файл Базы рекламаций по выбранным столбцам"""
    year_select = year if year else "все годы"
    filename = f"ЖУРНАЛ УЧЕТА_{year_select}_{date_today}.xlsx"
    return os.path.join(BASE_REPORTS_DIR, filename)


# ========================= CLAIMS ===========================


def get_claims_dashboard_chart_path(year):
    """Путь к PNG графику Dashboard претензий"""
    filename = f"Dashboard претензий {year}_{date_today}.png"
    return os.path.join(BASE_REPORTS_DIR, filename)


def get_claims_dashboard_table_path(year):
    """Путь к TXT таблице TOP потребителей"""
    filename = f"Претензии {year}_TOP потребители_{date_today}.txt"
    return os.path.join(BASE_REPORTS_DIR, filename)


def get_consumer_analysis_chart_path(year, consumer_name):
    """Путь к PNG графику анализа по потребителю"""
    filename = f"Претензии {consumer_name} {year}_{date_today}.png"
    return os.path.join(BASE_REPORTS_DIR, filename)


def get_consumer_analysis_table_path(year, consumer_name):
    """Путь к таблице анализа по потребителю"""
    filename = f"Претензии {consumer_name} {year}_{date_today}.txt"
    return os.path.join(BASE_REPORTS_DIR, filename)


def get_reclamation_to_claim_chart_path(year, consumer_name):
    """Путь к PNG графику анализа конверсии рекламация-претензия"""
    filename = f"Конверсия рекламация-претензия {consumer_name} {year}_{date_today}.png"
    return os.path.join(BASE_REPORTS_DIR, filename)


def get_reclamation_to_claim_table_path(year, consumer_name):
    """Путь к таблице анализа конверсии рекламация-претензия"""
    filename = f"Конверсия рекламация-претензия {consumer_name} {year}_{date_today}.txt"
    return os.path.join(BASE_REPORTS_DIR, filename)


def get_time_analysis_chart_path(year, consumer_name):
    """Путь к графику временного анализа"""
    filename = f"Временной анализ {consumer_name} {year}_{date_today}.png"
    return os.path.join(BASE_REPORTS_DIR, filename)


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
