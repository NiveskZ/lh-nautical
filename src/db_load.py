import pandas as pd
from sqlalchemy import text
from src.db import get_engine

def recriar_schema(engine):
    schema = open('sql/schema/01_create_tables.sql').read()
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS fato_vendas CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS dim_custos CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS dim_clientes CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS dim_produtos CASCADE"))
        for statement in schema.split(';'):
            if statement.strip():
                conn.execute(text(statement))
        conn.commit()

def carregar(df, tabela, engine):
    df.to_sql(tabela,
              engine,
              if_exists='append',
              index=False,
              method='multi',
              chunksize=500)
    
    print(f"{tabela}: {len(df)} linhas carregadas")

if __name__ == "__main__":

    engine = get_engine()
    recriar_schema(engine)

    produtos = pd.read_csv('data/processed/produtos_clean.csv')
    clientes = pd.read_csv('data/processed/clientes_clean.csv')
    custos   = pd.read_csv('data/processed/custos_clean.csv')
    vendas   = pd.read_csv('data/processed/vendas_clean.csv')

    carregar(produtos, 'dim_produtos', engine)
    carregar(clientes, 'dim_clientes', engine)
    carregar(custos,   'dim_custos',   engine)
    carregar(vendas,   'fato_vendas',  engine)