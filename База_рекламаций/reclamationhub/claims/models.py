from django.db import models
from reclamations.models import Reclamation


class Claim(models.Model):
    """
    Модель претензии по рекламации.

    Связана с рекламацией (один к одному).
    Содержит информацию:
    - номер и дату претензии
    - сумму претензии
    - результат рассмотрения
    - ответ БЗА
    """

    class Result:
        ACCEPTED = "ACCEPTED"
        REJECTED = "REJECTED"
        PARTIAL = "PARTIAL"

        CHOICES = [
            (ACCEPTED, "Принята"),
            (REJECTED, "Отклонена"),
            (PARTIAL, "Частично удовлетворена"),
        ]

    reclamation = models.OneToOneField(
        Reclamation,
        on_delete=models.PROTECT,
        related_name="claim",
        verbose_name="Рекламация",
    )

    number = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="№ претензии"
    )
    date = models.DateField(null=True, blank=True, verbose_name="Дата претензии")
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Сумма по претензии",
    )
    response_number = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="№ ответа БЗА"
    )
    response_date = models.DateField(
        null=True, blank=True, verbose_name="Дата ответа БЗА"
    )
    result = models.CharField(
        max_length=20,
        choices=Result.CHOICES,
        null=True,
        blank=True,
        verbose_name="Результат рассмотрения претензии",
    )
    bza_costs = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Сумма затрат БЗА",
    )

    class Meta:
        db_table = "claim"
        verbose_name = "Претензия"
        verbose_name_plural = "Претензии"

    class Meta:
        db_table = "claim"
        verbose_name = "Претензия"
        verbose_name_plural = "Претензии"
        ordering = ["-number"]  # сортировка по номеру претензии
        indexes = [
            models.Index(fields=["number", "date"]),
        ]

    def __str__(self):
        if self.number and self.date:
            return f"Претензия №{self.number} от {self.date}"
        return f"Претензия отсутствует"

    @property
    def has_response(self):
        """Проверяет наличие ответа на претензию"""
        return bool(self.response_number and self.response_date)
