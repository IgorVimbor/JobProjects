# Программа для проверки нахождения в виртуальном окружении.
# Выводит в консоль сообщение с указанием наименования окружения.

import sys

def is_venv():
    return (hasattr(sys, 'real_prefix') or
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))

print('-' * 60)

if is_venv():
    name_venv = sys.prefix.split('\\')
    print(f"Вы находитесь ВНУТРИ виртуального окружения /{name_venv[-1]}\
          \nв каталоге {'/'.join(name_venv[:-1])}")
else:
    print('Вы находитесь НЕ в виртуальном, а ГЛОБАЛЬНОМ окружении.')

print('-' * 60)
