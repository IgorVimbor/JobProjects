from django.db import models


class PeriodDefect(models.Model):
    name = models.CharField(
        max_length=70, unique=True, verbose_name="Период выявления дефекта"
    )

    class Meta:
        db_table = "period_defect"
        verbose_name = "Период выявления дефекта"
        verbose_name_plural = "Период выявления дефектов"
        ordering = ["name"]  # сортировка по умолчанию

    def __str__(self):
        return self.name


class ProductType(models.Model):
    name = models.CharField(
        max_length=100, unique=True, verbose_name="Наименование изделия"
    )

    class Meta:
        db_table = "product_type"
        verbose_name = "Тип изделия"
        verbose_name_plural = "Типы изделий"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    product_type_id = models.ForeignKey(
        ProductType,
        on_delete=models.PROTECT,
        related_name="products",
        verbose_name="Тип изделия",
    )
    nomenclature = models.CharField(
        max_length=100, unique=True, verbose_name="Обозначение изделия"
    )
    product_number = models.CharField(
        max_length=10, verbose_name="Заводской номер изделия"
    )
    manufacture_date = models.CharField(
        max_length=10, null=True, blank=True, verbose_name="Дата изготовления изделия"
    )

    class Meta:
        db_table = "product"
        verbose_name = "Изделие"
        verbose_name_plural = "Изделия"
        ordering = ["nomenclature"]
        unique_together = ["nomenclature", "product_number"]

    def __str__(self):
        return f"{self.nomenclature} №{self.product_number}"


class EngineTransport(models.Model):
    engine_brand = models.CharField(max_length=50, verbose_name="Марка двигателя")
    engine_number = models.CharField(max_length=50, verbose_name="Номер двигателя")
    transport_name = models.CharField(
        max_length=200, verbose_name="Транспортное средство"
    )
    transport_number = models.CharField(
        max_length=100, verbose_name="Номер транспортного средства"
    )

    class Meta:
        db_table = "engine_transport"
        verbose_name = "Двигатель и Транспортное средство"
        verbose_name_plural = "Двигатели и Транспортные средства"

    def __str__(self):
        return f"Двигатель № {self.engine_number}"
