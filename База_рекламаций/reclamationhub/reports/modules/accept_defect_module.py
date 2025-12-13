# reports/modules/accept_defect_module.py
"""
Модуль приложения "Количество признанных/непризнанных" с основной логикой.

Включает класс:
- `AcceptDefectProcessor` - Обработка данных для отчета по признанным рекламациям
"""

import pandas as pd
from datetime import date
import os
from django.db.models import Q

from investigations.models import Investigation
from reclamations.models import Reclamation
from reports.config.paths import (
    get_accept_defect_txt_path,
    ACCEPT_DEFECT_DIR,  # BASE_REPORTS_DIR,
)


class AcceptDefectProcessor:
    """Обработка данных для отчета по признанным рекламациям"""

    def __init__(self, year=None, months=None):
        self.today = date.today()
        self.year = year or self.today.year  # Если год не передан, используем текущий
        self.months = (
            months or []
        )  # Список выбранных месяцев [1, 2, 3] или [] для всех месяцев
        self.result_df = pd.DataFrame()
        # Используем готовую функцию из конфига
        self.txt_file_path = get_accept_defect_txt_path(0)

    def _get_month_names(self):
        """Возвращает названия выбранных месяцев для отчета"""
        if not self.months:
            return "все месяцы"

        month_names = {
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

        selected_names = [month_names[month] for month in sorted(self.months)]

        if len(selected_names) == 1:
            return selected_names[0]
        elif len(selected_names) == 2:
            return f"{selected_names[0]} и {selected_names[1]}"
        else:
            return f"{', '.join(selected_names[:-1])} и {selected_names[-1]}"

    def process_data(self):
        """Основная логика обработки данных с фильтрацией по месяцам"""

        # 1. Формируем фильтр для рекламаций
        reclamations_filter = Q(year=self.year)
        if self.months:  # Если выбраны конкретные месяцы
            reclamations_filter &= Q(message_received_date__month__in=self.months)

        # Получаем ВСЕ рекламации за указанный год и месяцы
        all_reclamations = (
            Reclamation.objects.filter(reclamations_filter)
            .select_related("defect_period", "product_name")
            .values("defect_period__name", "product_name__name", "products_count")
        )

        if not all_reclamations.exists():
            period_text = f"{self.year} год"
            if self.months:
                month_names = self._get_month_names()
                period_text = f"{month_names} {self.year} года"
            return False, f"Нет данных за {period_text}"

        # Создаем DataFrame всех рекламаций
        df_all = pd.DataFrame(list(all_reclamations))

        if df_all.empty:
            period_text = f"{self.year} год"
            if self.months:
                month_names = self._get_month_names()
                period_text = f"{month_names} {self.year} года"
            return False, f"DataFrame пустой за {period_text}"

        df_all.rename(
            columns={
                "defect_period__name": "Потребитель",
                "product_name__name": "Изделие",
                "products_count": "Количество",
            },
            inplace=True,
        )

        # Группируем по Потребителю и Изделию (общее количество рекламаций)
        total_df = (
            df_all.groupby(["Потребитель", "Изделие"])["Количество"].sum().reset_index()
        )

        # 2. Формируем фильтр для исследований
        investigations_filter = Q(
            reclamation__isnull=False, reclamation__year=self.year
        )
        if self.months:  # Если выбраны конкретные месяцы
            investigations_filter &= Q(
                reclamation__message_received_date__month__in=self.months
            )

        # Получаем данные по виновникам из Investigation
        investigations = (
            Investigation.objects.filter(investigations_filter)
            .select_related("reclamation__defect_period", "reclamation__product_name")
            .values(
                "reclamation__defect_period__name",
                "reclamation__product_name__name",
                "fault_type",
                "reclamation__products_count",
            )
        )

        # Создаем сводную таблицу по виновникам (если есть исследования)
        if investigations.exists():
            df_investigations = pd.DataFrame(list(investigations))
            df_investigations.rename(
                columns={
                    "reclamation__defect_period__name": "Потребитель",
                    "reclamation__product_name__name": "Изделие",
                    "fault_type": "Виновник",
                    "reclamation__products_count": "Количество_вин",
                },
                inplace=True,
            )

            # Группируем по виновникам
            grouped_investigations = (
                df_investigations.groupby(["Потребитель", "Изделие", "Виновник"])[
                    "Количество_вин"
                ]
                .sum()
                .reset_index()
            )

            # Создаем pivot table для виновников
            pivot_investigations = grouped_investigations.pivot_table(
                index=["Потребитель", "Изделие"],
                columns="Виновник",
                values="Количество_вин",
                aggfunc="sum",
                fill_value=0,
            ).reset_index()

            # Убираем имя колонок
            pivot_investigations.columns.name = None

            # Если каких-то виновников нет, создаем столбцы с нулями
            fault_types = ["bza", "consumer", "compliant", "unknown"]
            for fault_type in fault_types:
                if fault_type not in pivot_investigations.columns:
                    pivot_investigations[fault_type] = 0
        else:
            # Если исследований нет, создаем пустую таблицу виновников
            # БЫЛО: total_df.copy()
            pivot_investigations = total_df[["Потребитель", "Изделие"]].copy()
            for fault_type in ["bza", "consumer", "compliant", "unknown"]:
                pivot_investigations[fault_type] = 0

        # 3. Объединяем общее количество рекламаций с данными по виновникам
        result_df = total_df.merge(
            pivot_investigations, on=["Потребитель", "Изделие"], how="left"
        )

        # Заполняем NaN нулями для тех, где нет исследований
        fault_columns = ["bza", "consumer", "compliant", "unknown"]
        for col in fault_columns:
            if col in result_df.columns:
                result_df[col] = result_df[col].fillna(0)
            else:
                result_df[col] = 0

        # 4. Применяем ИСХОДНЫЕ формулы (ваша логика)
        result_df["Признано"] = result_df["bza"] + result_df["unknown"]
        result_df["Отклонено"] = result_df["consumer"] + result_df["compliant"]
        result_df["Не_поступало"] = result_df["Количество"] - (
            result_df["Признано"] + result_df["Отклонено"]
        )

        # Финальный результат
        self.result_df = result_df[
            [
                "Потребитель",
                "Изделие",
                "Количество",
                "Признано",
                "Отклонено",
                "Не_поступало",
            ]
        ].copy()

        # ПРИВОДИМ ВСЕ ЧИСЛОВЫЕ СТОЛБЦЫ К INT
        numeric_columns = ["Количество", "Признано", "Отклонено", "Не_поступало"]
        for col in numeric_columns:
            self.result_df[col] = self.result_df[col].astype(int)

        return True  # f"Обработано записей: {len(self.result_df)}"

    def save_to_txt(self):
        """Сохранение в TXT файл"""
        with open(self.txt_file_path, "w", encoding="utf-8") as f:
            # Формируем заголовок с учетом выбранных месяцев
            period_text = f"{self.year} год"
            if self.months:
                month_names = self._get_month_names()
                period_text = f"{month_names} {self.year} года"

            print(
                f"\n\n\tСправка по количеству признанных рекламаций\n\tза {period_text} на {self.today.strftime('%d-%m-%Y')}\n\n",
                file=f,
            )
            f.write(self.result_df.to_string())

    def generate_report(self):
        """Основной метод генерации отчета"""
        try:
            # Обрабатываем данные
            success = self.process_data()

            if not success:
                return {"success": False, "message_type": "info"}

            # Сохраняем TXT файл
            self.save_to_txt()

            # Преобразуем DataFrame в список словарей для шаблона
            report_data = (
                self.result_df.to_dict("records") if not self.result_df.empty else []
            )

            # Формируем сообщение с учетом периода
            period_text = f"{self.year} год"
            if self.months:
                month_names = self._get_month_names()
                period_text = f"{month_names} {self.year} года"

            return {
                "success": True,
                "message": f"Отчет за {period_text} сформирован.",
                "full_message": f"Файл отчета находится в папке {ACCEPT_DEFECT_DIR}",
                "txt_path": self.txt_file_path,
                "filename": os.path.basename(self.txt_file_path),
                "report_data": report_data,
                "message_type": "success",
                "period_text": period_text,  # Для использования в шаблоне
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Ошибка при формировании отчета: {str(e)}",
                "message_type": "error",
            }
