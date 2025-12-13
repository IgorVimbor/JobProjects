# analytics\modules\mileage_chart_modul.py
"""
Модуль анализа распределения рекламаций по пробегу.

Включает класс:
- `MileageChartProcessor` - Анализ распределения рекламаций по пробегу
"""

import pandas as pd
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# import seaborn as sns
import base64
from io import BytesIO
from datetime import date
from django.db.models import Q

from reclamations.models import Reclamation
from reports.config.paths import (
    BASE_REPORTS_DIR,
    get_mileage_chart_txt_path,
    get_mileage_chart_png_path,
)


class MileageChartProcessor:
    """Анализ распределения рекламаций по пробегу"""

    def __init__(self, year=None, consumers=None, product=None, step=1000):
        self.today = date.today()
        self.year = year or self.today.year
        self.consumers = consumers or []  # Список потребителей
        self.product = product
        self.step = step  # Шаг разбиения пробега
        self.df = pd.DataFrame()
        self.bins_data = pd.Series()

    def value_probeg(self, str_in):
        """Преобразование пробега в километры"""
        str_in = str(str_in).replace(",", ".").replace(" ", "").rstrip(".")

        if str_in.endswith("м/ч"):  # если строка заканчивается на м/ч
            # срезом убираем м/ч, переводим в число и умножаем на 9
            str_in = float(str_in[:-3]) * 9

        elif str_in.endswith("км"):  # если строка заканчивается на км
            # срезом убираем км и переводим в float
            str_in = float(str_in[:-2])

        return str_in

    def _get_filter_names(self):
        """Возвращает названия фильтров для отчета"""
        filter_parts = []

        if self.consumers:
            if len(self.consumers) == 1:
                filter_parts.append(self.consumers[0])
            else:
                filter_parts.append(f"{len(self.consumers)} потребителей")

        if self.product:
            filter_parts.append(self.product)

        if not filter_parts:
            return "всех потребителей"

        return ", ".join(filter_parts)

    def get_data_from_db(self):
        """Получение и обработка данных из Django ORM"""
        # Проверяем, что изделие выбрано
        if not self.product:
            return None, "Не выбрано изделие для анализа"

        # Формируем фильтр
        queryset_filter = Q(
            year=self.year,  # Фильтр по году
            away_type__in=["kilometre", "moto"],  # Исключаем "notdata" и "psi"
            product_name__name=self.product,  # Фильтр по одному изделию
        )

        # Добавляем фильтры по потребителям
        if self.consumers:
            consumer_q = Q()
            for consumer in self.consumers:
                consumer_q |= Q(defect_period__name=consumer)
            queryset_filter &= consumer_q

        # Получаем данные
        queryset = (
            Reclamation.objects.filter(queryset_filter)
            .select_related("defect_period", "product_name")
            .values(
                "defect_period__name",
                "product_name__name",
                "mileage_operating_time",
                "away_type",
            )
        )

        # Если нет данных ...
        if not queryset.exists():
            filter_text = self._get_filter_names()
            return None, f"Нет данных для {filter_text} за {self.year} год"

        # Преобразуем в DataFrame
        df = pd.DataFrame(list(queryset))
        df.rename(
            columns={
                "defect_period__name": "Потребитель",
                "product_name__name": "Изделие",
                "mileage_operating_time": "Пробег_наработка",
                "away_type": "Единица_измерения",
            },
            inplace=True,
        )

        # Фильтруем только записи с км и м/ч (дополнительная проверка)
        df = df[
            (df["Пробег_наработка"].str.contains("км", na=False))
            | (df["Пробег_наработка"].str.contains("м/ч", na=False))
        ]

        if df.empty:
            filter_text = self._get_filter_names()
            return None, f"Нет данных с пробегом для {filter_text} за {self.year} год"

        try:
            # Применяем функцию преобразования
            df["Пробег_км"] = df["Пробег_наработка"].apply(self.value_probeg)

            # Исключаем аномальные значения
            df = df[df["Пробег_км"] < 300000]

            if df.empty:
                return None, "После фильтрации аномальных значений данных не осталось"

            self.df = df
            return True, f"Обработано записей: {len(df)}"

        except Exception as e:
            return None, f"Ошибка обработки данных: {str(e)}"

    def create_analysis(self):
        """Создание анализа по бинам с настраиваемым шагом"""
        if self.df.empty:
            return False

        # Определяем максимальное значение для создания бинов
        max_value = self.df["Пробег_км"].max()

        # Создаем бины с выбранным шагом
        bins = np.arange(0, max_value + self.step, self.step)

        # Создаем новый столбец с бинами
        self.df["Пробег_бин"] = pd.cut(self.df["Пробег_км"], bins=bins, right=False)

        # Группируем по бинам и ФИЛЬТРУЕМ нулевые значения
        self.bins_data = self.df.groupby("Пробег_бин")["Пробег_км"].count()
        self.bins_data = self.bins_data[self.bins_data > 0]

        return True

    def create_chart_base64(self):
        """Создание графика в base64"""
        if self.bins_data.empty:
            return None

        plt.figure(figsize=(12, 6))

        # Создаем график

        # # вариант 1 (используем seaborn)
        # ax = sns.countplot(data=self.df, x="Пробег_бин")
        # ax.bar_label(ax.containers[0], label_type="edge")

        # вариант 2 (используем matplotlib)
        # # Подсчитываем количество в каждом бине
        # bin_counts = self.df["Пробег_бин"].value_counts().sort_index()
        # Используем уже отфильтрованные данные
        bin_counts = self.bins_data  # Вместо value_counts()
        len_bin_counts = len(bin_counts)

        # Создаем столбчатую диаграмму
        bars = plt.bar(
            range(len_bin_counts),
            bin_counts.values,
            color="skyblue",
            edgecolor="black",
        )

        # Добавляем подписи на столбцы (аналог bar_label)
        for i, bar in enumerate(bars):
            height = bar.get_height()
            if height > 0:  # Показываем только ненулевые значения
                plt.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height + 0.02,  # расстояние от столбца до цифры
                    str(int(height)),
                    ha="center",
                    va="bottom",
                )

        # Создаем красивые подписи для оси X
        x_labels = []
        for interval in bin_counts.index:
            start = int(interval.left)
            end = int(interval.right)
            x_labels.append(f"{start}-{end}")

        # Настраиваем подписи для оси X
        # Если столбцов больше 10 - вертикальные подписи по оси Х, иначе - горизонтальные
        if len_bin_counts > 10:
            plt.xticks(range(len_bin_counts), x_labels, rotation=89)
        else:
            plt.xticks(range(len_bin_counts), x_labels)

        filter_text = self._get_filter_names()
        plt.title(
            f"Распределение по пробегу с шагом {self.step} км. для {filter_text} за {self.year} год"
        )
        plt.xlabel("Пробег (диапазоны)")
        plt.ylabel("Количество")

        # Добавляем информацию в правый верхний угол

        # # вариант 1
        # plt.legend(fontsize=10, title=f"Всего дефектных изделий {len(self.df)} шт.")

        # # вариант 2 - Текст с общей информацией, заметками в любом месте графика по координатам
        # plt.figtext(  # Размещает текст в любом месте графика по координатам - (0.02, 0.02) означают левый нижний угол
        #     0.98,  # (0.98, 0.98) - координаты правого верхнего угла
        #     0.98,
        #     f"Всего дефектных изделий: {len(self.df)} шт.",
        #     fontsize=10,
        #     ha="right",
        #     va="top",
        #     bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"),
        # )

        # вариант 3 - Простой текст без рамки
        plt.text(
            0.98,
            0.95,
            f"Проанализировано рекламаций: {len(self.df)} шт.",
            transform=plt.gca().transAxes,
            ha="right",
            va="top",
            fontsize=10,
        )

        plt.tight_layout()

        # Конвертируем в base64
        buffer = BytesIO()
        plt.savefig(buffer, format="png", dpi=300, bbox_inches="tight")
        buffer.seek(0)
        plot_data = buffer.getvalue()
        buffer.close()
        plt.close()

        return base64.b64encode(plot_data).decode("utf-8")

    def save_files(self):
        """Сохранение файлов на диск"""

        # TXT файл
        txt_path = get_mileage_chart_txt_path()
        filter_text = self._get_filter_names()

        with open(txt_path, "w", encoding="utf-8") as f:
            print(
                f"\n\tРаспределение по пробегу с шагом {self.step} км. для {filter_text} за {self.year} год\n\n",
                file=f,
            )
            f.write(self.bins_data.to_string())

        # PNG файл
        png_path = get_mileage_chart_png_path()

        # Пересоздаем график для сохранения
        plt.figure(figsize=(12, 6))

        # Используем уже отфильтрованные данные
        bin_counts = self.bins_data
        len_bin_counts = len(bin_counts)

        # Создаем столбчатую диаграмму
        bars = plt.bar(
            range(len_bin_counts),
            bin_counts.values,
            color="skyblue",
            edgecolor="black",
        )

        # Добавляем подписи на столбцы
        for i, bar in enumerate(bars):
            height = bar.get_height()
            if height > 0:  # Показываем только ненулевые значения
                plt.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height + 0.02,
                    str(int(height)),
                    ha="center",
                    va="bottom",
                )

        # Создаем красивые подписи для оси X
        x_labels = []
        for interval in bin_counts.index:
            start = int(interval.left)
            end = int(interval.right)
            x_labels.append(f"{start}-{end}")

        # Настраиваем подписи для оси X
        if len_bin_counts > 10:
            plt.xticks(range(len_bin_counts), x_labels, rotation=89)
        else:
            plt.xticks(range(len_bin_counts), x_labels)

        filter_text = self._get_filter_names()
        plt.title(
            f"Распределение по пробегу с шагом {self.step} км. для {filter_text} за {self.year} год"
        )
        plt.xlabel("Пробег (диапазоны)")
        plt.ylabel("Количество")

        # Добавляем информацию в правый верхний угол
        plt.text(
            0.98,
            0.95,
            f"Проанализировано рекламаций: {len(self.df)} шт.",
            transform=plt.gca().transAxes,
            ha="right",
            va="top",
            fontsize=10,
        )

        plt.tight_layout()

        # Сохраняем в файл
        plt.savefig(png_path, dpi=300, bbox_inches="tight")
        plt.close()

        return txt_path, png_path

    def generate_report(self):
        """Главный метод генерации отчета"""
        try:
            # Получаем данные
            success, message = self.get_data_from_db()
            if not success:
                return {"success": False, "message": message, "message_type": "info"}

            # Создаем анализ
            if not self.create_analysis():
                return {
                    "success": False,
                    "message": "Ошибка создания анализа",
                    "message_type": "error",
                }

            # Создаем график для веб
            chart_base64 = self.create_chart_base64()

            # Преобразуем Interval ключи в строки и добавляем проценты
            table_data = {}
            total_records = len(self.df)
            for interval, count in self.bins_data.items():
                # Преобразуем pandas Interval в строку
                interval_str = f"{int(interval.left)}-{int(interval.right)} км"
                count_int = int(count)
                # Считаем процент (2 знака после запятой)
                percentage = round((count_int / total_records) * 100, 2)

                table_data[interval_str] = {
                    "count": count_int,
                    "percentage": percentage,
                }

            # Сохраняем файлы
            txt_path, png_path = self.save_files()

            filter_text = self._get_filter_names()

            return {
                "success": True,
                "message": f"Анализ для {filter_text} завершен",
                "full_message": f"Файлы с таблицей и графиком находятся в папке {BASE_REPORTS_DIR}",
                "table_data": table_data,
                "chart_base64": chart_base64,
                "total_records": len(self.df),
                "filter_text": filter_text,
                "year": self.year,
                "txt_path": txt_path,
                "png_path": png_path,
                "message_type": "success",
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Ошибка при анализе: {str(e)}",
                "message_type": "error",
            }
