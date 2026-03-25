import json
import pandas as pd

with open('../../data/raw/custos_importacao.json', encoding='utf-8') as f:
    custos = json.load(f)

registros = []
for produto in custos:
    for entrada in produto['historic_data']:
        registros.append({
            'product_id':   produto['product_id'],
            'product_name': produto['product_name'],
            'category':     produto['category'],
            'start_date':   entrada['start_date'],
            'usd_price':    entrada['usd_price']
        })

df = pd.DataFrame(registros)
df['start_date'] = pd.to_datetime(df['start_date'], format='%d/%m/%Y').dt.date

print(f"Total de registros: {len(df)}")

df.to_csv('./custos_importacao.csv', index=False)

