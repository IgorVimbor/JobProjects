from django.db import models
from django.core.validators import MinValueValidator
from products.models import PeriodDefect, Product, EngineTransport
from investigations.models import Investigation
from claims.models import Claim


class ReclamationAct(models.Model):
    number = models.CharField(max_length=100, verbose_name="Номер рекламационного акта")
    date = models.DateField(verbose_name="Дата рекламационного акта")
    organization = models.ForeignKey(
        PeriodDefect,
        on_delete=models.PROTECT,
        related_name="reclamation_acts",
        verbose_name="Организация",
    )

    class Meta:
        db_table = "reclamation_act"
        verbose_name = "Рекламационный акт"
        verbose_name_plural = "Рекламационные акты"
        unique_together = ["number", "organization"]

    def __str__(self):
        return f"Акт №{self.number} от {self.date}"


class Reclamation(models.Model):
    STATUS_CHOICES = [
        ("NEW", "Новая"),
        ("IN_PROGRESS", "В работе"),
        ("INVESTIGATION", "На исследовании"),
        ("CLOSED", "Закрыта"),
    ]

    RETURN_CONDITION_CHOICES = [
        ("REPAIRED", "Отремонтировано"),
        ("REPLACED", "Заменено на новое"),
        ("RETURNED_AS_IS", "Возвращено как есть"),
        ("DISPOSED", "Утилизировано"),
    ]

    # Основная информация
    incoming_number = models.CharField(max_length=100, verbose_name="Входящий № по ОТК")
    message_received_date = models.DateField(
        verbose_name="Дата поступления сообщения в ОТК"
    )
    sender = models.CharField(max_length=200, verbose_name="Кто отправил сообщение")
    sender_outgoing_number = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="Исходящий № отправителя"
    )
    message_sent_date = models.DateField(
        null=True, blank=True, verbose_name="Дата отправления сообщения"
    )

    # Период выявления дефекта
    defect_detection_period = models.ForeignKey(
        PeriodDefect,
        on_delete=models.PROTECT,
        related_name="reclamations",
        verbose_name="Период выявления дефекта",
    )
    country_rejected = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Государство, где забраковано изделие",
    )

    # Связанные объекты
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="reclamations",
        verbose_name="Изделие",
    )
    purchaser = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name="Организация-приобретатель",
    )
    end_consumer = models.CharField(
        max_length=200, null=True, blank=True, verbose_name="Конечный потребитель"
    )
    vehicle = models.ForeignKey(
        EngineTransport,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reclamations",
        verbose_name="Транспортное средство",
    )

    # Рекламационные акты
    purchaser_act = models.ForeignKey(
        ReclamationAct,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="purchaser_reclamations",
        verbose_name="Рекламационный акт приобретателя",
    )
    consumer_act_number = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Номер рекламационного акта конечного потребителя",
    )
    consumer_act_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Дата рекламационного акта конечного потребителя",
    )

    # Информация о дефекте
    defect_detection_date = models.DateField(
        null=True, blank=True, verbose_name="Дата выявления дефекта изделия"
    )
    mileage_operating_time = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="Пробег, наработка"
    )
    claimed_defect = models.TextField(verbose_name="Заявленный дефект изделия")
    consumer_requirement = models.TextField(
        null=True, blank=True, verbose_name="Требование потребителя"
    )

    # Принятые меры
    measures_taken = models.TextField(
        null=True, blank=True, verbose_name="Принятые меры по сообщению"
    )
    outgoing_document_number = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="Исходящий № документа"
    )
    outgoing_document_date = models.DateField(
        null=True, blank=True, verbose_name="Дата исходящего документа"
    )
    letter_sending_method = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name="Способ отправления письма по принятым мерам",
    )

    # Ответ потребителя
    consumer_response = models.TextField(
        null=True, blank=True, verbose_name="Ответ потребителя на сообщение"
    )
    consumer_response_number = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Исходящий № ответа потребителя",
    )
    consumer_response_date = models.DateField(
        null=True, blank=True, verbose_name="Дата ответа потребителя"
    )

    # Поступление изделия
    product_received_date = models.DateField(
        null=True, blank=True, verbose_name="Дата поступления изделия"
    )
    product_sender = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name="Организация-отправитель изделия",
    )
    receipt_invoice_number = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Номер накладной прихода изделия",
    )
    receipt_invoice_date = models.DateField(
        null=True, blank=True, verbose_name="Дата накладной прихода изделия"
    )
    products_quantity = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        verbose_name="Количество предъявленных изделий",
    )
    reclamation_documents = models.TextField(
        null=True, blank=True, verbose_name="Документы по рекламационному изделию"
    )

    # Исследование
    investigation = models.OneToOneField(
        Investigation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reclamation",
        verbose_name="Исследование",
    )

    # ПКД (Предупреждающие и корректирующие действия)
    pkd_number = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="Номер ПКД"
    )
    pkd_completion_mark = models.BooleanField(
        default=False, verbose_name="Отметка о выполнении ПКД"
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

    # Возврат изделия
    recipient = models.CharField(
        max_length=200, null=True, blank=True, verbose_name="Получатель"
    )
    shipment_date = models.DateField(
        null=True, blank=True, verbose_name="Дата отправки"
    )
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
    return_condition = models.CharField(
        max_length=50,
        choices=RETURN_CONDITION_CHOICES,
        null=True,
        blank=True,
        verbose_name="Состояние возвращаемого потребителю изделия",
    )
    return_condition_explanation = models.TextField(
        null=True,
        blank=True,
        verbose_name="Пояснения по состоянию возвращаемого изделия",
    )

    # Претензия
    claim = models.ForeignKey(
        Claim,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reclamations",
        verbose_name="Претензия",
    )

    # Системные поля
    status = models.CharField(
        max_length=50, choices=STATUS_CHOICES, default="NEW", verbose_name="Статус"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        db_table = "reclamation"
        verbose_name = "Рекламация"
        verbose_name_plural = "Рекламации"
        ordering = ["-message_received_date"]

    def __str__(self):
        return f"Рекламация №{self.incoming_number} от {self.message_received_date}"

    @property
    def registration_month(self):
        """Вычисляемое поле - месяц регистрации из даты"""
        return (
            self.message_received_date.strftime("%Y-%m")
            if self.message_received_date
            else None
        )

    @property
    def status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)
