from pdf2image import convert_from_path
import pytesseract
import re
from PIL import Image
import cv2
import numpy as np

class PDFProcessingError(Exception):
    """Пользовательское исключение для обработки ошибок PDF"""
    pass

# class PDFProcessor:
#     # Регулярные выражения как константы класса
#     # ACT_PATTERN = r"Акт гарантийного ремонта[^\d]*(\d+)\s*от\s*(\d{2}.\d{2}.\d{4})"
#     ACT_PATTERN = r"Ак[тгр]\s*[-\w]?\s*[гт]арантийного ремонта[^\d]*(\d+)\s*от\s*(\d{2}.\d{2}.\d{4})"
#     ENGINE_PATTERN = r"знак ТС\s+(.*?)(?:ФИО Заявителя|Номер и |Адрес заявителя)"

class PDFProcessor:
    # Регулярные выражения как константы класса
    # ACT_PATTERN = r"Ак[тгр]\s*[-\w]?\s*[гт]арантийного ремонта[^\d]*(\d+)\s*от\s*(\d{2}.\d{2}.\d{4})"
    ACT_PATTERN = r"Ак[тгр]\s*[-\w]?\s*[гт]арантийного ремонта[^\d]*(\d+)\s+\w{1,2}\s+(\d{2}.\d{2}.\d{4})"
    ENGINE_PATTERN = r"знак ТС\s+(.*?)(?:ФИО Заявителя|Номер и |Адрес заявителя)"
    # SERVICE_PATTERN = r'"([^"]+)"'  # Ищет текст между первой парой кавычек
    SERVICE_PATTERN = r'["“”]([^"“”]+)["“”]'  # Ищет текст между любыми кавычками (обычными или ")

    def __init__(self, pdf_path):
        """
        Инициализация обработчика PDF
        pdf_path: Путь к PDF файлу
        """
        self.pdf_path = pdf_path
        pytesseract.pytesseract.tesseract_cmd = r'C:/Program Files/Tesseract-OCR/tesseract.exe'

    def preprocess_image(self, image, enhance_quality=False):
        """
        Предобработка изображения для улучшения качества распознавания

        Args:
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
        """
        Расширенные методы улучшения качества изображения
        """
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

    def get_raw_text(self):
        """
        Получение необработанного текста из PDF
        """
        try:
            # Конвертируем только первую страницу PDF
            images = convert_from_path(self.pdf_path, first_page=1, last_page=1)

            if not images:
                raise PDFProcessingError("Не удалось получить изображения из PDF")

            # Пробуем сначала обычную обработку
            processed_image = self.preprocess_image(images[0])
            text = pytesseract.image_to_string(processed_image, lang='rus')

            # Если текст не распознан или содержит много ошибок,
            # пробуем расширенную обработку
            if not text.strip() or len(text) < 100:  # можно настроить пороговое значение
                # Улучшаем качество изображения
                enhanced_image = self.enhance_image_quality(images[0])
                # Применяем предобработку с улучшением качества
                processed_image = self.preprocess_image(enhanced_image, enhance_quality=True)
                text = pytesseract.image_to_string(processed_image, lang='rus')

            if not text.strip():
                raise PDFProcessingError("Не удалось распознать текст в документе")

            return text

        except Exception as e:
            raise PDFProcessingError(f"Ошибка при распознавании текста: {str(e)}")

    def extract_data(self):
        """
        Извлечение структурированных данных из распознанного текста
        """
        try:
            text = self.get_raw_text()
            data = {}

            # Извлечение номера и даты акта
            act_match = re.search(self.ACT_PATTERN, text)
            if act_match:
                data["Номер акта"] = act_match.group(1)
                data["Дата акта"] = act_match.group(2)
            else:
                data["Номер акта"] = "Не найдено"
                data["Дата акта"] = "Не найдено"

            # Извлечение сервисного предприятия
            service_match = re.search(self.SERVICE_PATTERN, text)
            text = service_match.group(1)
            if len(text) < 30:
                data["Сервисное предприятие"] = text
            else:
                data["Сервисное предприятие"] = "Не найдено"

            # Извлечение данных о двигателе
            engine_match = re.search(self.ENGINE_PATTERN, text, re.DOTALL)
            if engine_match:
                full_text = engine_match.group(1)
                all_groups = [g.strip() for g in full_text.split()]
                filtered_groups = self.filter_groups(all_groups)

                if len(filtered_groups) > 2:
                    data["Модель двигателя"] = filtered_groups[1]
                    data["Номер двигателя"] = filtered_groups[2]
                elif len(filtered_groups) == 2:
                    data["Модель двигателя"] = filtered_groups[0]
                    data["Номер двигателя"] = filtered_groups[1]
                else:
                    data["Модель двигателя"] = "Не найдено"
                    data["Номер двигателя"] = "Не найдено"
            else:
                data["Модель двигателя"] = "Не найдено"
                data["Номер двигателя"] = "Не найдено"

            return data

        except Exception as e:
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