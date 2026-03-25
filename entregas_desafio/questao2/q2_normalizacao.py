import re
import unicodedata
import pandas as pd

produtos = pd.read_csv('../../data/raw/produtos_raw.csv')
# Converter price para numérico:
if 'R$' in str(produtos['price'][0]):
    produtos['price'] = (
        produtos['price']
        .str.replace("R$", '', regex=False)
        .str.strip()
        .astype(float)
    )

# normalizar categorias
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

produtos['actual_category'] = produtos['actual_category'].apply(normalizar_categoria)

# Parte 3: remover duplicatas por code
produtos = produtos.drop_duplicates(subset=['code'], keep='first')

print(f"Produtos após limpeza: {len(produtos)}")
print(produtos['actual_category'].value_counts())

produtos.to_csv('entregas_desafio/q2_produtos/produtos_normalizados.csv', index=False)