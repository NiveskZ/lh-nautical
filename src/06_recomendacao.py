# %%
from itertools import combinations

import pandas as pd

from db import get_engine

engine = get_engine()
# %%

compras = pd.read_sql(
    """
    SELECT fv.id_cliente, fv.id_produto, dp.nome_produto, dp.categoria
    FROM fato_vendas fv
    JOIN dim_produtos dp ON fv.id_produto = dp.id_produto
    """,
    engine
)

compras
# %% [markdown]
# ## Abordagem: Co-ocorrência de compras por cliente
# Com 49 clientes únicos, a filtragem colaborativa item-item baseada em
# co-ocorrência é a escolha mais interessantet, pois não depende de muitos usuários.

# %%
# Separando por id todos os produtos comprados por cliente
por_cliente = (
    compras
    .groupby('id_cliente')['id_produto']
    .apply(lambda x: list(set(x)))
    .reset_index()
)

por_cliente
# %%
pares = []
for _, row in por_cliente.iterrows():
    if len(row['id_produto']) > 1:
        for p1,p2 in combinations(sorted(row['id_produto']),2):
            pares.append((p1,p2))

# %%
co_oc = (
    pd.DataFrame(pares, columns=['produto_a', 'produto_b'])
    .groupby(['produto_a', 'produto_b'])
    .size()
    .reset_index(name='contagem')
    .sort_values('contagem', ascending=False)
)

co_oc
# %%
def recomendar(id_cliente, n=5):
    produtos_do_cliente = set(
        compras[compras['id_cliente'] == id_cliente]['id_produto']
    )

    mask = (
        co_oc['produto_a'].isin(produtos_do_cliente) |
        co_oc['produto_b'].isin(produtos_do_cliente)
    )

    candidatos = co_oc[mask].copy()
    # Seleciona candidatos de recomendação
    candidatos['recomendado'] = candidatos.apply(
        lambda r: r['produto_b'] if r['produto_a'] in produtos_do_cliente
                  else r['produto_a'],
        axis=1
    )
    # Remove o que o cliente já comprou
    candidatos = candidatos[~candidatos['recomendado'].isin(produtos_do_cliente)]

    top = (
        candidatos
        .groupby('recomendado')['contagem']
        .nlargest(n)
        .reset_index()
    )

    return top.merge(
        compras[['id_produto', 'nome_produto', 'categoria']].drop_duplicates(),
        left_on='recomendado', right_on='id_produto'
    )

recomendar(10)
# %%
