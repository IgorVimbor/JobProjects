// =============== Создание кнопки Свернуть / Развернуть фильтры на админ-панели ================

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

// ============= Создание выпадающих списков обозначений изделий в зависимости от наименования =============

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

// ================ Автоматическое добавление суффиксов в поле пробега/наработки ==================

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

// ================ Динамическое изменение подписей валюты в форме "Претензии" ================

window.addEventListener('load', function() {
    var moneySelect = document.getElementById('id_type_money'); // select вместо radio
    var moneyFieldIds = [
        'id_claim_amount_all',
        'id_claim_amount_act',
        'id_costs_act',
        'id_costs_all'
    ];

    if (!moneySelect) return;

    // Функция для обновления подписей валюты
    function updateCurrencyLabels(currency) {
        moneyFieldIds.forEach(function(fieldId) {
            // Формируем id для help_text: id_поле_helptext
            var helpTextId = fieldId + '_helptext';
            var helpTextElement = document.getElementById(helpTextId);

            if (helpTextElement) {
                // Находим div внутри help_text и обновляем текст
                var textDiv = helpTextElement.querySelector('div');
                if (textDiv) {
                    textDiv.textContent = `Валюта: ${currency}`;
                } else {
                    // Если div не найден, обновляем весь текст
                    helpTextElement.textContent = `Валюта: ${currency}`;
                }
            }
        });
    }

    // Обработчик изменения select
    moneySelect.addEventListener('change', function() {
        updateCurrencyLabels(this.value);
    });

    // Устанавливаем начальное значение при загрузке страницы
    updateCurrencyLabels(moneySelect.value);
});

// =================== Поиск и автозаполнение полей для претензий =====================

window.addEventListener('load', function() {
    // Находим поля для поиска
    var reclamationNumberField = document.getElementById('id_reclamation_act_number');
    var reclamationDateField = document.getElementById('id_reclamation_act_date');
    var engineNumberField = document.getElementById('id_engine_number');

    // Если поля не найдены на странице, выходим из функции
    if (!reclamationNumberField || !reclamationDateField || !engineNumberField) return;

    // Функция для проверки и запуска поиска
    function checkAndSearch() {
        // Получаем значения из полей
        var searchNumber = reclamationNumberField.value.trim();
        var searchDate = reclamationDateField.value.trim();
        var engineNumber = engineNumberField.value.trim();

        var searchParams = '';

        // Определяем тип поиска
        if (searchNumber && searchDate && !engineNumber) {
            // Поиск по номеру и дате акта
            searchParams = `reclamation_act_number=${encodeURIComponent(searchNumber)}&reclamation_act_date=${encodeURIComponent(searchDate)}`;
        } else if (engineNumber && !searchNumber && !searchDate) {
            // Поиск по номеру двигателя
            searchParams = `engine_number=${encodeURIComponent(engineNumber)}`;
        } else {
            // Не все условия выполнены для поиска
            return;
        }

        // Отправляем AJAX запрос на сервер для поиска данных
        fetch(`/admin/search-related-data/?${searchParams}`)
        .then(response => response.json())
        .then(data => {
            if (data.found) {
                // Заполняем найденные поля
                fillField('id_engine_number', data.engine_number);
                fillField('id_reclamation_act_number', data.reclamation_act_number);
                fillField('id_reclamation_act_date', data.reclamation_act_date);
                fillField('id_message_received_date', data.message_received_date);
                fillField('id_receipt_invoice_number', data.receipt_invoice_number);
                fillField('id_investigation_act_number', data.investigation_act_number);
                fillField('id_investigation_act_date', data.investigation_act_date);
                fillField('id_investigation_act_result', data.investigation_act_result);
                fillField('id_consumer_name', data.consumer_name);
            }

            // Показываем предупреждение если есть
            if (data.warning) {
                showWarning(data.warning);
            }
        })
        .catch(error => {
            console.error('Ошибка при поиске данных:', error);
        });

    }

    // Добавляем обработчики события "потеря фокуса" на все поля
    reclamationNumberField.addEventListener('blur', checkAndSearch);
    reclamationDateField.addEventListener('blur', checkAndSearch);
    engineNumberField.addEventListener('blur', checkAndSearch);

    // Вспомогательная функция для заполнения полей формы
    function fillField(fieldId, value) {
        var field = document.getElementById(fieldId);
        if (field && value) {
            field.value = value;
        }
    }

    // Функция для показа предупреждений
    function showWarning(message) {
        // Убираем старые предупреждения
        removeWarnings();

        var warning = document.createElement('div');
        warning.className = 'alert alert-warning auto-warning';
        warning.style.cssText = 'margin: 10px 0; padding: 10px; border-radius: 5px;';
        warning.innerHTML = message;

        // Вставляем после поля reclamation_act_date
        var dateField = document.getElementById('id_reclamation_act_date');
        if (dateField && dateField.parentElement) {
            dateField.parentElement.insertAdjacentElement('afterend', warning);
        }
    }

    function removeWarnings() {
        var warnings = document.querySelectorAll('.auto-warning');
        warnings.forEach(w => w.remove());
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