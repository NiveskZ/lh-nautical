SELECT dia_semana, num_dia_sem,
       ROUND(AVG(valor_total),2) AS media_por_venda,
       COUNT(*) AS total_vendas
FROM fato_vendas
GROUP BY dia_semana, num_dia_sem
ORDER BY num_dia_sem;