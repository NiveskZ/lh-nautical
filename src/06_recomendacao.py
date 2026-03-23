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
# ## Sistema de Recomendação - Co-ocorrência
#
# Com apenas 49 clientes, algoritmos colaborativos baseados em usuário
# (user-based) seriam instáveis. A abordagem escolhida é item-item:
# 
# - recomenda produtos que outros clientes compraram junto com os produtos
# do cliente em questão.
#
# A "força" da recomendação é a contagem de clientes que compraram
# os dois produtos. Quanto maior, mais confiável a sugestão.
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
    candidatos['id_produto_recomendado'] = candidatos.apply(
        lambda r: r['produto_b'] if r['produto_a'] in produtos_do_cliente
                  else r['produto_a'],
        axis=1
    )
    # Remove o que o cliente já comprou
    candidatos = candidatos[~candidatos['id_produto_recomendado'].isin(produtos_do_cliente)]

    top = (
        candidatos
        .groupby('id_produto_recomendado')['contagem']
        .sum()
        .nlargest(n)
        .reset_index()
    )

    return top.merge(
        compras[['id_produto', 'nome_produto', 'categoria']].drop_duplicates(),
        left_on='id_produto_recomendado', right_on='id_produto'
    )[['id_produto_recomendado', 'contagem', 'nome_produto', 'categoria']]

# %% [markdown]
# ### Validação
# Testando a função para o cliente 10:
# esperamos produtos de categorias variadas, priorizando os mais
# frequentemente comprados em conjunto com o histórico desse cliente.
recomendar(10)
# %%
