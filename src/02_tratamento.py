# %%
import json
import re
import unicodedata

import pandas as pd

# %%
produtos_raw = pd.read_csv('../data/raw/produtos_raw.csv')
produtos = produtos_raw.copy()
produtos

# %% [markdown]
# ### Produtos — Passo 1: Corrigir o tipo de `price`
#
# **Problema:**
# `"R$ 33122.52"` como string.
#
# **Decisão:**
# Remover `"R$ "` e converter para float.
#
# **Risco:**
# Verificar se há algum formato diferente (vírgula como decimal?).

# %%
amostras_price = produtos['price'].head(20).tolist()
amostras_price
# %%
if 'R$' in str(produtos['price'][0]):
    produtos['price'] = (
        produtos['price']
        .str.replace("R$", '', regex=False)
        .str.strip()
        .astype(float)
    )

print(f"Price range: R$ {produtos['price'].min():.2f} a R$ {produtos['price'].max():.2f}")

# %% [markdown]
# ### Produtos — Passo 2: Normalizar coluna `actual_category`
#
# **Problema:** Variação de categorias iguais mal formatadas.
#
# **Decisão:** Normalização por regras de texto (lowercase + strip + regex).

# %%
def normalizar_categoria(texto):
    """
    Mapeia qualquer variante para uma das 3 categorias: 
    {'eletronicos', 'propulsao','ancoragem'}
    """

    if pd.isna(texto):
        return 'desconhecido'
    
    # Normalização: lowercase, remove espaços e acentos

    t = texto.lower().strip()
    t = re.sub(r'\s+', '', t)
    t = (unicodedata.normalize('NFKD', t)
                    .encode('ascii', errors='ignore')
                    .decode('ascii'))

    if re.search(r'eletr',t):
        return 'eletronicos'
    elif re.search(r'prop', t):
        return 'propulsao'
    elif re.search(r'anc|enc', t):
        return 'ancoragem'
    else:
        return 'desconhecido'

produtos['categoria'] = produtos['actual_category'].apply(normalizar_categoria)
pd.crosstab(produtos['actual_category'], produtos['categoria'])

# Confirmando que foram todos tratados corretamente
print(f"\nDesconhecidos: {(produtos['categoria'] == 'desconhecido').sum()}")
# %% [markdown]
# ### Produtos — Passo 3: Remover duplicatas
#
# **Problema:** Códigos únicos repetidos, remover 7 linhas extras.
#
# **Investigação:** Os registros duplicados têm mesmo code, name e price,
# mas actual_category diferente (mesma categoria, escrita diferente).
# 
# **Decisão:** Manter a primeira ocorrência (keep='first').
#
# Justificativa: após normalização de categoria, todos os registros duplicados
# apontam para a mesma categoria canônica. Qualquer um deles é equivalente.
# %%
produtos = produtos.drop_duplicates(subset=['code'], keep='first')
produtos.shape
# %%
produtos = produtos[['code', 'name', 'price', 'categoria']].rename(
    columns={
        'code':'id_produto',
        'name':'nome_produto',
        'price': 'preco'
    }
)

produtos.to_csv('../data/processed/produtos_clean.csv', index=False)
# %%
vendas_raw = pd.read_csv('../data/raw/vendas_2023_2024.csv')
vendas = vendas_raw.copy()
vendas
# %%
# %% [markdown]
# ### Vendas — Passo 1: Resolver os dois formatos de data
#
# **Problema:** sale_date mistura YYYY-MM-DD e DD-MM-YYYY.
#
# **Estratégia:** Detectar o formato de cada linha e parsear corretamente.
#
# Não é possível usar pd.to_datetime com um único formato.
# %%
def parse_data(data_str):
    """
    Parseia datas no formato YYYY-MM-DD e DD-MM-YYYY.
    Identifica o formato pelo padrão do primeiro segmento.
    """

    try:
        partes = data_str.split('-')
        if len(partes[0]) == 4:
            return pd.to_datetime(data_str, format='%Y-%m-%d')
        else:
            return pd.to_datetime(data_str, format='%d-%m-%Y')
    except (ValueError, AttributeError):
        return pd.NaT
# %%
vendas['sale_date'] = vendas['sale_date'].apply(parse_data)
datas_invalidas = vendas['sale_date'].isna().sum()
print(f"Datas não parseadas: {datas_invalidas}")
print(f"Range: {vendas['sale_date'].min().date()} a {vendas['sale_date'].max().date()}")

# %% [markdown]
# ### Vendas — Passo 2: Engenharia de features temporais
#
# Criamos estas colunas agora, uma vez, para não repetir lógica nas análises.

vendas['ano'] = vendas['sale_date'].dt.year
vendas['mes'] = vendas['sale_date'].dt.month
vendas['nome_mes']   = vendas['sale_date'].dt.strftime('%B').str.capitalize()
vendas['dia_semana'] = vendas['sale_date'].dt.strftime('%A').str.capitalize()
vendas['num_dia_sem'] = vendas['sale_date'].dt.day_of_week
vendas['trimestre'] = vendas['sale_date'].dt.quarter
vendas
# %%
vendas = vendas.rename(
    columns={
        'id': 'id_venda',
        'id_client': 'id_cliente',
        'id_product': 'id_produto',
        'total': 'valor_total',
        'sale_date': 'data_venda'
    }
)

vendas.to_csv('../data/processed/vendas_clean.csv', index=False)
# %%
with open('../data/raw/clientes_crm.json', encoding='utf-8') as f:
    clientes_raw = json.load(f)

clientes = pd.DataFrame(clientes_raw)
clientes
# %% [markdown]
# ### Clientes — Passo 1: Corrigir emails
#
# **Problema:** 30/49 emails têm '#' no lugar de '@'.
#
# **Decisão:** Substituição simples.

# %%
clientes['email'] = clientes['email'].str.replace('#', '@', regex=False)
clientes

# %% [markdown]
# ### Clientes — Passo 2: Extrair cidade e estado de `location`
#
# **Problema:** Separadores variáveis (' , ', ',', ' - ', '-', '/', ' / ')
# e ordem inconsistente (estado-cidade ou cidade-estado).
#
# **Estratégia:**
#   1. Normalizar separador para ','
#   2. Identificar qual parte é UF (2 letras maiúsculas ou sigla conhecida)
#   3. O outro lado é a cidade

# %%
ESTADOS_BRASILEIROS = {
    'AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS',
    'MG','PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC',
    'SP','SE','TO'
}

def extrair_cidade_estado(location):
    if pd.isna(location):
        return pd.Series({'cidade': None, 'estado': None})
    
    # Normalizar separador para virgula
    loc = re.sub(r'\s*[,/\-]\s*', ',', str(location).strip())
    partes = [p.strip() for p in loc.split(',') if p.strip()]
    
    uf, cidade = None, None
    for i, parte in enumerate(partes):
        parte_limpa = re.sub(r'\(.*?\)', '', parte).strip()
        if parte_limpa.upper() in ESTADOS_BRASILEIROS:
            uf = parte_limpa.upper()

            cidade_partes = [p for j,p in enumerate(partes) if j != i]
            cidade = ', '.join(cidade_partes)
            break

    return pd.Series({'cidade': cidade, 'estado': uf})

clientes[['cidade','estado']] = clientes['location'].apply(extrair_cidade_estado)
clientes
# %%

clientes = clientes.rename(
    columns={
        'code': 'id_cliente',
        'full_name': 'nome_completo',
    }
)[['id_cliente','nome_completo','email','cidade','estado']]

clientes.to_csv('../data/processed/clientes_clean.csv', index=False)

# %% [markdown]
# ## Custos — Flattening e lógica de custo vigente
#
# **Desafio:** O JSON é aninhado (lista de histórico por produto).
# Precisamos de uma tabela onde cada linha seja um "período de vigência" de custo.
#
# **Problema do USD:** Custos estão em dólar.
#
# **Decisão de simplificação:** Usaremos uma cotação média de
# R$5.10/USD para todo o período 2023-2024. (fonte: BCB)

# %%
USD_BRL = 5.10  

with open('../data/raw/custos_importacao.json', encoding='utf-8') as f:
    custos_raw_json = json.load(f)

custos_raw_json
# %%
registros = []

for produto in custos_raw_json:
    historico = sorted(
        produto['historic_data'],
        key=lambda x: pd.to_datetime(x['start_date'], format='%d/%m/%Y')
    )

    for i, entrada in enumerate(historico):
        inicio = pd.to_datetime(entrada['start_date'], format='%d/%m/%Y')
        
        if i < len(historico) - 1:
            proximo = pd.to_datetime(historico[i+1]['start_date'],
                                     format='%d/%m/%Y')
            fim = proximo - pd.Timedelta(days=1)
        else:
            fim = pd.Timestamp('2099-12-31')
    
        registros.append(
            {
                'id_produto': produto['product_id'],
                'vigencia_inicio': inicio.date(),
                'vigencia_fim': fim.date(),
                'custo_usd': entrada['usd_price'],
                'custo_brl': round(entrada['usd_price'] * USD_BRL, 2)
            }
        )

custos_flat = pd.DataFrame(registros)
custos_flat
# %%

custos_flat.to_csv('../data/processed/custos_clean.csv', index=False)
# %%
