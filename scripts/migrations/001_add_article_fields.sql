-- Миграция: Добавление новых полей в таблицу articles
-- Дата: 2025-11-24
-- Описание: Добавляем поля для иерархии ТК РФ, метаинформации источника и характеристик статей

BEGIN;

-- 1. Создаем ENUM тип для статуса статьи
CREATE TYPE article_status AS ENUM ('active', 'abolished', 'suspended');

-- 2. Добавляем новые колонки
ALTER TABLE articles
    -- Иерархическая структура ТК РФ
    ADD COLUMN part VARCHAR(100),
    ADD COLUMN section VARCHAR(200),
    -- chapter уже есть, но проверим что nullable
    ALTER COLUMN chapter DROP NOT NULL;

-- 3. Характеристики статьи
ALTER TABLE articles
    ADD COLUMN text_length INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN status article_status NOT NULL DEFAULT 'active';

-- 4. Метаинформация источника
ALTER TABLE articles
    ADD COLUMN source VARCHAR(100),
    ADD COLUMN source_url VARCHAR(500),
    ADD COLUMN fetched_at TIMESTAMP;

-- 5. Обновляем text_length для существующих записей
UPDATE articles 
SET text_length = LENGTH(content)
WHERE text_length = 0;

-- 6. Создаем индексы для улучшения поиска
CREATE INDEX idx_articles_part ON articles(part);
CREATE INDEX idx_articles_section ON articles(section);
CREATE INDEX idx_articles_status ON articles(status);
CREATE INDEX idx_articles_text_length ON articles(text_length);

COMMIT;

-- Откат миграции (если нужно):
-- BEGIN;
-- DROP INDEX IF EXISTS idx_articles_text_length;
-- DROP INDEX IF EXISTS idx_articles_status;
-- DROP INDEX IF EXISTS idx_articles_section;
-- DROP INDEX IF EXISTS idx_articles_part;
-- ALTER TABLE articles 
--     DROP COLUMN fetched_at,
--     DROP COLUMN source_url,
--     DROP COLUMN source,
--     DROP COLUMN status,
--     DROP COLUMN text_length,
--     DROP COLUMN section,
--     DROP COLUMN part;
-- DROP TYPE article_status;
-- COMMIT;
