# DATA-226 Homework 5: Porting Homework #5 to Airflow

All tasks use the @task decorator with proper dependencies and configurations.

## 📋 Overview
This project ports Homework #4 into an Airflow DAG that:
- Extracts stock data from Alpha Vantage API
- Transforms it
- Loads it into Snowflake

## ⚙️ Setup
1. Start Airflow using Docker Compose:
   ```bash
   docker compose up -d
