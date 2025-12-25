"""Класс-миксин для поиска по номеру изделия и двигателя"""

# reclamations\search_mixin.py

from django.db.models import Q


class ProductEngineSearchMixin:
    """
    Миксин с логикой независимого поиска по номеру изделия и двигателя.

    Особенности:
    1. Работает как с прямыми полями (Reclamation), так и со связанными (Investigation)
    2. Использует внутренний метод для фильтрации, который можно переиспользовать
    3. Не переопределяет ключевые методы, если они уже есть в классе админки
    4. Поддерживает композицию логики через вызов внутренних методов
    """

    def get_search_results(self, request, queryset, search_term):
        """
        Переопределяем стандартный метод поиска Django.

        Порядок вызова:
        1. Сначала вызываем родительский метод для стандартной фильтрации
        2. Затем применяем дополнительную фильтрацию по изделию/двигателю
        3. Возвращаем результат с флагом использования distinct
        """
        # Вызываем родительский метод (из admin.ModelAdmin или другого миксина)
        queryset, use_distinct = super().get_search_results(
            request, queryset, search_term
        )

        # Применяем дополнительную фильтрацию по номеру изделия и двигателя
        queryset = self._apply_product_engine_filter(request, queryset)

        # Возвращаем результат
        return queryset, use_distinct

    def _apply_product_engine_filter(self, request, queryset):
        """
        ВНУТРЕННИЙ МЕТОД: Применяет фильтрацию по номеру изделия и двигателя.
        - Не предназначен для вызова извне класса
        - Можно безопасно переопределять в дочерних классах
        - Логика фильтрации изолирована и переиспользуема

        Аргументы:
        - request: объект HTTP-запроса с GET-параметрами
        - queryset: QuerySet для фильтрации

        Возвращает:
        - Отфильтрованный QuerySet
        """

        # Получаем значения из GET-параметров, удаляем лишние пробелы
        product_number = request.GET.get("product_number", "").strip()
        engine_number = request.GET.get("engine_number", "").strip()

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

    def changelist_view(self, request, extra_context=None):
        """
        Добавляет значения полей поиска в контекст шаблона.

        Зачем это нужно:
        - Чтобы поля поиска сохраняли введенные значения при пагинации/сортировке
        - Для отображения текущих фильтров в интерфейсе
        - Для работы JavaScript-логики (если есть)

        Аргументы:
        - request: объект HTTP-запроса
        - extra_context: дополнительный контекст от родительских классов

        Возвращает:
        - Результат вызова родительского метода changelist_view
        """

        # Инициализируем контекст, если он None
        extra_context = extra_context or {}

        # Добавляем значения полей поиска в контекст
        # Эти переменны будут доступны в шаблоне как {{ product_number_value }}
        extra_context.update(
            {
                "product_number_value": request.GET.get("product_number", ""),
                "engine_number_value": request.GET.get("engine_number", ""),
            }
        )
        # Вызываем родительский метод с обновленным контекстом
        return super().changelist_view(request, extra_context)

    def _get_filtered_queryset(self, request, queryset):
        """
        ДОПОЛНИТЕЛЬНЫЙ ВСПОМОГАТЕЛЬНЫЙ МЕТОД (опционально).

        Можно использовать, если нужна только фильтрация без изменения
        метода get_search_results.

        Пример использования в классе админки:
            queryset = self._get_filtered_queryset(request, queryset)
        """
        return self._apply_product_engine_filter(request, queryset)
