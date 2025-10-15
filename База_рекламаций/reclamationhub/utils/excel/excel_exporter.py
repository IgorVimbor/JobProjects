from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from reclamations.models import Reclamation
from reports.config.paths import get_excel_exporter_path


class UniversalExcelExporter:
    """Универсальный экспортер Excel с выбором полей"""

    def __init__(self, selected_fields=None, year=None):
        self.wb = Workbook()
        self.ws = self.wb.active
        self.ws.title = "Выгрузка данных"
        self.selected_fields = selected_fields or []
        # Доступные поля для экспорта
        self.field_config = self._get_field_configuration()
        self.year = year  # Год данных из базы
        # Путь для сохранения файла с учетом выбранного года
        self.save_path = get_excel_exporter_path(year)

    def _get_field_configuration(self):
        """Конфигурация доступных полей для экспорта"""
        return {
            # Поля Reclamation
            "reclamation.id": {
                "header": "Номер строки",
                "model": "reclamation",
                "field": "id",
                "type": "direct",
            },
            "reclamation.message_received_date": {
                "header": "Дата поступления сообщения",
                "model": "reclamation",
                "field": "message_received_date",
                "type": "direct",
            },
            # "reclamation.status": {
            #     "header": "Статус рекламации",
            #     "model": "reclamation",
            #     "field": "status",
            #     "type": "choice_display",  # Для полей с choices
            # },
            "reclamation.defect_period": {
                "header": "Период выявления дефекта",
                "model": "reclamation",
                "field": "defect_period",
                "type": "related_str",  # Для связанных объектов
            },
            "reclamation.product_name": {
                "header": "Наименование изделия",
                "model": "reclamation",
                "field": "product_name",
                "type": "related_str",
            },
            "reclamation.product": {
                "header": "Обозначение изделия",
                "model": "reclamation",
                "field": "product",
                "type": "related_str",
            },
            "reclamation.products_count": {
                "header": "Количество изделий",
                "model": "reclamation",
                "field": "products_count",
                "type": "direct",
            },
            "reclamation.product_number": {
                "header": "Номер изделия",
                "model": "reclamation",
                "field": "product_number",
                "type": "direct",
            },
            "reclamation.manufacture_date": {
                "header": "Дата изготовления",
                "model": "reclamation",
                "field": "manufacture_date",
                "type": "direct",
            },
            "reclamation.claimed_defect": {
                "header": "Заявленный дефект",
                "model": "reclamation",
                "field": "claimed_defect",
                "type": "direct",
            },
            "reclamation.consumer_act_number": {
                "header": "Номер акта рекламации",
                "model": "reclamation",
                "field": "consumer_act_number",
                "type": "direct",
            },
            "reclamation.consumer_act_date": {
                "header": "Дата акта рекламации",
                "model": "reclamation",
                "field": "consumer_act_date",
                "type": "direct",
            },
            "reclamation.engine_brand": {
                "header": "Марка двигателя",
                "model": "reclamation",
                "field": "engine_brand",
                "type": "direct",
            },
            "reclamation.engine_number": {
                "header": "Номер двигателя",
                "model": "reclamation",
                "field": "engine_number",
                "type": "direct",
            },
            "reclamation.transport_name": {
                "header": "Транспортное средство",
                "model": "reclamation",
                "field": "transport_name",
                "type": "direct",
            },
            "reclamation.mileage_operating_time": {
                "header": "Пробег/наработка",
                "model": "reclamation",
                "field": "mileage_operating_time",
                "type": "direct",
            },
            "reclamation.receipt_invoice_number": {
                "header": "Накладная прихода",
                "model": "reclamation",
                "field": "receipt_invoice_number",
                "type": "direct",
            },
            "reclamation.receipt_invoice_date": {
                "header": "Дата накладной прихода",
                "model": "reclamation",
                "field": "receipt_invoice_date",
                "type": "direct",
            },
            "reclamation.pkd_number": {
                "header": "Номер 8D (ПКД)",
                "model": "reclamation",
                "field": "pkd_number",
                "type": "direct",
            },
            # Поля Investigation
            "investigation.act_number": {
                "header": "Номер акта исследования",
                "model": "investigation",
                "field": "act_number",
                "type": "related_field",  # поля связанной модели
            },
            "investigation.act_date": {
                "header": "Дата акта исследования",
                "model": "investigation",
                "field": "act_date",
                "type": "related_field",
            },
            "investigation.solution": {
                "header": "Заключение",
                "model": "investigation",
                "field": "solution",
                "type": "related_choice_display",
            },
            "investigation.guilty_department": {
                "header": "Виновное подразделение",
                "model": "investigation",
                "field": "guilty_department",
                "type": "related_field",
            },
            "investigation.defect_causes": {
                "header": "Причины дефекта",
                "model": "investigation",
                "field": "defect_causes",
                "type": "related_field",
            },
            "investigation.defect_causes_explanation": {
                "header": "Пояснения к причинам",
                "model": "investigation",
                "field": "defect_causes_explanation",
                "type": "related_field",
            },
            "investigation.defective_supplier": {
                "header": "Поставщик дефектного комплектующего",
                "model": "investigation",
                "field": "defective_supplier",
                "type": "related_field",
            },
            "investigation.shipment_invoice_number": {
                "header": "Накладная отгрузки",
                "model": "investigation",
                "field": "shipment_invoice_number",
                "type": "related_field",
            },
            "investigation.shipment_invoice_date": {
                "header": "Дата накладной отгрузки",
                "model": "investigation",
                "field": "shipment_invoice_date",
                "type": "related_field",
            },
        }

    @classmethod
    def get_available_fields(cls):
        """Получить список всех доступных полей для выбора"""
        exporter = cls()
        fields = []

        for field_key, config in exporter.field_config.items():
            fields.append(
                {
                    "key": field_key,
                    "header": config["header"],
                    "model": config["model"],
                    "group": (
                        "Рекламации"
                        if config["model"] == "reclamation"
                        else "Исследования"
                    ),
                }
            )

        return fields

    def _get_field_value(self, reclamation, field_key):
        """Получить значение поля по конфигурации"""
        config = self.field_config[field_key]

        try:
            if config["type"] == "direct":
                return getattr(reclamation, config["field"])

            elif config["type"] == "choice_display":
                return getattr(reclamation, f"get_{config['field']}_display")()

            elif config["type"] == "related_str":
                related_obj = getattr(reclamation, config["field"])
                return str(related_obj) if related_obj else ""

            elif config["type"] == "related_field":
                try:
                    investigation = reclamation.investigation
                    return getattr(investigation, config["field"])
                except Reclamation.investigation.RelatedObjectDoesNotExist:
                    return ""

            elif config["type"] == "related_choice_display":
                try:
                    investigation = reclamation.investigation
                    return getattr(investigation, f"get_{config['field']}_display")()
                except Reclamation.investigation.RelatedObjectDoesNotExist:
                    return ""

        except Exception:
            return ""

    def _apply_cell_formatting(self, cell, is_header=False):
        """Применить форматирование к ячейке"""

        # Границы для всех ячеек
        border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        )

        # Центрирование по центру (горизонтально и вертикально) + перенос строк
        alignment = Alignment(wrap_text=True, horizontal="center", vertical="center")

        if is_header:
            # Заголовки: размер 8, не жирный
            cell.font = Font(size=8, bold=False)
            # Серый фон для заголовков
            cell.fill = PatternFill(
                start_color="D3D3D3", end_color="D3D3D3", fill_type="solid"
            )
        else:
            # Обычные ячейки: размер 9
            cell.font = Font(size=9)
            # Фон по умолчанию (белый)

        # Применяем границы и выравнивание ко всем ячейкам
        cell.border = border
        cell.alignment = alignment

    def _write_data(self):
        """Записать данные в Excel согласно выбранным полям"""
        if not self.selected_fields:
            return

        # Записываем заголовки
        headers = []
        for field_key in self.selected_fields:
            if field_key in self.field_config:
                headers.append(self.field_config[field_key]["header"])

        for col, header in enumerate(headers, 1):
            cell = self.ws.cell(row=1, column=col, value=header)
            # Применяем форматирование заголовка
            self._apply_cell_formatting(cell, is_header=True)

        # # Получаем данные с оптимизацией запросов
        # reclamations = (
        #     Reclamation.objects.all()
        #     .select_related("product_name", "product")
        #     .prefetch_related("investigation")
        # )

        # Получаем данные с фильтрацией по году
        queryset = Reclamation.objects.select_related(
            "product_name", "product"
        ).prefetch_related("investigation")

        # Применяем фильтр по году если выбран
        if self.year and str(self.year) != "all":
            queryset = queryset.filter(year=self.year)

        reclamations = queryset

        # Записываем данные
        for row, reclamation in enumerate(reclamations, 2):
            for col, field_key in enumerate(self.selected_fields, 1):
                if field_key in self.field_config:
                    value = self._get_field_value(reclamation, field_key)
                    cell = self.ws.cell(row=row, column=col, value=value)
                    # Применяем форматирование данных
                    self._apply_cell_formatting(cell, is_header=False)

    def _adjust_column_width(self):
        """Настройка ширины колонок"""
        # Словарь: название поля → ширина столбца
        custom_widths = {
            "Номер строки": 9,
            "Дата поступления сообщения": 14,
            "Период выявления дефекта": 17,
            "Наименование изделия": 16,
            "Обозначение изделия": 17,
            "Количество изделий": 10,
            "Номер изделия": 10,
            "Дата изготовления": 10,
            "Заявленный дефект": 20,
            "Номер акта рекламации": 14,
            "Дата акта рекламации": 14,
            "Марка двигателя": 14,
            "Номер двигателя": 14,
            "Транспортное средство": 16,
            "Пробег/наработка": 14,
            "Накладная прихода": 11,
            "Дата накладной прихода": 12,
            "Номер 8D (ПКД)": 14,
            "Номер акта исследования": 14,
            "Дата акта исследования": 14,
            "Заключение": 11,
            "Виновное подразделение": 13,
            "Причины дефекта": 22,
            "Пояснения к причинам дефекта": 25,
            "Поставщик дефектного комплектующего": 22,
            "Накладная отгрузки": 11,
            "Дата накладной отгрузки": 12,
        }

        # Получаем заголовки для сопоставления
        headers = []
        for field_key in self.selected_fields:
            if field_key in self.field_config:
                headers.append(self.field_config[field_key]["header"])

        # Устанавливаем ширину для каждого столбца
        for col_num, header in enumerate(headers, 1):
            column_letter = get_column_letter(col_num)

            # Берем ширину из словаря или ставим дефолтную
            width = custom_widths.get(header, 20)  # 20 - дефолтная ширина

            self.ws.column_dimensions[column_letter].width = width

    def _apply_filter_and_freeze_row(self):
        """Добавить автофильтр к строке заголовков и закрепить заголовки"""
        if self.ws.max_row > 1:  # Проверяем, что есть данные
            # Фильтр только для первой строки (заголовки)
            header_range = f"A1:{get_column_letter(len(self.selected_fields))}1"
            self.ws.auto_filter.ref = header_range

            # Закрепляем первую строку (заголовки)
            self.ws.freeze_panes = "A2"

    def export_to_excel(self):
        """Основной метод экспорта в файл Excel"""

        if not self.selected_fields:
            raise ValueError("Не выбраны поля для экспорта")

        self._write_data()  # Записываем данные с форматированием
        self._adjust_column_width()  # Настраиваем ширину столбцов
        self._apply_filter_and_freeze_row()  # Добавляем фильтры и закрпляем заголовок

        # Сохраняем файл на диск
        self.wb.save(self.save_path)
        return True
