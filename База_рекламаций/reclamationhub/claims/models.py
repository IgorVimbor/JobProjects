from django.db import models
from django.core.validators import MinValueValidator

from reclamations.models import Reclamation


class Claim(models.Model):
    """
    Модель претензии по рекламации.
    Связана с рекламацией (один к одному).
    """

    class Result(models.TextChoices):
        ACCEPTED = "ACCEPTED", "Принята"
        REJECTED = "REJECTED", "Отклонена"

    reclamation = models.OneToOneField(
        Reclamation,
        on_delete=models.PROTECT,
        related_name="claim",
        verbose_name="Рекламация",
    )

    registration_number = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        default="009-11/ ",
        verbose_name="Номер ЮС регистрации",
    )
    registration_date = models.DateField(
        null=True, blank=True, verbose_name="Дата регистрации"
    )

    claim_number = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="Номер претензии"
    )
    claim_date = models.DateField(null=True, blank=True, verbose_name="Дата претензии")

    claim_amount_all = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Сумма по претензии",
    )

    reclamation_act_number = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="Номер акта рекламации"
    )

    reclamation_act_date = models.DateField(
        null=True, blank=True, verbose_name="Дата акта рекламации"
    )

    claim_amount_act = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Сумма по акту",
    )
    investigation_act_number = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="Номер акта исследования"
    )
    investigation_act_date = models.DateField(
        null=True, blank=True, verbose_name="Дата акта исследования"
    )
    result = models.CharField(
        max_length=20,
        choices=Result.choices,
        default=Result.REJECTED,
        null=True,
        blank=True,
        verbose_name="Результат рассмотрения",
    )
    comment = models.CharField(
        max_length=250, null=True, blank=True, verbose_name="Комментарий"
    )
    costs_act = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Признано по акту",
    )
    costs_all = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Признано по претензии",
    )
    response_number = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="Номер ответа БЗА"
    )
    response_date = models.DateField(
        null=True, blank=True, verbose_name="Дата ответа БЗА"
    )

    class Meta:
        db_table = "claim"
        verbose_name = "Претензия"
        verbose_name_plural = "Претензии"
        ordering = ["-claim_number"]
        indexes = [
            models.Index(fields=["claim_number", "claim_date"]),
        ]

    def __str__(self):
        if self.claim_number and self.claim_date:
            return f"Претензия №{self.claim_number} от {self.claim_date}"
        return "Претензия (без номера)"

    @property
    def has_response(self):
        """Проверяет наличие ответа на претензию"""
        return bool(self.response_number and self.response_date)
