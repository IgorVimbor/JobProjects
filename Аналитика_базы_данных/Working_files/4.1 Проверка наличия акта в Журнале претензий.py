import pandas as pd

file = "//Server/otk/ПРЕТЕНЗИИ/ЖУРНАЛ претензий_ЯМЗ.xlsx"

# читаем файл Excel и создаем датафрейм
df = pd.read_excel(file, sheet_name="ЯМЗ 2024", usecols=["Номер и дата акта исследования"], header=1)

# Из колонки "Номер и дата акта" создаем список, заменяя отсутствующие значения пустой строкой
lst = df["Номер и дата акта исследования"].fillna("").to_list()
# Убираем из списка пустые строки
lst = [s for s in lst if s]

# Проходим циклом по списку актов и если в ячейке указано несколько актов через "\n",
# то сплитуем по символу и дважды делаем замену символов, приводя к виду "nnn-dd-mm-yy".
# Если указан один акт, то сразу делаем замену символов.
acts = []
for s in lst:
    if "\n" in s:
        tmp_lst = s.split("\n")
        for s_tmp in tmp_lst:
            act = s_tmp.replace(" от ", "-").replace(".", "-")
            acts.append(act)
    else:
        act = s.replace(" от ", "-").replace(".", "-")
        acts.append(act)

# Список актов для проверки присутствия в Журнале
new_act = ['785-15-08-24', '786-15-08-24', '787-15-08-24', '788-15-08-24', '789-15-08-24']

# Результат проверки: номер акта - True/False
for n_a in new_act:
    print(f"{n_a} - {n_a in acts}")

# Сортированный список номеров актов для использования в 4.2
num_act = sorted(int(act.split("-")[0]) for act in new_act)
print(num_act)
print(len(num_act))
