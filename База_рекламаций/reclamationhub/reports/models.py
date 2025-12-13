from django.db import models


class EnquiryPeriod(models.Model):
    """
    Модель для метаданных справок о поступивших сообщениях за период.
    Заменяет JSON файл из десктопного приложения.
    Аналог JSON: {"0": ["3", "08-01-2025"], "1": ["171", "22-01-2025"]}
    """

    sequence_number = models.PositiveIntegerField(verbose_name="Номер справки")

    last_processed_id = models.PositiveIntegerField(
        verbose_name="ID последней записи"
    )  # ID записи по которой формировался последний отчет

    report_date = models.DateField(verbose_name="Дата формирования справки")

    class Meta:
        verbose_name = "Справка по сообщениям за период"
        verbose_name_plural = "Справки по сообщениям за период"
        ordering = ["-sequence_number"]  # сортировка по убыванию

    def __str__(self):
        return f"Справка № {self.sequence_number} от {self.report_date}"
