from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.standard.operators.bash import BashOperator
from datetime import datetime, timedelta
from dotenv import dotenv_values
import os
import subprocess, sys

PROJECT_ROOT = os.path.expanduser('~/Documentos/lh_nauticals')
config = dotenv_values(f'{PROJECT_ROOT}/.env')

default_args = {
    'owner': 'dados',
    'retries': 2,
    'retry_delay': timedelta(minutes=5)
}

def etapa_limpeza():
    subprocess.run([sys.executable, f'{PROJECT_ROOT}/src/02_tratamento.py'],
                    cwd=f'{PROJECT_ROOT}/src',
                    check=True)

def etapa_carga():
    subprocess.run([sys.executable, f'{PROJECT_ROOT}/src/db_load.py'],
                    cwd=PROJECT_ROOT,
                    check=True)

with DAG(dag_id='lh_nautical_pipeline',
    default_args=default_args,
    schedule='0 6 * * *',
    start_date=datetime(2024,1,1),
    catchup=False,
    tags=['lh_nautical'],
) as dag:
    
    limpeza = PythonOperator(task_id='limpeza_dados', python_callable=etapa_limpeza)
    carga = PythonOperator(task_id='carga_postgres', python_callable=etapa_carga)
    views = BashOperator(
        task_id='refresh_views',
        bash_command=(
            f"psql postgresql://{config['DB_USER']}:{config['DB_PASSWORD']}"
            f"@{config['DB_HOST']}:{config['DB_PORT']}/{config['DB_NAME']} "
            f"-f {PROJECT_ROOT}/sql/views/vw_vendas.sql"
        )
    )

    limpeza >> carga >> views
