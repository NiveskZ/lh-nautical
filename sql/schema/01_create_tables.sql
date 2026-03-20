CREATE TABLE IF NOT EXISTS dim_produtos (
    id_produto INTEGER PRIMARY KEY,
    nome_produto VARCHAR(255) NOT NULL,
    preco NUMERIC(12,2),
    categoria VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS dim_clientes (
    id_cliente INTEGER PRIMARY KEY,
    nome_completo VARCHAR(255),
    email VARCHAR(255),
    cidade VARCHAR(150),
    estado CHAR(2)
);

CREATE TABLE IF NOT EXISTS dim_custos (
    id SERIAL PRIMARY KEY,
    id_produto INTEGER REFERENCES dim_produtos(id_produto),
    vigencia_inicio DATE NOT NULL,
    vigencia_fim DATE NOT NULL,
    custo_usd NUMERIC(12,2),
    custo_brl NUMERIC(12,2)
);

CREATE TABLE IF NOT EXISTS fato_vendas (
    id_venda INTEGER PRIMARY KEY,
    id_cliente INTEGER REFERENCES dim_clientes(id_cliente),
    id_produto INTEGER REFERENCES dim_produtos(id_produto),
    data_venda DATE NOT NULL,
    qtd INTEGER NOT NULL,
    valor_total NUMERIC(12,2) NOT NULL,
    ano INTEGER,
    mes INTEGER,
    nome_mes VARCHAR(20),
    trimestre INTEGER,
    dia_semana VARCHAR(20),
    num_dia_sem INTEGER
);

-- Índices analíticos
CREATE INDEX IF NOT EXISTS idx_vendas_data ON fato_vendas(data_venda);
CREATE INDEX IF NOT EXISTS idx_vendas_produto ON fato_vendas(id_produto);
CREATE INDEX IF NOT EXISTS idx_vendas_cliente ON fato_vendas(id_cliente);
CREATE INDEX IF NOT EXISTS idx_custos_produto ON dim_custos(id_produto,vigencia_inicio);