WITH todos_dias AS (
	SELECT generate_series(
		(SELECT MIN(data_venda) FROM fato_vendas),
		(SELECT MAX(data_venda) FROM fato_vendas),
		'1 day'::interval
	)::date AS data
),

dias_com_info AS (
	SELECT
		data,
		EXTRACT(DOW FROM data)::INT AS num_dia,
		TRIM(TO_CHAR(data, 'Day')) AS dia_semana
	FROM todos_dias
),

vendas_diarias AS (
	SELECT 
		data_venda,
		SUM(valor_total) AS faturamento
	FROM fato_vendas
	GROUP BY data_venda
)

SELECT
	d.num_dia,
	d.dia_semana,
	COUNT(d.data) AS total_dias_no_periodo,
	COUNT(v.data_venda) AS qtd_dias_com_venda,
	COUNT(d.data) - COUNT(v.data_venda) AS qtd_dias_sem_venda,
	ROUND(coalesce(SUM(v.faturamento),0),2) AS faturamento_total,
	ROUND(coalesce(SUM(v.faturamento),0)/COUNT(d.data),2) AS media_faturamento_dia
	ROUND(COALESCE(AVG(v.faturamento),0),2) AS media_faturamento_dia_ativo
FROM dias_com_info d
LEFT JOIN vendas_diarias v
ON d.DATA = v.data_Venda
GROUP BY d.num_dia, d.dia_semana
ORDER BY d.num_dia;


