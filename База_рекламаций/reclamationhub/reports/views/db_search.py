# reports\views\db_search.py
"""Представление для страницы поиска в базе рекламаций по номеру двигателя или акта"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import FileResponse, Http404, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import os

from reports.config.paths import get_db_search_txt_path
from reports.forms import DbSearchForm
from reports.modules.db_search_module import perform_search


def db_search_page(request):
    """Страница модуля поиска по базе рекламаций"""

    if request.method == "POST":
        return handle_search(request)

    # GET запрос - проверяем нужно ли очистить сессию
    if request.GET.get("clear") == "1":
        # Очищаем все данные поиска из сессии
        request.session.pop("form_data", None)
        request.session.pop("search_results", None)
        request.session.pop("download_info", None)
        # Редирект без параметра clear
        return redirect("reports:db_search")

    # Восстанавливаем данные формы из сессии (если есть)
    form_data = request.session.get("form_data", {})
    form = DbSearchForm(initial=form_data) if form_data else DbSearchForm()

    # Получаем информацию для отображения из сессии
    search_results = request.session.get("search_results", None)
    download_info = request.session.get("download_info", None)

    # Удаляем только download_info после показа (одноразовое сообщение)
    if download_info:
        del request.session["download_info"]

    context = {
        "page_title": "Поиск по базе рекламаций",
        "description": "Поиск информации по номеру двигателя или акта рекламации",
        "form": form,
        "search_results": search_results,
        "download_info": download_info,
    }
    return render(request, "reports/db_search.html", context)


def handle_search(request):
    """Обработка поискового запроса"""
    form = DbSearchForm(request.POST)

    if not form.is_valid():
        # Если форма невалидна, показываем ошибки
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{form.fields[field].label}: {error}")
        return redirect("reports:db_search")

    # Получаем данные из формы
    year = form.cleaned_data["year"]
    engine_numbers_str = form.cleaned_data["engine_numbers"]
    act_numbers_str = form.cleaned_data["act_numbers"]

    # СОХРАНЯЕМ данные формы в сессии
    request.session["form_data"] = {
        "year": year,
        "engine_numbers": engine_numbers_str,
        "act_numbers": act_numbers_str,
    }

    # Определяем тип поиска по нажатой кнопке
    search_type = "detailed" if "detailed_search" in request.POST else "quick"

    # Выполняем поиск
    result = perform_search(year, engine_numbers_str, act_numbers_str, search_type)

    # Обрабатываем результат
    if result["success"]:
        if search_type == "quick":
            # Быстрый поиск - сохраняем результаты в сессии
            messages.success(request, "✅ Поиск выполнен")
            request.session["search_results"] = {
                "results": result["results"],
                "year": year,
                "engine_numbers": engine_numbers_str,
                "act_numbers": act_numbers_str,
            }
        else:
            # Детальный поиск - показываем информацию о файле
            messages.success(request, f"✅ {result['message']}")
            request.session["download_info"] = {
                "message": result["full_message"],
                "filename": result["filename"],
                "records_count": result["records_count"],
            }
    else:
        # Обработка ошибок
        if result["message_type"] == "info":
            messages.info(request, result["message"])
        elif result["message_type"] == "warning":
            messages.warning(request, result["message"])
        else:
            messages.error(request, result["message"])

    # Редирект для обновления страницы
    return redirect("reports:db_search")


def download_search_report(request):
    """Открытие TXT файла отчета в браузере с кастомным заголовком и возможностью печати"""
    try:
        file_path = get_db_search_txt_path()

        if not os.path.exists(file_path):
            raise Http404("Файл отчета не найден")

        # Читаем содержимое файла
        with open(file_path, "r", encoding="utf-8") as file:
            report_content = file.read()

        # Создаем простую HTML страницу с кнопкой печати
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Отчет по базе рекламаций</title>
            <style>
                body {{ margin: 2px 20px; font-family: monospace; }}
                .container {{ white-space: pre-wrap; display: inline-block; }}
                .print-btn {{ text-align: right; margin-bottom: 0; }}
                @media print {{ .print-btn {{ display: none; }} }}
            </style>
        </head>
        <body>
            <div class="container">
                {report_content}
                <div class="print-btn">
                    <button onclick="window.print()">🖨️ Распечатать</button>
                </div>
            </div>
        </body>
        </html>
        """

        return HttpResponse(html_content, content_type="text/html; charset=utf-8")

    except Exception:
        raise Http404("Ошибка при открытии файла")
