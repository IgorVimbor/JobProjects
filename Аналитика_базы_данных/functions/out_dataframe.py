import pandas as pd
import numpy as np
from datetime import date

# --------------------- Вспомогательные функции и переменные ----------------------------

# словарь для перевода наименования месяца регистрации в номер месяца
months_to_num = {
    "январь": "01",
    "февраль": "02",
    "март": "03",
    "апрель": "04",
    "май": "05",
    "июнь": "06",
    "июль": "07",
    "август": "08",
    "сентябрь": "09",
    "октябрь": "10",
    "ноябрь": "11",
    "декабрь": "12",
}


# функция очистки данных даты изготовления
def value_date_prod(str_in):
    str_in = str(str_in)
    if len(str_in) != 5 or not str_in[-1].isdigit():
        str_in = np.nan

    return str_in


# функция очистки данных по пробегу и перевода пробега в километры
def value_probeg(str_in):
    str_in = str(str_in).replace(",", ".").replace(" ", "").rstrip(".")

    if str_in.endswith("м/ч"):  # если строка заканчивается на м/ч
        # срезом убираем м/ч, переводим в int и умножаем на 9
        str_in = round(float(str_in[:-3])) * 9

    elif str_in.endswith("км"):  # если строка заканчивается на км
        # срезом убираем км и переводим в int
        str_in = round(float(str_in[:-2]))

    else:
        str_in = 0

    return str_in


year_now = date.today().year  # текущий год
# имя файла с учетом текущего года
file = "//Server/otk/1 ГАРАНТИЯ на сервере/" + str(year_now) + "-2019_ЖУРНАЛ УЧЁТА.xlsm"
# file = f"D:/РАБОТА/{str(year_now)}-2019_ЖУРНАЛ УЧЁТА.xlsm"

# ----------------------------------------------------------------------------------------


class MyFrame:
    def __init__(self, year: int, client: str, product: str) -> None:
        self.year = str(year)
        self.client = client
        self.product = product

    def get_frame(self):
        # считываем файл Excel и создаем датафрейм
        df = pd.read_excel(
            file,
            sheet_name=self.year,
            usecols=[
                "Месяц регистрации",
                "Период выявления дефекта (отказа)",
                "Наименование изделия",
                "Обозначение изделия",
                "Дата изготовления изделия",
                "Транспортное средство (установка)",
                "Пробег, наработка",
                "Причины возникновения дефектов",
                "Пояснения к причинам возникновения дефектов",
                "Поставщик дефектного комплектующего",
            ],
            header=1,
        )

        # делаем выборку из общей базы по наименованию потребителя и изделия
        df_client = df.loc[
            (df["Период выявления дефекта (отказа)"] == self.client)
            & (df["Наименование изделия"] == self.product)
        ].copy()

        # удаляем не нужные столбцы в датафрейме df_ymz_2023
        df_client.drop(columns=["Период выявления дефекта (отказа)", "Наименование изделия"], inplace=True)

        # изменяем значения в столбцах:
        # 'Месяц регистрации' -> названия месяцев в строковый вид 'mm.yy'
        df_client.loc[:, "Месяц регистрации"] = df_client.loc[:, "Месяц регистрации"].map(lambda s: f"{months_to_num[s]}.{self.year[2:]}")
        # 'Дата изготовления изделия' -> в строковый вид 'mm.yy'
        df_client.loc[:, "Дата изготовления изделия"] = df_client.loc[:, "Дата изготовления изделия"].map(value_date_prod)
        # 'Пробег, наработка' -> удаляем символы "км." и "м/ч" -> пересчитываем м/ч в километры
        df_client.loc[:, "Пробег, наработка"] = df_client.loc[:, "Пробег, наработка"].map(value_probeg)

        # изменяем типы данных в столбцах:
        # 'Месяц регистрации' и 'Дата изготовления изделия' - datetime64[ns]
        # 'Пробег, наработка' - int32,
        # 'Поставщик дефектного комплектующего' - category
        df_client.loc[:, ["Месяц регистрации", "Дата изготовления изделия"]] = df_client.loc[:, ["Месяц регистрации", "Дата изготовления изделия"]].apply(pd.to_datetime, format="%m.%y")
        df_client = df_client.astype({"Пробег, наработка": "int32", "Поставщик дефектного комплектующего": "category"})

        return df_client


if __name__ == "__main__":

    # потребитель - период выявления дефекта (отказа)
    client = "ММЗ - эксплуатация"
    product = "водяной насос"  # наименование изделия по которому делается датафрейм

    data_2025 = MyFrame(2025, client, product).get_frame()
    data_2024 = MyFrame(2024, client, product).get_frame()
    data_2023 = MyFrame(2023, client, product).get_frame()
    data_2022 = MyFrame(2022, client, product).get_frame()

    print("2024:", data_2024.shape)
    print("2023:", data_2023.shape)  # (236, 7)
    print("2022:", data_2022.shape)  # (210, 7)

    df = pd.concat([data_2025, data_2024, data_2023, data_2022])
    print(df.head())
    print(df.info())
