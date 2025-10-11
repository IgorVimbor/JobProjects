from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font
from openpyxl.utils import get_column_letter
from django.http import HttpResponse
from datetime import datetime
from urllib.parse import quote
from django.apps import apps

from reclamations.models import Reclamation
from investigations.models import Investigation
from reports.config.paths import BASE_REPORTS_DIR, get_excel_exporter_path


class UniversalExcelExporter:
    """Универсальный экспортер Excel с выбором полей"""

    def __init__(self, selected_fields=None):
        self.wb = Workbook()
        self.ws = self.wb.active
        self.ws.title = "Выгрузка данных"
        self.selected_fields = selected_fields or []
        self.field_config = self._get_field_configuration()
        # Путь для сохранения файла
        self.save_path = get_excel_exporter_path()

    def _get_field_configuration(self):
        """Конфигурация доступных полей для экспорта"""
        return {
            # Поля Reclamation
            "reclamation.id": {
                "header": "ID рекламации",
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
            "investigation.defect_causes": {
                "header": "Причины дефекта",
                "model": "investigation",
                "field": "defect_causes",
                "type": "related_field",
            },
            "investigation.defect_causes_explanation": {
                "header": "Пояснения к причинам дефекта",
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
            # Стиль заголовка
            cell.fill = PatternFill(
                start_color="D3D3D3", end_color="D3D3D3", fill_type="solid"
            )
            cell.font = Font(bold=True)

        # Получаем данные с оптимизацией запросов
        reclamations = (
            Reclamation.objects.all()
            .select_related("product_name", "product")
            .prefetch_related("investigation")
        )

        # Записываем данные
        for row, reclamation in enumerate(reclamations, 2):
            for col, field_key in enumerate(self.selected_fields, 1):
                if field_key in self.field_config:
                    value = self._get_field_value(reclamation, field_key)
                    self.ws.cell(row=row, column=col, value=value)

    def _adjust_column_width(self):
        """Автоматическая настройка ширины колонок"""
        for column in self.ws.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)

            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass

            adjusted_width = min(max_length + 2, 50)  # Ограничиваем максимальную ширину
            self.ws.column_dimensions[column_letter].width = adjusted_width

    def export_to_excel(self):
        """Основной метод экспорта в файл Excel"""

        if not self.selected_fields:
            raise ValueError("Не выбраны поля для экспорта")

        self._write_data()
        self._adjust_column_width()

        # Сохраняем файл на диск
        self.wb.save(self.save_path)
        return True
