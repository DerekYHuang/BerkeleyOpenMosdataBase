-- load_parquet.sql
-- Seeds the Parquet file into DuckDB as a table
{{ config(materialized='table') }}

select * from read_parquet('../data/parquet/bomb_transistor_flat.parquet')
