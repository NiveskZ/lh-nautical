# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from db import get_engine

engine = get_engine()
vendas = pd.read_sql(
    "SELECT id_venda, id_cliente, data_venda, valor_total FROM fato_vendas",
    engine,
    parse_dates=['data_venda']
)
# %% [markdown]
# ## RFM — Recência, Frequência, Monetário
# Com 49 clientes e ~200 compras por cliente em média, esses clientes se comportam
# mais como distribuidores do que consumidores finais.
# 
# Com RFM vamos avaliar quem está mais ativo vs. em risco.
# %%
data_ref = vendas['data_venda'].max()

rfm = vendas.groupby('id_cliente').agg(
    recencia = ('data_venda', lambda x:(data_ref - x.max()).days),
    frequencia = ('id_venda', 'count'),
    monetario = ('valor_total','sum')
).reset_index()

rfm
# %%

rfm['R'] = pd.qcut(rfm['recencia'].rank(method='first'), q=5, labels=[5,4,3,2,1]).astype(int)
rfm['F'] = pd.qcut(rfm['frequencia'].rank(method='first'), q=5, labels=[1,2,3,4,5]).astype(int)
rfm['M'] = pd.qcut(rfm['monetario'].rank(method='first'), q=5, labels=[1,2,3,4,5]).astype(int)
rfm['rfm_total'] = rfm['R'] + rfm['F'] + rfm['M']

rfm
# %%
def segmentar(row):
    if row['R'] >= 4 and row['F'] >= 4: return 'Campeão'
    elif row['R'] >= 3 and row['F'] >= 3: return 'Leal'
    elif row['R'] >= 4 and row['F'] <= 2: return 'Novo/Potencial'
    elif row['R'] <= 2 and row['F'] >= 3: return 'Em Risco'
    elif row['R'] <= 2 and row['F'] <= 2: return 'Inativo'
    else: return 'Atenção Necessária'

rfm['segmento'] = rfm.apply(segmentar, axis=1)
rfm['segmento'].value_counts()
# %%
rfm.to_csv('../data/outputs/tables/clientes_rfm.csv', index=False)
