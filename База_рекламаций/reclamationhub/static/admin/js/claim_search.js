// static\admin\js\claim_search.js
// Скрипт для проверки дубликатов при заполнении формы претензий и измения названия валюты в подписях полей.

// =================== Поиск дубликатов и автозаполнение полей для претензий =====================

window.addEventListener('load', function() {
    // Находим поля для поиска
    var reclamationNumberField = document.getElementById('id_reclamation_act_number');
    var reclamationDateField = document.getElementById('id_reclamation_act_date');
    var engineNumberField = document.getElementById('id_engine_number');
    var investigationActField = document.getElementById('id_investigation_act_number');

    // Если поля не найдены на странице, выходим из функции
    if (!reclamationNumberField || !reclamationDateField || !engineNumberField) return;

    // Функция для проверки и запуска поиска
    function checkAndSearch() {
        // Получаем значения из полей
        var searchNumber = reclamationNumberField.value.trim();
        var searchDate = reclamationDateField.value.trim();
        var engineNumber = engineNumberField.value.trim();
        var investigationActNumber = investigationActField.value.trim();

        var searchParams = '';

        // Определяем тип поиска: акт рекламации → двигатель → акт исследования
        if (searchNumber && searchDate && !engineNumber && !investigationActNumber) {
            // Поиск по номеру и дате акта рекламации
            searchParams = `reclamation_act_number=${encodeURIComponent(searchNumber)}&reclamation_act_date=${encodeURIComponent(searchDate)}`;
        } else if (engineNumber && !searchNumber && !searchDate && !investigationActNumber) {
            // Поиск по номеру двигателя
            searchParams = `engine_number=${encodeURIComponent(engineNumber)}`;
        } else if (investigationActNumber && !searchNumber && !searchDate && !engineNumber) {  // ← НОВОЕ
            // Поиск по номеру акта исследования
            searchParams = `investigation_act_number=${encodeURIComponent(investigationActNumber)}`;
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
    investigationActField.addEventListener('blur', checkAndSearch);

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