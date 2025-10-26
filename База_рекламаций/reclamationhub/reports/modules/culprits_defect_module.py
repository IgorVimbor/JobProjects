# reports/modules/culprits_defect_module.py
# Модуль приложения "Дефекты по виновникам" с основной логикой

import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta

from investigations.models import Investigation


class CulpritsDefectProcessor:
    """Обработка данных для анализа дефектов по виновникам"""

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

    def __init__(self, user_number=None):
        self.today = date.today()
        self.user_number = user_number
        self.bza_df = pd.DataFrame()
        self.not_bza_df = pd.DataFrame()
        self.max_act_number = None

        # Определяем год анализа по прошлому месяцу
        # Это покрывает случай 1 января (анализ за декабрь прошлого года)
        self.prev_month = self.today - relativedelta(months=1)
        self.analysis_year = self.prev_month.year
        self.month_name = self.MONTH_NAMES[self.prev_month.month]

    def process_data(self):
        """Основная логика обработки данных с pandas"""

        try:
            # 1. Получаем все данные из Investigation с связанными моделями
            investigations_queryset = Investigation.objects.select_related(
                "reclamation__defect_period", "reclamation__product_name"
            ).values(
                "act_number",
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
                return False, "Нет данных в таблице исследований"

            # 2. Создаем DataFrame
            df = pd.DataFrame(list(investigations_queryset))

            # Переименовываем столбцы для удобства
            df.rename(
                columns={
                    "act_number": "Номер акта исследования",
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

            # 3. Первая фильтрация - только признанные рекламации (solution = "ACCEPT")
            df_accepted = df[df["Решение"] == "ACCEPT"].copy()

            if df_accepted.empty:
                return False, "Нет признанных рекламаций в данных"

            # 4. Удаляем строки с отсутствующим номером акта исследования
            df_accepted.dropna(subset=["Номер акта исследования"], inplace=True)

            if df_accepted.empty:
                return False, "Нет записей с номерами актов исследования"

            # 4.1 Удаляем акты со значением "не требуется"
            df_accepted = df_accepted[
                df_accepted["Номер акта исследования"] != "не требуется"
            ].copy()

            if df_accepted.empty:
                return (
                    False,
                    "Нет записей с номерами актов исследования (после исключения специальных значений)",
                )

            # 5. Извлекаем год и номер акта исследования
            # Формат: "2025 № 1067" → год=2025, номер=1067
            df_accepted["Год акта"] = (
                df_accepted["Номер акта исследования"]
                .str.split(" № ")
                .str[0]
                .astype(int)
            )
            df_accepted["Номер акта (короткий)"] = (
                df_accepted["Номер акта исследования"].str.split(" № ").str[1]
            )

            # 6. Фильтрация по году анализа
            df_year_filtered = df_accepted[
                df_accepted["Год акта"] == self.analysis_year
            ].copy()

            if df_year_filtered.empty:
                return False, f"Нет данных за {self.analysis_year} год"

            # 7. Функция для безопасного извлечения числовой части для сравнения
            def get_numeric_part(act_str):
                """Извлекает числовую часть для сравнения: '1067-1' -> 1067"""
                try:
                    return int(str(act_str).split("-")[0])
                except (ValueError, IndexError, AttributeError):
                    return 0

            # Создаем столбец для сравнения
            df_year_filtered["act_number"] = df_year_filtered[
                "Номер акта (короткий)"
            ].apply(get_numeric_part)

            # 8. Фильтрация по номеру акта (оставляем акты с номером > user_number)
            df_filtered = df_year_filtered[
                df_year_filtered["act_number"] > self.user_number
            ].copy()

            if df_filtered.empty:
                return (
                    False,
                    f"Нет данных за {self.analysis_year} год начиная с акта № {self.user_number + 1}",
                )

            # 9. Изменяем тип данных с float на int
            df_filtered["Количество предъявленных изделий"] = df_filtered[
                "Количество предъявленных изделий"
            ].astype("int32")

            # 10. Находим максимальный номер акта для следующего анализа
            act_numbers = df_filtered["Номер акта (короткий)"].unique()
            if len(act_numbers) > 0:
                max_act_number = sorted(
                    act_numbers,
                    key=lambda x: (
                        int(str(x).split("-")[0]) if "-" in str(x) else int(x),
                        int(str(x).split("-")[1]) if "-" in str(x) else 0,
                    ),
                )[-1]
                self.max_act_number = max_act_number

            # 11. Убираем служебные столбцы
            df_filtered = df_filtered.drop(columns=["Год акта", "act_number"])

            # 12. Группировка и агрегация
            df_grouped = df_filtered.groupby(
                [
                    "Виновное подразделение",
                    "Период выявления дефекта",
                    "Обозначение изделия",
                ]
            ).agg(
                {
                    "Заводской номер изделия": lambda x: ", ".join(
                        x.dropna().astype(str).unique()
                    ),
                    "Дата изготовления изделия": lambda x: ", ".join(
                        x.dropna().astype(str).unique()
                    ),
                    "Количество предъявленных изделий": "sum",
                    "Номер акта (короткий)": lambda x: ", ".join(x.dropna().unique()),
                    "Причины дефектов": lambda x: ", ".join(x.dropna().unique()),
                    "Пояснения к причинам дефектов": lambda x: ", ".join(
                        x.dropna().unique()
                    ),
                }
            )

            # 13. Разделение на БЗА ("Не определено") и не БЗА
            self.bza_df = df_grouped.loc[
                df_grouped.index.get_level_values("Виновное подразделение")
                == "Не определено"
            ]
            self.not_bza_df = df_grouped.loc[
                df_grouped.index.get_level_values("Виновное подразделение")
                != "Не определено"
            ]

            return True, f"Обработано записей: {len(df_filtered)}"

        except Exception as e:
            return False, f"Ошибка обработки данных: {str(e)}"

    def _prepare_table_data(self, df, include_culprit=False):
        """Подготовка данных для отображения в таблице"""
        if df.empty:
            return []

        result = []
        for index, row in df.iterrows():
            data = {
                "Потребитель": index[1],  # Период выявления дефекта
                "Изделие": index[2],  # Обозначение изделия
                "Заводской_номер": row["Заводской номер изделия"],
                "Дата_изготовления": row["Дата изготовления изделия"],
                "Количество": int(row["Количество предъявленных изделий"]),
                "Номера_актов": row["Номер акта (короткий)"],
                "Причины": row["Причины дефектов"],
                "Пояснения": row["Пояснения к причинам дефектов"],
            }

            # Для таблицы "не БЗА" - добавляем виновника
            if include_culprit:
                data["Виновник"] = index[0]  # Виновное подразделение

            result.append(data)

        return result

    def generate_analysis(self):
        """Основной метод генерации анализа"""
        try:
            # Обрабатываем данные
            success, message = self.process_data()

            if not success:
                return {"success": False, "message": message, "message_type": "warning"}

            # Подготавливаем данные для таблиц
            bza_data = self._prepare_table_data(self.bza_df, include_culprit=False)
            not_bza_data = self._prepare_table_data(
                self.not_bza_df, include_culprit=True
            )

            return {
                "success": True,
                "message": f"Справка по виновникам дефектов за {self.month_name} {self.analysis_year} года составлена начиная с акта исследования № {self.user_number + 1}",
                "bza_data": bza_data,
                "not_bza_data": not_bza_data,
                "bza_count": len(bza_data),
                "not_bza_count": len(not_bza_data),
                "max_act_number": self.max_act_number,
                "analysis_year": self.analysis_year,
                "message_type": "success",
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Ошибка при выполнении анализа: {str(e)}",
                "message_type": "warning",
            }
