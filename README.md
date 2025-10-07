# DATA-226 Homework 5: Porting Homework #4 to Airflow

## 📋 Overview
This project ports Homework #4 into an Airflow DAG that:
- Extracts stock data from Alpha Vantage API
- Transforms it
- Loads it into Snowflake

## ⚙️ Setup
1. Start Airflow using Docker Compose:
   ```bash
   docker compose up -d
