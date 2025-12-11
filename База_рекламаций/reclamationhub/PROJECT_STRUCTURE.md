# СТРУКТУРА ПРОЕКТА: reclamationhub

*Сгенерировано: 2025-12-11 21:40:39*

---

## Django-приложения

### `analytics`

> Конфигурация приложения

**Модули (processors):**

- `combined_chart_modul.py` → `DefectDateDataProcessor` — Получение и подготовка данных из БД
- `combined_chart_modul.py` → `DefectDateChartGenerator` — Генерация графиков (работает с готовым DataFrame)
- `combined_chart_modul.py` → `DefectDateReportManager` — Главный класс-координатор
- `mileage_chart_modul.py` → `MileageChartProcessor` — Анализ распределения рекламаций по пробегу

---

### `claims`

> Конфигурация приложения

**Модели:**

- `Claim` — Модель претензии по рекламации. Связана с рекламацией (многие ко многим)

**Модули (processors):**

- `claim_prognosis_processor.py` → `ClaimPrognosisProcessor` — Процессор прогнозирования претензий (оркестратор)
- `consumer_analysis_processor.py` → `ConsumerAnalysisProcessor` — Анализ претензий по выбранному потребителю
- `dashboard_processor.py` → `DashboardProcessor` — Обработка данных для Dashboard претензий
- `reclamation_to_claim_processor.py` → `ReclamationToClaimProcessor` — Анализ связи рекламация → претензия
- `time_analysis_processor.py` → `TimeAnalysisProcessor` — Временной анализ конверсии: количество рекламаций → сумма претензий

---

### `core`

> Конфигурация приложения

---

### `investigations`

> Конфигурация приложения

**Модели:**

- `Investigation` — Модель акта исследования рекламационного изделия.

---

### `project_docs`

> Конфигурация приложения

---

### `reclamations`

> Конфигурация приложения

**Модели:**

- `Reclamation` — Модель рекламации на изделие.

---

### `reports`

> Конфигурация приложения

**Модели:**

- `EnquiryPeriod` — Метаданные для справок о поступивших сообщениях за период.

**Модули (processors):**

- `accept_defect_module.py` → `AcceptDefectProcessor` — Обработка данных для отчета по признанным рекламациям
- `culprits_defect_module.py` → `CulpritsDefectProcessor` — Обработка данных для анализа дефектов по виновникам
- `db_search_module.py` → `DbSearchProcessor` — Класс для поиска по базе рекламаций с точным сопоставлением номеров
- `enquiry_period_module.py` → `MetadataLoader` — Аналог TextDatabaseLoader - работа с Django моделью вместо JSON
- `enquiry_period_module.py` → `DataProcessor` — Аналог MakeResultDataframe - получение данных из Django ORM вместо Excel
- `enquiry_period_module.py` → `ExcelWriter` — Аналог WriteResult - создание Excel файла
- `length_study_module.py` → `LengthStudyProcessor` — Анализ длительности исследований

---

### `sourcebook`

> Конфигурация приложения

**Модели:**

- `PeriodDefect` — PeriodDefect(id, name)
- `ProductType` — ProductType(id, name)
- `Product` — Модель изделия.

---

### `utils`

> Конфигурация приложения

---

## ДЕРЕВО ФАЙЛОВ

```
reclamationhub/
├── analytics/  # Django App
│   ├── modules/  # Процессоры
│   │   ├──  combined_chart_modul.py  # Модуль анализа рекламаций по датам изготовления и уведомления о дефектах
│   │   └──  mileage_chart_modul.py
│   ├── templates/  # Шаблоны
│   │   └── analytics/
│   │       ├──  analytic.html  # Шаблон основной страницы с аналитикой
│   │       ├──  combined_chart.html  # Показываем карточку генерации отчета ТОЛЬКО если нет отчета
│   │       ├──  consumer_defect.html  # <h1>{{ page_title }}</h1>
│   │       ├──  mileage_chart.html  # Показываем карточку генерации отчета ТОЛЬКО если нет отчета
│   │       └──  product_defect.html  # <h1>{{ page_title }}</h1>
│   ├── views/  # Представления
│   │   ├──  __init__.py
│   │   ├──  analytic.py
│   │   ├──  combined_chart.py
│   │   ├──  consumer_defect.py
│   │   ├──  mileage_chart.py
│   │   └──  product_defect.py
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
│   │   │   ├──  base.py
│   │   │   ├──  ml.py  # Методы машинного обучения для прогнозирования
│   │   │   ├──  statistical.py
│   │   │   └──  statistical_comment.txt
│   │   ├──  __init__.py
│   │   ├──  claim_prognosis_processor.py  # Процессор для прогнозирования претензий с разными методами
│   │   ├──  consumer_analysis_processor.py
│   │   ├──  dashboard_processor.py
│   │   ├──  reclamation_to_claim_processor.py
│   │   └──  time_analysis_processor.py
│   ├── templates/  # Шаблоны
│   │   └── claims/
│   │       ├── blocks/
│   │       │   ├──  conversion_results.html  # claims/templates/claims/blocks/conversion_results.html
│   │       │   ├──  prognosis_results.html  # claims/templates/claims/blocks/prognosis_results.html
│   │       │   └──  time_analysis_results.html  # claims/templates/claims/blocks/time_analysis_results.html
│   │       ├──  claim_main.html  # claims/templates/claims/claim_main.html
│   │       ├──  claim_prognosis.html  # claims/templates/claims/claim_prognosis.html
│   │       ├──  consumer_analysis.html  # claims/templates/claims/consumer_analysis.html
│   │       ├──  dashboard.html  # claims/templates/claims/dashboard.html
│   │       └──  reclamation_to_claim.html  # claims/templates/claims/reclamation_to_claim.html
│   ├── views/  # Представления
│   │   ├──  __init__.py
│   │   ├──  claim_form.py
│   │   ├──  claim_main.py
│   │   ├──  claim_prognosis.py
│   │   ├──  consumer_analysis.py
│   │   ├──  dashboard.py
│   │   ├──  reclamation_to_claim.py
│   │   └──  time_analysis.py
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
│   │   ├──  analyzers.py
│   │   ├──  formatters.py
│   │   └──  parsers.py
│   ├── management/  # Команды
│   │   ├── commands/  # Команды
│   │   │   ├──  __init__.py
│   │   │   └──  generate_structure.py
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
│   │   └──  paths.py
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
