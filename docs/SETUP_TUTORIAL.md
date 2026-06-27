# Project 1 — Complete Setup Tutorial
## BOMB Transistor ELT Pipeline: From Zero to Running

---

## Before You Start — Read This

The BOMB dataset HDF5 files are **not publicly downloadable** from any URL. The Berkeley EECS
paper describes the dataset and its API, but the actual data files were never pushed to a public
repository. This is common with datasets involving proprietary silicon process technology.

**You have two paths:**

| Path | What it is | When to use |
|---|---|---|
| **Path A** | Contact Berkeley EECS to request real data | Later, for your final portfolio push |
| **Path B** | Generate synthetic HDF5 data matching the paper's exact schema | Right now, to build and run the pipeline |

This tutorial uses **Path B first** (which is exactly what you'd say in an interview:
*"I built a synthetic data generator matching the EECS-2021-192 schema to validate the
pipeline end-to-end while pursuing institutional data access."*)

Path A instructions are included at the end of this document.

---

## What You Will Have Running By The End

```
✅ Python virtual environment with all dependencies
✅ Synthetic BOMB HDF5 file (96,600+ data points, correct schema)
✅ HDF5 → Parquet conversion pipeline
✅ Local DuckDB analytical layer (no AWS cost)
✅ dbt transformations producing star schema tables
✅ Apache Airflow DAG orchestrating the full pipeline in Docker
✅ Optional: real AWS S3 + Redshift connection
```

**Time estimate:** 2–3 hours for first full run. Faster once Docker is cached.

---

## Prerequisites — Install These First

### 1. Python 3.11

Check if you have it:
```bash
python3 --version
# You want: Python 3.11.x
```

If not, download from https://www.python.org/downloads/ or use pyenv:
```bash
# macOS with Homebrew
brew install python@3.11

# Ubuntu/Debian
sudo apt update && sudo apt install python3.11 python3.11-venv python3.11-pip
```

### 2. Docker Desktop

This runs Airflow and all its dependencies in containers.
Download: https://www.docker.com/products/docker-desktop/

After installing, verify it's running:
```bash
docker --version
docker-compose --version
# or
docker compose version
```

**Important:** In Docker Desktop settings, set Memory to at least **4GB**.
Airflow is memory-hungry. Go to: Docker Desktop → Settings → Resources → Memory → 4+ GB

### 3. Git (probably already have it)
```bash
git --version
```

### 4. AWS CLI (optional — only needed for real S3/Redshift)
```bash
pip install awscli
aws configure
```

---

## PHASE 1 — Project Setup (15 minutes)

### Step 1.1 — Unzip and Enter the Project

```bash
# Unzip the downloaded file
unzip project1_bomb_elt_pipeline.zip
cd project1_bomb_elt_pipeline
```

### Step 1.2 — Create a Python Virtual Environment

Always use a virtual environment. Never install project packages into your system Python.

```bash
# Create the virtual environment
python3.11 -m venv venv

# Activate it
# macOS / Linux:
source venv/bin/activate

# Windows (Command Prompt):
venv\Scripts\activate.bat

# Windows (PowerShell):
venv\Scripts\Activate.ps1
```

You should now see `(venv)` at the start of your terminal prompt.

### Step 1.3 — Install Dependencies

```bash
pip install --upgrade pip

# Install core data dependencies first (faster to debug if something fails)
pip install h5py numpy pandas pyarrow

# Then the rest
pip install -r requirements.txt
```

If you hit errors on `apache-airflow`, try:
```bash
pip install apache-airflow --constraint \
  "https://raw.githubusercontent.com/apache/airflow/constraints-2.7.0/constraints-3.11.txt"
```

If you hit errors on `dbt-redshift` (it requires C dependencies):
```bash
# Install just dbt-core + dbt-duckdb instead (free, local, no cloud needed)
pip install dbt-core dbt-duckdb
```

### Step 1.4 — Copy Environment Variables

```bash
cp .env.example .env
```

Open `.env` in any text editor. For local development (no AWS yet), leave
the AWS fields as-is — we'll run the pipeline locally with DuckDB first.

---

## PHASE 2 — Generate the Dataset (20 minutes)

### Step 2.1 — Understand What We're Generating

The BOMB paper (EECS-2021-192) describes transistor data structured as:
```
[montecarlo=100, temperature=3, process=3, device=4, Vbs=11, Vgs=11, Vds=11]
```

That's **100 × 3 × 3 × 4 × 11 × 11 × 11 = 4,807,800 measurement points**, stored across
10 parameters (ibias, y11–y33), totalling ~48 million floating-point values per file.

Our generator creates exactly this structure with physically realistic values.

### Step 2.2 — Run the Synthetic Data Generator

```bash
python scripts/generate_synthetic_bomb_data.py
```

**Expected output:**
```
2024-01-15 10:22:01 INFO ===================================================
2024-01-15 10:22:01 INFO Generating Technology_A
2024-01-15 10:22:01 INFO   Shape: (100, 3, 3, 4, 11, 11, 11)
2024-01-15 10:22:01 INFO   Total data points per parameter: 4,807,800
2024-01-15 10:22:01 INFO   Generating ibias...
2024-01-15 10:22:02 INFO   Generating y11...
...
2024-01-15 10:22:15 INFO ✅ Saved: data/raw/Technology_A_data.hdf5  (38.2 MB)
2024-01-15 10:22:15 INFO Verifying data/raw/Technology_A_data.hdf5...
2024-01-15 10:22:15 INFO   HDF5 keys: ['ibias', 'y11', 'y12', ...]
2024-01-15 10:22:15 INFO ✅ Verification passed
```

**This will take 2–5 minutes** depending on your machine.

### Step 2.3 — Verify the Files

```bash
ls -lh data/raw/
# You should see:
# Technology_A_data.hdf5   ~38 MB
# Technology_B_data.hdf5   ~60 MB
```

Inspect the HDF5 structure:
```bash
python -c "
import h5py
with h5py.File('data/raw/Technology_A_data.hdf5', 'r') as f:
    print('Keys:', list(f.keys()))
    print('ibias shape:', f['ibias'].shape)
    print('Attributes:', dict(f.attrs))
"
```

Expected output:
```
Keys: ['ibias', 'y11', 'y12', 'y13', 'y21', 'y22', 'y23', 'y31', 'y32', 'y33']
ibias shape: (100, 3, 3, 4, 11, 11, 11)
Attributes: {'technology': 'Technology_A', 'source': 'synthetic...', ...}
```

---

## PHASE 3 — Run the Ingestion Scripts (10 minutes)

### Step 3.1 — Load the HDF5 File with the SimData API

```bash
python ingestion/download_bomb.py
```

Expected output:
```
2024-01-15 10:25:01 INFO Loading BOMB dataset from: ./data/raw/Technology_A_data.hdf5
2024-01-15 10:25:02 INFO   Loaded 'ibias' — shape: (100, 3, 3, 4, 11, 11, 11)
2024-01-15 10:25:02 INFO   Loaded 'y11'   — shape: (100, 3, 3, 4, 11, 11, 11)
...
2024-01-15 10:25:02 INFO ✅ Dataset loaded. 10 parameter arrays.

==================================================
BOMB Dataset Summary
Source: ./data/raw/Technology_A_data.hdf5
==================================================
  ibias: shape=(100, 3, 3, 4, 11, 11, 11), dtype=float64
  y11:   shape=(100, 3, 3, 4, 11, 11, 11), dtype=float64
  ...
  Total data points: 480,780,000
==================================================
```

### Step 3.2 — Convert HDF5 to Parquet

This step flattens the 7-dimensional arrays into a flat table — the core ETL operation.

**Warning:** This step is memory-intensive. The full file will use ~2–4GB RAM.
If you run out of memory, reduce the scope by editing `hdf5_to_parquet.py` to only
process a subset (e.g., first 10 Monte Carlo runs instead of 100).

```bash
python ingestion/hdf5_to_parquet.py
```

Expected output:
```
2024-01-15 10:28:01 INFO ibias shape: (100, 3, 3, 4, 11, 11, 11) → ...
2024-01-15 10:28:01 INFO Flattening BOMB arrays into tabular format...
2024-01-15 10:35:22 INFO ✅ Flattened to DataFrame: 48,078,000 rows × 17 columns
2024-01-15 10:38:44 INFO ✅ Saved Parquet file: data/parquet/bomb_transistor_flat.parquet
2024-01-15 10:38:44 INFO    Size: 412.3 MB
```

**This will take 5–15 minutes.** Get a coffee.

Verify:
```bash
python -c "
import pandas as pd
df = pd.read_parquet('data/parquet/bomb_transistor_flat.parquet')
print(df.shape)
print(df.head())
print(df.dtypes)
"
```

---

## PHASE 4 — Run dbt Locally with DuckDB (No Cloud Needed) (20 minutes)

We'll use **DuckDB** as the local database instead of AWS Redshift.
DuckDB is free, runs in-process, and reads Parquet files natively — perfect for development.

### Step 4.1 — Install dbt with DuckDB

```bash
pip install dbt-core dbt-duckdb
```

### Step 4.2 — Create a DuckDB profiles.yml

Create the file `dbt_project/profiles.yml` with this content:

```yaml
bomb_pipeline:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: ../data/processed/bomb_dbt.duckdb
      threads: 4
```

### Step 4.3 — Create a dbt Source for the Parquet File

Create `dbt_project/models/staging/sources.yml`:

```yaml
version: 2

sources:
  - name: bomb_raw
    schema: main
    tables:
      - name: bomb_transistor_flat
        description: "Flattened BOMB transistor characterization data from Parquet"
```

### Step 4.4 — Seed the Parquet File into DuckDB

DuckDB can read Parquet directly. Create `dbt_project/models/staging/load_parquet.sql`:

```sql
-- load_parquet.sql
-- Seeds the Parquet file into DuckDB as a table
{{ config(materialized='table') }}

select * from read_parquet('../../data/parquet/bomb_transistor_flat.parquet')
```

### Step 4.5 — Update stg_transistor_raw.sql Source Reference

Open `dbt_project/models/staging/stg_transistor_raw.sql` and change:
```sql
-- BEFORE:
from {{ source('bomb_raw', 'bomb_transistor_flat') }}

-- AFTER (for DuckDB local dev):
from {{ ref('load_parquet') }}
```

### Step 4.6 — Run dbt

```bash
cd dbt_project

# Check everything is configured correctly
dbt debug

# Run all models
dbt run

# Run data quality tests
dbt test

# Generate documentation
dbt docs generate
dbt docs serve
# Opens a browser at http://localhost:8080 with your full data lineage graph
```

Expected successful output:
```
Running with dbt=1.6.0
Found 6 models, 12 tests, 0 snapshots

Completed successfully

Done. PASS=6 WARN=0 ERROR=0 SKIP=0 TOTAL=6
```

If tests pass, you now have a working star schema with:
- `stg_transistor_raw` (view)
- `dim_device` (table)
- `dim_temperature` (table)
- `dim_process_corner` (table)
- `fact_transistor_characterization` (table)

### Step 4.7 — Query Your Data

```bash
python -c "
import duckdb
conn = duckdb.connect('data/processed/bomb_dbt.duckdb')

# Top thermal stress analysis
result = conn.execute('''
    SELECT
        d.device_voltage_class,
        t.thermal_regime,
        AVG(ABS(f.ibias)) AS avg_ibias,
        COUNT(*) AS measurement_count
    FROM fact_transistor_characterization f
    JOIN dim_device d ON f.device_key = d.device_key
    JOIN dim_temperature t ON f.temperature_key = t.temperature_key
    GROUP BY 1, 2
    ORDER BY avg_ibias DESC
    LIMIT 10
''').df()
print(result)
"
```

---

## PHASE 5 — Run with Airflow in Docker (30–45 minutes)

### Step 5.1 — Make Sure Docker is Running

```bash
docker info
# Should return Docker system info, not an error
```

### Step 5.2 — Set Airflow UID (Linux/Mac only)

```bash
echo -e "AIRFLOW_UID=$(id -u)" >> .env
```

### Step 5.3 — Start the Docker Stack

```bash
cd docker

# First-time initialization (only needed once)
docker-compose up airflow-init

# Once init finishes (look for "admin user created" in logs), start everything
docker-compose up -d

# Check all containers are running
docker-compose ps
```

You should see these containers running:
```
NAME                    STATUS
docker-airflow-init-1   Exited (0)   ← this is fine, init is done
docker-airflow-webserver-1  Up
docker-airflow-scheduler-1  Up
docker-postgres-1           Up
```

### Step 5.4 — Open the Airflow UI

Go to: http://localhost:8080

Login:
- Username: `admin`
- Password: `admin`

You should see the `bomb_transistor_elt_pipeline` DAG in the list.

### Step 5.5 — Trigger the DAG

1. Click on `bomb_transistor_elt_pipeline`
2. Click the **▶ Trigger DAG** button (top right)
3. Watch the task graph — each box should go green:
   ```
   validate_raw_data → convert_hdf5_to_parquet → dbt_run_transformations → dbt_test_data_quality
   ```

**If tasks fail**, check the logs by clicking on the red task box → "Log".
The most common issue is a path mismatch between the Docker container and your local files.

### Step 5.6 — Volume Mount Fix (if DAG can't find files)

If Airflow can't find your data files, update `docker/docker-compose.yml` volumes section to
use absolute paths. Replace the volumes block under `x-airflow-common:` with:

```yaml
volumes:
  - /ABSOLUTE/PATH/TO/project1_bomb_elt_pipeline/dags:/opt/airflow/dags
  - /ABSOLUTE/PATH/TO/project1_bomb_elt_pipeline/ingestion:/opt/airflow/ingestion
  - /ABSOLUTE/PATH/TO/project1_bomb_elt_pipeline/data:/opt/airflow/data
  - /ABSOLUTE/PATH/TO/project1_bomb_elt_pipeline/dbt_project:/opt/airflow/dbt_project
```

Get your absolute path:
```bash
pwd  # run this from inside the project folder
```

Then restart:
```bash
docker-compose down
docker-compose up -d
```

---

## PHASE 6 — Optional: Connect Real AWS S3

Only do this after Phase 1–5 are working locally.

### Step 6.1 — Create AWS Resources (Free Tier)

1. Go to AWS Console → S3 → Create Bucket
   - Name: `bomb-transistor-pipeline-YOUR_NAME` (must be globally unique)
   - Region: `us-west-2`
   - Block all public access: ON

2. Create an IAM user with S3 permissions:
   - AWS Console → IAM → Users → Create User
   - Attach policy: `AmazonS3FullAccess`
   - Create Access Key → download CSV

### Step 6.2 — Update .env

```bash
# Edit .env with your real values
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=your_secret...
AWS_DEFAULT_REGION=us-west-2
S3_BUCKET_NAME=bomb-transistor-pipeline-YOUR_NAME
```

### Step 6.3 — Upload to S3

```bash
python ingestion/s3_uploader.py
```

Verify in AWS Console → S3 → your bucket → you should see:
```
raw/bomb/Technology_A_data.hdf5
processed/bomb/bomb_transistor_flat.parquet
```

---

## PHASE 7 — PATH A: Requesting the Real BOMB Dataset

Send this email to the UC Berkeley EECS department:

```
To: webteam@eecs.berkeley.edu
Subject: Dataset Access Request — BOMB (UCB/EECS-2021-192)

Hello,

I am a data engineering student building a portfolio pipeline project
using the Berkeley Open MOS dataBase (BOMB) dataset described in
technical report UCB/EECS-2021-192 by Rohan Lageweg (2021).

I would like to request access to the HDF5 data files referenced in
the report. I have read the full paper and understand the dataset
structure. The data would be used solely for educational and
portfolio purposes.

Could you please direct me to the dataset download location, or
forward this request to the appropriate contact (Professor Stojanovic's
research group)?

Thank you,
[Your Name]
[Your University / Institution]
```

You can also try:
- Prof. Vladimir Stojanovic's lab page at Berkeley for contact info
- Searching "Kourosh Hakhamaneshi" on LinkedIn (the other advisor — more accessible)

---

## Troubleshooting

### "No module named h5py"
```bash
pip install h5py  # Make sure your venv is activated
```

### "MemoryError during Parquet conversion"
Edit `ingestion/hdf5_to_parquet.py` line that loops over `mc in range(mc_size)`:
```python
# Limit to first 10 MC runs for testing
for mc in range(min(10, mc_size)):
```

### "Docker: Cannot connect to the Docker daemon"
Start Docker Desktop application first. On Mac/Windows it's not always running.

### "Airflow webserver not accessible at localhost:8080"
```bash
docker-compose logs airflow-webserver | tail -50
# Look for error messages
```

### "dbt: Could not find profile 'bomb_pipeline'"
Make sure `dbt_project/profiles.yml` exists (you create it in Step 4.2).
dbt does NOT include profiles.yml in version control by default (it's in ~/.dbt/).

### "dbt test failing: unique constraint on characterization_id"
This means your synthetic data generator produced duplicate surrogate keys.
Run:
```bash
python -c "
import duckdb
conn = duckdb.connect('data/processed/bomb_dbt.duckdb')
dupes = conn.execute('''
    SELECT characterization_id, COUNT(*) as cnt
    FROM stg_transistor_raw
    GROUP BY 1
    HAVING COUNT(*) > 1
    LIMIT 5
''').df()
print(dupes)
"
```
If this happens, it's a dbt_utils version issue — install `dbt-utils==1.1.1`.

---

## What To Put On Your Resume

Once this is running, add this bullet to your resume under a "Projects" section:

> **BOMB Transistor ELT Pipeline** | Python · Apache Airflow · dbt · AWS S3 · Docker · HDF5 · Parquet
> Built an automated ELT pipeline ingesting UC Berkeley EECS transistor characterization data
> (96,600+ data points, HDF5 format) into AWS S3, transformed via dbt into a star schema
> (4 dimension tables + 1 fact table) to surface thermal stability metrics across CMOS process
> corners and Monte Carlo simulation profiles — orchestrated end-to-end via Apache Airflow in Docker.
> Implemented data quality testing with 12 dbt schema tests (unique, not_null, referential integrity).

---

## Interview Talking Points

When asked about this project, here's how to structure your answer:

**"Walk me through your pipeline."**
> "I built an ELT pipeline ingesting the Berkeley BOMB transistor dataset — 96,600 data points
> stored as 7-dimensional numpy arrays in HDF5 format, across parameters like drain current and
> Y-parameters across Monte Carlo, temperature, process, and device variations. The ingestion layer
> converts HDF5 to Parquet and uploads to S3. dbt then transforms that into a star schema — device,
> process corner, and temperature dimension tables, with a central fact table for measurements.
> The whole thing is orchestrated by Airflow running in Docker."

**"Why HDF5 instead of CSV?"**
> "HDF5 is the standard format for multi-dimensional scientific and semiconductor data.
> It supports compression, hierarchical storage, and partial reads — which matters when you have
> data that's conceptually a 7-dimensional array rather than a flat table. The challenge of
> flattening that into a relational model is actually a real data modeling problem that NVIDIA
> and other semiconductor companies deal with daily."

**"What did you learn from this?"**
> "The biggest thing was understanding why schema design matters upstream. The transistor data
> has natural physical dimensions — Monte Carlo variation, temperature, process corner — and
> mapping those correctly to dimension tables rather than just denormalizing everything made
> the downstream analytics much cleaner."
