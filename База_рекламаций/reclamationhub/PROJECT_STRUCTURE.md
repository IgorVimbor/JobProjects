# СТРУКТУРА ПРОЕКТА reclamationhub

*Создано: 2025-12-13 15:08:45*

---

## Django-приложения

### `analytics`

**Модули (modules):**

- `combined_chart_modul.py` — 
  Модуль анализа рекламаций по виду изделия, датам изготовления и уведомления.  
  Включает классы:  
  - `DefectDateDataProcessor` - Получение и подготовка данных из БД  
  - `DefectDateChartGenerator` - Генерация графиков (работает с готовым DataFrame)  
  - `DefectDateReportManager` - Главный класс-координатор  
- `mileage_chart_modul.py` — 
  Модуль анализа распределения рекламаций по пробегу.  
  Включает класс:  
  - `MileageChartProcessor` - Анализ распределения рекламаций по пробегу  

**Представления (views):**

- `analytic.py` — Представление для основной страницы аналитики
- `combined_chart.py` — Представления для страницы анализа по датам изготовления и уведомления.
- `consumer_defect.py` — Представление для страницы анализа дефектности по потребителю.
- `mileage_chart.py` — Представление для страницы анализа рекламаций по пробегу.
- `product_defect.py` — Представление для страницы анализа дефектности по изделию.

**Шаблоны (templates):**

- `analytics\analytic.html` — Шаблон основной страницы с аналитикой
- `analytics\combined_chart.html` — Шаблон страницы анализа рекламаций по виду изделия, датам изготовления и уведомления
- `analytics\consumer_defect.html` — Шаблон страницы анализа дефектности по потребителям
- `analytics\mileage_chart.html` — Шаблон страницы анализа по пробегу
- `analytics\product_defect.html` — Шаблон страницы анализа дефектности по конкретному изделию

---

### `claims`

**Модели:**

- `Claim` — Модель претензии по рекламации. Связана с рекламацией (многие ко многим)

**Модули (modules):**

- `claim_prognosis_processor.py` — 
  Процессор для прогнозирования претензий с методами статистического анализа и машинного обучения.  
  Включает класс:  
  - `ClaimPrognosisProcessor` - Процессор прогнозирования претензий (оркестратор) с 6-ю методами  
- `consumer_analysis_processor.py` — 
  Процессор для анализа претензий по потребителям  
  Включает класс:  
  - `ConsumerAnalysisProcessor` - Анализ претензий по выбранному потребителю  
- `dashboard_processor.py` — 
  Процессор для Dashboard (сводной информации) по претензиям.  
  Включает класс:  
  - `DashboardProcessor` - Обработка данных для Dashboard претензий  
- `reclamation_to_claim_processor.py` — 
  Процессор для анализа конверсии рекламация → претензия  
  Включает класс:  
  - `ReclamationToClaimProcessor` - Анализ связи рекламация → претензия  
- `time_analysis_processor.py` — 
  Процессор для временного анализа: количество рекламаций → сумма претензий  
  Включает класс:  
  - `TimeAnalysisProcessor` - Анализ конверсии количество рекламаций → сумма претензий  
- `forecast\base.py` — 
  Базовый модуль для всех методов прогнозирования  
  Включает класс:  
  - `BaseForecast` - Абстрактный базовый класс для методов прогнозирования  
- `forecast\ml.py` — 
  Модуль методов машинного обучения.  
  Включает класс:  
  - `MachineLearningForecast` - Методы машинного обучения для прогнозирования  
- `forecast\statistical.py` — 
  Модуль методов статистическего анализа.  
  Включает класс:  
  - `StatisticalForecast` - Статистические методы прогнозирования  

**Представления (views):**

- `claim_form.py` — AJAX endpoint для получения данных по рекламации в зависимости от результатов поиска.
- `claim_main.py` — Представление для основной страницы аналитики претензий.
- `claim_prognosis.py` — Представление для страницы прогнозирования претензий.
- `consumer_analysis.py` — Представление для страницы анализа претензий по потребителю.
- `dashboard.py` — Представления для страницы Dashboard претензий.
- `reclamation_to_claim.py` — Представления для страницы анализа конверсии рекламация → претензия.
- `time_analysis.py` — Представление для страницы временного анализа рекламация → претензия.

**Шаблоны (templates):**

- `claims\claim_main.html` — Шаблон основной страницы аналитики претензий
- `claims\claim_prognosis.html` — Шаблон страницы с формой прогнозирования претензий
- `claims\consumer_analysis.html` — Шаблон страницы с формой анализа претензий по потребителям
- `claims\dashboard.html` — Шаблон с формой Dashboard претензий
- `claims\reclamation_to_claim.html` — Шаблон с формой анализа конверсии рекламация → претензия
- `claims\blocks\conversion_results.html` — Блок результатов анализа конверсии рекламация → претензия
- `claims\blocks\prognosis_results.html` — Блок результатов прогноза рекламаций и претензий
- `claims\blocks\time_analysis_results.html` — Блок результатов временного анализа рекламация → претензия

---

### `core`

---

### `investigations`

**Модели:**

- `Investigation` — Модель акта исследования рекламационного изделия.

**Представления (views):**

- `add_group_investigation.py` — —
- `add_invoice_out.py` — —

---

### `project_docs`

---

### `reclamations`

**Модели:**

- `Reclamation` — Модель рекламации на изделие.

**Представления (views):**

- `disposal_act.py` — —
- `invoice_intake.py` — —
- `product_utils.py` — —
- `reclamation_form.py` — AJAX endpoint для проверки дубликатов рекламаций.
Проверяет каждое поле отдельно и возвращает предупреждение если найден дубликат.

---

### `reports`

**Модели:**

- `EnquiryPeriod` — Метаданные для справок о поступивших сообщениях за период.

**Модули (modules):**

- `accept_defect_module.py` — 
  —  
- `culprits_defect_module.py` — 
  —  
- `db_search_module.py` — 
  —  
- `enquiry_period_module.py` — 
  —  
- `length_study_module.py` — 
  —  

**Представления (views):**

- `accept_defect.py` — —
- `culprits_defect.py` — —
- `date_pretence.py` — —
- `db_search.py` — —
- `enquiry_period.py` — —
- `length_study.py` — —
- `references.py` — —

**Шаблоны (templates):**

- `reports\accept_defect.html` — reports/templates/reports/accept_defect.html
- `reports\culprits_defect.html` — reports/templates/reports/culprits_defect.html
- `reports\date_pretence.html` — reports/templates/reports/db_search.html
- `reports\db_search.html` — reports/templates/reports/db_search.html
- `reports\enquiry_period.html` — reports/templates/reports/enquiry_period.html
- `reports\length_study.html` — reports/templates/reports/length_study.html
- `reports\references.html` — Шаблон основной страницы со справками и отчетами

---

### `sourcebook`

**Модели:**

- `PeriodDefect` — PeriodDefect(id, name)
- `ProductType` — ProductType(id, name)
- `Product` — Модель изделия.

---

### `utils`

**Шаблоны (templates):**

- `utils\excel_exporter.html` — utils/templates/utils/excel_exporter.html

---

## ДЕРЕВО ФАЙЛОВ

```
reclamationhub/
├── analytics/  # Django App
│   ├── modules/  # Процессоры
│   │   ├──  combined_chart_modul.py  # Модуль анализа рекламаций по виду изделия, датам изготовления и уведомления.
│   │   └──  mileage_chart_modul.py  # Модуль анализа распределения рекламаций по пробегу.
│   ├── templates/  # Шаблоны
│   │   └── analytics/
│   │       ├──  analytic.html  # Шаблон основной страницы с аналитикой
│   │       ├──  combined_chart.html  # Шаблон страницы анализа рекламаций по виду изделия, датам изготовления и уведомления
│   │       ├──  consumer_defect.html  # Шаблон страницы анализа дефектности по потребителям
│   │       ├──  mileage_chart.html  # Шаблон страницы анализа по пробегу
│   │       └──  product_defect.html  # Шаблон страницы анализа дефектности по конкретному изделию
│   ├── views/  # Представления
│   │   ├──  __init__.py
│   │   ├──  analytic.py  # Представление для основной страницы аналитики
│   │   ├──  combined_chart.py  # Представления для страницы анализа по датам изготовления и уведомления.
│   │   ├──  consumer_defect.py  # Представление для страницы анализа дефектности по потребителю.
│   │   ├──  mileage_chart.py  # Представление для страницы анализа рекламаций по пробегу.
│   │   └──  product_defect.py  # Представление для страницы анализа дефектности по изделию.
│   ├──  __init__.py
│   ├──  admin.py  # Настройка админ-панели
│   ├──  apps.py  # Конфигурация приложения
│   ├──  models.py  # Модели данных (ORM)
│   └──  urls.py  # Маршрутизация URL
│
├── claims/  # Django App
│   ├── modules/  # Процессоры
│   │   ├── forecast/
│   │   │   ├──  __init__.py  # Модуль методов прогнозирования
│   │   │   ├──  base.py  # Базовый модуль для всех методов прогнозирования
│   │   │   ├──  ml.py  # Модуль методов машинного обучения.
│   │   │   ├──  statistical.py  # Модуль методов статистическего анализа.
│   │   │   └──  statistical_comment.txt
│   │   ├──  __init__.py
│   │   ├──  claim_prognosis_processor.py  # Процессор для прогнозирования претензий с методами статистического анализа и машинного обучения.
│   │   ├──  consumer_analysis_processor.py  # Процессор для анализа претензий по потребителям
│   │   ├──  dashboard_processor.py  # Процессор для Dashboard (сводной информации) по претензиям.
│   │   ├──  reclamation_to_claim_processor.py  # Процессор для анализа конверсии рекламация → претензия
│   │   └──  time_analysis_processor.py  # Процессор для временного анализа: количество рекламаций → сумма претензий
│   ├── templates/  # Шаблоны
│   │   └── claims/
│   │       ├── blocks/
│   │       │   ├──  conversion_results.html  # Блок результатов анализа конверсии рекламация → претензия
│   │       │   ├──  prognosis_results.html  # Блок результатов прогноза рекламаций и претензий
│   │       │   └──  time_analysis_results.html  # Блок результатов временного анализа рекламация → претензия
│   │       ├──  claim_main.html  # Шаблон основной страницы аналитики претензий
│   │       ├──  claim_prognosis.html  # Шаблон страницы с формой прогнозирования претензий
│   │       ├──  consumer_analysis.html  # Шаблон страницы с формой анализа претензий по потребителям
│   │       ├──  dashboard.html  # Шаблон с формой Dashboard претензий
│   │       └──  reclamation_to_claim.html  # Шаблон с формой анализа конверсии рекламация → претензия
│   ├── views/  # Представления
│   │   ├──  __init__.py
│   │   ├──  claim_form.py  # AJAX endpoint для получения данных по рекламации в зависимости от результатов поиска.
│   │   ├──  claim_main.py  # Представление для основной страницы аналитики претензий.
│   │   ├──  claim_prognosis.py  # Представление для страницы прогнозирования претензий.
│   │   ├──  consumer_analysis.py  # Представление для страницы анализа претензий по потребителю.
│   │   ├──  dashboard.py  # Представления для страницы Dashboard претензий.
│   │   ├──  reclamation_to_claim.py  # Представления для страницы анализа конверсии рекламация → претензия.
│   │   └──  time_analysis.py  # Представление для страницы временного анализа рекламация → претензия.
│   ├──  __init__.py
│   ├──  admin.py  # Настройка админ-панели
│   ├──  apps.py  # Конфигурация приложения
│   ├──  forms.py  # Формы Django
│   ├──  models.py  # Модели данных (ORM)
│   └──  urls.py  # Маршрутизация URL
│
├── core/  # Django App
│   ├──  __init__.py
│   ├──  apps.py  # Конфигурация приложения
│   ├──  urls.py  # Маршрутизация URL
│   └──  views.py  # Представления (контроллеры)
│
├── fixtures/
│   └──  db.json
│
├── investigations/  # Django App
│   ├── views/  # Представления
│   │   ├──  __init__.py
│   │   ├──  add_group_investigation.py
│   │   └──  add_invoice_out.py
│   ├──  __init__.py
│   ├──  admin.py  # Настройка админ-панели
│   ├──  apps.py  # Конфигурация приложения
│   ├──  forms.py  # Формы Django
│   ├──  models.py  # Модели данных (ORM)
│   └──  storages.py
│
├── project_docs/  # Django App
│   ├── generators/
│   │   ├──  __init__.py  # Генераторы документации проекта.
│   │   ├──  analyzers.py  # Анализаторы структуры Django-проекта.
│   │   ├──  formatters.py  # Форматировщик вывода в Markdown.
│   │   └──  parsers.py  # Парсеры для извлечения описаний из файлов разных типов.
│   ├── management/  # Команды
│   │   ├── commands/  # Команды
│   │   │   ├──  __init__.py
│   │   │   └──  generate_structure.py  # Management command для генерации документации проекта.
│   │   └──  __init__.py
│   ├──  __init__.py  # Приложение для генерации документации структуры Django-проекта.
│   └──  apps.py  # Конфигурация приложения
│
├── reclamationhub/
│   ├── settings/
│   │   ├──  __init__.py
│   │   ├──  base.py  # Django settings for reclamationhub project.
│   │   ├──  development.py
│   │   └──  production.py
│   ├──  __init__.py
│   ├──  admin.py  # Настройка админ-панели
│   ├──  asgi.py  # ASGI-конфигурация
│   ├──  urls.py  # Маршрутизация URL
│   └──  wsgi.py  # WSGI-конфигурация
│
├── reclamations/  # Django App
│   ├── views/  # Представления
│   │   ├──  __init__.py
│   │   ├──  disposal_act.py
│   │   ├──  invoice_intake.py
│   │   ├──  product_utils.py
│   │   └──  reclamation_form.py  # AJAX endpoint для проверки дубликатов рекламаций.
│   ├──  __init__.py
│   ├──  admin.py  # Настройка админ-панели
│   ├──  apps.py  # Конфигурация приложения
│   ├──  forms.py  # Формы Django
│   └──  models.py  # Модели данных (ORM)
│
├── reports/  # Django App
│   ├── config/
│   │   └──  paths.py  # Общие пути к каталогам и файлам для всех аналитических модулей
│   ├── modules/  # Процессоры
│   │   ├──  accept_defect_module.py
│   │   ├──  culprits_defect_module.py
│   │   ├──  db_search_module.py
│   │   ├──  enquiry_period_module.py
│   │   └──  length_study_module.py
│   ├── templates/  # Шаблоны
│   │   └── reports/
│   │       ├──  accept_defect.html  # reports/templates/reports/accept_defect.html
│   │       ├──  culprits_defect.html  # reports/templates/reports/culprits_defect.html
│   │       ├──  date_pretence.html  # reports/templates/reports/db_search.html
│   │       ├──  db_search.html  # reports/templates/reports/db_search.html
│   │       ├──  enquiry_period.html  # reports/templates/reports/enquiry_period.html
│   │       ├──  length_study.html  # reports/templates/reports/length_study.html
│   │       └──  references.html  # Шаблон основной страницы со справками и отчетами
│   ├── views/  # Представления
│   │   ├──  __init__.py
│   │   ├──  accept_defect.py
│   │   ├──  culprits_defect.py
│   │   ├──  date_pretence.py
│   │   ├──  db_search.py
│   │   ├──  enquiry_period.py
│   │   ├──  length_study.py
│   │   └──  references.py
│   ├──  __init__.py
│   ├──  admin.py  # Настройка админ-панели
│   ├──  apps.py  # Конфигурация приложения
│   ├──  forms.py  # Формы Django
│   ├──  models.py  # Модели данных (ORM)
│   └──  urls.py  # Маршрутизация URL
│
├── sourcebook/  # Django App
│   ├──  __init__.py
│   ├──  admin.py  # Настройка админ-панели
│   ├──  apps.py  # Конфигурация приложения
│   ├──  models.py  # Модели данных (ORM)
│   └──  views.py  # Представления (контроллеры)
│
├── static/  # Статика
│   ├── admin/
│   │   ├── css/
│   │   │   └──  custom_admin.css  # ---------------------- Стили для таблиц в админ-панели ---------------------
│   │   └── js/
│   │       ├──  claim_search.js  # static\admin\js\claim_search.js
│   │       ├──  custom_admin.js  # static\admin\js\custom_admin.js
│   │       ├──  reclamation_duplicates.js  # Скрипт для проверки дубликатов рекламаций в режиме реального времени.
│   │       └──  reclamation_form.js  # static\admin\js\reclamation_form.js
│   ├── css/
│   │   ├──  bootstrap.min.css  # !
│   │   └──  bootstrap.min.css.map
│   ├── custom_js/
│   │   ├──  charts.js  # JavaScript для построения графиков на главной странице с учетом выбора года и сохранения их в файл
│   │   └──  year_selector.js  # JavaScript для переключения годов на главной странице
│   ├── js/
│   │   ├──  bootstrap.bundle.min.js
│   │   ├──  bootstrap.bundle.min.js.map
│   │   ├──  chart.js
│   │   └──  chartjs-plugin-datalabels.js
│   └──  favicon.png
│
├── templates/  # Шаблоны
│   ├── admin/
│   │   ├──  add_disposal_act.html  # Шаблон для добавления акта утилизации для рекламаций
│   │   ├──  add_group_investigation.html  # Если нужны дополнительные стили специфичные для формы актов исследования
│   │   ├──  add_group_invoice_into.html  # Если нужны дополнительные стили специфичные для формы накладных
│   │   ├──  add_group_invoice_out.html  # Если нужны дополнительные стили специфичные для формы накладных
│   │   ├──  base_site.html  # templates\admin\base_site.html
│   │   ├──  change_form.html  # Базовый шаблон для форм добавления/изменения актов рекламаций и исследования.
│   │   ├──  change_list.html  # Базовый шаблон страницы списка рекламаций или актов исследования.
│   │   ├──  claim_changelist.html  # Дочерний шаблон страницы списка претензий
│   │   ├──  group_form_base.html  # Базовый шаблон для форм группового добавления данных (накладной, актов исследования и др.)
│   │   ├──  investigation_changelist.html  # Дочерний шаблон страницы списка актов исследования.
│   │   ├──  nav_sidebar.html  # Шаблон для изменения надписей в стандартной панели фильтров (в левой части страницы)
│   │   └──  reclamation_changelist.html  # Дочерний шаблон страницы списка рекламаций.
│   ├──  base.html  # templates\base.html
│   ├──  base_navigation.html  # templates\base_navigation.html
│   ├──  base_statistic_cards.html  # templates/base_statistic_cards.html
│   └──  home.html  # Главная страница сайта
│
├── utils/  # Django App
│   ├── excel/
│   │   ├──  __init__.py
│   │   └──  excel_exporter.py
│   ├── templates/  # Шаблоны
│   │   └── utils/
│   │       └──  excel_exporter.html  # utils/templates/utils/excel_exporter.html
│   ├──  __init__.py
│   ├──  apps.py  # Конфигурация приложения
│   ├──  urls.py  # Маршрутизация URL
│   └──  views.py  # Представления (контроллеры)
│
├──  .env.local
├──  .env.production
├──  backup_and_commit.py
├──  email_send.py
├──  manage.py  # CLI Django
└──  PROJECT_STRUCTURE.md
```
