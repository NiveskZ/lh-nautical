WITH por_produto AS (
	SELECT
		nome_produto,
		categoria,
		COUNT(*) AS n_vendas,
		SUM(qtd) AS unidades_vendidas,
		ROUND(SUM(valor_total),2) AS receita,
		ROUND(SUM(custo_total_usd), 2) AS custo,
		ROUND(SUM(lucro_bruto_usd), 2) AS lucro,
		ROUND(AVG(margem_pct), 2) AS margem_media_pct
	FROM vw_vendas
	GROUP BY nome_produto, categoria
)

SELECT
	*,
	CASE 
		WHEN lucro < 0 THEN 'PREJUÍZO'
		WHEN margem_media_pct < 10 THEN 'MARGEM CRÍTICA'
		ELSE 'SAUDÁVEL'
	END AS status_margem
FROM por_produto
ORDER BY lucro ASC;