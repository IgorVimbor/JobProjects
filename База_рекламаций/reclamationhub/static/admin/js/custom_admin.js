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