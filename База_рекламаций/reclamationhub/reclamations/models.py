from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone
from django.utils.html import mark_safe

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
    class Status(models.TextChoices):
        NEW = "NEW", "Новая"
        IN_PROGRESS = "IN_PROGRESS", "Исследование"
        CLOSED = "CLOSED", "Закрыта"

    # Используем класс Status в поле модели
    status = models.CharField(
        max_length=50,
        choices=Status.choices,  # .choices вместо .CHOICES
        default=Status.NEW,
        verbose_name="Статус рекламации",
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
    message_received_date = models.DateField(
        default=timezone.now, verbose_name="Дата поступления сообщения"
    )
    sender = models.CharField(
        max_length=200, blank=True, null=True, verbose_name="Кто отправил сообщение"
    )
    sender_outgoing_number = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Исх. № отправителя (Номер ПСА)",
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
        default="Россия",
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

    # Определяем класс для выбора единицы измерения пробега/наработки
    class AwayType(models.TextChoices):
        NOTDATA = "notdata", "н/д"
        KILOMETRE = "kilometre", "км"
        MOTO = "moto", "м/ч"
        PSI = "psi", "ПСИ"

    away_type = models.CharField(
        max_length=20,
        choices=AwayType.choices,
        verbose_name="Единица измерения",
        null=False,  # поле не может содержать NULL в базе данных
        blank=False,  # поле не может быть пустым при заполнении формы
        default=AwayType.NOTDATA,  # Добавляем значение по умолчанию
    )
    mileage_operating_time = models.CharField(
        max_length=100, default="н/д", verbose_name="Пробег, наработка"
    )
    claimed_defect = models.CharField(
        max_length=250, default="течь", verbose_name="Заявленный дефект изделия"
    )

    consumer_requirement = models.CharField(
        max_length=250,
        null=True,
        blank=True,
        default="исследование",
        verbose_name="Требование потребителя",
    )
    products_count = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name="Количество изделий",
    )

    # Принятые меры по сообщению о дефекте
    measures_taken = models.CharField(
        max_length=250, null=True, blank=True, verbose_name="Принятые меры по сообщению"
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
    consumer_response = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name="Ответ потребителя на сообщение",
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

    # ПКД (Предупреждающие и корректирующие действия)
    pkd_number = models.CharField(
        max_length=250, null=True, blank=True, verbose_name="Номерок 8D (ПКД)"
    )

    volume_removal_reference = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Справка снятия с объёмов",
    )

    reclamation_documents = models.CharField(
        max_length=250,
        null=True,
        blank=True,
        verbose_name="Дополнительные сведения по рекламации",
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
        verbose_name="Накладная прихода изделия",
    )
    receipt_invoice_date = models.DateField(
        null=True, blank=True, verbose_name="Дата накладной прихода"
    )
    # ------------------------------------------------------------------------------------------

    # Системные поля
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        db_table = "reclamation"
        verbose_name = "Рекламация"
        verbose_name_plural = "Рекламации"
        ordering = ["-id"]
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

    def __str__(self):
        """Отображение рекламации в строковом виде (консоль, логи и др.)"""
        return f"{self.pk} - {self.product_name} - {self.product}"

    # def admin_display_by_reclamation(self):
    #     """Отображение рекламации в две строки в админ-панели актов исследований"""
    #     return mark_safe(f"{self.pk} - {self.product_name}<br>{self.product}")

    def admin_display_by_reclamation(self):
        """Отображение рекламации (в две строки с активной ссылкой) в админ-панели актов исследований"""
        url = reverse("admin:reclamations_reclamation_changelist")
        filtered_url = f"{url}?id={self.pk}"
        return mark_safe(
            f'<a href="{filtered_url}" '
            # f'style="text-decoration: none; transition: font-weight 0.2s;" '
            f"onmouseover=\"this.style.fontWeight='bold'\" "
            f"onmouseout=\"this.style.fontWeight='normal'\" "
            f'title="Перейти к рекламации">'
            f"{self.pk}</a> - {self.product_name}<br>{self.product}"
        )

    admin_display_by_reclamation.short_description = "Рекламация"

    def admin_display_by_consumer_act(self):
        """Отображение акта рекламации в админ-панели актов исследований"""
        # Если есть акт рекламации приобретателя - выводим его
        if self.consumer_act_number and self.consumer_act_date:
            return mark_safe(
                f"№ {self.consumer_act_number}<br>{self.consumer_act_date}"
            )
        # Если акт рекламации приобретателя нет, но есть конечного потребителя - выводим его
        elif self.end_consumer_act_number and self.end_consumer_act_date:
            return mark_safe(
                f"№ {self.end_consumer_act_number}<br>{self.end_consumer_act_date}"
            )
        # Если актов нет - выводим пустую строку
        else:
            return ""

    admin_display_by_consumer_act.short_description = "Номер и дата акта рекламации"

    def clean(self):
        """Метод для базовой проверки данных на уровне модели"""
        super().clean()

        # Проверяем, что указан хотя бы один акт рекламации (приобретателя или конечного потребителя)
        if not self.consumer_act_number and not self.end_consumer_act_number:
            raise ValidationError(
                "Необходимо заполнить хотя бы один номер акта (приобретателя или конечного потребителя)"
            )

        # Проверяем, что даты не больше сегодняшней
        today = timezone.now().date()
        date_fields = [
            "message_received_date",
            "message_sent_date",
            "consumer_act_date",
            "end_consumer_act_date",
            "defect_detection_date",
            "outgoing_document_date",
            "consumer_response_date",
            "product_received_date",
            "receipt_invoice_date",
        ]  # список полей с типом DateField

        errors = {}
        for field_name in date_fields:
            field_value = getattr(self, field_name)
            if field_value and field_value > today:
                errors[field_name] = "Дата не может быть больше сегодняшней"

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()  # обязательно нужен для запуска валидации
        super().save(*args, **kwargs)

    def update_status_on_receipt(self):
        """Обновление статуса рекламации при изменении накладной"""
        if self.receipt_invoice_number and self.is_new():
            self.status = self.Status.IN_PROGRESS
        elif not self.receipt_invoice_number and self.status == self.Status.IN_PROGRESS:
            self.status = self.Status.NEW
        self.save()

    def update_status_on_investigation(self):
        """Обновление статуса рекламации в зависимости от акта исследования"""
        if hasattr(self, "investigation"):
            if (
                self.investigation
                and self.investigation.act_number
                and self.investigation.act_date
            ):
                self.status = self.Status.CLOSED
            else:
                self.status = self.Status.IN_PROGRESS
            self.save()
