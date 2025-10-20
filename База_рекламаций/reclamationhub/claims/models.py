from django.db import models
from django.utils.safestring import mark_safe

from reclamations.models import Reclamation


class Claim(models.Model):
    """
    Модель претензии по рекламации.
    Связана с рекламацией (один к одному).
    """

    class Result(models.TextChoices):
        ACCEPTED = "ACCEPTED", "Принять"
        REJECTED = "REJECTED", "Отклонить"

    class Money(models.TextChoices):
        RUR = "RUR", "RUR"
        BYN = "BYN", "BYN"

    reclamations = models.ManyToManyField(
        Reclamation,
        related_name="claims",
        verbose_name="Рекламации",
        blank=True,
        # Делаем поле необязательным, т.к. бывают претензии без привязки к рекламационному акту.
        # В таком случае претензия просто регистрируется с обязательным комментарием.
        help_text="Рекламации, связанные с данной претензией"
    )

    registration_number = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        default="009-11/",
        verbose_name="Номер регистрации",
    )
    # registration_date = models.DateField(
    #     null=True, blank=True, verbose_name="Дата регистрации"
    # )

    claim_number = models.CharField(
        max_length=100, null=True, blank=False, verbose_name="Номер претензии"
    )
    claim_date = models.DateField(null=True, blank=False, verbose_name="Дата претензии")

    type_money = models.CharField(
        max_length=10,
        choices=Money.choices,
        default=Money.RUR,
        null=True,
        blank=False,
        verbose_name="Денежная единица",
    )

    claim_amount_all = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=False,
        verbose_name="Сумма по претензии",
    )

    reclamation_act_number = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="Номер акта рекламации"
    )

    reclamation_act_date = models.DateField(
        null=True, blank=True, verbose_name="Дата акта рекламации"
    )

    engine_number = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Номер двигателя",
        help_text=mark_safe(
            "<li>При положительном результате поиска поля формы заполнятся автоматически.<br>"
            "Переходите к регистрации претензии и заполнению формы далее.</li>"
            "<li>Если поля формы НЕ заполнились - нажмите СОХРАНИТЬ для получения результатов поиска<br>"
            "и добавьте комментарий для регистрации претензии.</li>"
        ),
    )

    claim_amount_act = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Сумма по акту рекламации",
    )
    message_received_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Дата уведомления",
    )
    receipt_invoice_number = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Накладная прихода изделия",
    )
    investigation_act_number = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="Номер акта исследования"
    )
    investigation_act_date = models.DateField(
        null=True, blank=True, verbose_name="Дата акта исследования"
    )
    investigation_act_result = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Результат расcмотрения рекламации",
    )
    comment = models.CharField(
        max_length=250, null=True, blank=True, verbose_name="Комментарий"
    )
    result_claim = models.CharField(
        max_length=20,
        choices=Result.choices,
        default=Result.ACCEPTED,
        null=True,
        blank=False,
        verbose_name="Решение по претензии",
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
        max_length=100, null=True, blank=True, verbose_name="Номер ответа на претензию"
    )
    response_date = models.DateField(
        null=True, blank=True, verbose_name="Дата ответа на претензию"
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
            return f"№{self.claim_number} от {self.claim_date}"
        return "без номера"

    @property
    def has_response(self):
        """Проверяет наличие ответа на претензию"""
        return bool(self.response_number and self.response_date)
