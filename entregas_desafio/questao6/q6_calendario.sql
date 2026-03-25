WITH todos_dias AS (
    SELECT generate_series(
        (SELECT MIN(data_venda) FROM fato_vendas),
        (SELECT MAX(data_venda) FROM fato_vendas),
        '1 day'::interval
    )::date AS data
),
dias AS (
    SELECT
        data,
        EXTRACT(DOW FROM data)::INT AS num_dia,
        CASE EXTRACT(DOW FROM data)::INT
            WHEN 0 THEN 'Domingo'
            WHEN 1 THEN 'Segunda-feira'
            WHEN 2 THEN 'Terça-feira'
            WHEN 3 THEN 'Quarta-feira'
            WHEN 4 THEN 'Quinta-feira'
            WHEN 5 THEN 'Sexta-feira'
            WHEN 6 THEN 'Sábado'
        END AS dia_semana
    FROM todos_dias
),
vendas_diarias AS (
    SELECT data_venda, SUM(valor_total) AS faturamento
    FROM fato_vendas
    GROUP BY data_venda
)
SELECT
    d.num_dia,
    d.dia_semana,
    COUNT(d.data)                                           AS total_dias,
    COUNT(v.data_venda)                                     AS dias_com_venda,
    ROUND(COALESCE(SUM(v.faturamento), 0) / COUNT(d.data), 2) AS media_real
FROM dias d
LEFT JOIN vendas_diarias v ON d.data = v.data_venda
GROUP BY d.num_dia, d.dia_semana
ORDER BY d.num_dia;