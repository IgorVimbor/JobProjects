// JavaScript для переключения годов на главной странице

// Инициализация селектора годов
function initYearSelector(availableYears, currentYear) {
    const selector = document.getElementById('yearSelector');

    // Очищаем существующие опции (кроме текущего года)
    selector.innerHTML = '';

    // Добавляем все доступные годы
    availableYears.forEach(year => {
        const option = document.createElement('option');
        option.value = year;
        option.textContent = year;
        option.selected = (year == currentYear);
        selector.appendChild(option);
    });

    // Обработчик изменения года
    selector.addEventListener('change', function() {
        const selectedYear = this.value;
        loadYearData(selectedYear);
    });
}

// Загрузка данных по выбранному году
function loadYearData(year) {
    const spinner = document.getElementById('loadingSpinner');

    // Показываем спиннер
    spinner.classList.remove('d-none');

    // AJAX запрос
    fetch(`/ajax/year-data/?year=${year}`)
        .then(response => response.json())
        .then(data => {
            // Обновляем карточки статистики
            updateStatsCards(data);

            // Создаем новые графики
            initProductsChart(data.products_data);
            initMonthlyChart(data.monthly_data);

            // Обновляем таблицу последних рекламаций
            updateRecentReclamationsTable(data.latest_reclamations);

            // Скрываем спиннер
            spinner.classList.add('d-none');
        })
        .catch(error => {
            console.error('Ошибка загрузки данных:', error);
            spinner.classList.add('d-none');
            alert('Ошибка загрузки данных');
        });
}

// Обновление карточек статистики
function updateStatsCards(data) {
    // Обновляем значения в карточках
    const statsContainer = document.getElementById('statsContainer');

    // ДОБАВЛЯЕМ ЭТУ ПРОВЕРКУ:
    if (!statsContainer) {
        console.error('Элемент statsContainer не найден!');
        return;
    }

    // Создаем новый HTML для карточек
    const newStatsHTML = `
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card text-white bg-primary">
                    <div class="card-body">
                        <h5 class="card-title">Всего рекламаций</h5>
                        <p class="card-text display-4">${data.total_reclamations}</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-white bg-info">
                    <div class="card-body">
                        <h5 class="card-title">Новые</h5>
                        <p class="card-text display-4">${data.new_reclamations}</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-white bg-warning">
                    <div class="card-body">
                        <h5 class="card-title">В работе</h5>
                        <p class="card-text display-4">${data.in_progress}</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-white bg-success">
                    <div class="card-body">
                        <h5 class="card-title">Закрытые</h5>
                        <p class="card-text display-4">${data.closed_reclamations}</p>
                    </div>
                </div>
            </div>
        </div>
    `;

    statsContainer.innerHTML = newStatsHTML;
}

// Обновление таблицы последних рекламаций
function updateRecentReclamationsTable(reclamations) {
    const tableContainer = document.getElementById('recentReclamationsTable');

    // ДОБАВЛЯЕМ ПРОВЕРКУ:
    if (!tableContainer) {
        console.error('Элемент recentReclamationsTable не найден!');
        return;
    }

    let tableHTML = `
        <table class="table table-striped">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Изделие</th>
                    <th>Период выявления дефекта</th>
                    <th>Дефект</th>
                    <th>Количество</th>
                </tr>
            </thead>
            <tbody>
    `;

    if (reclamations.length > 0) {
        reclamations.forEach(rec => {
            tableHTML += `
                <tr>
                    <td>${rec.id}</td>
                    <td>${rec.product_name__name} - ${rec.product__nomenclature}</td>
                    <td>${rec.defect_period__name}</td>
                    <td>${truncateText(rec.claimed_defect || '', 50)}</td>
                    <td>${rec.products_count || ''}</td>
                </tr>
            `;
        });
    } else {
        tableHTML += `
            <tr>
                <td colspan="5" class="text-center">Нет данных за выбранный год</td>
            </tr>
        `;
    }

    tableHTML += `
            </tbody>
        </table>
    `;

    tableContainer.innerHTML = tableHTML;
}

// Вспомогательная функция для обрезки текста
function truncateText(text, maxLength) {
    if (text.length <= maxLength) {
        return text;
    }
    return text.substring(0, maxLength - 3) + '...';
}