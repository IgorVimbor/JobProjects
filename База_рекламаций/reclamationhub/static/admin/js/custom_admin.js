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