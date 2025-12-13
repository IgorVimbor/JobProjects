# analytics\modules\combined_chart_modul.py
"""
Модуль анализа рекламаций по виду изделия, датам изготовления и уведомления.

Включает классы:
- `DefectDateDataProcessor` - Получение и подготовка данных из БД
- `DefectDateChartGenerator` - Генерация графиков (работает с готовым DataFrame)
- `DefectDateReportManager` - Главный класс-координатор
"""

import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import base64
from io import BytesIO
from datetime import date
from django.db.models import Q

from reclamations.models import Reclamation
from reports.config.paths import (
    BASE_REPORTS_DIR,
    get_defect_chart_product_path,
    get_defect_chart_manufacture_path,
    get_defect_chart_message_path,
    get_defect_chart_combined_path,
)


class DefectDateDataProcessor:
    """Получение и подготовка данных из БД"""

    # def __init__(self, year, consumers, product):
    def __init__(self, year, consumers, products):
        self.today = date.today()
        self.year = year  # "all", 2024, 2023, ...
        self.consumers = consumers or []  # Список потребителей
        # self.product = product  # ОДНО изделие (обязательно)
        self.products = products or []  # Список изделий
        self.df = pd.DataFrame()

    def parse_manufacture_date(self, date_str):
        """
        Преобразование "07.24" → "2024-07"
        Возвращает None если формат неверный или NULL
        """
        if pd.isna(date_str) or not date_str:
            return None

        try:
            # "07.24" → ["07", "24"]
            parts = str(date_str).strip().split(".")
            if len(parts) != 2:
                return None

            month, year_short = parts

            # Проверяем корректность месяца
            month_int = int(month)
            if month_int < 1 or month_int > 12:
                return None

            # Дополняем год (24 → 2024, 23 → 2023)
            year_full = f"20{year_short}"

            # Возвращаем в формате "2024-07"
            return f"{year_full}-{month.zfill(2)}"

        except (ValueError, AttributeError):
            return None

    def format_message_date(self, date_obj):
        """
        Преобразование DateField → "2024-03"
        """
        if pd.isna(date_obj) or not date_obj:
            return None

        try:
            # Если это строка - конвертируем
            if isinstance(date_obj, str):
                date_obj = pd.to_datetime(date_obj)

            return date_obj.strftime("%Y-%m")
        except (ValueError, AttributeError):
            return None

    def _get_filter_names(self):
        """Возвращает названия фильтров для отчета"""
        filter_parts = []

        # if self.consumers:
        #     if len(self.consumers) == 1:
        #         filter_parts.append(self.consumers[0])
        #     else:
        #         filter_parts.append(f"{len(self.consumers)} потребителей")

        if self.consumers:
            filter_parts += self.consumers

        # if self.product:
        #     filter_parts.append(self.product)

        if self.products:
            filter_parts += self.products

        if not filter_parts:
            return "всех данных"

        return ", ".join(filter_parts)

    def get_data_from_db(self):
        """Получение и обработка данных из Django ORM"""

        # # Проверяем, что изделие выбрано
        # if not self.product:
        #     return None, "Не выбрано изделие для анализа"

        # # Формируем фильтр
        # queryset_filter = Q(
        #     product_name__name=self.product,  # Фильтр по одному изделию
        # )

        # Формируем фильтр
        queryset_filter = Q()

        # Добавляем фильтры по изделиям
        if self.products:
            product_q = Q()
            for product in self.products:
                queryset_filter |= Q(product_name__name=product)  # Фильтр по изделию
            queryset_filter &= product_q

        # Применяем фильтр по году если выбран
        if self.year and str(self.year) != "all":
            queryset_filter &= Q(year=int(self.year))

        # Добавляем фильтры по потребителям
        if self.consumers:
            consumer_q = Q()
            for consumer in self.consumers:
                consumer_q |= Q(defect_period__name=consumer)
            queryset_filter &= consumer_q

        # Получаем данные
        queryset = (
            Reclamation.objects.filter(queryset_filter)
            .select_related("defect_period", "product_name", "product")
            .values(
                "defect_period__name",
                "product_name__name",
                "product__nomenclature",
                "message_received_date",
                "manufacture_date",
            )
        )

        # Если нет данных
        if not queryset.exists():
            filter_text = self._get_filter_names()
            year_text = (
                f"за {self.year} год" if str(self.year) != "all" else "за все годы"
            )
            return None, f"Нет данных для {filter_text} {year_text}"

        # Преобразуем в DataFrame
        df = pd.DataFrame(list(queryset))
        df.rename(
            columns={
                "defect_period__name": "Потребитель",
                "product_name__name": "Вид_изделия",
                "product__nomenclature": "Обозначение_изделия",
                "message_received_date": "Дата_сообщения",
                "manufacture_date": "Дата_изготовления_raw",
            },
            inplace=True,
        )

        if df.empty:
            filter_text = self._get_filter_names()
            year_text = (
                f"за {self.year} год" if str(self.year) != "all" else "за все годы"
            )
            return None, f"Нет данных для {filter_text} {year_text}"

        self.df = df
        return True, f"Получено записей: {len(df)}"

    def prepare_data(self):
        """Подготовка данных: преобразование дат, форматирование"""

        if self.df.empty:
            return False, "Нет данных для обработки"

        try:
            # Преобразуем дату сообщения
            self.df["Дата_сообщения_formatted"] = self.df["Дата_сообщения"].apply(
                self.format_message_date
            )

            # Преобразуем дату изготовления
            self.df["Дата_изготовления_formatted"] = self.df[
                "Дата_изготовления_raw"
            ].apply(self.parse_manufacture_date)

            # Сортируем по дате сообщения
            self.df = self.df.sort_values(by="Дата_сообщения_formatted")

            return True, "Данные подготовлены"

        except Exception as e:
            return False, f"Ошибка обработки данных: {str(e)}"


class DefectDateChartGenerator:
    """Генерация графиков (работает с готовым DataFrame)"""

    def __init__(self, filter_text, year):
        self.filter_text = filter_text
        self.year = year

    def create_chart_by_product(self, df, save_to_file=False):
        """График по обозначению изделия"""

        if df.empty:
            return None

        plt.figure(figsize=(12, 6))

        # Подсчитываем количество по обозначениям и сортируем по убыванию
        product_counts = (
            df["Обозначение_изделия"].value_counts().sort_values(ascending=False)
        )

        # Создаем столбчатую диаграмму
        ax = sns.countplot(data=df, x="Обозначение_изделия", order=product_counts.index)
        ax.bar_label(ax.containers[0], label_type="edge")
        ax.set_ylabel("Количество")
        ax.set_xlabel("Обозначение изделия")

        year_text = f"{self.year} год" if str(self.year) != "all" else "все годы"
        plt.title(
            f"Распределение по обозначению изделия для {self.filter_text} ({year_text})"
        )
        plt.xticks(rotation=90)

        # Добавляем информацию
        plt.text(
            0.98,
            0.95,
            f"Всего рекламаций: {len(df)} шт.",
            transform=plt.gca().transAxes,
            ha="right",
            va="top",
            fontsize=10,
        )

        plt.tight_layout()

        # Конвертируем в base64
        chart_base64 = self._save_to_base64()

        # Сохраняем PNG
        png_path = None
        if save_to_file:
            png_path = get_defect_chart_product_path()
            plt.savefig(png_path, dpi=300, bbox_inches="tight")

        plt.close()

        return {
            "base64": chart_base64,
            "png_path": png_path,
            "title": "График по обозначению изделия",
        }

    def create_chart_by_manufacture_date(self, df, save_to_file=False):
        """График по дате изготовления"""

        # Фильтруем только записи с валидной датой изготовления
        df_filtered = df.dropna(subset=["Дата_изготовления_formatted"])

        if df_filtered.empty:
            return None

        plt.figure(figsize=(12, 6))

        # Сортируем по дате изготовления
        df_filtered = df_filtered.sort_values(by="Дата_изготовления_formatted")

        # Подсчитываем количество по датам
        date_counts = (
            df_filtered["Дата_изготовления_formatted"].value_counts().sort_index()
        )

        # Создаем столбчатую диаграмму
        ax = sns.countplot(
            data=df_filtered,
            x="Дата_изготовления_formatted",
            order=date_counts.index,
        )
        ax.bar_label(ax.containers[0], label_type="edge")
        ax.set_ylabel("Количество")
        ax.set_xlabel("Дата изготовления (год-месяц)")

        year_text = f"{self.year} год" if str(self.year) != "all" else "все годы"
        plt.title(
            f"Распределение по дате изготовления для {self.filter_text} ({year_text})"
        )
        plt.xticks(rotation=90)

        # Добавляем информацию
        plt.text(
            0.98,
            0.95,
            f"Проанализировано: {len(df_filtered)} шт.\n(пропущено записей без даты: {len(df) - len(df_filtered)})",
            transform=plt.gca().transAxes,
            ha="right",
            va="top",
            fontsize=10,
        )

        plt.tight_layout()

        # Конвертируем в base64
        chart_base64 = self._save_to_base64()

        # Сохраняем PNG
        png_path = None
        if save_to_file:
            png_path = get_defect_chart_manufacture_path()
            plt.savefig(png_path, dpi=300, bbox_inches="tight")

        plt.close()

        return {
            "base64": chart_base64,
            "png_path": png_path,
            "title": "График по дате изготовления",
        }

    def create_chart_by_message_date(self, df, save_to_file=False):
        """График по дате получения сообщения о дефекте"""

        if df.empty:
            return None

        plt.figure(figsize=(12, 6))

        # Подсчитываем количество по датам
        date_counts = df["Дата_сообщения_formatted"].value_counts().sort_index()

        # Создаем столбчатую диаграмму
        ax = sns.countplot(
            data=df, x="Дата_сообщения_formatted", order=date_counts.index
        )
        ax.bar_label(ax.containers[0], label_type="edge")
        ax.set_ylabel("Количество")
        ax.set_xlabel("Дата получения сообщения (год-месяц)")

        year_text = f"{self.year} год" if str(self.year) != "all" else "все годы"
        plt.title(
            f"Распределение по дате получения сообщения для {self.filter_text} ({year_text})"
        )
        plt.xticks(rotation=90)

        # Добавляем информацию
        plt.text(
            0.98,
            0.95,
            f"Всего рекламаций: {len(df)} шт.",
            transform=plt.gca().transAxes,
            ha="right",
            va="top",
            fontsize=10,
        )

        plt.tight_layout()

        # Конвертируем в base64
        chart_base64 = self._save_to_base64()

        # Сохраняем PNG
        png_path = None
        if save_to_file:
            png_path = get_defect_chart_message_path()
            plt.savefig(png_path, dpi=300, bbox_inches="tight")

        plt.close()

        return {
            "base64": chart_base64,
            "png_path": png_path,
            "title": "График по дате получения сообщения",
        }

    def create_combined_chart(self, df, save_to_file=False):
        """Совмещенный график: дата изготовления + дата сообщения"""

        # Фильтруем только записи с валидной датой изготовления
        df_filtered = df.dropna(subset=["Дата_изготовления_formatted"])

        if df_filtered.empty:
            return None

        plt.figure(figsize=(12, 6))

        # Объединяем значения из обеих колонок для оси X
        all_values = pd.concat(
            [
                df_filtered["Дата_сообщения_formatted"],
                df_filtered["Дата_изготовления_formatted"],
            ]
        ).unique()

        # Сортируем значения
        all_values_sorted = sorted(all_values)

        # Преобразовываем данные в длинный формат
        df_melted = pd.melt(
            df_filtered,
            value_vars=["Дата_сообщения_formatted", "Дата_изготовления_formatted"],
            var_name="Тип_даты",
            value_name="Дата",
        )

        # Переименовываем для легенды
        df_melted["Тип_даты"] = df_melted["Тип_даты"].replace(
            {
                "Дата_сообщения_formatted": "Дата получения сообщения",
                "Дата_изготовления_formatted": "Дата изготовления",
            }
        )

        # Создаем график
        ax = sns.countplot(
            data=df_melted, x="Дата", hue="Тип_даты", order=all_values_sorted
        )

        # Добавляем подписи на столбцы
        ax.bar_label(ax.containers[0], label_type="edge")
        ax.bar_label(ax.containers[1], label_type="edge")

        ax.set_ylabel("Количество")
        ax.set_xlabel("Год-Месяц")

        year_text = f"{self.year} год" if str(self.year) != "all" else "все годы"
        plt.title(f"Совмещенный график для {self.filter_text} ({year_text})")
        plt.legend(title="Тип даты")
        plt.xticks(rotation=90)

        # Добавляем информацию
        plt.text(
            0.19,
            0.78,
            f"Проанализировано: {len(df_filtered)} шт.",
            transform=plt.gca().transAxes,
            ha="right",
            va="top",
            fontsize=10,
        )

        plt.tight_layout()

        # Конвертируем в base64
        chart_base64 = self._save_to_base64()

        # Сохраняем PNG
        png_path = None
        if save_to_file:
            png_path = get_defect_chart_combined_path()
            plt.savefig(png_path, dpi=300, bbox_inches="tight")

        plt.close()

        return {
            "base64": chart_base64,
            "png_path": png_path,
            "title": "Совмещенный график",
        }

    def _save_to_base64(self):
        """Конвертация текущего графика в base64"""
        buffer = BytesIO()
        plt.savefig(buffer, format="png", dpi=300, bbox_inches="tight")
        buffer.seek(0)
        plot_data = buffer.getvalue()
        buffer.close()
        return base64.b64encode(plot_data).decode("utf-8")


class DefectDateReportManager:
    """Главный класс-координатор"""

    # def __init__(self, year=None, consumers=None, product=None):
    def __init__(self, year=None, consumers=None, products=None):
        self.year = year or date.today().year
        self.consumers = consumers or []
        # self.product = product
        self.products = products or []

        self.data_processor = DefectDateDataProcessor(
            year=self.year, consumers=self.consumers, products=self.products
        )
        self.chart_generator = None  # Создадим после получения filter_text

    def generate_report(self, chart_type="all"):
        """
        Главный метод генерации отчета

        chart_type:
        - "product" - график по обозначению изделия
        - "manufacture" - график по дате изготовления
        - "message" - график по дате сообщения
        - "combined" - совмещенный график
        - "all" - все графики
        """

        try:
            # Получаем данные
            success, message = self.data_processor.get_data_from_db()
            if not success:
                return {"success": False, "message": message, "message_type": "info"}

            # Подготавливаем данные
            success, message = self.data_processor.prepare_data()
            if not success:
                return {"success": False, "message": message, "message_type": "error"}

            # Получаем filter_text и создаем генератор графиков
            filter_text = self.data_processor._get_filter_names()
            self.chart_generator = DefectDateChartGenerator(
                filter_text=filter_text, year=self.year
            )

            df = self.data_processor.df

            # Генерируем нужные графики БЕЗ сохранения в файл
            charts = {}

            if chart_type in ["product", "all"]:
                chart_data = self.chart_generator.create_chart_by_product(
                    df, save_to_file=False
                )
                if chart_data:
                    charts["product"] = chart_data

            if chart_type in ["manufacture", "all"]:
                chart_data = self.chart_generator.create_chart_by_manufacture_date(
                    df, save_to_file=False
                )
                if chart_data:
                    charts["manufacture"] = chart_data

            if chart_type in ["message", "all"]:
                chart_data = self.chart_generator.create_chart_by_message_date(
                    df, save_to_file=False
                )
                if chart_data:
                    charts["message"] = chart_data

            if chart_type in ["combined", "all"]:
                chart_data = self.chart_generator.create_combined_chart(
                    df, save_to_file=False
                )
                if chart_data:
                    charts["combined"] = chart_data

            if not charts:
                return {
                    "success": False,
                    "message": "Не удалось создать графики",
                    "message_type": "error",
                }

            year_text = (
                f"за {self.year} год" if str(self.year) != "all" else "за все годы"
            )

            return {
                "success": True,
                "message": f"Анализ для {filter_text} {year_text} завершен",
                "full_message": f"Файлы с графиками находятся в папке {BASE_REPORTS_DIR}",
                "charts": charts,
                "chart_type": chart_type,
                "total_records": len(df),
                "filter_text": filter_text,
                "year": self.year,
                "message_type": "success",
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Ошибка при анализе: {str(e)}",
                "message_type": "error",
            }

    def save_to_files(self, analysis_data=None):
        """Сохранение графиков в файлы"""
        try:
            # Используем переданные данные или генерируем заново
            if analysis_data is None:
                analysis_data = self.generate_report()

            if not analysis_data["success"]:
                return {
                    "success": False,
                    "error": "Не удалось сгенерировать данные для сохранения",
                }

            charts = analysis_data.get("charts", {})
            saved_files = []

            # Получаем данные заново для сохранения (без auto-save)
            success, message = self.data_processor.get_data_from_db()
            if not success:
                return {"success": False, "error": message}

            success, message = self.data_processor.prepare_data()
            if not success:
                return {"success": False, "error": message}

            df = self.data_processor.df
            filter_text = self.data_processor._get_filter_names()

            # Создаем генератор БЕЗ автосохранения
            chart_generator = DefectDateChartGenerator(
                filter_text=filter_text, year=self.year
            )

            # Сохраняем каждый график отдельно
            if "product" in charts:
                path = chart_generator.create_chart_by_product(df, save_to_file=True)
                if path:
                    saved_files.append(path)

            if "manufacture" in charts:
                path = chart_generator.create_chart_by_manufacture_date(
                    df, save_to_file=True
                )
                if path:
                    saved_files.append(path)

            if "message" in charts:
                path = chart_generator.create_chart_by_message_date(
                    df, save_to_file=True
                )
                if path:
                    saved_files.append(path)

            if "combined" in charts:
                path = chart_generator.create_combined_chart(df, save_to_file=True)
                if path:
                    saved_files.append(path)

            return {
                "success": True,
                "base_dir": BASE_REPORTS_DIR,
                "saved_files": saved_files,
                "files_count": len(saved_files),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}
