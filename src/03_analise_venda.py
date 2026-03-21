# %%
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

from db import get_engine

engine = get_engine()
# %% [markdown]
# ## Análise de Prejuízo por Produto
# %%
df_prejuizo = pd.read_sql(
    "SELECT * FROM vw_vendas",
    engine
)

por_produto = (
    df_prejuizo
    .groupby(['nome_produto', 'categoria'])
    .agg(lucro=('lucro_bruto_usd', 'sum'), receita=('valor_total','sum'))
    .reset_index()
    .sort_values('lucro')
)

por_produto
# %%
# %%
bottom10 = por_produto.head(10).sort_values('lucro', ascending=True)
top10    = por_produto.tail(10).sort_values('lucro', ascending=True)

fig, (ax_top, ax_bot) = plt.subplots(2, 1, figsize=(11, 10))

# Top 10
ax_top.barh(top10['nome_produto'], top10['lucro'], color='#2ca02c')
ax_top.set_title('10 Produtos Mais Lucrativos', fontweight='bold', loc='left')
ax_top.xaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f'${x/1e6:.0f}M'))
ax_top.set_xlabel('')

# Bottom 10
ax_bot.barh(bottom10['nome_produto'], bottom10['lucro'], color='#ff7f0e')
ax_bot.set_title('10 Produtos Menos Lucrativos', fontweight='bold', loc='left')
ax_bot.xaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f'${x/1e3:.0f}K'))
ax_bot.set_xlabel('Lucro Bruto (USD)')

fig.suptitle('Ranking de Lucratividade por Produto', fontsize=13, fontweight='bold', y=1.01)
plt.tight_layout()
plt.savefig('../data/outputs/imgs/ranking_lucratividade.png', dpi=150)
plt.show()
# %%
