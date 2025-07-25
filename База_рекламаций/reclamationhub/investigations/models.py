from django.db import models


class Investigation(models.Model):
    act_number = models.CharField(
        max_length=100, verbose_name="Номер акта исследования"
    )
    act_date = models.DateField(verbose_name="Дата акта исследования")
    fault_bza = models.BooleanField(
        default=False, verbose_name="Виновник дефекта - БЗА"
    )
    guilty_department = models.CharField(
        max_length=200, null=True, blank=True, verbose_name="Виновное подразделение"
    )
    statistics_month = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="Месяц отражения в статистике БЗА",
    )
    fault_consumer = models.BooleanField(
        default=False, verbose_name="Виновник дефекта - потребитель"
    )
    compliant_with_specs = models.BooleanField(
        default=False, verbose_name="Изделие соответствует ТУ"
    )
    fault_unknown = models.BooleanField(
        default=False, verbose_name="Виновник не установлен"
    )
    defect_causes = models.TextField(
        null=True, blank=True, verbose_name="Причины возникновения дефектов"
    )
    defect_causes_explanation = models.TextField(
        null=True,
        blank=True,
        verbose_name="Пояснения к причинам возникновения дефектов",
    )
    defective_supplier = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name="Поставщик дефектного комплектующего",
    )

    class Meta:
        db_table = "investigation"
        verbose_name = "Исследование"
        verbose_name_plural = "Исследования"

    def __str__(self):
        return f"Исследование №{self.act_number} от {self.act_date}"
