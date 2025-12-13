// JavaScript функции для формы добавления/редактирования рекламаций

// static\admin\js\reclamation_form.js

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


// ============= Дублирование значений из акта приобретателя в поля акта конечного потребителя =============

// Вариант с единоразовой синхронизацией
document.addEventListener('DOMContentLoaded', function() {
    const $ = django.jQuery;

    // Получаем элементы
    const srcNumber = $('#id_consumer_act_number');
    const srcDate = $('#id_consumer_act_date');
    const destNumber = $('#id_end_consumer_act_number');
    const destDate = $('#id_end_consumer_act_date');

    // Проверяем наличие элементов
    if (!srcNumber.length || !srcDate.length || !destNumber.length || !destDate.length) return;

    // Главная функция синхронизации
    function syncFields() {
        // Проверяем заполненность обоих полей
        if (srcNumber.val() && srcDate.val()) {
            // Копируем значения
            destNumber.val(srcNumber.val());
            destDate.val(srcDate.val());

            // УДАЛЯЕМ ВСЕ ОБРАБОТЧИКИ (ключевое улучшение!)
            srcNumber.off('input', syncFields);
            srcDate.off('change blur', syncFields);
            $(document).off('click', '.datetimeshortcuts a', syncCalendar);
        }
    }

    // Вспомогательная функция для календаря
    function syncCalendar() {
        setTimeout(syncFields, 100);
    }

    // Вешаем обработчики
    srcNumber.on('input', syncFields);  // Для текстового ввода
    srcDate.on('change blur', syncFields);  // Для изменения даты

    // Специальный обработчик для календаря
    $(document).on('click', '.datetimeshortcuts a', syncCalendar);

    // Проверка при загрузке (на случай предзаполненных данных)
    setTimeout(syncFields, 50);
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