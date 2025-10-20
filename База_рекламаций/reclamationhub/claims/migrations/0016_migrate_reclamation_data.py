from django.db import migrations

def transfer_reclamation_data(apps, schema_editor):
    """Переносим данные из reclamation (ForeignKey) в reclamations (ManyToMany)"""
    Claim = apps.get_model('claims', 'Claim')

    # Считаем количество претензий с привязанными рекламациями
    claims_with_reclamation = Claim.objects.filter(reclamation__isnull=False)
    count = claims_with_reclamation.count()

    print(f"Найдено {count} претензий с привязанными рекламациями")

    # Переносим данные
    for i, claim in enumerate(claims_with_reclamation, 1):
        claim.reclamations.add(claim.reclamation)
        if i % 10 == 0 or i == count:  # Показываем прогресс каждые 10 записей
            print(f"Обработано: {i}/{count}")

def reverse_transfer_reclamation_data(apps, schema_editor):
    """Обратная операция - переносим обратно в ForeignKey"""
    Claim = apps.get_model('claims', 'Claim')

    for claim in Claim.objects.all():
        first_reclamation = claim.reclamations.first()
        if first_reclamation:
            claim.reclamation = first_reclamation
            claim.save()

class Migration(migrations.Migration):
    dependencies = [
        ('claims', '0015_add_reclamations_field'),
    ]

    operations = [
        migrations.RunPython(
            transfer_reclamation_data,
            reverse_transfer_reclamation_data
        ),
    ]