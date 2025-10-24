from django.db import migrations


def extract_consumer_prefix(period_name):
    """Извлекает префикс потребителя из полного названия"""
    if not period_name:
        return ""
    if " - " in period_name:
        return period_name.split(" - ")[0].strip()
    return period_name.strip()


def fill_consumer_names(apps, schema_editor):
    """Заполняет consumer_name для существующих претензий"""
    Claim = apps.get_model("claims", "Claim")

    updated = 0
    skipped = 0

    for claim in Claim.objects.all():
        # Если уже заполнено - пропускаем
        if claim.consumer_name:
            continue

        # Берём первую связанную рекламацию
        first_reclamation = claim.reclamations.first()

        if first_reclamation and first_reclamation.defect_period:
            claim.consumer_name = extract_consumer_prefix(
                first_reclamation.defect_period.name
            )
            claim.save()
            updated += 1
        else:
            # Оставляем пустым - потребует ручного заполнения
            skipped += 1

    if updated > 0:
        print(f"✅ Заполнено consumer_name для {updated} претензий")
    if skipped > 0:
        print(f"⚠️ Пропущено {skipped} претензий (требуют ручного заполнения)")


def reverse_func(apps, schema_editor):
    """Откат миграции - очищаем consumer_name"""
    Claim = apps.get_model("claims", "Claim")
    Claim.objects.update(consumer_name=None)


class Migration(migrations.Migration):

    dependencies = [
        (
            "claims",
            "0018_claim_consumer_name",
        ),
    ]

    operations = [
        migrations.RunPython(fill_consumer_names, reverse_func),
    ]
