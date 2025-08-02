from django.db import models
from django.core.exceptions import ValidationError
from reclamations.models import Reclamation


class Investigation(models.Model):
    """
    Модель акта исследования рекламационного изделия.

    Связана с рекламацией (один к одному).
    Содержит информацию о:
    - результатах исследования
    - виновнике дефекта
    - причинах дефекта
    - утилизации (если проводилась)
    - отгрузке изделия взамен
    """

    class ReturnCondition:
        REPAIRED = "REPAIRED"
        REPLACED = "REPLACED"
        RETURNED_AS_IS = "RETURNED_AS_IS"

        CHOICES = [
            (REPAIRED, "Отремонтировано"),
            (REPLACED, "Заменено на новое"),
            (RETURNED_AS_IS, "Возвращено как есть"),
        ]

    reclamation = models.OneToOneField(
        Reclamation,
        on_delete=models.PROTECT,  # защищаем от удаления рекламации
        related_name="investigation",
        verbose_name="ID рекламации",
    )
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

    # ПКД (Предупреждающие и корректирующие действия)
    pkd_number = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="Номер ПКД"
    )

    # Утилизация
    disposal_act_number = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="Номер акта утилизации"
    )
    disposal_act_date = models.DateField(
        null=True, blank=True, verbose_name="Дата акта утилизации"
    )
    volume_removal_reference = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Номер и месяц справки снятия с объёмов",
    )

    # Отправка результатов исследования
    recipient = models.CharField(
        max_length=200, null=True, blank=True, verbose_name="Получатель"
    )
    shipment_date = models.DateField(
        null=True, blank=True, verbose_name="Дата отправки акта исследования"
    )

    # Отгрузка (возврат) изделия потребителю
    shipment_invoice_number = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Номер накладной отгрузки изделия потребителю",
    )
    shipment_invoice_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Дата накладной отгрузки изделия потребителю",
    )
    # Используем ReturnCondition.CHOICES в поле модели
    return_condition = models.CharField(
        max_length=50,
        choices=ReturnCondition.CHOICES,
        null=True,
        blank=True,
        verbose_name="Состояние возвращаемого потребителю изделия",
    )
    return_condition_explanation = models.TextField(
        null=True,
        blank=True,
        verbose_name="Пояснения по состоянию возвращаемого изделия",
    )

    class Meta:
        db_table = "investigation"
        verbose_name = "Исследование"
        verbose_name_plural = "Исследования"
        indexes = [
            models.Index(fields=["act_number", "act_date"]),
        ]

    def __str__(self):
        return (
            f"Акт исследования {self.act_number} от {self.act_date.strftime('%d.%m.%Y')} "
            f"({self.reclamation.product})"
        )

    def clean(self):
        """Проверка виновников дефекта"""
        fault_count = sum([self.fault_bza, self.fault_consumer, self.fault_unknown])

        if fault_count > 1:
            raise ValidationError(
                "Может быть указан только один виновник дефекта или соответствие ТУ"
            )

        if fault_count == 0:
            raise ValidationError(
                "Необходимо указать виновника дефекта или соответствие ТУ"
            )

    def save(self, *args, **kwargs):
        """Обновление статуса рекламации"""
        super().save(*args, **kwargs)

        # После сохранения акта проверяем и обновляем статус рекламации
        if self.act_number and self.act_date:
            if not self.reclamation.is_closed():
                self.reclamation.status = self.reclamation.Status.CLOSED
                self.reclamation.save()
