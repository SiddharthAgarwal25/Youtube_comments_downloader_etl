from datetime import timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable
from airflow.utils.dates import days_ago
from datetime import datetime
from youtube_comment_etl_script import run_etl


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2020, 11, 8),
    'email': ['airflow@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1)
}

dag = DAG(
    'youtube_dag',
    default_args=default_args,
    description='Our first DAG with ETL process!',
    schedule_interval=None,
)


def run_etl_with_args(**kwargs):
    # Access Airflow variables
    args = Variable.get("youtube_args", deserialize_json=True)

    # Pass the variables to your function
    run_etl(args['api_key'], args['playlist_ids'])


run_etl_pipe = PythonOperator(
    task_id='complete_twitter_etl',
    python_callable=run_etl_with_args,
    dag=dag, 
)

run_etl_pipe