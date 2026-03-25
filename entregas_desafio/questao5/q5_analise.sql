-- Questão 5.1 - Parte 1
-- Ticket médio e diversidade de categorias por cliente
-- Filtro dos 10 clientes fiéis

WITH vendas_normalizadas AS (
    SELECT
        NULLIF(TRIM(id::text), '')::INTEGER         AS id_venda,
        NULLIF(TRIM(id_client::text), '')::INTEGER  AS id_cliente,
        NULLIF(TRIM(id_product::text), '')::INTEGER AS id_produto,
        NULLIF(TRIM(qtd::text), '')::INTEGER        AS qtd,
        NULLIF(TRIM(total::text), '')::NUMERIC      AS valor_total
    FROM raw_vendas_2023_2024
),

vendas_com_categoria AS (
    SELECT
        v.id_venda,
        v.id_cliente,
        v.id_produto,
        v.qtd,
        v.valor_total,
        p.actual_category AS categoria
    FROM vendas_normalizadas v
    LEFT JOIN produtos_normalizados p
        ON p.code = v.id_produto
),

metricas_cliente AS (
    SELECT
        id_cliente,
        ROUND(SUM(valor_total) / NULLIF(COUNT(DISTINCT id_venda), 0), 2) AS ticket_medio,
        COUNT(DISTINCT categoria) AS diversidade_categorias,
        COUNT(DISTINCT id_venda) AS frequencia,
        ROUND(SUM(valor_total), 2) AS faturamento_total
    FROM vendas_com_categoria
    WHERE id_cliente IS NOT NULL
      AND id_venda IS NOT NULL
    GROUP BY id_cliente
),

top10 AS (
    SELECT
        ROW_NUMBER() OVER (
            ORDER BY ticket_medio DESC, id_cliente ASC
        ) AS ranking,
        id_cliente,
        ticket_medio,
        diversidade_categorias,
        frequencia,
        faturamento_total
    FROM metricas_cliente
    WHERE diversidade_categorias >= 3
)

SELECT
    ranking,
    id_cliente,
    ticket_medio,
    diversidade_categorias,
    frequencia,
    faturamento_total
FROM top10
WHERE ranking <= 10
ORDER BY ranking;

-- Questão 5.1 - Parte 2
-- Categoria mais vendida em quantidade total de itens
-- considerando apenas os 10 clientes fiéis
WITH vendas_normalizadas AS (
    SELECT
        NULLIF(TRIM(id::text), '')::INTEGER         AS id_venda,
        NULLIF(TRIM(id_client::text), '')::INTEGER  AS id_cliente,
        NULLIF(TRIM(id_product::text), '')::INTEGER AS id_produto,
        NULLIF(TRIM(qtd::text), '')::INTEGER        AS qtd,
        NULLIF(TRIM(total::text), '')::NUMERIC      AS valor_total
    FROM raw_vendas_2023_2024
),

vendas_com_categoria AS (
    SELECT
        v.id_venda,
        v.id_cliente,
        v.id_produto,
        v.qtd,
        v.valor_total,
        p.actual_category AS categoria
    FROM vendas_normalizadas v
    LEFT JOIN produtos_normalizados p
        ON p.code = v.id_produto
),

metricas_cliente AS (
    SELECT
        id_cliente,
        ROUND(SUM(valor_total) / NULLIF(COUNT(DISTINCT id_venda), 0), 2) AS ticket_medio,
        COUNT(DISTINCT categoria) AS diversidade_categorias
    FROM vendas_com_categoria
    WHERE id_cliente IS NOT NULL
      AND id_venda IS NOT NULL
    GROUP BY id_cliente
),

top10 AS (
    SELECT
        id_cliente
    FROM (
        SELECT
            id_cliente,
            ROW_NUMBER() OVER (
                ORDER BY ticket_medio DESC, id_cliente ASC
            ) AS ranking
        FROM metricas_cliente
        WHERE diversidade_categorias >= 3
    ) x
    WHERE ranking <= 10
),

categoria_dominante AS (
    SELECT
        vc.categoria,
        SUM(vc.qtd) AS total_itens,
        RANK() OVER (ORDER BY SUM(vc.qtd) DESC) AS pos
    FROM vendas_com_categoria vc
    WHERE vc.id_cliente IN (SELECT id_cliente FROM top10)
    GROUP BY vc.categoria
)

SELECT
    categoria,
    total_itens
FROM categoria_dominante
WHERE pos = 1;