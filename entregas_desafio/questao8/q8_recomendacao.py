# %%
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

vendas = pd.read_csv('../../data/raw/vendas_2023_2024.csv')
produtos = pd.read_csv('../../data/raw/produtos_raw.csv')[['code', 'name']].drop_duplicates()
produtos.columns = ['id_product', 'nome_produto']

PRODUTO_REF = 'GPS Garmin Vortex Maré Drift'

# Matriz usuário x produto (presença/ausência)
matriz = (
    vendas.groupby(['id_client', 'id_product'])['id']
    .count()
    .unstack(fill_value=0)
    .clip(upper=1)  # binário: 1 se comprou, 0 se não
)

# Similaridade de cosseno produto x produto
sim = cosine_similarity(matriz.T)
sim_df = pd.DataFrame(sim, index=matriz.columns, columns=matriz.columns)

# ID do produto de referência
id_ref = produtos[produtos['nome_produto'] == PRODUTO_REF]['id_product'].values[0]

# Top 5 mais similares (excluindo o próprio)
similares = (
    sim_df[id_ref]
    .drop(id_ref)
    .sort_values(ascending=False)
    .head(5)
    .reset_index()
)
similares.columns = ['id_product', 'similaridade']
similares = similares.merge(produtos, on='id_product')

print(f"Produto de referência: {PRODUTO_REF}")
print(f"\nTop 5 produtos mais similares:")
print(similares[['nome_produto', 'similaridade']])
# %%
similares.to_csv('./top5_similares.csv', index=False)
# %%
