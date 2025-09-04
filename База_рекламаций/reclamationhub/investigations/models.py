from django.db import models
from django.core.validators import FileExtensionValidator
import os

from reclamations.models import Reclamation


# def investigation_act_path(instance, filename):
#     """
#     Функция для формирования пути сохранения файла pdf.
#     Пробелы и спецсимволы в имени файла автоматически заменяются на подчеркивание.
#     """
#     from django.utils.encoding import force_str

#     year = instance.act_number[:4]
#     # Используем оригинальный номер акта исследования
#     filename = force_str(f"{instance.act_number}.pdf")
#     return f"investigations/{year}/{filename}"


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
        verbose_name="Причины дефекта",
    )
    defect_causes_explanation = models.CharField(
        max_length=250,
        null=True,
        blank=True,
        verbose_name="Пояснения к причинам дефекта",
    )
    defective_supplier = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name="Поставщик дефектного комплектующего",
    )

    # Отправка результатов исследования
    recipient = models.CharField(
        max_length=200, null=True, blank=True, verbose_name="Получатель"
    )
    shipment_date = models.DateField(
        null=True, blank=True, verbose_name="Дата отправки акта исследования"
    )

    # Сканированная копия акта исследования
    act_scan = models.FileField(
        # upload_to=investigation_act_path,
        upload_to="",  # пустая строка означает сохранение прямо в media
        verbose_name="Скан акта исследования",
        # help_text="Загрузите скан акта в формате PDF",
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["pdf"], message="Разрешены только файлы PDF"
            )
        ],
    )

    # Утилизация
    disposal_act_number = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="Номер акта утилизации"
    )
    disposal_act_date = models.DateField(
        null=True, blank=True, verbose_name="Дата акта утилизации"
    )

    # Отгрузка (возврат) изделия потребителю
    shipment_invoice_number = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Накладная отгрузки изделия",
    )
    shipment_invoice_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Дата накладной отгрузки изделия",
    )
    # Используем класс ReturnCondition в поле модели
    return_condition = models.CharField(
        max_length=50,
        choices=ReturnCondition.choices,
        null=True,
        blank=True,
        verbose_name="Состояние возвращаемого изделия",
    )
    return_condition_explanation = models.CharField(
        max_length=250,
        null=True,
        blank=True,
        verbose_name="Пояснения к состоянию изделия",
    )

    class Meta:
        db_table = "investigation"
        verbose_name = "Акт исследования"
        verbose_name_plural = "Акты исследования"
        indexes = [
            models.Index(fields=["act_number", "act_date"]),
        ]

    @property
    def has_act_scan(self):
        return bool(self.act_scan)

    @property
    def act_scan_filename(self):
        """Получение только имени файла без пути"""
        if self.act_scan:
            return self.act_scan.name.split("/")[-1]
        return None

    def __str__(self):
        return (
            f"Акт исследования {self.act_number} от {self.act_date.strftime('%d.%m.%Y')} "
            f"({self.reclamation.product})"
        )

    # def clean(self):
    #     if not self.fault_type:
    #         raise ValidationError(
    #             "Необходимо указать виновника дефекта или соответствие ТУ"
    #         )

    def delete_act_scan(self):
        """Метод для удаления файла"""
        if self.act_scan:
            if os.path.isfile(self.act_scan.path):
                os.remove(self.act_scan.path)

    # def save(self, *args, **kwargs):
    #     """Обновление статуса рекламации"""
    #     # После сохранения акта проверяем и обновляем статус рекламации
    #     super().save(*args, **kwargs)
    #     self.reclamation.update_status_on_investigation()

    def save(self, *args, **kwargs):
        """Обновление статуса рекламации и обработка файлов"""
        # Обработка файла
        if self.pk:  # если запись уже существует
            try:
                old_instance = Investigation.objects.get(pk=self.pk)
                if old_instance.act_scan and (
                    not self.act_scan or old_instance.act_scan != self.act_scan
                ):
                    old_instance.delete_act_scan()
            except Investigation.DoesNotExist:
                pass

        # Сохранение записи и обновление статуса рекламации
        super().save(*args, **kwargs)
        self.reclamation.update_status_on_investigation()

    def delete(self, *args, **kwargs):
        """Переопределяем метод удаления"""
        self.delete_act_scan()
        super().delete(*args, **kwargs)
