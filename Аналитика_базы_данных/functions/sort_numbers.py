# функция для сортировки номеров актов и двигателей
def sort_numbers(nums_in: str):
    return " ".join(sorted(nums_in.split()))


if __name__ == "__main__":
    # строка номеров актов или двигателей (записанная через пробел между номерами)
    lst_in = "1719-24 1885-24 1398-24 1472-24"

    print(sort_numbers(lst_in))
