# %% [markdown]
# # Dashboard de Análise — LH Nautical
# Visualizações geradas a partir dos dados limpos das Questões 1–4.
 
# %% Imports e configuração
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from sklearn.metrics import mean_absolute_error
 
plt.rcParams.update({
    'figure.facecolor': 'white',
    'axes.facecolor':   '#f8f9fa',
    'axes.grid':        True,
    'grid.color':       'white',
    'grid.linewidth':   0.8,
    'font.family':      'sans-serif',
    'axes.spines.top':  False,
    'axes.spines.right':False,
})
 
# %% Carregamento de dados
def parse_data(s):
    try:
        p = s.split('-')
        return pd.to_datetime(s, format='%Y-%m-%d' if len(p[0])==4 else '%d-%m-%Y')
    except:
        return pd.NaT
 
vendas   = pd.read_csv('../data/raw/vendas_2023_2024.csv')
produtos = pd.read_csv('./questao2/produtos_normalizados.csv')
custos   = pd.read_csv('./questao3/custos_importacao.csv')
cambio   = pd.read_csv('./questao4/cambio_usd_brl_bcb.csv')
 
vendas['sale_date']   = vendas['sale_date'].apply(parse_data)
vendas                = vendas.dropna(subset=['sale_date'])
cambio['sale_date']   = pd.to_datetime(cambio['sale_date'])
custos['start_date']  = pd.to_datetime(custos['start_date'])
custos                = custos.sort_values(['product_id', 'start_date'])
cambio_map            = cambio.set_index('sale_date')['cotacao_venda_usd_brl'].to_dict()
 
def custo_vigente(id_prod, data):
    h = custos[(custos['product_id'] == id_prod) & (custos['start_date'] <= data)]
    return h.iloc[-1]['usd_price'] if not h.empty else None
 
print("Calculando custos e câmbio por transação...")
vendas['custo_usd'] = vendas.apply(lambda r: custo_vigente(r['id_product'], r['sale_date']), axis=1)
vendas['cambio']    = vendas['sale_date'].map(cambio_map)
vendas['custo_brl'] = vendas['custo_usd'] * vendas['qtd'] * vendas['cambio']
vendas['lucro_brl'] = vendas['total'] - vendas['custo_brl']
 
por_produto = vendas.groupby('id_product').agg(
    receita_total  =('total',     'sum'),
    prejuizo_total =('lucro_brl', lambda x: x[x < 0].sum())
).reset_index()
por_produto['pct_perda'] = (
    por_produto['prejuizo_total'].abs() / por_produto['receita_total'] * 100
).round(2)
por_produto = por_produto.merge(
    produtos[['code', 'name', 'actual_category']],
    left_on='id_product', right_on='code', how='left'
)
com_prejuizo = por_produto[por_produto['prejuizo_total'] < 0].copy()
print(f"Produtos com prejuízo: {len(com_prejuizo)}")

# %%
# GRÁFICO 1 - Top 20 produtos com maior prejuízo absoluto
top20_abs = com_prejuizo.nsmallest(20, 'prejuizo_total').sort_values('prejuizo_total')
labels = top20_abs['name'].str[:40]
valores = top20_abs['prejuizo_total'].abs()
 
fig, ax = plt.subplots(figsize=(12, 9))
bars = ax.barh(labels, valores, color='#a32d2d', height=0.65)
 
# Anotação de valor em cada barra
for bar, val in zip(bars, valores):
    ax.text(bar.get_width() + valores.max() * 0.01,
            bar.get_y() + bar.get_height() / 2,
            f'R${val/1e6:.1f}M',
            va='center', fontsize=9, color='#444')
 
ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f'R${x/1e6:.0f}M'))
ax.set_xlabel('Prejuízo Total (BRL)', fontsize=11)
ax.set_title('Top 20 Produtos - Prejuízo Total (Valor Absoluto)',
             fontsize=13, fontweight='bold', pad=14)
plt.tight_layout()
plt.savefig('./visualizacoes/grafico_prejuizo_absoluto.png', dpi=150)
plt.show()
 
# %%
# GRÁFICO 2 - Top 20 produtos com maior % de perda
top20_pct = com_prejuizo.nlargest(20, 'pct_perda').sort_values('pct_perda')
labels_pct = top20_pct['name'].str[:40]
 
fig, ax = plt.subplots(figsize=(12, 9))
bars = ax.barh(labels_pct, top20_pct['pct_perda'], color='#c04848', height=0.65)
 
for bar, val in zip(bars, top20_pct['pct_perda']):
    ax.text(bar.get_width() + 0.3,
            bar.get_y() + bar.get_height() / 2,
            f'{val:.1f}%',
            va='center', fontsize=9, color='#444')
 
ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f'{x:.0f}%'))
ax.set_xlabel('% de Perda (Prejuízo / Receita)', fontsize=11)
ax.set_title('Top 20 Produtos - Maior % de Perda Relativa',
             fontsize=13, fontweight='bold', pad=14)
plt.tight_layout()
plt.savefig('./visualizacoes/grafico_prejuizo_percentual.png', dpi=150)
plt.show()
 
# %%
# GRÁFICO 3 - Prejuízo por categoria
por_categoria = com_prejuizo.groupby('actual_category').agg(
    prejuizo_total=('prejuizo_total', 'sum'),
    n_produtos    =('id_product',     'count')
).reset_index().sort_values('prejuizo_total')
 
fig, ax = plt.subplots(figsize=(8, 4))
cores = {'eletronicos': '#a32d2d', 'propulsao': '#c04848', 'ancoragem': '#e06060'}
bars = ax.barh(
    por_categoria['actual_category'],
    por_categoria['prejuizo_total'].abs(),
    color=[cores.get(c, '#999') for c in por_categoria['actual_category']],
    height=0.5
)
for bar, row in zip(bars, por_categoria.itertuples()):
    ax.text(bar.get_width() + por_categoria['prejuizo_total'].abs().max() * 0.01,
            bar.get_y() + bar.get_height() / 2,
            f'R${abs(row.prejuizo_total)/1e6:.1f}M  ({row.n_produtos} produtos)',
            va='center', fontsize=10, color='#444')
 
ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f'R${x/1e6:.0f}M'))
ax.set_xlabel('Prejuízo Total (BRL)', fontsize=11)
ax.set_title('Prejuízo Total por Categoria', fontsize=13, fontweight='bold', pad=14)
plt.tight_layout()
plt.savefig('./visualizacoes/grafico_prejuizo_categoria.png', dpi=150)
plt.show()

# %%
# GRÁFICO 4 - Q7: Previsão de demanda x valores reais (Jan/2024)
PRODUTO = 'Motor de Popa Yamaha Evo Dash 155HP'
id_produto = produtos[produtos['name'] == PRODUTO]['code'].values[0]
 
serie = (
    vendas[vendas['id_product'] == id_produto]
    .groupby('sale_date')['qtd']
    .sum()
    .reset_index()
    .rename(columns={'sale_date': 'data', 'qtd': 'vendas'})
)
idx = pd.date_range(serie['data'].min(), '2024-01-31', freq='D')
serie = serie.set_index('data').reindex(idx, fill_value=0).reset_index()
serie.columns = ['data', 'vendas']
 
serie['previsao'] = serie['vendas'].shift(1).rolling(window=7, min_periods=1).mean()
 
teste = serie[(serie['data'] >= '2024-01-01') & (serie['data'] <= '2024-01-31')].copy()
mae = mean_absolute_error(teste['vendas'], teste['previsao'].fillna(0))
 
fig, ax = plt.subplots(figsize=(12, 5))
ax.bar(teste['data'], teste['vendas'],
       color='#2c7bb6', alpha=0.7, label='Vendas reais', width=0.6)
ax.plot(teste['data'], teste['previsao'].fillna(0),
        color='#d62728', linewidth=2, marker='o', markersize=5, label='Previsão (MM7)')
ax.set_title(f'Previsão de Demanda — {PRODUTO}\nJaneiro 2024 | MAE = {mae:.4f} unidades',
             fontsize=12, fontweight='bold', pad=12)
ax.set_xlabel('Data', fontsize=11)
ax.set_ylabel('Unidades vendidas', fontsize=11)
ax.legend(fontsize=10)
ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%d/%m'))
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('./visualizacoes/grafico_previsao_demanda.png', dpi=150)
plt.show()
print(f"Gráfico 4 salvo. MAE = {mae:.4f}")
 
print("\n\tRESUMO FINAL")
print(f"Produtos com prejuízo: {len(com_prejuizo)}/150")
print(f"Prejuízo total geral: R${com_prejuizo['prejuizo_total'].sum():,.0f}")
print(f"Produto com maior % de perda: id={com_prejuizo.nlargest(1,'pct_perda')['id_product'].values[0]}")
print(f"MAE previsão Q7: {mae:.4f}")
# %%
