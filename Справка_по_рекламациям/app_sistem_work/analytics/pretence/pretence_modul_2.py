import pandas as pd
from typing import List, Tuple, Dict

import paths_work  # импортируем файл с путями до базы данных, отчетов и др.


class ActsFromJournal:
    def __init__(self, sheet_name: str, new_acts: List[str]):
        """
        Инициализация класса с именем листа Excel и списком новых актов для проверки.
        :param sheet_name: Имя листа Excel.
        :param new_acts: Список новых актов.
        """
        self.sheet_name = sheet_name
        self.new_acts = new_acts
        self.acts_in_journal: List[str] = []
        self.numbers_acts: List[int] = []
        self.years_list_acts: Dict[str, List[int]] = {}

        # Путь к файлу Журнала претензий по потребителю
        self.file_path = f"{paths_work.journal_pretence}_{self.sheet_name.split()[0]}.xlsx"


    def get_acts_from_journal(self) -> List[str]:
        """
        Читает Excel-файл журнала претензий и возвращает список актов с датами в формате 'nnn-dd-mm-yy'.
        :return: Список строк с актами.
        """
        # Считываем файл Excel и сохраняем в DataFrame столбец "Номер и дата акта исследования"
        df = pd.read_excel(self.file_path, sheet_name=self.sheet_name, usecols=["Номер и дата акта исследования"], header=1)
        # Удаляем пустые строки и преобразуем в список строк
        acts_raw = df["Номер и дата акта исследования"].dropna().tolist()

        # Проходим циклом по списку актов и если в ячейке указано несколько актов через "\n",
        # то сплитуем по символу и дважды делаем замену символов, приводя к виду "nnn-dd-mm-yy".
        # Если указан один акт, то сразу делаем замену символов.
        acts = []
        for entry in acts_raw:
            parts = entry.split("\n") if "\n" in entry else [entry]
            for part in parts:
                act = part.replace(" от ", "-").replace(".", "-")
                acts.append(act)
        return acts


    def calculate_results(self) -> Tuple[List[str], List[int], Dict[str, List[int]]]:
        """
        Сравнивает новые акты с актами из журнала, возвращает найденные акты, отсортированные номера и словарь по годам.
        :return: Кортеж из (акты в журнале, отсортированные номера актов, словарь актов по годам).
        """
        # Получаем список всех актов исследования с датой из Журнала
        acts_in_journal_all = self.get_acts_from_journal()
        self.acts_in_journal = [act for act in self.new_acts if act in acts_in_journal_all]
        # Сортированный список номеров актов для использования в 4.2 (классе Date_to_act основного модуля)
        self.numbers_acts = sorted(int(act.split("-")[0]) for act in self.new_acts)

        # Множество годов (года), в котором оформлены акты
        set_years_acts = set(act[-2:] for act in self.new_acts)
        # Словарь со списками актов по каждому году: ключ - год, значение - список актов
        self.years_list_acts = {}
        for year in set_years_acts:
            self.years_list_acts[f"20{year}"] = sorted(int(act.split("-")[0]) for act in self.new_acts if act.endswith(year))

        return self.acts_in_journal, self.numbers_acts, self.years_list_acts
