DROP TABLE IF EXISTS cambio_bcb_ptax;
DROP TABLE IF EXISTS custos_importacao;

CREATE TABLE IF NOT EXISTS cambio_bcb_ptax (
    sale_date             DATE           NOT NULL,
    cotacao_venda_usd_brl NUMERIC(10, 4) NOT NULL,
    CONSTRAINT pk_cambio PRIMARY KEY (sale_date)
);

CREATE TABLE IF NOT EXISTS custos_importacao (
    product_id   INTEGER        NOT NULL,
    product_name TEXT,
    category     TEXT,
    start_date   DATE           NOT NULL,
    usd_price    NUMERIC(12, 2) NOT NULL,
    CONSTRAINT pk_custos PRIMARY KEY (product_id, start_date)
);