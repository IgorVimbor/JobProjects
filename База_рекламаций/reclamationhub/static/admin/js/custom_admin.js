// Общие JavaScript функции для всех моделей

// static\admin\js\custom_admin.js


// =============== Кнопка Свернуть/Развернуть фильтры ================

window.addEventListener('load', function() {
    var filterSection = document.getElementById('changelist-filter');
    if (!filterSection) return;

    // Определяем, та же это страница или новая
    var basePath = window.location.pathname;
    var isSamePage = sessionStorage.getItem('filter_page_path') === basePath;
    sessionStorage.setItem('filter_page_path', basePath);

    if (!isSamePage) {
        sessionStorage.removeItem('admin_filters_collapsed');
        sessionStorage.removeItem('admin_filters_details');
    }

    // 1. Создаём кнопку
    var toggleButton = document.createElement('div');
    toggleButton.className = 'filter-toggle';

    // 2. Определяем начальное состояние панели
    var savedCollapsed = sessionStorage.getItem('admin_filters_collapsed');
    var isCollapsed = isSamePage && savedCollapsed !== null
        ? savedCollapsed === 'true'
        : true;

    toggleButton.textContent = isCollapsed ? 'Развернуть фильтры' : 'Свернуть фильтры';
    if (isCollapsed) {
        filterSection.classList.add('collapsed');
    }
    filterSection.insertBefore(toggleButton, filterSection.firstChild);

    // 3. Оборачиваем контент в div
    var filterContent = document.createElement('div');
    filterContent.className = 'filter-content';
    while (filterSection.children.length > 1) {
        filterContent.appendChild(filterSection.children[1]);
    }
    filterSection.appendChild(filterContent);

    // 4. Управляем состоянием отдельных фильтров
    initDetailsState(filterContent, isSamePage);

    // 5. Обработчик кнопки
    toggleButton.addEventListener('click', function() {
        var isNowCollapsed = filterSection.classList.toggle('collapsed');
        toggleButton.textContent = isNowCollapsed ? 'Развернуть фильтры' : 'Свернуть фильтры';
        sessionStorage.setItem('admin_filters_collapsed', isNowCollapsed);
    });
});

// Инициализирует состояние отдельных фильтров (элементов <details>)
function initDetailsState(container, isSamePage) {
    var allDetails = container.querySelectorAll('details');
    // Получаем сохранённое состояние или null, если его нет
    var savedState = isSamePage && JSON.parse(sessionStorage.getItem('admin_filters_details') || 'null');

    allDetails.forEach(function(details, index) {
        // Имя фильтра из атрибута или индекс как запасной вариант
        var filterName = details.getAttribute('data-filter-title') || String(index);

        // Флаг состояния - определяем, должен ли фильтр быть открыт:
        // - Если есть сохранённое состояние — используем его
        // - Иначе: первый фильтр (index=0) открыт, остальные закрыты
        var shouldOpen = savedState
            ? savedState[filterName]
            : index === 0;

        // toggleAttribute('open', true) — добавляет атрибут open
        // toggleAttribute('open', false) — удаляет атрибут open
        details.toggleAttribute('open', shouldOpen);

        // Сохраняем новое состояние всех фильтров
        // При клике на <summary> срабатывает событие 'toggle'
        details.addEventListener('toggle', function() {
            saveDetailsState(container);
        });
    });
}

// Сохраняет текущее состояние всех фильтров в sessionStorage.
function saveDetailsState(container) {
    var state = {};
    container.querySelectorAll('details').forEach(function(details, index) {
        // Ключ — название фильтра или его индекс
        var filterName = details.getAttribute('data-filter-title') || String(index);
        // details.open — встроенное свойство, возвращает true/false
        state[filterName] = details.open;
    });
    sessionStorage.setItem('admin_filters_details', JSON.stringify(state));
}


// ============ Прокрутка к секции "Принятые меры" в форме рекламаций ===============

window.addEventListener('load', function() {
    // Если в URL есть #measures-section
    if (window.location.hash === '#measures-section') {
        // Находим секцию
        var measuresSection = document.querySelector('.measures-section');
        if (measuresSection) {
            // Прокручиваем к ней
            measuresSection.scrollIntoView({ behavior: 'smooth' });

            // Добавляем подсветку секции
            measuresSection.style.backgroundColor = '#fff3e0';
            setTimeout(function() {
                measuresSection.style.transition = 'background-color 1s';
                measuresSection.style.backgroundColor = 'transparent';
            }, 2000);
        }
    }
});


// ============ Прокрутка к секции "Отправка акта" в форме актов исследования ===============

window.addEventListener('load', function() {
    // Если в URL есть #shipment-section
    if (window.location.hash === '#shipment-section') {
        // Находим секцию
        var shipmentSection = document.querySelector('.shipment-section');
        if (shipmentSection) {
            // Прокручиваем к ней
            shipmentSection.scrollIntoView({ behavior: 'smooth' });

            // Добавляем подсветку секции
            shipmentSection.style.backgroundColor = '#fff3e0';
            setTimeout(function() {
                shipmentSection.style.transition = 'background-color 1s';
                shipmentSection.style.backgroundColor = 'transparent';
            }, 2000);
        }
    }
});


// ============= Обновление title для текстовых полей =============

window.addEventListener('load', function() {
    // Находим все поля из списка text_fields в формах рекламаций и актов исследования
    const textFields = document.querySelectorAll(`
        input[name="measures_taken"],
        input[name="consumer_response"],
        input[name="defect_causes"],
        input[name="defect_causes_explanation"],
        input[name="return_condition_explanation"]
    `);

    textFields.forEach(function(field) {
        // Устанавливаем начальное значение title
        field.title = field.value;

        // Обновляем title при вводе текста
        field.addEventListener('input', function() {
            this.title = this.value;
        });
    });
});