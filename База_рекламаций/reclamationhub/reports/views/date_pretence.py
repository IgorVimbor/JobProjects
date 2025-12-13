# reports\views\date_pretence.py
"""Представление страницы получения информации из базы данных по номеру претензии"""

from django.shortcuts import render
from django.http import HttpResponse
from datetime import datetime

from claims.models import Claim


def date_pretence_page(request):
    """Страница модуля экспорта данных претензии"""

    if request.method == "POST":
        claim_number = request.POST.get("claim_number", "").strip()

        if not claim_number:
            return render(
                request,
                "reports/date_pretence.html",
                {
                    "page_title": "Даты уведомления",
                    "description": "Получение информации из базы данных по номеру претензии",
                    "error": "Необходимо указать номер претензии",
                },
            )

        # Ищем ВСЕ записи с таким номером претензии
        claims = Claim.objects.filter(claim_number=claim_number).prefetch_related(
            "reclamations"
        )
        # select_related - для ForeignKey и OneToOneField
        # prefetch_related - для ManyToManyField и обратных связей

        if not claims.exists():
            return render(
                request,
                "reports/date_pretence.html",
                {
                    "page_title": "Даты уведомления",
                    "description": "Получение информации из базы данных по номеру претензии",
                    "error": f'Претензия с номером "{claim_number}" не найдена',
                },
            )

        # Создаем TXT файл с таблицей данных
        txt_content = generate_claims_table(claims, claim_number)

        # Создаем HTML страницу с кнопкой печати
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Данные претензии №{claim_number}</title>
            <style>
                body {{ margin: 2px 20px; font-family: monospace; }}
                .container {{ white-space: pre-wrap; display: inline-block; }}
                .print-btn {{ text-align: right; margin-bottom: 0; }}
                @media print {{ .print-btn {{ display: none; }} }}
            </style>
        </head>
        <body>
            <div class="container">
                {txt_content}
                <div class="print-btn">
                    <button onclick="window.print()">🖨️ Распечатать</button>
                </div>
            </div>
        </body>
        </html>
        """

        return HttpResponse(html_content, content_type="text/html; charset=utf-8")

    # GET запрос - показываем форму
    context = {
        "page_title": "Даты уведомления",
        "description": "Получение информации из базы данных по номеру претензии",
    }
    return render(request, "reports/date_pretence.html", context)


def generate_claims_table(claims, claim_number):
    """Генерирует таблицу с данными всех актов по претензии"""

    content = []
    content.append(f"ДАННЫЕ АКТОВ ПО ПРЕТЕНЗИИ № {claim_number}")
    content.append("\n")  # 2 пустых строки
    content.append(f"Количество актов: {claims.count()}")
    content.append(f"Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    content.append("")  # пустая строка

    # Заголовки таблицы (5 столбцов)
    content.append("-" * 95)
    headers = [
        "№ п/п".ljust(5),
        "Акт рекламации".ljust(27),
        "Акт исследования".ljust(20),
        "Дата уведомления".ljust(17),
        "Приход на БЗА".ljust(20),
    ]
    content.append(" | ".join(headers))
    content.append("-" * 95)

    # Строки с данными
    for i, claim in enumerate(claims, 1):
        # Формируем акт рекламации
        if claim.reclamation_act_number and claim.reclamation_act_date:
            reclamation_act = f"{claim.reclamation_act_number} от {claim.reclamation_act_date.strftime('%d.%m.%Y')}"
        elif claim.reclamation_act_number:
            reclamation_act = claim.reclamation_act_number
        else:
            reclamation_act = "Не указан"

        # Формируем акт исследования
        if claim.investigation_act_number and claim.investigation_act_date:
            try:
                # Берем третью часть номера акта исследования
                inv_number_part = (
                    claim.investigation_act_number.split()[2]
                    if len(claim.investigation_act_number.split()) > 1
                    else claim.investigation_act_number
                )
                investigation_act = f"{inv_number_part} от {claim.investigation_act_date.strftime('%d.%m.%Y')}"
            except (IndexError, AttributeError):
                investigation_act = f"{claim.investigation_act_number} от {claim.investigation_act_date.strftime('%d.%m.%Y')}"
        elif claim.investigation_act_number:
            try:
                inv_number_part = (
                    claim.investigation_act_number.split()[1]
                    if len(claim.investigation_act_number.split()) > 1
                    else claim.investigation_act_number
                )
                investigation_act = inv_number_part
            except (IndexError, AttributeError):
                investigation_act = claim.investigation_act_number
        else:
            investigation_act = "Не указан"

        # Формируем строку таблицы
        row = [
            str(i).ljust(5),
            reclamation_act[:30].ljust(27),
            investigation_act[:25].ljust(20),
            (
                claim.message_received_date.strftime("%d.%m.%Y")
                if claim.message_received_date
                else "Не указана"
            ).ljust(17),
            (claim.receipt_invoice_number or "Не указан")[:25].ljust(20),
        ]
        content.append(" | ".join(row))

    content.append("-" * 95)
    content.append(f"Всего записей: {claims.count()}")
    content.append("")  # пустая строка
    content.append(
        "Если в столбце 'Приход на БЗА' указан номер ТТН - изделие поступало на БЗА"
    )
    content.append("Если в столбце указано 'фото' - изделие НЕ поступало")

    return "\n".join(content)
