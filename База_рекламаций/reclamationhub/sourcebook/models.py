from django.db import models


class PeriodDefect(models.Model):
    name = models.CharField(
        max_length=70, unique=True, verbose_name="Период выявления дефекта"
    )

    class Meta:
        db_table = "period_defect"
        verbose_name = "Период выявления дефекта"
        verbose_name_plural = "Периоды выявления дефектов"
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
        verbose_name_plural = "Наименования изделий"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    """
    Модель изделия.
    Связана с нименованием изделия (ProductType).
    Используется в рекламациях для указания изделия, по которому поступила рекламация.
    """

    product_type = models.ForeignKey(
        ProductType,
        on_delete=models.PROTECT,
        related_name="products",
        verbose_name="Наименование изделия",
    )
    nomenclature = models.CharField(
        max_length=100, unique=True, verbose_name="Обозначение изделия"
    )

    class Meta:
        db_table = "product"
        verbose_name = "Обозначение изделия"
        verbose_name_plural = "Обозначения изделий"
        ordering = ["nomenclature"]
        indexes = [
            models.Index(fields=["nomenclature"]),
            models.Index(fields=["product_type", "nomenclature"]),
        ]

    def __str__(self):
        return f"{self.nomenclature}"

    @property
    def full_name(self):
        """Полное название изделия с типом"""
        return f"{self.product_type} {self.nomenclature}"

    @property
    def total_reclamations_count(self):
        """Общее количество рекламаций"""
        return self.reclamations.count()

    @property
    def active_reclamations_count(self):
        """Количество активных (не закрытых) рекламаций"""
        return self.reclamations.exclude(status="CLOSED").count()
