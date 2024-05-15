import matplotlib.pyplot as plt


def show_stolb_graph(
    dct_value: dict, width=10, height=5, size=5, title_graph=None, path_out_file=None
):
    """
    функция сохраняет в файл и выводит в консоль столбчатую диаграмму
    dct_value - словарь значений для построения диаграммы: ключи - наименования столбиков диаграммы,
    значения - количество
    width - ширина графика (по умолчанию 10)
    height - высота графика (по умолчанию 5)
    size - размер шрифта подписей данных по оси Х (по умолчанию 5)
    title_graph - заголовок графика
    path_out_file - путь для сохранения графика (по умолчанию пустая строка, т.е. без сохранения)
    """
    name_stolb = [key for key in dct_value.keys()]  # формируем список значений по оси Х
    cnt_by_stolb = [
        value for value in dct_value.values()
    ]  # формируем список количества по каждому столбику

    # создаем график и задаем размеры (ширина, высота)
    plt.figure(figsize=(width, height))  # (20, 5)

    # устанавливаем размер шрифта подписей данных по оси Х
    plt.rc("xtick", labelsize=size)

    # создаем список с количеством столбцов диаграммы
    index = list(range(len(name_stolb)))

    # наносим на график столбцы диаграммы в соответствии с количеством по столбцам
    plt.bar(index, cnt_by_stolb)

    # подписываем столбцы диаграммы по оси Х
    plt.xticks(index, name_stolb)

    # циклом добавляем число сверху на каждый столбец и устанавливаем его по центру
    for x, y in zip(index, cnt_by_stolb):
        plt.text(x, y, f"{y}", ha="center", va="bottom")

    # создаем легенду и вносим текст
    plt.legend(fontsize=10, title=f"Общее количество: {sum(cnt_by_stolb)}")

    # создаем заголовок графика
    plt.title(title_graph)

    # если указан путь для сохранения графика - сохраняем в файл по указанному пути и выводим сообщение в консоль
    if path_out_file:
        plt.savefig(path_out_file)
        print(f"\n\tФайл сохранен в каталог {path_out_file}")

    # выводим график в консоль
    plt.show()


if __name__ == "__main__":

    dct = {"aaa": 4, "bbb": 2, "ccc": 8, "dd": 5, "eee": 10, "fff": 3, "gg": 5, "h": 10}
    title = f"Количество сообщений за 2021 - 2023 год"
    path = (
        f"//Server/otk/ОТЧЕТНОСТЬ БЗА/АНАЛИТИКА дефектности БЗА/Информация по ЯМЗ_2021-2023"
        + ".pdf"
    )

    show_stolb_graph(dct, size=10)
