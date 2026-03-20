# %%
import json
from datetime import datetime

import numpy as np
import pandas as pd

from IPython.display import display
# %%
produtos_raw = pd.read_csv('../data/raw/produtos_raw.csv')
produtos_raw.head(10)

# %%
vendas_raw = pd.read_csv('../data/raw/vendas_2023_2024.csv')
vendas_raw.head(10)
# %%
with open('../data/raw/clientes_crm.json', encoding='utf-8') as f:
    clientes_raw = json.load(f)
clientes_raw = pd.DataFrame(clientes_raw)

clientes_raw
# %%
with open('../data/raw/custos_importacao.json', encoding='utf-8') as f:
    custos_raw = json.load(f)

custos_raw #json Aninhado
# %%
# Função para identificar o que precisa ser corrigido

def diagnostico(df, nome):
    print(f"BASE: {nome}")

    print(f"\nTamanho: {df.shape[0]} linhas x {df.shape[1]} colunas")

    print(f"\nTipos:")
    print(df.dtypes.to_string())
    print(f"\nNulos (%):")
    nulos = (df.isna().sum() / len(df) * 100)
    print(nulos[nulos > 0].to_string() if nulos.any() else "  Nenhum nulo encontrado.")
    print(f"\nDuplicatas: {df.duplicated().sum()}")
    print(f"\nAmostra:")
    display(df.head(5))
# %%
# Analisando tabela Produtos
diagnostico(produtos_raw, 'Produtos')

#  price é string (deveria ser numérico)
# %%
produtos_raw['actual_category'].value_counts()
# %%
# Verificando se os códigos são únicos
print(f"Linhas: {produtos_raw.shape[0]} | Códigos únicos: {produtos_raw['code'].nunique()}")
# %%
# Identificando produtos inseridos mais de uma vez
produtos_raw[produtos_raw.duplicated(subset=['code'], keep=False)].sort_values('code')
# %%
# Analisando tabela de Vendas
diagnostico(vendas_raw, 'Vendas')

# %%
# sale_date é string - verificando se a conversão direta funciona
teste = pd.to_datetime(vendas_raw['sale_date'], errors='coerce')
print(f"Não convertidas: {teste.isna().sum()}")
print(f"Range: {teste.min()} → {teste.max()}")

# %%
fmt1 = vendas_raw['sale_date'].str.match(r'^\d{4}-\d{2}-\d{2}$').sum()
fmt2 = vendas_raw['sale_date'].str.match(r'^\d{2}-\d{2}-\d{4}$').sum()
print(f"YYYY-MM-DD: {fmt1} | DD-MM-YYYY: {fmt2} | Outros: {len(vendas_raw) - fmt1 - fmt2}")

# Verificando integridade dos valores numéricos
print(f"qtd <= 0: {(vendas_raw['qtd'] <= 0).sum()}")
print(f"total <= 0: {(vendas_raw['total'] <= 0).sum()}")

# os IDs batem com os outros datasets?
print(f"\nid_product: {vendas_raw['id_product'].min()} → {vendas_raw['id_product'].max()}")
print(f"id_client:  {vendas_raw['id_client'].min()} → {vendas_raw['id_client'].max()}")
# %%
# Analisando tabela de clientes
diagnostico(clientes_raw, 'Clientes CRM')

# Verificando emails mal formatados sem @

invalidos = clientes_raw[~clientes_raw['email'].str.contains('@')]
print(f"\nEmails sem '@': {len(invalidos)}")

# %%
# Analisando tabela de custos

print(type(custos_raw))
print(type(custos_raw[0]))
custos_raw[0]

# %%
n_produtos  = len(custos_raw)
n_registros = sum(len(v['historic_data']) for v in custos_raw)
print(f"Produtos: {n_produtos} | Registros de custo: {n_registros} | Média: {n_registros/n_produtos:.1f}")

# %%
# Estrutura do historic_data
exemplo = custos_raw[0]['historic_data']
print(f"Entradas de custo do produto 1: {len(exemplo)}")
for e in exemplo[-3:]:  # últimas 3 entradas
    print(e)
# %%
# Verificando o range de datas dos custos vs vendas
todas_datas_custo = [
    datetime.strptime(h['start_date'], '%d/%m/%Y')
    for c in custos_raw
    for h in c['historic_data']
]
print(f"Datas de custo: {min(todas_datas_custo).date()} a {max(todas_datas_custo).date()}")
# %%
# %%
# Frequência média de compra por cliente
print(f"Transações: {len(vendas_raw)} | Clientes: {clientes_raw.shape[0]}")
print(f"Média: {len(vendas_raw) / clientes_raw.shape[0]:.0f} compras por cliente")
# %% [markdown]
# ## Hipóteses levantadas na EDA
#
# 1. **Perfil dos clientes**: média de ~200 compras por cliente sugere distribuidores
#    ou lojistas. Confirmar na análise de clientes.
#
# 2. **Sazonalidade**: mercado náutico tende a concentrar vendas no verão (nov-mar).
#    Confirmar na análise temporal de vendas.
#
# 3. **Concentração de receita**: provável que poucos produtos gerem a maior parte
#    do faturamento. Confirmar com ranking de produtos.
#
# 4. **Margem real**: custos em USD, períodos de dólar alto podem inverter margem
#    de produtos aparentemente lucrativos. Confirmar ao cruzar custos com câmbio.
# %%
