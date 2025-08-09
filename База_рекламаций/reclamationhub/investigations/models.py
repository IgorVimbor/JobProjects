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

    class FaultType(models.TextChoices):
        BZA = "bza", "БЗА"
        CONSUMER = "consumer", "Потребитель"
        COMPLIANT = "compliant", "Соответствует ТУ"
        UNKNOWN = "unknown", "Не установлен"

    class ReturnCondition(models.TextChoices):
        REPAIRED = "REPAIRED", "Отремонтировано"
        REPLACED = "REPLACED", "Заменено на новое"
        RETURNED_AS_IS = "RETURNED_AS_IS", "Возвращено как есть"

    reclamation = models.OneToOneField(
        Reclamation,
        on_delete=models.PROTECT,  # защищаем от удаления рекламации
        related_name="investigation",
        verbose_name="Рекламация (ID и изделие)",
    )
    act_number = models.CharField(
        max_length=100, verbose_name="Номер акта исследования"
    )
    act_date = models.DateField(verbose_name="Дата акта исследования")

    # Используем класс FaultType в поле модели
    fault_type = models.CharField(
        max_length=10,
        choices=FaultType.choices,
        verbose_name="Виновник дефекта",
        null=False,  # поле не может содержать NULL в базе данных
        blank=False,  # поле не может быть пустым при заполнении формы
        default=FaultType.UNKNOWN,  # Добавляем значение по умолчанию
    )
    guilty_department = models.CharField(
        max_length=100, default="Не определено", verbose_name="Виновное подразделение"
    )
    defect_causes = models.CharField(
        max_length=250,
        null=True,
        blank=True,
        verbose_name="Причины возникновения дефектов",
    )
    defect_causes_explanation = models.CharField(
        max_length=250,
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
    # volume_removal_reference = models.CharField(
    #     max_length=100,
    #     null=True,
    #     blank=True,
    #     verbose_name="Номер и месяц справки снятия с объёмов",
    # )

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
    # Используем класс ReturnCondition в поле модели
    return_condition = models.CharField(
        max_length=50,
        choices=ReturnCondition.choices,
        null=True,
        blank=True,
        verbose_name="Состояние возвращаемого потребителю изделия",
    )
    return_condition_explanation = models.CharField(
        max_length=250,
        null=True,
        blank=True,
        verbose_name="Пояснения по состоянию возвращаемого изделия",
    )

    class Meta:
        db_table = "investigation"
        verbose_name = "Акт исследования"
        verbose_name_plural = "Акты исследования"
        indexes = [
            models.Index(fields=["act_number", "act_date"]),
        ]

    def __str__(self):
        return (
            f"Акт исследования {self.act_number} от {self.act_date.strftime('%d.%m.%Y')} "
            f"({self.reclamation.product})"
        )

    # def clean(self):
    # if not self.fault_type:
    #     raise ValidationError(
    #         "Необходимо указать виновника дефекта или соответствие ТУ"
    #     )

    # if self.fault_type == self.FaultType.BZA and not self.guilty_department:
    #     raise ValidationError(
    #         "При указании БЗА как виновника необходимо указать виновное подразделение"
    #     )

    def save(self, *args, **kwargs):
        """Обновление статуса рекламации"""
        # После сохранения акта проверяем и обновляем статус рекламации
        super().save(*args, **kwargs)
        self.reclamation.update_status_on_investigation()
