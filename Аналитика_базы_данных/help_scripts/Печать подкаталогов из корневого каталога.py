import os


rootdir = '//Server/otk/'  # Корневой каталог

# for file in os.listdir(rootdir):
#     d = os.path.join(rootdir, file)
#     if os.path.isdir(d):
#         print(file)

# Циклом по файлам корневого каталога
for it in os.scandir(rootdir):
    if it.is_dir():  # если файл является каталогом
        print(it.name)  # выводим на печать


for dirpath, dirnames, filenames in os.walk(rootdir):
    for dirname in dirnames:
        print("Каталог:", os.path.join(dirpath, dirname))  # перебираем каталоги
    for filename in filenames:
        print("Файл:", os.path.join(dirpath, filename))   # перебираем файлы
