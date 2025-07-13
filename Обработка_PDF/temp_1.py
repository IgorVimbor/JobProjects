# pdf_processor.py

import json
import os
from pdf2image import convert_from_path
import pytesseract
import re
from PIL import Image
import cv2
import numpy as np


class PDFProcessingError(Exception):
    """Пользовательское исключение для обработки ошибок PDF"""
    pass

class ExcelError(Exception):
    """Пользовательское исключение для обработки ошибок Excel"""
    pass


class PDFProcessor:
    """Базовый класс для обработки PDF документов"""

    def __init__(self, pdf_path, lang='rus'):
        self.pdf_path = pdf_path
        self.lang = lang  # язык для распознавания OCR

        # Словарь для хранения извлеченных данных загружаем из config.json
        with open('config.json', 'r', encoding='utf-8') as file:
            config = json.load(file)
            self.data = config['default_data'].copy()

        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


    def preprocess_image(self, image, enhance_quality=False):
        """
        Общий метод предобработки изображения для улучшения качества распознавания
        image: Исходное изображение
        enhance_quality: Флаг для дополнительного улучшения качества
        """
        try:
            # Конвертируем в numpy array
            img_array = np.array(image)

            # Конвертируем в градации серого
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

            if enhance_quality:
                # Улучшение качества для плохих изображений

                # Увеличение резкости
                kernel_sharpening = np.array([[-1,-1,-1],
                                            [-1, 9,-1],
                                            [-1,-1,-1]])
                gray = cv2.filter2D(gray, -1, kernel_sharpening)

                # Улучшение контраста
                alpha = 1.5 # Коэффициент контраста (1.0-3.0)
                beta = 10   # Коэффициент яркости (0-100)
                gray = cv2.convertScaleAbs(gray, alpha=alpha, beta=beta)

                # Уменьшение шума (если изображение зашумлено)
                gray = cv2.GaussianBlur(gray, (3,3), 0)

            # Применяем бинаризацию Оцу
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            return Image.fromarray(binary)

        except Exception as e:
            raise PDFProcessingError(f"Ошибка при предобработке изображения: {str(e)}")


    def enhance_image_quality(self, image):
        """Общий метод улучшения качества изображения с использованием расширенных методов"""
        try:
            # Конвертируем в numpy array
            img_array = np.array(image)

            # Автоматическая коррекция гаммы
            def adjust_gamma(image, gamma=1.0):
                inv_gamma = 1.0 / gamma
                table = np.array([((i / 255.0) ** inv_gamma) * 255
                    for i in np.arange(0, 256)]).astype("uint8")
                return cv2.LUT(image, table)

            # Пробуем разные значения гаммы
            gamma_variants = [0.5, 0.8, 1.2, 1.5]
            best_gamma = 1.0
            max_variance = 0

            for gamma in gamma_variants:
                adjusted = adjust_gamma(img_array, gamma)
                variance = np.var(adjusted)
                if variance > max_variance:
                    max_variance = variance
                    best_gamma = gamma

            # Применяем лучшее значение гаммы
            img_array = adjust_gamma(img_array, best_gamma)

            # Автоматическое выравнивание гистограммы
            lab = cv2.cvtColor(img_array, cv2.COLOR_RGB2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            l = clahe.apply(l)
            lab = cv2.merge((l,a,b))
            img_array = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)

            return Image.fromarray(img_array)

        except Exception as e:
            raise PDFProcessingError(f"Ошибка при улучшении качества изображения: {str(e)}")


    def get_raw_text(self, enhance_quality=False):
        """
        Общий метод получения необработанного текста из PDF
        enhance_quality: Флаг для применения расширенной обработки изображения
        """
        try:
            # Конвертируем только первую страницу PDF
            images = convert_from_path(self.pdf_path, first_page=1, last_page=1)

            if not images:
                raise PDFProcessingError("Не удалось получить изображения из PDF")

            if enhance_quality:
                # Улучшаем качество изображения
                enhanced_image = self.enhance_image_quality(images[0])
                # Применяем предобработку с улучшением качества
                processed_image = self.preprocess_image(enhanced_image, enhance_quality=True)
            else:
                # Обычная предобработка
                processed_image = self.preprocess_image(images[0])

            # Распознаем текст
            text = pytesseract.image_to_string(processed_image, lang=self.lang)
            # text = pytesseract.image_to_string(processed_image, lang='rus')

            if not text.strip():
                raise PDFProcessingError("Не удалось распознать текст в документе")

            return text

        except Exception as e:
            raise PDFProcessingError(f"Ошибка при распознавании текста: {str(e)}")


    def filter_groups(self, groups):
        """Общий метод фильтрации групп с учетом специфики сырых считанных данных"""
        filtered = []
        stop_words = {'и', 'в', 'на', 'по', 'от', 'тс', 'знак'}

        for group in groups:
            # Очистка от лишних символов
            cleaned_group = re.sub(r'[^\w\s.-]', '', group).strip()

            # Пропускаем пустые строки и короткие группы
            if not cleaned_group or len(cleaned_group) <= 1:
                continue

            # Пропускаем группы из спецсимволов
            if all(not c.isalnum() for c in cleaned_group):
                continue

            # Пропускаем стоп-слова
            if cleaned_group.lower() in stop_words:
                continue

            filtered.append(cleaned_group)

            # Прекращаем после десяти групп
            if len(filtered) == 10:
                break

        # print(f"Отфильтрованные группы: {filtered}")
        return filtered


    def count_not_found(self):
        """Общий метод подсчета ненайденных значений"""
        return sum(1 for value in self.data.values() if value == "")


    def parse_text(self, text):
        """Абстрактный метод разбора текста"""
        raise NotImplementedError("В дочерних подклассах должен быть реализован метод parse_text")


    def extract_data(self):
        """Общий метод извлечения структурированных данных из распознанного текста"""
        try:
            # Получаем текст с обычной обработкой
            text = self.get_raw_text(enhance_quality=False)
            self.parse_text(text)

            # Если много "Не найдено", пробуем расширенную обработку
            if self.count_not_found() > 4:
                text = self.get_raw_text(enhance_quality=True)
                self.parse_text(text)

            return self.data

        except Exception as e:
            return {"Ошибка": str(e)}


class PDFProcessorYMZ(PDFProcessor):
    """Класс для обработки формы ЯМЗ"""

    # Регулярные выражения специфичные для ЯМЗ
    ACT_PATTERN = r".*?А[кК][тгрТ].*?арантийног.*?емонта.*?(\d+).*?(\d{2}.\d{2}.\d{4})"  # .*? - любые символы (нежадный поиск)
    ENGINE_PATTERN = r"(?:Рег\.)?\s*(?i)знак ТС[^A-Za-zА-Яа-я\d_]*?(.*?)(?:ФИО|Номер|Адрес|Контактный)"  # паттерн для номера двигателя
    SERVICE_PATTERN = r'["“”]([^"“”]+)["“”]'  # паттерн для сервисного предприятия (текст между любыми кавычками)
    # MILEAGE_PATTERN = r'Дата начала гарант.*?(\d{2}.\d{2}.\d{4})\s*[^0-9]*(\d{4,7}).*?писание неисправност'  # паттерн для пробега
    MILEAGE_PATTERN = r'Дата начала гарант.*?(\d{2}.\d{2}.\d{4})\s*[^0-9]*(\d{4,7})[^0-9]'
    # MILEAGE_PATTERN = r'Дата начала гарантии.*?(\d{2}.\d{2}.\d{4}).*?[\n\s](\d{4,7})[\s|]'


    def __init__(self, pdf_path):
        super().__init__(pdf_path, lang='rus')


    def parse_text(self, text):
        """Реализация парсинга текста и заполнение словаря данных для формы ЯМЗ"""
        # Извлечение номера и даты акта
        act_match = re.search(self.ACT_PATTERN, text)
        if act_match:
            self.data["Номер акта рекламации"] = act_match.group(1)
            self.data["Дата акта"] = act_match.group(2)

        # Извлечение сервисного предприятия
        service_match = re.search(self.SERVICE_PATTERN, text)
        text_service_match = service_match.group(1)
        if len(text_service_match) <= 30:
            self.data["Сервисное предприятие"] = text_service_match

        # Извлечение данных о двигателе
        engine_match = re.search(self.ENGINE_PATTERN, text, re.DOTALL)
        # print(f"Найдено совпадение по двигателю: {bool(engine_match)}")
        if engine_match:
            full_text = engine_match.group(1)
            all_groups = [g.strip() for g in full_text.split()]
            filtered_groups = self.filter_groups(all_groups)
            # print(filtered_groups)

            if len(filtered_groups) > 4:
                self.data["Модель двигателя"] = filtered_groups[2]
                self.data["Номер двигателя"] = filtered_groups[3]
            elif 2 < len(filtered_groups) <= 4:
                self.data["Модель двигателя"] = filtered_groups[1]
                self.data["Номер двигателя"] = filtered_groups[2]
            elif len(filtered_groups) == 2:
                self.data["Модель двигателя"] = filtered_groups[0]
                self.data["Номер двигателя"] = filtered_groups[1]

        # Извлечение пробега
        mileage_match = re.search(self.MILEAGE_PATTERN, text, re.DOTALL)
        # print(f"Найдено совпадение по пробегу: {bool(mileage_match)}")
        if mileage_match:
            # Дата в group(1), пробег в group(2)
            mileage = mileage_match.group(2)
            # print(f"Извлеченный текст о пробеге: {mileage_match.group(1)}, {mileage}")
            # Проверяем, что значение похоже на пробег (только цифры и разумная длина)
            if mileage.isdigit() and 1 <= len(mileage) <= 7:
            # if mileage.isdigit() and 0 <= int(mileage) <= 999999:
                self.data["Пробег/наработка"] = f'{mileage} км'


class PDFProcessorRSM(PDFProcessor):
    """Класс для обработки формы РСМ"""

    # Словарь для преобразования месяцев
    MONTHS = {
        'января': '01', 'февраля': '02', 'марта': '03', 'апреля': '04',
        'мая': '05', 'июня': '06', 'июля': '07', 'августа': '08',
        'сентября': '09', 'октября': '10', 'ноября': '11', 'декабря': '12'
    }

    # Паттерн для номера и даты акта
    ACT_PATTERN = r'Рек[лп]амационный [аa][кr][тr]\s*№\s*(\d+)\s*[оo][тr]\s*[""“«]?(\d+)[""“»]?\s+([а-яА-Я]+)\s+(\d{4})'
    # Паттерн для названия сервисного предприятия (текст между двумя вхождениями "Наименование организации")
    SERVICE_PATTERN = r'Наименование организации\s*(.*?)\s*Наименование организации'
    # Паттерн для транспортного средства
    VEHICLE_PATTERN = r'((?:NOVA|KSU|ACROS).*?)(?=\sR[0O])'

    def __init__(self, pdf_path):
        super().__init__(pdf_path, lang='rus+eng')


    def parse_text(self, text):
        """Реализация разбора текста для формы РСМ"""
        # Извлечение номера и даты акта
        act_match = re.search(self.ACT_PATTERN, text)
        if act_match:
            act_number = act_match.group(1)
            day = act_match.group(2)
            month = self.MONTHS.get(act_match.group(3).lower(), '00')
            year = act_match.group(4)

            self.data["Номер акта рекламации"] = act_number
            self.data["Дата акта"] = f"{day}.{month}.{year}"

        # Извлечение сервисного предприятия
        self.data["Сервисное предприятие"] = self.extract_service_name(text)

        # Извлечение данных о транспортном средстве
        vehicle_match = re.search(self.VEHICLE_PATTERN, text)
        # print(f"Найденный текст: {vehicle_match.group() if vehicle_match else 'Не найдено'}")  # для отладки
        if vehicle_match:
            # Берем первую группу (до текста, который начинается с "RO")
            self.data["Транспортное средство"] = vehicle_match.group(1).strip()


    def extract_service_name(self, text):
        """Извлечение названия сервисного предприятия"""
        # Ищем текст между двумя вхождениями "Наименование организации"
        service_match = re.search(self.SERVICE_PATTERN, text, re.DOTALL)

        if not service_match:
            return ""

        # Получаем весь текст между маркерами
        service_text = service_match.group(1)

        # Разбиваем на группы и фильтруем
        groups = service_text.split()
        filtered_groups = self.filter_groups(groups)

        if not filtered_groups:
            return ""

        # Собираем название организации из первых групп
        # Ищем группы, идущие подряд и содержащие организационно-правовую форму или кавычки
        org_name = []
        for group in filtered_groups:
            if (any(form in group for form in ['ООО', 'АО', 'ПАО', 'КФХ', 'ИП']) or
                any(quote in group for quote in '"«»"') or
                group.isupper() or
                (org_name and (group.isupper() or '.' in group))):
                org_name.append(group)
            elif org_name:  # если уже начали собирать название и встретили что-то другое
                break

        return ' '.join(org_name) if org_name else filtered_groups[0]


class PDFProcessorMAZ(PDFProcessor):
    def extract_data(self):
        """Переопределяем метод для МАЗ. Возвращаем пустой словарь для ручного заполнения"""
        return self.data

    def get_raw_text(self):
        """Переопределяем метод, так как распознавание текста не требуется"""
        return ""


class PDFProcessorMAZ_2(PDFProcessor):
    def extract_data(self):
        """Переопределяем метод для МАЗ-2. Возвращаем пустой словарь для ручного заполнения"""
        return self.data

    def get_raw_text(self):
        """Переопределяем метод, так как распознавание текста не требуется"""
        return ""


class PDFProcessorAnother(PDFProcessor):
    def extract_data(self):
        """Переопределяем метод для Другая. Возвращаем пустой словарь для ручного заполнения"""
        return self.data

    def get_raw_text(self):
        """Переопределяем метод, так как распознавание текста не требуется"""
        return ""
