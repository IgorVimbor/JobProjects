# core\modules\search_mixin.py

"""
Логика для поиска по номеру изделия и двигателя.

Включает класс:
- `ProductEngineSearchMixin` - миксин с логикой независимой фильтрации по номеру изделия и двигателя.
"""

from django.db.models import Q


class ProductEngineSearchMixin:
    """
    Миксин с логикой независимого поиска по номеру изделия и двигателя.

    1. Работает как с прямыми полями (Reclamation), так и со связанными (Investigation)
    2. Использует внутренний метод для фильтрации, который можно переиспользовать
    3. Не переопределяет стандартные методы, если они уже есть в классе админки
    """

    def _apply_product_engine_filter(self, request, queryset):
        """
        Применяет фильтрацию по номеру изделия и двигателя.

        Использование в админке:
            queryset = self._apply_product_engine_filter(request, queryset)

        Аргументы:
        - request: объект HTTP-запроса с GET-параметрами
        - queryset: QuerySet для фильтрации

        Возвращает:
        - Отфильтрованный QuerySet
        """

        # Приоритетно читаем из атрибута request (установлен в changelist_view)
        # или получаем значения из GET-параметров
        product_number = (
            getattr(request, "_product_number", "")
            or request.GET.get("product_number", "").strip()
        )
        engine_number = (
            getattr(request, "_engine_number", "")
            or request.GET.get("engine_number", "").strip()
        )

        # Если нет параметров - ничего не фильтруем
        if not product_number and not engine_number:
            return queryset

        conditions = []  # Собираем условия фильтрации в список

        # ================ ФИЛЬТРАЦИЯ ПО НОМЕРУ ИЗДЕЛИЯ =================

        if product_number:
            # Проверяем, есть ли прямое поле product_number в модели
            if hasattr(queryset.model, "product_number"):
                # Для Reclamation: фильтруем по прямому полю
                conditions.append(Q(product_number__icontains=product_number))
            # Проверяем, есть ли связь с моделью Reclamation
            elif hasattr(queryset.model, "reclamation"):
                # Для Investigation: фильтруем через ForeignKey связь
                conditions.append(
                    Q(reclamation__product_number__icontains=product_number)
                )

        # ================ ФИЛЬТРАЦИЯ ПО НОМЕРУ ДВИГАТЕЛЯ =================

        if engine_number:
            # Аналогичная логика для поля engine_number
            if hasattr(queryset.model, "engine_number"):
                conditions.append(Q(engine_number__icontains=engine_number))
            elif hasattr(queryset.model, "reclamation"):
                conditions.append(
                    Q(reclamation__engine_number__icontains=engine_number)
                )

        # Применяем все условия через AND (каждое условие должно выполняться)
        if conditions:
            q_object = Q()
            for condition in conditions:
                q_object &= condition  # Используем AND (&)
            queryset = queryset.filter(q_object)

        return queryset

    def _add_product_engine_context(self, request, extra_context):
        """
        Добавляет значения полей поиска в контекст шаблона.

        Использование в админке:
            extra_context = self._add_product_engine_context(request, extra_context)

        Зачем это нужно:
        - Чтобы поля поиска сохраняли введенные значения при пагинации/сортировке
        - Для отображения текущих фильтров в интерфейсе

        Аргументы:
        - request: объект HTTP-запроса
        - extra_context: дополнительный контекст от родительских классов

        Возвращает:
        - Обновленный контекст
        """

        # Инициализируем контекст, если он None
        extra_context = extra_context or {}

        # Добавляем значения полей поиска в контекст
        # Эти переменны будут доступны в шаблоне как {{ product_number_value }}
        extra_context.update(
            {  # Читаем из атрибута (приоритет) или GET
                "product_number_value": getattr(request, "_product_number", "")
                or request.GET.get("product_number", ""),
                "engine_number_value": getattr(request, "_engine_number", "")
                or request.GET.get("engine_number", ""),
            }
        )

        return extra_context
