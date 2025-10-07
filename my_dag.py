from airflow import DAG
from airflow.models import Variable
from airflow.decorators import task
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
from datetime import datetime, timedelta
import requests

SNOWFLAKE_CONN_ID = "snowflake_conn"
ALPHA_VANTAGE_API_KEY = Variable.get("vantag_api_key")
SYMBOL = "goog"
DATABASE = "ASSIGNMENT3_KH"
SCHEMA = "RAW"

def get_snowflake_conn():
    hook = SnowflakeHook(
        snowflake_conn_id=SNOWFLAKE_CONN_ID , database= DATABASE
    )
    return hook.get_conn()

@task
def extract_data(): 
    url = (
        f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY"
        f"&symbol={SYMBOL}&apikey={ALPHA_VANTAGE_API_KEY}"
    )
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    data = r.json()
    results = []
    cutoff_date = datetime.now() - timedelta(days=90)
    for d, stock_info in data["Time Series (Daily)"].items():
        date_obj = datetime.strptime(d, "%Y-%m-%d")
        if date_obj >= cutoff_date:
            results.append((d, stock_info))
    return results

@task
def transform_data(raw_data):
    records = []
    for date_str, daily_info in raw_data:
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            record = (
                SYMBOL,
                date_obj,
                float(daily_info["1. open"]),
                float(daily_info["4. close"]),
                float(daily_info["2. high"]),
                float(daily_info["3. low"]),
                int(daily_info["5. volume"])
            )
            records.append(record)
        except Exception as e:
            print(f"Skipping {date_str}: {e}")
    return records

@task(task_id='load_data')
def load_data(records):
    conn = get_snowflake_conn()
    cursor = conn.cursor()
    target_table = f"{DATABASE}.{SCHEMA}.STOCK_PRICE"
    try:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DATABASE}")
        cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {DATABASE}.{SCHEMA}")
        cursor.execute("BEGIN;")
        cursor.execute(
            f"""CREATE TABLE IF NOT EXISTS {target_table} (
              symbol VARCHAR(10) NOT NULL,
              date DATE NOT NULL,
              open DECIMAL(12,4) NOT NULL,
              close DECIMAL(12,4) NOT NULL,
              high DECIMAL(12,4) NOT NULL,
              low DECIMAL(12,4) NOT NULL,
              volume BIGINT NOT NULL,
              PRIMARY KEY (symbol, date)
            );"""
        )
        cursor.execute(f"DELETE FROM {target_table}")
        insert_sql = f"""
            INSERT INTO {target_table} (symbol, date, open, close, high, low, volume)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.executemany(insert_sql, records)
        cursor.execute("COMMIT;")
        print(f"Loaded {len(records)} rows into {target_table}")
    except Exception as e:
        cursor.execute("ROLLBACK;")
        print(f"Error loading data: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

with DAG(
    dag_id="DATA-226_Homework5",
    start_date=datetime(2025, 10, 3),
    schedule="0 15 * * *",
    catchup=False,
    tags=["ETL_DAG_HOMEWORK"]
) as dag:
    raw = extract_data()
    transformed = transform_data(raw)
    load_data(transformed)
