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
# ----------------------------------------------------------------------------------------


class MyFrame:
    def __init__(self, file: str, sheet: str, client: str = None, product: str = None) -> None:
        self.file = file
        self.sheet = sheet
        self.client = client
        self.product = product

    def get_frame(self):
        # считываем файл Excel и создаем датафрейм
        df = pd.read_excel(
            self.file,
            sheet_name=self.sheet,
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
        if self.client and self.product:
            df_client = df.loc[
                (df["Период выявления дефекта (отказа)"] == self.client)
                & (df["Наименование изделия"] == self.product)
            ].copy()

            # удаляем не нужные столбцы в датафрейме, если выбран потребитель и изделие
            df_client.drop(columns=["Период выявления дефекта (отказа)", "Наименование изделия"], inplace=True)
        else:
            df_client = df.loc[df["Период выявления дефекта (отказа)"].notna()]

        # изменяем значения в столбцах:
        # 'Месяц регистрации' -> названия месяцев в строковый вид 'mm.yy'
        df_client.loc[:, "Месяц регистрации"] = df_client.loc[:, "Месяц регистрации"].map(lambda s: f"{months_to_num[s]}.{self.sheet[2:]}")
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

    year_now = date.today().year  # текущий год
    # # имя файла с учетом текущего года
    # file = "//Server/otk/1 ГАРАНТИЯ на сервере/" + str(year_now) + "-2019_ЖУРНАЛ УЧЁТА.xlsm"
    file = f"D:/РАБОТА/{str(year_now)}-2019_ЖУРНАЛ УЧЁТА.xlsm"

    client = "ММЗ - эксплуатация"  # потребитель, по которому строится датафрейм
    product = "водяной насос"  # наименование изделия, по которому строится датафрейм

    # data_2025 = MyFrame(file, '2025').get_frame()
    data_2025 = MyFrame(file, '2025', client, product).get_frame()

    print(data_2025.shape)

    # df = pd.concat([data_2024, data_2023, data_2022])
    print(data_2025.head())
