#%%
import pandas as pd
from sklearn.metrics import mean_absolute_error

vendas = pd.read_csv('../../data/raw/vendas_2023_2024.csv')

def parse_data(s):
    try:
        p = s.split('-')
        return pd.to_datetime(s, format='%Y-%m-%d' if len(p[0])==4 else '%d-%m-%Y')
    except:
        return pd.NaT

vendas['sale_date'] = vendas['sale_date'].apply(parse_data)

# Filtrar produto específico
PRODUTO = 'Motor de Popa Yamaha Evo Dash 155HP'
produtos = pd.read_csv('../../data/raw/produtos_raw.csv')
id_produto = produtos[produtos['name'] == PRODUTO]['code'].values[0]

serie = (
    vendas[vendas['id_product'] == id_produto]
    .groupby('sale_date')['qtd']
    .sum()
    .reset_index()
    .rename(columns={'sale_date': 'data', 'qtd': 'vendas'})
)

# Série completa com zeros
idx = pd.date_range(serie['data'].min(), '2024-01-31', freq='D')
serie = serie.set_index('data').reindex(idx, fill_value=0).reset_index()
serie.columns = ['data', 'vendas']

# Split: treino até 31/12/2023, teste jan/2024
treino = serie[serie['data'] <= '2023-12-31'].copy()
teste  = serie[(serie['data'] >= '2024-01-01') & (serie['data'] <= '2024-01-31')].copy()

# Média móvel 7 dias — usando apenas dados anteriores (sem data leakage)
serie_completa = serie.copy()
serie_completa['previsao'] = (
    serie_completa['vendas']
    .shift(1)
    .rolling(window=7, min_periods=1)
    .mean()
)

previsao_teste = serie_completa[
    (serie_completa['data'] >= '2024-01-01') &
    (serie_completa['data'] <= '2024-01-31')
].copy()

mae = mean_absolute_error(previsao_teste['vendas'], previsao_teste['previsao'].fillna(0))
print(f"MAE: {mae:.4f} unidades")
print(previsao_teste[['data', 'vendas', 'previsao']])
# %%
previsao_teste.to_csv('entregas_desafio/q7_previsao/previsao_janeiro_2024.csv', index=False)