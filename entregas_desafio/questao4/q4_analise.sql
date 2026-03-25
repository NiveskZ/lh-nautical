WITH vendas_normalizadas AS (
    -- Normaliza as datas do campo raw (que mistura YYYY-MM-DD e DD-MM-YYYY)
    -- e converte os tipos necessários para o cálculo
    SELECT
        id::INTEGER                                         AS id_venda,
        id_product::INTEGER                                 AS id_produto,
        qtd::INTEGER                                        AS qtd,
        total::NUMERIC                                      AS valor_total,
        CASE
            -- Formato YYYY-MM-DD: primeiro segmento tem 4 dígitos
            WHEN SPLIT_PART(sale_date, '-', 1)::TEXT ~ '^\d{4}$'
                THEN TO_DATE(sale_date, 'YYYY-MM-DD')
            -- Formato DD-MM-YYYY
            ELSE TO_DATE(sale_date, 'DD-MM-YYYY')
        END                                                 AS data_venda
    FROM raw_vendas_2023_2024
    WHERE sale_date IS NOT NULL
),

custo_vigente AS (
    -- Para cada venda, localiza o custo USD vigente na data:
    -- "o último start_date registrado que seja <= data da venda"
    SELECT
        v.id_venda,
        v.id_produto,
        v.qtd,
        v.valor_total,
        v.data_venda,
        c.usd_price                                         AS custo_usd_unitario
    FROM vendas_normalizadas v
    JOIN custos_importacao c
        ON  c.product_id  = v.id_produto
        AND c.start_date  = (
                SELECT MAX(c2.start_date)
                FROM   custos_importacao c2
                WHERE  c2.product_id  = v.id_produto
                  AND  c2.start_date <= v.data_venda
            )
),

transacoes AS (
    -- Cruza com câmbio do dia e calcula lucro por transação
    SELECT
        cv.id_venda,
        cv.id_produto,
        cv.qtd,
        cv.valor_total                                      AS receita_brl,
        cv.custo_usd_unitario,
        cb.cotacao_venda_usd_brl                            AS taxa_cambio,

        -- Custo total em BRL = custo unitário USD × qtd × câmbio do dia da venda
        ROUND(cv.custo_usd_unitario * cv.qtd
              * cb.cotacao_venda_usd_brl, 2)                AS custo_brl_total,

        -- Lucro bruto em BRL
        ROUND(cv.valor_total
              - (cv.custo_usd_unitario * cv.qtd
                 * cb.cotacao_venda_usd_brl), 2)            AS lucro_brl
    FROM custo_vigente cv
    JOIN cambio_bcb_ptax cb
        ON cb.sale_date = cv.data_venda
)

-- Agregação final por produto 
SELECT
    t.id_produto,

    -- Receita total: considera TODAS as vendas (com e sem prejuízo)
    ROUND(SUM(t.receita_brl), 2)                            AS receita_total_brl,

    -- Prejuízo total: soma apenas das transações com lucro negativo
    ROUND(SUM(CASE WHEN t.lucro_brl < 0 THEN t.lucro_brl
                   ELSE 0 END), 2)                          AS prejuizo_total_brl,

    -- Percentual de perda = |prejuízo_total| / receita_total × 100
    ROUND(
        ABS(SUM(CASE WHEN t.lucro_brl < 0 THEN t.lucro_brl
                     ELSE 0 END))
        / NULLIF(SUM(t.receita_brl), 0) * 100
    , 2)                                                    AS pct_perda

FROM transacoes t
GROUP BY t.id_produto
HAVING SUM(CASE WHEN t.lucro_brl < 0 THEN t.lucro_brl ELSE 0 END) < 0
ORDER BY pct_perda DESC;   -- Q4.2: maior % de perda no topo