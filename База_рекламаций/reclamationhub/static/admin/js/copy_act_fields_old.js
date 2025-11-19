// JavaScript для дублирования значений из полей номер и дата акта приобретателя
// в поля номер и дата акта конечного потребителя

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


// Вариант с постоянной синхронизацией
/*
document.addEventListener('DOMContentLoaded', function() {
    // Используем jQuery из Django админки
    const $ = django.jQuery;

    // Получаем элементы полей
    const srcNumber = $('#id_consumer_act_number');
    const srcDate = $('#id_consumer_act_date');
    const destNumber = $('#id_end_consumer_act_number');
    const destDate = $('#id_end_consumer_act_date');

    // Проверяем, что все элементы существуют
    if (!srcNumber.length || !srcDate.length || !destNumber.length || !destDate.length) return;

    // Функция для синхронизации значений
    function syncFields() {
        const numberVal = srcNumber.val();
        const dateVal = srcDate.val();

        if (numberVal && dateVal) {
            destNumber.val(numberVal);
            destDate.val(dateVal);
        }
    }

    // Запускаем периодическую проверку каждые 300 мс
    setInterval(syncFields, 300);
});
*/