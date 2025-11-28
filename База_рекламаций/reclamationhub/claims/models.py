from django.db import models
from django.utils.safestring import mark_safe
from django.utils import timezone

from reclamations.models import Reclamation


class Claim(models.Model):
    """Модель претензии по рекламации. Связана с рекламацией (многие ко многим)"""

    class Result(models.TextChoices):
        ACCEPTED = "ACCEPTED", "Принять"
        REJECTED = "REJECTED", "Отклонить"

    class Money(models.TextChoices):
        RUR = "RUR", "RUR"
        BYN = "BYN", "BYN"

    # По умолчанию для всех полей:
    # null=False  #  поле НЕ может быть NULL в БД
    # blank=False  # поле обязательно для заполнения в формах

    reclamations = models.ManyToManyField(
        Reclamation,
        related_name="claims",
        verbose_name="Рекламации",
        blank=True,
        # Делаем поле необязательным для заполнения, т.к. бывают претензии без привязки
        # к рекламационному акту. Тогда претензия регистрируется с обязательным комментарием.
        help_text="Рекламации, связанные с данной претензией",
    )

    current_year = timezone.now().year  # текущий год

    year = models.PositiveIntegerField(
        default=current_year,
        verbose_name="Год претензии"
    )  # Обязательное поле

    registration_number = models.CharField(
        max_length=100,
        default="009-11/",
        verbose_name="Номер регистрации",
        help_text=f"Регистрационный номер ЮС в {current_year} году",
    )  # Обязательное поле

    consumer_name = models.CharField(
        max_length=100,
        verbose_name="Потребитель",
        help_text="Заполняется автоматически или вручную (ЯМЗ, ММЗ, ПТЗ и т.д.)",
    )  # Обязательное поле

    claim_number = models.CharField(max_length=100, verbose_name="Номер претензии")
    claim_date = models.DateField(verbose_name="Дата претензии")  # Обязательные поля

    type_money = models.CharField(
        max_length=10,
        choices=Money.choices,
        default=Money.RUR,
        verbose_name="Денежная единица",
    )  # Обязательное поле

    claim_amount_all = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Сумма по претензии",
    )  # Обязательное поле

    claim_amount_act = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Сумма по акту рекламации",
    )  # Обязательное поле

    reclamation_act_number = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="Номер акта рекламации"
    )

    reclamation_act_date = models.DateField(
        null=True, blank=True, verbose_name="Дата акта рекламации"
    )

    engine_number = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="Номер двигателя"
    )

    investigation_act_number = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="Номер акта исследования"
    )

    investigation_act_date = models.DateField(
        null=True, blank=True, verbose_name="Дата акта исследования",
        help_text=mark_safe(
            "<li>При положительном результате поиска поля формы заполнятся автоматически.<br>"
            "Переходите к регистрации претензии и заполнению формы далее.</li>"
            "<li>Если поля формы НЕ заполнились - нажмите СОХРАНИТЬ для получения результатов поиска<br>"
            "и добавьте комментарий для регистрации претензии.</li>"
        ),
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
        verbose_name="Решение по претензии",
    )  # Обязательное поле

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
        ordering = ["-year", "-claim_number"]
        # unique_together = [['year', 'claim_number']]  # Гарантируем уникальность номера
        # Дополнительные индексы для производительности поиска и сортировки
        indexes = [
            models.Index(fields=["year", "claim_number", "claim_date"]),
        ]

    def __str__(self):
        if self.claim_number and self.claim_date:
            return f"№{self.claim_number} от {self.claim_date}"
        return "без номера"

    @property
    def has_response(self):
        """Проверяет наличие ответа на претензию"""
        return bool(self.response_number and self.response_date)

    @staticmethod
    def extract_consumer_prefix(period_name):
        """
        Извлекает префикс потребителя из полного названия
        "ЯМЗ - эксплуатация" → "ЯМЗ"
        """
        if not period_name:
            return ""

        if " - " in period_name:
            return period_name.split(" - ")[0].strip()

        return period_name.strip()
