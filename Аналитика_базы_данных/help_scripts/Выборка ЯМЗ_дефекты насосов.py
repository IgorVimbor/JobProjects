import pandas as pd
from datetime import date


year_now = date.today().year  # текущий год
file = (
    "//Server/otk/1 ГАРАНТИЯ на сервере/" + str(year_now) + "-2019_ЖУРНАЛ УЧЁТА.xlsx"
)  # имя файла с учетом текущего года

sheet = str(year_now)  # делаем активным Лист базы ОТК по году поиска
df = pd.read_excel(
    file, sheet_name=sheet, header=1
)  # читаем файл Excel и создаем датафрейм
k = 3  # поправочный коэффициент нумерации строк

# выборка из базы водяных насосов ЯМЗ (сразу по двум столбцам, где & - И, | - ИЛИ)
nasos_ymz = df[
    (df["Период выявления дефекта (отказа)"] == "ЯМЗ - эксплуатация")
    & (df["Наименование изделия"] == "водяной насос")
]
# print(nasos_ymz.shape)  # размер выборки (датафрейма) строк-столбцов (86, 68)

# строки из датафрейма nasos_ymz по наименованию колонки для значений, которые известны (метод notna)
defect_nasos = nasos_ymz[
    nasos_ymz["Пояснения к причинам возникновения дефектов"].notna()
]["Пояснения к причинам возникновения дефектов"]
# print(defect_nasos)  # печать датафрейма defect_nasos (строк из колонки 'Пояснения к причинам дефектов')
# print(defect_nasos.shape)   # (52,)

tp_defect = tuple(defect_nasos)
# [print(t) for t in tp_defect]   # печать эл-ов кортежа строк из колонки 'Пояснения к причинам дефектов'
# print(len(tp_defect))  # 52
dct = {}
for t in tp_defect:
    dct.setdefault(t, tp_defect.count(t))
lst_sort = sorted(dct.items(), key=lambda x: x[1], reverse=True)

s = 0
print("-" * 50)
for key, value in lst_sort:
    s += value
    print(f"{key}: {value}")
print("\nОбщее количество:", s)
print("-" * 50)
