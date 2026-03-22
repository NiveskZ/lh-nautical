# %%
import pandas as pd
from prophet import Prophet
from sklearn import metrics
from db import get_engine

engine = get_engine()
# %%
df_ts = pd.read_sql(
    """
    SELECT data_venda AS ds, SUM(valor_total) AS y
    FROM fato_vendas
    GROUP BY data_venda
    ORDER BY data_venda
    """, engine
)

df_ts['ds'] = pd.to_datetime(df_ts['ds'])

df_ts
# %%
# Pegando datas sem venda
idx = pd.date_range(df_ts['ds'].min(), df_ts['ds'].max(), freq='D')
df_ts = df_ts.set_index('ds').reindex(idx, fill_value=0).reset_index()
df_ts.columns = ['ds', 'y']

print(f"Total de dias: {len(df_ts)}")
print(f"Dias sem venda: {(df_ts['y'] == 0).sum()}")
df_ts
# %% [markdown]
# ## Split temporal
# Separando os últimos 90 dias como teste.
split_date = df_ts['ds'].max() - pd.Timedelta(days=90)
train = df_ts[df_ts['ds'] < split_date]
test = df_ts[df_ts['ds'] >= split_date]

print(f"Treino: {len(train)} dias")
print(f"Teste:  {len(test)} dias")
# %%
model = Prophet(
    yearly_seasonality=True,
    weekly_seasonality=True,
    daily_seasonality=False,
    seasonality_mode='multiplicative'
)
# Levando em consideração que os clientes são brasileiros.
model.add_country_holidays(country_name='BR')
model.fit(train)

future = model.make_future_dataframe(periods=len(test), freq='D')
forecast = model.predict(future)

# Métricas no período de teste

y_real = test['y'].values
y_pred = forecast[forecast['ds'].isin(test['ds'])]['yhat'].clip(lower=0).values

mae = metrics.mean_absolute_error(y_real, y_pred)
mape = metrics.mean_absolute_percentage_error(y_real + 1, y_pred + 1) * 100

print(f"\nMAE: USD {mae:,.2f}")
print(f"MAPE: USD {mape:,.2f}")
# %%
