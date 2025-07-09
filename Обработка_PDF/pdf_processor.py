from pdf2image import convert_from_path
import pytesseract
import re
from PIL import Image
import cv2
import numpy as np

class PDFProcessor:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        # Для Windows укажите путь к исполняемому файлу tesseract
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

    def preprocess_image(self, image):
        """Предобработка изображения для улучшения качества распознавания"""
        # Конвертируем в numpy array
        img_array = np.array(image)

        # Конвертируем в градации серого
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

        # Применяем пороговое значение
        _, threshold = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Возвращаем как PIL Image
        return Image.fromarray(threshold)

    def get_raw_text(self):
        """Получение необработанного текста из PDF"""
        try:
            # Конвертируем PDF в изображения
            images = convert_from_path(self.pdf_path)

            # Берем первую страницу
            first_page = images[0]

            # Предобработка изображения
            processed_image = self.preprocess_image(first_page)

            # Распознаем текст
            text = pytesseract.image_to_string(processed_image, lang='rus')

            return text

        except Exception as e:
            print(f"Ошибка при получении текста: {str(e)}")
            return f"Ошибка при распознавании текста: {str(e)}"

    # def extract_data(self):
    #     """Извлечение структурированных данных из распознанного текста"""
    #     try:
    #         text = self.get_raw_text()
    #         data = {}

            # Ищем всю строку с актом и извлекаем из неё номер и дату
            # pattern = r"Акт гарантийного ремонта[^\d]*(\d+)\s*от\s*(\d{2}.\d{2}.\d{4})"

            # match = re.search(pattern, text)
            # if match:
            #     data["Номер акта"] = match.group(1)
            #     data["Дата акта"] = match.group(2)
            # else:
            #     data["Номер акта"] = "Не найдено"
            #     data["Дата акта"] = "Не найдено"

            # Ищем номер ТС, модель двигателя и номер двигателя
            # Три захватывающие группы, разделенные пробелами
            # # \s+ - один или более пробельных символов
            # # ([^\s]+) - захватывает все символы до следующего пробела
            # {2,} - квантификатор, означающий "два или более раза"
        #     ts_pattern = r"знак ТС\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)"
        #     # ts_pattern = r"знак ТС\s+([^\s]+)\s+([^\s]{2,})\s+([^\s]{2,})"
        #     ts_match = re.search(ts_pattern, text)
        #     if ts_match:
        #         data["Номер ТС"] = ts_match.group(1)
        #         data["Модель двигателя"] = ts_match.group(2)
        #         data["Номер двигателя"] = ts_match.group(3)
        #     else:
        #         data["Номер ТС"] = "Не найдено"
        #         data["Модель двигателя"] = "Не найдено"
        #         data["Номер двигателя"] = "Не найдено"

        #     return data

        # except Exception as e:
        #     print(f"Ошибка при извлечении данных: {str(e)}")
        #     return {"Ошибка": str(e)}

    def extract_data(self):
        """Извлечение структурированных данных из распознанного текста"""
        try:
            text = self.get_raw_text()
            data = {}

            # Ищем номер акта и дату
            act_pattern = r"Акт гарантийного ремонта[^\d]*(\d+)\s*от\s*(\d{2}.\d{2}.\d{4})"
            act_match = re.search(act_pattern, text)
            if act_match:
                data["Номер акта"] = act_match.group(1)
                data["Дата акта"] = act_match.group(2)
            else:
                data["Номер акта"] = "Не найдено"
                data["Дата акта"] = "Не найдено"

            # Ищем группы между "знак ТС" и одним из трех возможных окончаний
            ts_pattern = r"знак ТС\s+(.*?)(?:ФИО Заявителя|Номер и |Адрес заявителя)"
            ts_match = re.search(ts_pattern, text, re.DOTALL)
            if ts_match:
                # Получаем весь текст между маркерами и разбиваем его на группы
                full_text = ts_match.group(1)
                # Разбиваем на группы по пробелам и фильтруем
                all_groups = [g.strip() for g in full_text.split()]
                filtered_groups = self.filter_groups(all_groups)

                # Берем первые три группы, если они есть
                if len(filtered_groups) >= 3:
                    data["Номер ТС"] = filtered_groups[0]
                    data["Модель двигателя"] = filtered_groups[1]
                    data["Номер двигателя"] = filtered_groups[2]
                else:
                    data["Номер ТС"] = "Не найдено"
                    data["Модель двигателя"] = "Не найдено"
                    data["Номер двигателя"] = "Не найдено"
            else:
                data["Номер ТС"] = "Не найдено"
                data["Модель двигателя"] = "Не найдено"
                data["Номер двигателя"] = "Не найдено"

            return data

        except Exception as e:
            print(f"Ошибка при извлечении данных: {str(e)}")
            return {"Ошибка": str(e)}

    def filter_groups(self, groups):
        """
        Фильтрация групп с учетом специфики данных
        """
        filtered = []
        for group in groups:
            # Пропускаем пустые строки и одиночные символы
            if not group or len(group) <= 1:
                continue

            # Пропускаем группы, состоящие только из специальных символов
            if all(not c.isalnum() for c in group):
                continue

            # Пропускаем служебные слова
            if group.lower() in ['и', 'в', 'на', 'по', 'от', 'тс']:
                continue

            filtered.append(group)

            # Прекращаем после нахождения первых трех подходящих групп
            if len(filtered) == 3:
                break

        return filtered

    def detect_table_structure(self, image):
        """Определение структуры таблицы на изображении"""
        # Конвертируем в numpy array
        img_array = np.array(image)

        # Находим линии таблицы
        horizontal = np.copy(img_array)
        vertical = np.copy(img_array)

        # Определяем размер структурирующего элемента
        cols = horizontal.shape[1]
        horizontal_size = cols // 30

        # Определяем горизонтальные линии
        horizontalStructure = cv2.getStructuringElement(cv2.MORPH_RECT, (horizontal_size, 1))
        horizontal = cv2.erode(horizontal, horizontalStructure)
        horizontal = cv2.dilate(horizontal, horizontalStructure)

        # Аналогично для вертикальных линий
        rows = vertical.shape[0]
        verticalsize = rows // 30
        verticalStructure = cv2.getStructuringElement(cv2.MORPH_RECT, (1, verticalsize))
        vertical = cv2.erode(vertical, verticalStructure)
        vertical = cv2.dilate(vertical, verticalStructure)

        # Находим пересечения линий
        mask = cv2.bitwise_and(horizontal, vertical)

        return mask