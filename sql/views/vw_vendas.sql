DROP VIEW IF EXISTS vw_vendas;

CREATE OR REPLACE
VIEW vw_vendas AS
SELECT
	fv.id_venda,
	fv.data_venda,
	fv.ano,
	fv.mes,
	fv.trimestre,
	fv.dia_semana,
	fv.num_dia_sem,
	dp.nome_produto,
	dp.categoria,
	dp.preco AS preco_tabela,
	dc.nome_completo AS nome_cliente,
	dc.estado,
	fv.qtd,
	fv.valor_total_usd,
	c.custo_usd AS custo_unitario_usd,
	c.custo_usd * fv.qtd AS custo_total_usd,
	fv.valor_total - (c.custo_usd * fv.qtd) AS lucro_bruto_usd,
	CASE
		WHEN fv.valor_total > 0
		THEN ROUND(
			(fv.valor_total - c.custo_usd * fv.qtd)
			/ fv.valor_total * 100, 2
		)
		ELSE NULL
	END AS margem_pct
FROM
	fato_vendas fv
JOIN dim_produtos dp ON
	fv.id_produto = dp.id_produto
JOIN dim_clientes dc ON
	fv.id_cliente = dc.id_cliente
LEFT JOIN dim_custos c 
	ON
	c.id_produto = fv.id_produto
	AND fv.data_venda BETWEEN c.vigencia_inicio AND c.vigencia_fim;

SELECT
	*
FROM
	vw_vendas
LIMIT 5;