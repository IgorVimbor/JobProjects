from django.db import models


class Claim(models.Model):
    RESULT_CHOICES = [
        ("ACCEPTED", "Принята"),
        ("REJECTED", "Отклонена"),
        ("PARTIAL", "Частично удовлетворена"),
        ("PENDING", "На рассмотрении"),
    ]

    number = models.CharField(max_length=100, verbose_name="№ претензии")
    date = models.DateField(verbose_name="Дата претензии")
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
        choices=RESULT_CHOICES,
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

    def __str__(self):
        return f"Претензия №{self.number} от {self.date}"
