-- Перед загрузкой таблиц из фикстуры-бэкапа следует удалить таблицы
SET FOREIGN_KEY_CHECKS=0;

TRUNCATE TABLE investigation;
TRUNCATE TABLE reclamation;
-- добавьте другие таблицы, если они есть

SET FOREIGN_KEY_CHECKS=1;

-- Далее загружаем базу данных из фикстуры-бэкапа.Например: python manage.py loaddata fixtures/db_290825.json

-------------------------------------------------------------------------------------------------------------


-- Поиск дубликатов номеров двигателей в reclamation
-- Наименование и обозначение изделий берутся из таблиц product_type и product
SELECT r.id,
       r.engine_number,
       pt.name,
       p.nomenclature
FROM reclamation r
LEFT JOIN product_type pt ON r.product_name_id = pt.id
LEFT JOIN product p ON r.product_id = p.id
WHERE r.engine_number IN (
    SELECT engine_number
    FROM reclamation
    GROUP BY engine_number
    HAVING COUNT(*) > 1
)
ORDER BY r.engine_number;

------------------------------------------------------------------------------------------------------------


-- Запрос для вывода строк со значением NULL в столбце r.product_received_date (Дата поступления изделия)
-- Вывод: номер и дата акта исследования и ID рекламации
SELECT
    i.act_number as act_number,
    i.act_date,
    i.reclamation_id,
    r.product_received_date
FROM investigation i
INNER JOIN reclamation r
    ON i.reclamation_id = r.id
WHERE i.act_date IS NOT NULL AND r.product_received_date IS NULL;
-- ------------------------------------------------------------------------------------------------------


-- Записываем в столбец r.product_received_date (Дата поступления изделия) значения
-- из столбца receipt_invoice_date (Дата накладной прихода)
-- 1. Проверочный запрос - что будет изменено:
SELECT
    id,
    product_received_date as current_product_date,
    receipt_invoice_date as will_be_copied,
    message_received_date
FROM reclamation
WHERE product_received_date IS NULL
  AND receipt_invoice_date IS NOT NULL;

-- 2. UPDATE запрос - обновляем данные:
UPDATE reclamation
SET product_received_date = receipt_invoice_date
WHERE product_received_date IS NULL AND receipt_invoice_date IS NOT NULL;

-- 3. Проверка результата - сколько еще осталось пустых product_received_date
-- при заполненном receipt_invoice_date
SELECT
    COUNT(*) as still_empty
FROM reclamation
WHERE product_received_date IS NULL AND receipt_invoice_date IS NOT NULL;
-- --------------------------------------------------------------------------------------------------------


-------------------- Изменение ID и дат в таблице reclamation и связей в investigation ---------------------
-- ПРОВЕРКА ДО ВЫПОЛНЕНИЯ ИЗМЕНЕНИЙ:
-- 1. Общее количество записей в обеих таблицах
SELECT 'reclamation' as table_name, COUNT(*) as total_records FROM reclamation
UNION ALL
SELECT 'investigation' as table_name, COUNT(*) as total_records FROM investigation;
-- Вывод:
-- reclamation = 1340
-- investigation = 355

-- 2. Минимальный и максимальный ID в reclamation
SELECT MIN(id) as min_id, MAX(id) as max_id FROM reclamation;
-- Вывод:
-- min_id = 1 max_id = 1340

-- 3. Проверка связей между таблицами
SELECT i.act_number, i.reclamation_id, r.id
FROM investigation i
JOIN reclamation r ON i.reclamation_id = r.id
LIMIT 10;
-- Вывод:
-- act_number   reclamation_id  id
-- 2025 № 932	1256	        1256
-- 2025 № 931	1248	        1248
-- 2025 № 927	1246	        1246
-- 2025 № 925	1245	        1245
-- 2025 № 929	1244	        1244
-- 2025 № 930	1243	        1243
-- 2025 № 926	1242	        1242
-- 2025 № 890	1235	        1235
-- 2025 № 891	1234	        1234
-- 2025 № 899	1233	        1233

-- ВНЕСЕНИЕ ИЗМЕНЕНИЙ ---------------------------------------------------------
-- Часть 1 - Удаление 37 записей
DELETE FROM reclamation WHERE id < 38;

-- Проверка после удаления
SELECT COUNT(*) as total_records FROM reclamation;
-- Вывод: total_records = 1303
SELECT MIN(id) as min_id, MAX(id) as max_id FROM reclamation;
-- Вывод: min_id = 38 max_id = 1340
-- --------------------------------------------------------------------------------

-- Часть 2 - Обновление ID и дат в таблице reclamation и связей в investigation
-- Отключаем проверку внешних ключей
SET FOREIGN_KEY_CHECKS=0;
SET SQL_SAFE_UPDATES=0;

-- Обновляем ID в таблице reclamation
UPDATE reclamation
SET id = id - 37
WHERE id BETWEEN 38 AND 1340;

-- Устанавливаем автоматический счетчик в значение 1304 (т.е. следующая запись будет 1304)
ALTER TABLE reclamation AUTO_INCREMENT = 1304;

-- Включаем обратно проверку внешних ключей
SET FOREIGN_KEY_CHECKS=1;
SET SQL_SAFE_UPDATES=1;

-- Проверяем результат
SELECT MIN(id), MAX(id) FROM reclamation;
-- Вывод: min_id = 1 max_id = 1303

-- Обновляем даты
SET SQL_SAFE_UPDATES=0;

UPDATE reclamation
SET message_received_date =
    CASE
        WHEN id BETWEEN 1 AND 239 THEN '2025-01-01'
        WHEN id BETWEEN 240 AND 413 THEN '2025-02-01'
        WHEN id BETWEEN 414 AND 703 THEN '2025-03-01'
        WHEN id BETWEEN 704 AND 825 THEN '2025-04-01'
        WHEN id BETWEEN 826 AND 943 THEN '2025-05-01'
        WHEN id BETWEEN 944 AND 1032 THEN '2025-06-01'
        WHEN id BETWEEN 1033 AND 1216 THEN '2025-07-01'
        WHEN id BETWEEN 1217 AND 1303 THEN '2025-08-01'
    END;

SET SQL_SAFE_UPDATES=1;
-- ----------------------------------------------------------------------------------

-- Часть 3 - Обновление связей в investigation
-- Отключаем проверки
SET FOREIGN_KEY_CHECKS=0;
SET SQL_SAFE_UPDATES=0;

-- Обновляем reclamation_id в investigation
UPDATE investigation
SET reclamation_id = reclamation_id - 37
WHERE reclamation_id BETWEEN 830 AND 1340
ORDER BY reclamation_id;

-- Включаем проверки обратно
SET FOREIGN_KEY_CHECKS=1;
SET SQL_SAFE_UPDATES=1;

-- Проверяем результат
SELECT i.act_number, i.reclamation_id, r.id
FROM investigation i
JOIN reclamation r ON i.reclamation_id = r.id
ORDER BY i.reclamation_id
LIMIT 10;
-- Вывод:
-- act_number   reclamation_id  id
-- 2025 № 905	793	            793
-- 2025 № 771	828	            828
-- 2025 № 768	829	            829
-- 2025 № 776	830	            830
-- 2025 № 775	831	            831
-- 2025 № 772	832	            832
-- 2025 № 814	834	            834
-- 2025 № 811	835	            835
-- 2025 № 853	836	            836
-- 2025 № 811	837	            837
-- ---------------------------------------------------------------------------------------

-- ФИНАЛЬНАЯ ПРОВЕРКА ПОСЛЕ ВЫПОЛНЕНИЯ ТРАНЗАКЦИИ:
-- Проверка общего количества записей
SELECT 'reclamation' as table_name, COUNT(*) as total_records FROM reclamation
UNION ALL
SELECT 'investigation' as table_name, COUNT(*) as total_records FROM investigation;

-- Проверка новых диапазонов ID и дат в reclamation
SELECT
    month(message_received_date),
    COUNT(*) as count,
    MIN(id) as min_id,
    MAX(id) as max_id
FROM reclamation
GROUP BY month(message_received_date)
ORDER BY month(message_received_date);

-- Проверка сохранности связей
SELECT i.act_number, i.reclamation_id, r.id, r.message_received_date
FROM investigation i
JOIN reclamation r ON i.reclamation_id = r.id
LIMIT 10;

-- Проверка на пропуски в последовательности ID
SELECT
    COUNT(*) as total_records,
    MIN(id) as min_id,
    MAX(id) as max_id,
    MAX(id) - MIN(id) + 1 as expected_count
FROM reclamation;
--------------------------------------------------------------------------------------------


-- Устанавливаем ID от 1 по увеличению в investigation
SET FOREIGN_KEY_CHECKS=0;
SET SQL_SAFE_UPDATES=0;

-- Создаем временную таблицу с новыми id
CREATE TEMPORARY TABLE temp_ids
SELECT @row_num := @row_num + 1 as new_id, id as old_id
FROM investigation, (SELECT @row_num := 0) r
ORDER BY id;

-- Обновляем id в основной таблице
UPDATE investigation i
JOIN temp_ids t ON i.id = t.old_id
SET i.id = t.new_id;

-- Удаляем временную таблицу
DROP TABLE temp_ids;

-- Устанавливаем AUTO_INCREMENT
ALTER TABLE investigation AUTO_INCREMENT = 356;

SET FOREIGN_KEY_CHECKS=1;
SET SQL_SAFE_UPDATES=1;
-------------------------------------------------------------------------------------------


-- Хранение данных:
-- Все записи в одной таблице reclamation. MySQL автоматически использует индексы для ускорения

-- ------------- Быстрые запросы:

-- Все рекламации 2025 года - БЫСТРО (по индексу year)
-- recs_2025 = Reclamation.objects.filter(year=2025)

-- Конкретная рекламация - ОЧЕНЬ БЫСТРО (по составному индексу)
-- rec = Reclamation.objects.get(year=2025, yearly_number=15)

-- Последние 10 рекламаций - БЫСТРО (по индексу сортировки)
-- recent = Reclamation.objects.order_by('-year', '-yearly_number')[:10]

-- За несколько лет
-- multi_year = Reclamation.objects.filter(year__in=[2024, 2025, 2026])

-- -------------- Архивирование старых данных ------------------------------
-- Архивировать данные старше 5 лет
CREATE TABLE reclamation_archive AS
SELECT * FROM reclamation WHERE year < 2021;

DELETE FROM reclamation WHERE year < 2021;
-- -------------------------------------------------------------------------


-- ВСТАВКА ЗНАЧЕНИЙ В МНОЖЕСТВЕННЫЕ АКТЫ ИССЛЕДОВАНИЯ
-- Вывод записей по конкретному множественному акту исследования
select
	act_number,
	act_scan,
	solution
from investigation
where act_number = '2025 № 879';

-- Вставка имени файла акта исследования для множественных записей
update investigation
set act_scan = 'acts/2025/2025__879_ЯМЗ_ТН_2508612_.pdf'
where act_number = '2025 № 879' and solution is null;

-- Вставка значения 'ACCEPT' для множественных записей
update investigation
set solution = 'ACCEPT'
where act_number = '2025 № 879' and solution is null;

-- Все записи, где акт исследования (act_number) повторяется более одного раза
SELECT
    act_number,
    act_scan,
    solution
FROM investigation
WHERE act_number IN (
    SELECT act_number
    FROM investigation
    GROUP BY act_number
    HAVING COUNT(act_number) > 1
)
ORDER BY act_number;
-- ----------------------------------------------------------------------------

UPDATE claim
SET comment = REPLACE(comment, 'Совместно с ISKRA', 'Вместе с ISKRA')
WHERE comment LIKE '%Совместно с ISKRA%';

SELECT count(*) total
FROM claim
WHERE comment LIKE '%Вместе с ISKRA%';

SELECT id, comment
FROM claim
WHERE comment LIKE '%Вместе с ISKRA%';


SELECT
	count(distinct claim_number) claim_count,
	sum(distinct claim_amount_all) total_amount_byn,
	sum(distinct costs_all) total_costs_byn,
	sum(claim_amount_act) amount_act,
	sum(costs_act) costs_act
FROM claim
WHERE consumer_name = 'ММЗ';