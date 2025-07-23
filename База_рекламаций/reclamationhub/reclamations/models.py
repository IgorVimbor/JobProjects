from django.db import models


class Organization(models.Model):
    name = models.CharField(
        max_length=70, unique=True, verbose_name="Период выявления дефекта"
    )

    class Meta:
        db_table = "organization"
        verbose_name = "Период выявления дефекта"
        verbose_name_plural = "Период выявления дефекта"
        ordering = ["name"]  # сортировка по умолчанию

    def __str__(self):
        return self.name


class ProductType(models.Model):
    name = models.CharField(
        max_length=100, unique=True, verbose_name="Наименование изделия"
    )

    class Meta:
        db_table = "product_type"
        verbose_name = "Наименование изделия"
        verbose_name_plural = "Наименование изделий"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    product_type_id = models.ForeignKey(
        ProductType,
        on_delete=models.PROTECT,
        related_name="product",
        verbose_name="Наименование изделия",
    )
    nomenclature = models.CharField(
        max_length=100, unique=True, verbose_name="Обозначение изделия"
    )

    class Meta:
        db_table = "product"
        verbose_name = "Обозначение изделия"
        verbose_name_plural = "Обозначение изделий"
        ordering = ["nomenclature"]

    def __str__(self):
        return f"{self.nomenclature} ({self.product_type_id})"


class Reclamation(models.Model):
    STATUS_CHOICES = [
        ("NEW", "Новая"),
        ("PROGRESS", "В работе"),
        ("CLOSED", "Закрыта"),
    ]

    reclamation_number = models.CharField(
        max_length=50, unique=True, verbose_name="Номер рекламации"
    )
    date_received = models.DateField(verbose_name="Дата получения")
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="reclamation",
        verbose_name="Организация",
    )
    product = models.ForeignKey(
        Product,  # обновил название модели
        on_delete=models.PROTECT,
        related_name="reclamation",
        verbose_name="Изделие",
    )
    defect_description = models.TextField(verbose_name="Описание дефекта")
    status = models.CharField(
        max_length=50, choices=STATUS_CHOICES, default="NEW", verbose_name="Статус"
    )
    resolution = models.TextField(null=True, blank=True, verbose_name="Решение")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        db_table = "reclamation"
        verbose_name = "Рекламация"
        verbose_name_plural = "Рекламации"
        ordering = ["-date_received"]  # сортировка по дате, новые сверху

    def __str__(self):
        return f"Рекламация #{self.reclamation_number} от {self.organization}"

    @property
    def status_display(self):
        """Возвращает читаемое название статуса"""
        return dict(self.STATUS_CHOICES).get(self.status, self.status)
