import json

# Читаем файл базы данных в которую добавляем данные
with open("reclamationhub/fixtures/db.json", "r", encoding="utf-8") as f1:
    data1 = json.load(f1)
# Читаем файл базы данных из которой берем данные для добавления
with open("reclamationhub/fixtures/db_2.json", "r", encoding="utf-8") as f2:
    data2 = json.load(f2)

# Находим записи reclamations, которые будут заменены
reclamations_to_replace = [
    item
    for item in data1
    if item["model"] == "reclamations.reclamation" and 1155 <= item["pk"] <= 1187
]

# Находим записи investigations, которые будут заменены
investigations_to_replace = [
    item
    for item in data1
    if item["model"] == "investigations.investigation" and 66 <= item["pk"] <= 90
]

# Находим новые записи reclamations
new_reclamations = [
    item
    for item in data2
    if item["model"] == "reclamations.reclamation" and 1155 <= item["pk"] <= 1187
]

# Находим новые записи investigations
new_investigations = [
    item
    for item in data2
    if item["model"] == "investigations.investigation" and 66 <= item["pk"] <= 90
]

print("Будут заменены следующие записи:")
print("\nReclamations:")
for item in reclamations_to_replace:
    print(f"PK: {item['pk']}")

print("\nInvestigations:")
for item in investigations_to_replace:
    print(f"PK: {item['pk']}")

print(f"\nВсего будет заменено reclamations: {len(reclamations_to_replace)} записей")
print(f"Всего будет заменено investigations: {len(investigations_to_replace)} записей")
print(f"Будет добавлено reclamations: {len(new_reclamations)} записей")
print(f"Будет добавлено investigations: {len(new_investigations)} записей")

# Показать пересекающиеся pk для обоих типов записей
recl_existing_pks = {item["pk"] for item in reclamations_to_replace}
recl_new_pks = {item["pk"] for item in new_reclamations}
recl_overlapping_pks = recl_existing_pks.intersection(recl_new_pks)

inv_existing_pks = {item["pk"] for item in investigations_to_replace}
inv_new_pks = {item["pk"] for item in new_investigations}
inv_overlapping_pks = inv_existing_pks.intersection(inv_new_pks)

print("\nПересекающиеся PK для reclamations (будут заменены):")
print(sorted(list(recl_overlapping_pks)))
print("\nПересекающиеся PK для investigations (будут заменены):")
print(sorted(list(inv_overlapping_pks)))

# Удаляем старые записи обоих типов
data1 = [
    item
    for item in data1
    if not (
        (item["model"] == "reclamations.reclamation" and 1155 <= item["pk"] <= 1187)
        or (item["model"] == "investigations.investigation" and 66 <= item["pk"] <= 90)
    )
]

# Добавляем новые записи обоих типов
data1.extend(new_reclamations)
data1.extend(new_investigations)

# Сохраняем результат с указанием кодировки
with open("reclamationhub/fixtures/db_all.json", "w", encoding="utf-8") as f:
    json.dump(data1, f, indent=4, ensure_ascii=False)

print("Операция выполнена успешно!")
