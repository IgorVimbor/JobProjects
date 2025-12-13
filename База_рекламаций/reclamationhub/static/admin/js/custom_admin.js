// Общие JavaScript функции для всех моделей

// static\admin\js\custom_admin.js

// =============== Создание кнопки Свернуть/Развернуть фильтры на админ-панели ================

window.addEventListener('load', function() {
    var filterSection = document.getElementById('changelist-filter');
    if (filterSection) {
        var toggleButton = document.createElement('div');
        toggleButton.className = 'filter-toggle';

        // Проверяем сохраненное состояние
        var isCollapsed = localStorage.getItem('admin_filters_collapsed') === 'true';

        // Устанавливаем начальное состояние
        if (isCollapsed) {
            filterSection.classList.add('collapsed');
            toggleButton.textContent = 'Развернуть фильтры';
        } else {
            toggleButton.textContent = 'Свернуть фильтры';
        }

        filterSection.insertBefore(toggleButton, filterSection.firstChild);

        var filterContent = document.createElement('div');
        filterContent.className = 'filter-content';
        while (filterSection.children.length > 1) {
            filterContent.appendChild(filterSection.children[1]);
        }
        filterSection.appendChild(filterContent);

        toggleButton.addEventListener('click', function() {
            filterSection.classList.toggle('collapsed');
            var isNowCollapsed = filterSection.classList.contains('collapsed');
            toggleButton.textContent = isNowCollapsed ? 'Развернуть фильтры' : 'Свернуть фильтры';

            // Сохраняем новое состояние
            localStorage.setItem('admin_filters_collapsed', isNowCollapsed);
        });
    }
});


// ============ Прокрутка формы "Рекламация" к секции "Принятые меры" для внесения данных ===============

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


// ============ Прокрутка формы "Акт исследования" к секции отправки акта исследования ===============

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


// ==================== Обновление title для текстовых полей =====================

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