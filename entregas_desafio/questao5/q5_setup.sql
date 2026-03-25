CREATE TABLE IF NOT EXISTS produtos_normalizados (
    code             INTEGER PRIMARY KEY,
    name             TEXT,
    price            TEXT,           -- mantido como texto (formato "R$ 33122.52")
    actual_category  VARCHAR(20)     -- valores: eletronicos | propulsao | ancoragem
);