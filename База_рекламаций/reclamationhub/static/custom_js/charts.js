// JavaScript для построения графиков на главной странице и сохранения их в файл

// Функция для генерации случайных цветов
function generateColors(count) {
    const colors = [];
    for (let i = 0; i < count; i++) {
        const hue = (i * 360) / count;
        colors.push(`hsl(${hue}, 70%, 60%)`);
    }
    return colors;
}

// Инициализация графика по изделиям с подписями данных
function initProductsChart(productsData) {
    new Chart(document.getElementById('productsChart'), {
        type: 'bar',
        data: {
            labels: productsData.map(item => item.product_name__name),
            datasets: [{
                label: 'Количество рекламаций',
                data: productsData.map(item => item.count),
                backgroundColor: generateColors(productsData.length)
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                },
                datalabels: {  // добавляем значения над столбцами
                    anchor: 'end',  // точка привязки - конец столбца
                    align: 'top',   // выравнивание над столбцом
                    offset: 1,      // отступ от столбца
                    formatter: function(value) {
                        return value;
                    },
                    font: {
                        weight: 'bold',
                        size: 12
                    },
                    color: 'black'
                }
            },
            scales: {
                x: {
                    ticks: {
                        rotation: 0,  // горизонтальные подписи
                        font: {
                            size: 9  // размер шрифта подписей оси Х
                        },
                        callback: function(value) {
                            let label = this.getLabelForValue(value);
                            // Заменяем "турбокомпрессор" на "ТКР"
                            label = label.toLowerCase() === 'турбокомпрессор' ? 'ТКР' : label;
                            //  const label = this.getLabelForValue(value);

                            // Перенос длинных строк
                            const maxLength = 12; // максимальная длина строки
                            const words = label.split(' ');
                            const lines = [];
                            let line = '';

                            words.forEach(word => {
                                if (line.length + word.length > maxLength) {
                                    lines.push(line);
                                    line = word;
                                } else {
                                    line = line ? line + ' ' + word : word;
                                }
                            });
                            if (line) {
                                lines.push(line);
                            }
                            return lines;
                        }
                    }
                }
            }
        },
    });
}

// Инициализация графика по месяцам (с подписями данных)
function initMonthlyChart(monthlyData) {
    new Chart(document.getElementById('monthlyChart'), {
        type: 'line',
        data: {
            labels: monthlyData.map(item => {
                const date = new Date(item.month);
                // return date.toLocaleDateString('ru-RU', { month: 'long', year: 'numeric' });
                return date.toLocaleDateString('ru-RU', { month: 'long' });
            }),
            datasets: [{
                label: 'Количество рекламаций',
                data: monthlyData.map(item => item.count),
                borderColor: '#36A2EB',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                },
                datalabels: {
                    anchor: 'end',  // точка привязки - конец линии
                    align: 'top',   // выравнивание над точкой
                    offset: 0,      // отступ от точки (увеличен для линейного графика)
                    formatter: function(value) {
                        return value;
                    },
                    font: {
                        weight: 'bold',
                        size: 12
                    },
                    color: 'black',  // цвет подписей данных
                    // backgroundColor: 'white',  // добавляем белый фон для лучшей читаемости
                    // borderRadius: 4,           // скругляем углы фона
                    // padding: 4                 // отступы текста от фона
                }
            }
        }
    });
}

// Функция для скачивания графика динамики по месяцам
function downloadMonthlyChart() {
    // Получаем canvas элемент
    const canvas = document.getElementById('monthlyChart');

    // Создаем ссылку для скачивания
    const link = document.createElement('a');
    link.download = 'График_рекламаций_по_месяцам.png';

    // Конвертируем canvas в URL данных
    link.href = canvas.toDataURL('image/png');

    // Программно "кликаем" по ссылке для начала скачивания
    link.click();
}

// Функция для скачивания графика по количеству изделий
function downloadProductsChart() {
    // Получаем canvas элемент
    const canvas = document.getElementById('productsChart');
    // Создаем ссылку для скачивания
    const link = document.createElement('a');

    link.download = 'График_рекламаций_по_изделиям.png';

    // Конвертируем canvas в URL данных
    link.href = canvas.toDataURL('image/png');

    // Программно "кликаем" по ссылке для начала скачивания
    link.click();
}
