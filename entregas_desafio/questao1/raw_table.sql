DROP TABLE IF EXISTS raw_vendas_2023_2024;

CREATE TABLE raw_vendas_2023_2024 (
    id VARCHAR(50),
    id_client VARCHAR(50),
    id_product VARCHAR(50),
    qtd NUMERIC,
    total NUMERIC,
    sale_date VARCHAR(50)
);