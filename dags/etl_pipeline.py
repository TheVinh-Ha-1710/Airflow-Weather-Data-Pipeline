import pandas as pd
import requests
import json

from google.cloud import bigquery
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.google.cloud.hooks.bigquery import BigQueryHook
from datetime import datetime

# Step 1: Fetch weather data from Open-Meteo API
def fetch_weather_data():
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": -33.8688,  # Sydney Latitude
        "longitude": 151.2093,  # Sydney Longitude
        "hourly": "temperature_2m,windspeed_10m,precipitation,relative_humidity_2m",  # Hourly data
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,wind_direction_10m_dominant",  # Daily data
        "timezone": "auto",
        "models": "bom_access_global"
    }
    try:
        responses = requests.get(url=url, params=params)
        
        hourly_data = responses.json()['hourly']
        daily_data = responses.json()['daily']
        
        return json.dumps(hourly_data), json.dumps(daily_data)
    except:
        raise Exception("Failed to fetch data")

# Step 2: Parse the API data and transform into DataFrames
def parse_weather_data(hourly_json, daily_json):
    hourly_data = json.loads(hourly_json)
    daily_data = json.loads(daily_json)

    hourly_df = pd.DataFrame(hourly_data)
    daily_df = pd.DataFrame(daily_data)
    
    return hourly_df.to_json(), daily_df.to_json()

# Step 3: Upload data to Google Cloud Storage (GCS)
def upload_to_gcs(hourly_json, daily_json):
    # Make DataFrame
    hourly_data = pd.read_json(hourly_json)
    daily_data = pd.read_json(daily_json)
    
    # Convert the datetime column of the dataframes from Object to Datetime
    hourly_data['time'] = pd.to_datetime(hourly_data['time'], errors='coerce')
    daily_data['time'] = pd.to_datetime(daily_data['time'], errors='coerce')
    
    # Filter the hourly data to get the hourly data of only the current day
    today = datetime.today().date()
    hourly_data = hourly_data[hourly_data['time'].dt.date == today]

    # Initialize BigQuery Hook
    bq_hook = BigQueryHook(gcp_conn_id='google_cloud_default')
    
    # Define BigQuery params (project -> dataset -> tables)
    project_id = 'durable-river-442214-v0'
    dataset_id = 'weather_forecast_daily'
    hourly_table = 'hourly'
    daily_table = 'daily'
    
    # Get Client and upload data to BigQuery tables
    client = bq_hook.get_client()

    # Define schema using SchemaField
    hourly_schema = [
        bigquery.SchemaField('time', 'TIMESTAMP'),
        bigquery.SchemaField('temperature_2m', 'FLOAT'),
        bigquery.SchemaField('windspeed_10m', 'FLOAT'),
        bigquery.SchemaField('precipitation', 'FLOAT'),
        bigquery.SchemaField('relative_humidity_2m', 'FLOAT')
    ]
    
    daily_schema = [
        bigquery.SchemaField('time', 'DATE'),
        bigquery.SchemaField('temperature_2m_max', 'FLOAT'),
        bigquery.SchemaField('temperature_2m_min', 'FLOAT'),
        bigquery.SchemaField('precipitation_sum', 'FLOAT'),
        bigquery.SchemaField('wind_direction_10m_dominant', 'FLOAT')
    ]
    
    # Create job config for schema and write disposition
    hourly_job_config = bigquery.LoadJobConfig(
        schema=hourly_schema,
        write_disposition="WRITE_TRUNCATE"
    )
    
    daily_job_config = bigquery.LoadJobConfig(
        schema=daily_schema,
        write_disposition="WRITE_TRUNCATE"
    )

    try:
        client.load_table_from_dataframe( # Hourly data
            hourly_data,
            destination=f'{project_id}.{dataset_id}.{hourly_table}',
            job_config=hourly_job_config
        )
        
        client.load_table_from_dataframe( # Daily data
            daily_data,
            destination=f'{project_id}.{dataset_id}.{daily_table}',
            job_config=daily_job_config
        )
    except:
        raise Exception("Failed to upload data")
    
# Define the DAG and its arguments
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 11, 20),
    'retries': 1,
}

dag = DAG(
    'weather_data_pipeline',
    default_args=default_args,
    schedule_interval='@daily',  # Run daily
)

# Define tasks
fetch_task = PythonOperator(
    task_id='fetch_weather_data',
    python_callable=fetch_weather_data,
    dag=dag,
)

parse_task = PythonOperator(
    task_id='parse_weather_data',
    python_callable=parse_weather_data,
    op_args=[
        '{{ task_instance.xcom_pull(task_ids="fetch_weather_data")[0] }}', # Hourly data
        '{{ task_instance.xcom_pull(task_ids="fetch_weather_data")[1] }}', # Daily data
    ],
    dag=dag,
)

load_task = PythonOperator(
    task_id='load_weather_data',
    python_callable=upload_to_gcs,
    op_args=[
        '{{ task_instance.xcom_pull(task_ids="parse_weather_data")[0] }}', # Hourly data
        '{{ task_instance.xcom_pull(task_ids="parse_weather_data")[1] }}', # Daily data
    ],
    dag=dag,
)

# Set task dependencies
fetch_task >> parse_task >> load_task