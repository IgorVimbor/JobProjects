"""Песочница для отработки логики модулей перед переносом в проект"""
# Для исключения подчеркивания импорта моделей в песочнице в .vscode\settings.json надо добавить
# настройку "python.analysis.extraPaths": ["/путь/к/вашему/проекту/название_проекта"]

import os
import json
from datetime import date
import sys
import django
from dateutil.relativedelta import relativedelta
import pandas as pd

# Добавляем путь к проекту
project_path = 'E:/MyRepositories/JobProjects/База_рекламаций/reclamationhub'
sys.path.append(project_path)

# Настраиваем Django окружение
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reclamationhub.settings.development')
django.setup()

# Импортируем модели
from investigations.models import Investigation


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

today = date.today()

# Определяем год анализа по прошлому месяцу
prev_month = today - relativedelta(months=1)
analysis_year = prev_month.year
month_name = MONTH_NAMES[prev_month.month]


def process_data():
    """Основная логика обработки данных с pandas"""

    # Вспомогательная функция для извлечения числовой части акта для сравнения
    def get_numeric_part(act_str):
        """Извлекает числовую часть акта для сравнения: '1067-1' -> 1067"""
        try:
            return int(str(act_str).split("-")[0])
        except (ValueError, IndexError, AttributeError):
            return 0

    # =========== Получение данных из модели Investigation ============

    # Получаем все данные из Investigation со связанными моделями
    investigations_queryset = Investigation.objects.select_related(
        "reclamation__defect_period", "reclamation__product_name"
    ).values(
        "act_number",
        "act_date",
        "reclamation__defect_period__name",
        "reclamation__product_name__name",
        "reclamation__product_number",
        "reclamation__manufacture_date",
        "reclamation__products_count",
        "solution",
        "fault_type",
        "guilty_department",
        "defect_causes",
        "defect_causes_explanation",
    )

    if not investigations_queryset.exists():
        return False, "Нет данных по актам исследований и рекламациям"

    # =========== Создание датафрейма ============

    df = pd.DataFrame(list(investigations_queryset))

    # Переименовываем столбцы для удобства
    df.rename(
        columns={
            "act_number": "Номер акта исследования",
            "act_date": "Дата акта исследования",
            "reclamation__defect_period__name": "Период выявления дефекта",
            "reclamation__product_name__name": "Обозначение изделия",
            "reclamation__product_number": "Заводской номер изделия",
            "reclamation__manufacture_date": "Дата изготовления изделия",
            "reclamation__products_count": "Количество предъявленных изделий",
            "solution": "Решение",
            "fault_type": "Виновник дефекта",
            "guilty_department": "Виновное подразделение",
            "defect_causes": "Причины дефектов",
            "defect_causes_explanation": "Пояснения к причинам дефектов",
        },
        inplace=True,
    )

    # =========== Обработка отсутствующих значений ============

    # Удаляем строки с отсутствующим номером акта исследования
    df.dropna(subset=["Номер акта исследования"], inplace=True)

    if df.empty:
        return False, "Нет записей с номерами актов исследования"

    # Удаляем акты со значением "без исследования"
    df = df[df["Номер акта исследования"] != "без исследования"]

    if df.empty:
        return False, "Нет записей после исключения актов 'без исследования'"

    # =========== Фильтрация датафрейма ============

    # 1. Ограничиваем месяц акта исследования отчетным месяцем

    # Преобразуем даты в формат date и Timestamp
    df["Дата акта исследования"] = pd.to_datetime(df["Дата акта исследования"])
    prev_month_ts = pd.Timestamp(prev_month)

    # Создаем новый датафрейм - преобразуем даты в формат год-месяц и оставляем только отчетный месяц
    df_accepted = df[
        df["Дата акта исследования"].dt.to_period("M")
        == prev_month_ts.to_period("M")
    ]

    if df_accepted.empty:
        return (
            False,
            f"Нет данных за {month_name} {analysis_year} года",
        )

    # 2. Извлекаем год и номер акта исследования ("2025 № 1067" → год=2025, номер=1067)
    df_accepted["Год акта"] = (
        df_accepted["Номер акта исследования"]
        .str.split(" № ")
        .str[0]
        .astype(int)
    )
    df_accepted["Номер акта (короткий)"] = (  # создаем новый столбец
        df_accepted["Номер акта исследования"].str.split(" № ").str[1]
    )

    return df_accepted["Номер акта исследования"].min(), df_accepted["Номер акта исследования"].max()


print(process_data())
