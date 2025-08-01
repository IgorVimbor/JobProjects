from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone

from sourcebook.models import PeriodDefect, ProductType, Product


def get_default_product_type():
    """Метод для получения id водяного насоса из БД таблицы product_type"""
    return ProductType.objects.get(name="водяной насос").id


class Reclamation(models.Model):
    """
    Модель рекламации на изделие.

    Содержит информацию о рекламации, включая:
    - Данные о поступившем сообщении
    - Информацию об изделии
    - Акты приобретателя и конечного потребителя
    - Информацию о дефекте
    - Принятые меры
    - Поступление изделия на завод
    """

    # Определяем класс Status внутри модели
    class Status:
        NEW = "NEW"
        IN_PROGRESS = "IN_PROGRESS"
        CLOSED = "CLOSED"

        CHOICES = [
            (NEW, "Новая"),
            (IN_PROGRESS, "В работе"),
            (CLOSED, "Закрыта"),
        ]

    # Используем Status.CHOICES в поле модели
    status = models.CharField(
        max_length=50, choices=Status.CHOICES, default=Status.NEW, verbose_name="Статус"
    )

    # Методы для изменения статуса
    def start_processing(self):
        """Перевести рекламацию в работу"""
        self.status = self.Status.IN_PROGRESS
        self.save()

    def close_reclamation(self):
        """Закрыть рекламацию"""
        self.status = self.Status.CLOSED
        self.save()

    # Методы для проверки статуса
    def is_new(self):
        return self.status == self.Status.NEW

    def is_in_progress(self):
        return self.status == self.Status.IN_PROGRESS

    def is_closed(self):
        return self.status == self.Status.CLOSED

    # -------------------------------------------------------------------------------

    # Информация о поступившем сообщении
    incoming_number = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Входящий № по ОТК"
    )
    message_received_date = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата поступления сообщения в ОТК"
    )
    sender = models.TextField(
        blank=True, null=True, verbose_name="Кто отправил сообщение"
    )
    sender_outgoing_number = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="Исх. № отправителя"
    )
    message_sent_date = models.DateField(
        null=True, blank=True, verbose_name="Дата отправления сообщения"
    )

    # Период выявления дефекта (связанный объект)
    defect_period = models.ForeignKey(
        PeriodDefect,
        on_delete=models.PROTECT,
        related_name="reclamations",
        verbose_name="Период выявления дефекта",
    )

    # Наименование изделия (связанный объект)
    product_name = models.ForeignKey(
        ProductType,
        on_delete=models.PROTECT,
        related_name="reclamations",
        verbose_name="Наименование изделия",
        default=get_default_product_type,  # по умолчанию ID водяного насоса
    )

    # Обозначение изделия (связанный объект)
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="reclamations",
        verbose_name="Обозначение изделия",
    )

    product_number = models.CharField(
        max_length=10, null=True, blank=True, verbose_name="Номер изделия"
    )
    manufacture_date = models.CharField(
        max_length=10, null=True, blank=True, verbose_name="Дата изготовления"
    )

    # ---------------------------- Рекламационный акт -------------------------------

    # Рекламационный акт приобретателя изделия
    purchaser = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name="Организация-приобретатель изделия",
    )
    consumer_act_number = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Номер акта приобретателя изделия",
    )
    consumer_act_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Дата акта приобретателя изделия",
    )

    country_rejected = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Государство, где забраковано изделие",
    )

    # Рекламационный акт конечного потребителя
    end_consumer = models.CharField(
        max_length=200, null=True, blank=True, verbose_name="Конечный потребитель"
    )
    end_consumer_act_number = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Номер акта конечного потребителя",
    )
    end_consumer_act_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Дата акта конечного потребителя",
    )
    # Ниже в методе clean() проверяем, что либо purchaser, либо end_consumer не пусты
    # --------------------------------------------------------------------------------

    # Информация о двигателе и транспортном средстве
    engine_brand = models.CharField(
        max_length=50, null=True, blank=True, verbose_name="Марка двигателя"
    )
    engine_number = models.CharField(
        max_length=50, null=True, blank=True, verbose_name="Номер двигателя"
    )
    transport_name = models.CharField(
        max_length=200, null=True, blank=True, verbose_name="Транспортное средство"
    )
    transport_number = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Номер транспортного средства",
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

    products_count = models.PositiveIntegerField(
        null=True,
        blank=True,
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name="Количество предъявленных изделий",
    )

    # Принятые меры по сообщению о дефекте
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
        verbose_name="Способ отправки принятых мер",
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

    reclamation_documents = models.TextField(
        null=True, blank=True, verbose_name="Документы по рекламационному изделию"
    )
    # ------------------------------------------------------------------------------------------

    # Системные поля
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        db_table = "reclamation"
        verbose_name = "Рекламация"
        verbose_name_plural = "Рекламации"
        ordering = ["-message_received_date"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["defect_period"]),
            models.Index(fields=["product", "status"]),
        ]

    # Дополнительные аргументы экземпляра класса Reclamation
    @property
    def registration_month(self):
        """Вычисляемое поле - месяц регистрации из даты"""
        return (
            self.message_received_date.strftime("%Y-%m")
            if self.message_received_date
            else None
        )

    @property
    def has_investigation(self):
        """Проверка наличия исследования"""
        return hasattr(self, "investigation")

    @property
    def days_without_investigation(self):
        """
        Количество дней с даты поступления изделия, если нет акта исследования.
        Возвращает:
        - None, если дата поступления не указана
        - None, если есть акт исследования
        - количество дней с даты поступления, если акта исследования нет
        """
        # Проверяем наличие акта исследования
        if self.has_investigation:
            return None

        # Проверяем наличие даты поступления
        if not self.product_received_date:
            return None

        # Получаем текущую дату
        today = timezone.now().date()

        # Вычисляем разницу в днях
        delta = (today - self.product_received_date).days

        return delta

    @property
    def has_claim(self):
        """Проверка наличия претензии"""
        return hasattr(self, "claim")

    def clean(self):
        """
        Метод для базовой проверки данных на уровне модели
        """
        # Проверяем, что заполнена хотя бы одна пара по акту рекламации (приобретателя или конечного потребителя)
        # Первая пара полей
        has_consumer_act = bool(self.consumer_act_number and self.consumer_act_date)
        # Вторая пара
        has_end_consumer_act = bool(
            self.end_consumer_act_number and self.end_consumer_act_date
        )
        # Проверяем, что хотя бы одна пара заполнена
        if not has_consumer_act and not has_end_consumer_act:
            raise ValidationError(
                "Необходимо заполнить хотя бы один акт (приобретателя или конечного потребителя)"
            )

    def save(self, *args, **kwargs):
        self.full_clean()  # обязательно нужен для запуска валидации
        super().save(*args, **kwargs)
