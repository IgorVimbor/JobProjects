// Код для создания кнопки Свернуть / Развернуть фильтры на админ-панели Рекламаций

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

// Код для создания списков обозначений изделий в зависимости от наименования
window.addEventListener('load', function() {
    var $ = django.jQuery;
    var productNameSelect = $('#id_product_name');
    var productSelect = $('#id_product');

    if (productNameSelect.length && productSelect.length) {
        productNameSelect.on('select2:select', function(e) {
            var productTypeId = e.params.data.id;

            $.ajax({
                url: '/admin/get_products/',
                method: 'GET',
                data: {
                    'product_type_id': productTypeId
                },
                success: function(data) {
                    // Очищаем и добавляем пустую опцию
                    productSelect.empty();
                    productSelect.append(new Option('---------', '', true, true));

                    // Добавляем полученные опции
                    data.forEach(function(item) {
                        productSelect.append(new Option(item.nomenclature, item.id));
                    });
                }
            });
        });
    }
});

// Код для прокрутки к секции "Принятые меры" для внесения данных
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

// Обработка прокрутки к секции отправки акта исследования
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

// Код для автоматического добавления суффиксов в поле пробега/наработки
window.addEventListener('load', function() {
    var awayTypeRadios = document.querySelectorAll('input[type="radio"][name="away_type"]');
    var mileageField = document.getElementById('id_mileage_operating_time');

    if (!awayTypeRadios.length || !mileageField) return;

    // Обработчик изменения radio кнопок
    awayTypeRadios.forEach(function(radio) {
        radio.addEventListener('change', function() {
            if (this.value === 'psi') {
                mileageField.value = 'ПСИ';
                mileageField.readOnly = true;
            } else if (this.value !== 'notdata') {
                mileageField.readOnly = false;
                if (mileageField.value === 'ПСИ') {
                    mileageField.value = '';
                }
            }
        });
    });

    // Обработчик потери фокуса
    mileageField.addEventListener('blur', function() {
        var selectedRadio = document.querySelector('input[type="radio"][name="away_type"]:checked');
        if (!selectedRadio || ['psi', 'notdata'].includes(selectedRadio.value)) return;

        var value = this.value.replace(/\s*(км|м\/ч)$/, '');
        this.value = value + (selectedRadio.value === 'kilometre' ? ' км' : ' м/ч');
    });
});

// Обновление title для текстовых полей
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