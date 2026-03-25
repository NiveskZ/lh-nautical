# %%
import pandas as pd
import requests
from datetime import timedelta
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

# %%
# Carregar vendas e custos
vendas = pd.read_csv('../../data/raw/vendas_2023_2024.csv')
custos_json = pd.read_csv('../questao3/custos_importacao.csv')
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

vendas['sale_date'] = vendas['sale_date'].apply(parse_data)
datas_invalidas = vendas['sale_date'].isna().sum()
vendas = vendas.dropna(subset=['sale_date'])
# %%
# Buscar câmbio USD/BRL do BCB para cada data única
def buscar_cambio(data):
    """Busca taxa de câmbio USD/BRL no BCB para uma data específica."""
    data_str = data.strftime('%m-%d-%Y')
    url = (
        f"https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
        f"CotacaoDolarDia(dataCotacao=@dataCotacao)"
        f"?@dataCotacao='{data_str}'&$format=json&$select=cotacaoVenda"
    )
    try:
        resp = requests.get(url, timeout=10)
        dados = resp.json().get('value', [])
        if dados:
            return dados[-1]['cotacaoVenda']
    except:
        pass
    return None

# Buscar câmbio para todas as datas únicas
datas_unicas = vendas['sale_date'].dt.date.unique()
print(f"Buscando câmbio para {len(datas_unicas)} datas...")

cambio_map = {}
sem_cotacao = []
for i, data in enumerate(datas_unicas):
    taxa = buscar_cambio(pd.Timestamp(data))
    if taxa:
        cambio_map[data] = taxa
    else:
        datas_anteriores = [d for d in cambio_map if d < data]
        if datas_anteriores:
            cambio_map[data] = cambio_map[max(datas_anteriores)]
            sem_cotacao.append(str(data))
    if (i + 1) % 100 == 0:
        print(f"  {i+1}/{len(datas_unicas)}...")

print(f"Câmbio obtido para {len(cambio_map)} datas")
print(f"Datas sem cotação BCB (forward-fill aplicado): {len(sem_cotacao)}")

if sem_cotacao:
    print("  Datas com forward-fill:", sem_cotacao[:10], '...' if len(sem_cotacao) > 10 else '')

# Exportar CSV
rows = [
    {'sale_date': str(d), 'cotacao_venda_usd_brl': v}
    for d, v in sorted(cambio_map.items())
]
df_cambio = pd.DataFrame(rows)
df_cambio.to_csv('./cambio_usd_brl_bcb.csv', index=False)

vendas['cambio_brl'] = vendas['sale_date'].dt.date.map(cambio_map)

# Preparar custos com point-in-time lookup
custos_json['start_date'] = pd.to_datetime(custos_json['start_date'])
custos_json = custos_json.sort_values(['product_id', 'start_date'])


def custo_na_data(id_produto, data_venda):
    historico = custos_json[custos_json['product_id'] == id_produto]
    historico = historico[historico['start_date'] <= pd.Timestamp(data_venda)]
    if historico.empty:
        return None
    return historico.iloc[-1]['usd_price']

print("Calculando custo vigente por venda...")
vendas['custo_usd_unitario'] = vendas.apply(
    lambda r: custo_na_data(r['id_product'], r['sale_date']), axis=1
)

# Calcular prejuízo
vendas['custo_brl_total'] = vendas['custo_usd_unitario'] * vendas['qtd'] * vendas['cambio_brl']
vendas['lucro_brl'] = vendas['total'] - vendas['custo_brl_total']
vendas['tem_prejuizo'] = vendas['lucro_brl'] < 0

# Agregar por produto
por_produto = vendas.groupby('id_product').agg(
    receita_total=('total', 'sum'),
    prejuizo_total=('lucro_brl', lambda x: x[x < 0].sum())
).reset_index()

por_produto['pct_perda'] = (
    por_produto['prejuizo_total'].abs() / por_produto['receita_total'] * 100
).round(2)

com_prejuizo = por_produto[por_produto['prejuizo_total'] < 0].sort_values('prejuizo_total')
print(f"\nProdutos com prejuízo: {len(com_prejuizo)}")
print(com_prejuizo)
# %%
# Gráfico
if len(com_prejuizo) > 0:
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(com_prejuizo['id_product'].astype(str),
            com_prejuizo['prejuizo_total'].abs(),
            color='#d62728')
    ax.set_xlabel('Prejuízo Total (BRL)')
    ax.set_title('Prejuízo Total por Produto', fontweight='bold')
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f'R${x:,.0f}'))
    plt.tight_layout()
    plt.savefig('./grafico_prejuizo.png', dpi=150)
    plt.show()
else:
    print("Nenhum produto com prejuízo encontrado com câmbio real.")

por_produto.to_csv('./prejuizo_por_produto.csv', index=False)
# %%
