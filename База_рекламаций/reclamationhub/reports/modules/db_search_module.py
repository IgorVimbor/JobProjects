# reports/modules/db_search_module.py
"""Модуль приложения "Поиск по базе рекламаций" с основной логикой поиска.

Включает класс:
- `DbSearchProcessor` - Поиск по базе рекламаций с точным сопоставлением номеров
"""

import os
from datetime import date
from django.db.models import Q

from reclamations.models import Reclamation
from reports.config.paths import get_db_search_txt_path


class DbSearchProcessor:
    """Класс для поиска по базе рекламаций с точным сопоставлением номеров"""

    def __init__(self, year, engine_numbers=None, act_numbers=None):
        """
        Инициализация процессора поиска
        :param year: Год для фильтрации рекламаций
        :param engine_numbers: Список номеров двигателей для поиска
        :param act_numbers: Список номеров актов для поиска
        """
        self.year = year
        # Очищаем списки от пустых строк и пробелов
        self.engine_numbers = [
            num.strip() for num in (engine_numbers or []) if num.strip()
        ]
        self.act_numbers = [num.strip() for num in (act_numbers or []) if num.strip()]
        self.today = date.today()
        self._cached_records = None  # Кэш для результатов запроса к БД

    def _get_all_records(self):
        """
        Единый метод получения всех записей по критериям поиска
        Использует кэширование - запрос к БД выполняется только один раз
        Применяет ТОЧНЫЙ поиск (__in) вместо частичного (__icontains)
        """
        # Если данные уже загружены - возвращаем из кэша
        if self._cached_records is not None:
            return self._cached_records

        # Строим Q объекты для точного поиска
        q_objects = Q()

        if self.engine_numbers:
            # Точный поиск: номер двигателя должен ПОЛНОСТЬЮ совпадать
            q_objects |= Q(engine_number__in=self.engine_numbers)

        if self.act_numbers:
            # Точный поиск: номер акта должен ПОЛНОСТЬЮ совпадать
            q_objects |= Q(consumer_act_number__in=self.act_numbers)

        # Если нет критериев поиска - возвращаем пустой QuerySet
        if not q_objects:
            self._cached_records = Reclamation.objects.none()
            return self._cached_records

        # Выполняем единый оптимизированный запрос к БД
        self._cached_records = (
            Reclamation.objects.filter(year=self.year)  # Фильтруем по году
            .filter(q_objects)
            .select_related(
                # Загружаем связанные объекты заранее для избежания N+1 запросов
                "product_name",
                "product",
                "defect_period",
                "investigation",
            )
            .distinct()
        )  # Убираем дубликаты

        return self._cached_records

    def quick_search(self):
        """
        Быстрый поиск для предварительного просмотра результатов
        Возвращает список с информацией о найденных/не найденных номерах
        Аналог функции get_itog() из оригинального Tkinter приложения
        """
        # Получаем все найденные записи из БД (с кэшированием)
        records = self._get_all_records()
        results = []

        # Проверяем каждый введенный номер двигателя
        for engine_num in self.engine_numbers:
            # Находим ВСЕ записи с этим номером двигателя
            matching_records = [r for r in records if r.engine_number == engine_num]

            if matching_records:
                # Добавляем ВСЕ найденные записи
                for record in matching_records:
                    results.append(
                        {
                            "type": "engine",
                            "search_value": engine_num,
                            "found_value": record.engine_number,
                            "record_id": record.id,
                            "product_info": self._get_product_info(record),
                        }
                    )
            else:
                results.append(
                    {
                        "type": "engine",
                        "search_value": engine_num,
                        "found": False,
                        "message": f"Двигателя {engine_num} в базе нет",
                    }
                )

        # Проверяем каждый введенный номер акта
        for act_num in self.act_numbers:
            # Находим ВСЕ записи с этим номером акта
            matching_records = [r for r in records if r.consumer_act_number == act_num]

            if matching_records:
                # Добавляем ВСЕ найденные записи
                for record in matching_records:
                    results.append(
                        {
                            "type": "act",
                            "search_value": act_num,
                            "found_value": record.consumer_act_number,
                            "record_id": record.id,
                            "product_info": self._get_product_info(record),
                        }
                    )
            else:
                results.append(
                    {
                        "type": "act",
                        "search_value": act_num,
                        "found": False,
                        "message": f"Акта {act_num} в базе нет",
                    }
                )

        return results

    def detailed_search(self):
        """
        Детальный поиск с созданием TXT файла отчета
        Аналог функции otchet_output() из оригинального Tkinter приложения
        """
        try:
            # Получаем все найденные записи (используем тот же кэш что и в quick_search)
            records = self._get_all_records()

            # Проверяем есть ли данные для отчета
            if not records.exists():
                return {
                    "success": False,
                    "message": "Данные для отчета не найдены",
                    "message_type": "info",
                }

            # Создаем TXT файл с детальным отчетом
            txt_file_path = get_db_search_txt_path()
            self._generate_txt_report(records, txt_file_path)

            return {
                "success": True,
                "message": f"Отчет успешно сформирован",
                "full_message": f"Файл отчета находится в папке: {txt_file_path}",
                "txt_path": txt_file_path,
                "filename": os.path.basename(txt_file_path),
                "records_count": records.count(),
                "message_type": "success",
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Ошибка при формировании отчета: {str(e)}",
                "message_type": "error",
            }

    def _get_product_info(self, record):
        """
        Вспомогательный метод для получения краткой информации об изделии
        Используется в quick_search для отображения в интерфейсе
        """
        product_name = record.product_name.name if record.product_name else "Не указано"
        nomenclature = record.product.nomenclature if record.product else "Не указано"
        return f"{product_name} | {nomenclature}"

    def _generate_txt_report(self, records, file_path):
        """
        Генерация детального TXT отчета с информацией о всех введенных номерах
        :param records: QuerySet найденных записей из БД
        :param file_path: Путь к создаваемому TXT файлу
        """
        with open(file_path, "w", encoding="utf-8") as f:
            # print("\n" * 2, file=f)

            # Заголовок отчета с параметрами поиска
            print(
                f'\nДата формирования отчета: {self.today.strftime("%d.%m.%Y")}',
                file=f,
            )
            print(f"\nГод поиска: {self.year}", file=f)
            # print(file=f)

            if self.engine_numbers:
                print("Номера двигателей:", ", ".join(self.engine_numbers), file=f)
                # print(file=f)

            if self.act_numbers:
                print("Номера актов:", ", ".join(self.act_numbers), file=f)
                # print(file=f)

            print("=" * 80, file=f)
            print(file=f)

            # Обрабатываем каждый введенный номер двигателя
            for engine_num in self.engine_numbers:
                # Находим ВСЕ записи с этим номером
                matching_records = [r for r in records if r.engine_number == engine_num]

                if matching_records:
                    # Выводим ВСЕ найденные записи
                    for record in matching_records:
                        self._write_record_details(
                            record, f, search_type="engine", search_value=engine_num
                        )
                else:
                    print(f"Двигателя {engine_num} в базе нет", file=f)
                    print("-" * 80, file=f)
                    print(file=f)

            # Обрабатываем каждый введенный номер акта
            for act_num in self.act_numbers:
                # Находим ВСЕ записи с этим номером
                matching_records = [
                    r for r in records if r.consumer_act_number == act_num
                ]

                if matching_records:
                    # Выводим ВСЕ найденные записи
                    for record in matching_records:
                        self._write_record_details(
                            record, f, search_type="act", search_value=act_num
                        )
                else:
                    print(f"Акта {act_num} в базе нет", file=f)
                    print("-" * 80, file=f)
                    print(file=f)

    def _write_record_details(self, record, file, search_type=None, search_value=None):
        """
        Запись детальной информации об одной записи в TXT файл
        :param record: Объект записи рекламации из БД
        :param file: Файловый объект для записи
        :param search_type: Тип поиска ('engine' или 'act')
        :param search_value: Искомое значение для отображения в заголовке
        """
        # Заголовок записи с указанием что нашли
        engine_number = record.engine_number
        consumer_act_number = record.consumer_act_number

        if search_type == "engine":
            print(
                f"Двигатель {engine_number} | ID записи - {record.id} |",
                file=file,
            )
        elif search_type == "act":
            print(
                f"Акт {consumer_act_number} | ID записи - {record.id} |",
                file=file,
            )
        else:
            # Универсальный заголовок для обратной совместимости
            if engine_number:
                print(
                    f"Двигатель {engine_number} | ID записи - {record.id} |",
                    file=file,
                )
            elif consumer_act_number:
                print(
                    f"Акт {consumer_act_number} | ID записи - {record.id} |",
                    file=file,
                )
            else:
                print(f"Запись ID - {record.id} |", file=file)

        print("-" * 80, file=file)

        # Информация об изделии
        product_name = record.product_name.name if record.product_name else "не указано"
        product_nomenclature = (
            record.product.nomenclature if record.product else "не указано"
        )
        product_number = record.product_number or "б/н"
        manufacture_date = record.manufacture_date or ""

        print(
            f"{product_name} | {product_nomenclature} | зав.№: {product_number} {manufacture_date} |",
            file=file,
        )

        # Где выявлен дефект
        defect_period = (
            record.defect_period.name if record.defect_period else "не указан"
        )
        print(f"Где выявлен дефект: {defect_period} |", end=" ", file=file)

        # Рекламационный акт приобретателя
        if record.consumer_act_number:
            print(f"Р/А №: {record.consumer_act_number} |", end=" ", file=file)
        else:
            print("Р/А №: акта нет |", end=" ", file=file)

        # Заявленный дефект
        claimed_defect = record.claimed_defect or "не указан"
        print(f"Дефект: {claimed_defect}", file=file)

        # Информация о расследовании БЗА
        if hasattr(record, "investigation") and record.investigation:
            inv = record.investigation

            # Номер и дата акта исследования
            if inv.act_number:
                act_date = (
                    inv.act_date.strftime("%d.%m.%Y")
                    if inv.act_date
                    else "дата не указана"
                )
                print(f"Акт БЗА: {inv.act_number} от {act_date}", file=file)
            else:
                print("Акт БЗА: акта нет", file=file)

            # Решение БЗА (используем русский перевод через get_solution_display)
            if inv.solution:
                solution_display = (
                    inv.get_solution_display()
                )  # "Признать" или "Отклонить"
                print(f"Решение БЗА: {solution_display}", end=" ", file=file)
            else:
                print(f"Решение БЗА: не указано", end=" ", file=file)

            # Дополнительные комментарии
            if inv.defect_causes:
                print(f"| {inv.defect_causes}", file=file)
            else:
                print("", file=file)
        else:
            # Исследование не проводилось
            print("Акт БЗА: акта нет", file=file)
            print("Решение БЗА: исследование не проводилось", file=file)

        print("-" * 80, file=file)
        print(file=file)


def perform_search(year, engine_numbers_str, act_numbers_str, search_type="quick"):
    """
    Главная функция для выполнения поиска
    Точка входа для view функций Django

    :param year: Год для фильтрации
    :param engine_numbers_str: Строка с номерами двигателей через пробел
    :param act_numbers_str: Строка с номерами актов через пробел
    :param search_type: Тип поиска ('quick' или 'detailed')
    :return: Словарь с результатами поиска
    """
    # Разбираем строки на списки номеров (split по пробелам)
    engine_numbers = engine_numbers_str.split() if engine_numbers_str else []
    act_numbers = act_numbers_str.split() if act_numbers_str else []

    # Проверяем, что есть что искать
    if not engine_numbers and not act_numbers:
        return {
            "success": False,
            "message": "Введите номера двигателей или актов для поиска",
            "message_type": "warning",
        }

    # Создаем процессор поиска
    processor = DbSearchProcessor(year, engine_numbers, act_numbers)

    # Выполняем нужный тип поиска
    if search_type == "quick":
        results = processor.quick_search()
        return {"success": True, "results": results, "message_type": "success"}
    else:  # detailed
        return processor.detailed_search()
