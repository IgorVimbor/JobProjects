// Скрипт для проверки дубликатов рекламаций в режиме реального времени.

// static\admin\js\reclamation_duplicates.js

/**
Проверяет каждое поле отдельно при потере фокуса
Отправляет AJAX запрос на сервер для поиска дубликатов
Показывает предупреждение под соответствующим полем
Убирает предупреждение при очистке поля
*/

// =================== Проверка дубликатов рекламаций =====================

window.addEventListener('load', function() {

    // Список полей для проверки дубликатов в порядке заполнения пользователем
    const fieldsToCheck = [
        'sender_outgoing_number',    // Номер ПСА отправителя
        'product_number',            // Номер изделия
        'consumer_act_number',       // Номер акта приобретателя
        'end_consumer_act_number',   // Номер акта конечного потребителя
        'engine_number'              // Номер двигателя
    ];

    // Инициализация обработчиков для каждого поля
    fieldsToCheck.forEach(function(fieldName) {
        const field = document.getElementById('id_' + fieldName);

        if (field) {
            // Создаем контейнер для отображения предупреждений
            const warningDiv = document.createElement('div');
            warningDiv.id = 'warning_' + fieldName;
            warningDiv.className = 'duplicate-warning';
            warningDiv.style.cssText = 'color: #e74c3c; margin-top: 5px;';

            // Размещаем контейнер сразу после поля ввода
            field.parentElement.insertAdjacentElement('afterend', warningDiv);

            // Добавляем обработчик события "потеря фокуса"
            field.addEventListener('blur', function() {
                checkSingleFieldDuplicate(fieldName, field.value.trim());
            });
        }
    });

    /**
     * Проверка дубликатов для одного конкретного поля
     * @param {string} fieldName - Название поля для проверки
     * @param {string} fieldValue - Значение поля
     */
    function checkSingleFieldDuplicate(fieldName, fieldValue) {

        // Если поле пустое - убираем предупреждение для этого поля
        if (!fieldValue) {
            clearWarning(fieldName);
            return;
        }

        // Подготавливаем данные для отправки на сервер
        const formData = new FormData();
        formData.append('field_name', fieldName);    // Какое поле проверяем
        formData.append('field_value', fieldValue);  // Значение поля

        // Добавляем ID текущей рекламации (нужно для исключения при редактировании)
        const currentIdMatch = window.location.pathname.match(/\/(\d+)\/change\//);
        if (currentIdMatch) {
            formData.append('current_reclamation_id', currentIdMatch[1]);
        }

        // Добавляем CSRF токен для безопасности Django
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfToken) {
            formData.append('csrfmiddlewaretoken', csrfToken.value);
        }

        // Отправляем AJAX запрос на сервер
        fetch('/admin/ajax/check-reclamation-duplicates/', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            // Обрабатываем ответ от сервера
            if (data.duplicate_found) {
                // Найден дубликат - показываем предупреждение под полем
                showWarning(fieldName, data.warning);
            } else {
                // Дубликат не найден - убираем предупреждение
                clearWarning(fieldName);
            }
        })
        .catch(error => {
            // Обрабатываем ошибки сети
            console.error('Ошибка проверки дубликатов:', error);
        });
    }

    /**
     * Отображение предупреждения под конкретным полем
     * @param {string} fieldName - Название поля
     * @param {string} message - Текст предупреждения
     */
    function showWarning(fieldName, message) {
        const warningDiv = document.getElementById('warning_' + fieldName);
        if (warningDiv) {
            warningDiv.innerHTML = message;
        }
    }

    /**
     * Удаление предупреждения под конкретным полем
     * @param {string} fieldName - Название поля
     */
    function clearWarning(fieldName) {
        const warningDiv = document.getElementById('warning_' + fieldName);
        if (warningDiv) {
            warningDiv.innerHTML = '';
        }
    }
});