SELECT
    COUNT(*)                    AS total_linhas,
    (SELECT COUNT(*) AS total_colunas
		FROM information_schema.columns
		WHERE table_name = 'raw_vendas_2023_2024'),
	MIN(sale_date)              AS data_minima_raw,
    MAX(sale_date)              AS data_maxima_raw,
    MAX(total)                  AS valor_maximo,
    MIN(total)                  AS valor_minimo,
    ROUND(AVG(total), 2)        AS valor_medio
FROM raw_vendas_2023_2024;
