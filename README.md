# 🔬 BOMB Transistor ELT Pipeline
### Automated Data Pipeline · Berkeley EECS Dataset · Apache Airflow + dbt + AWS S3

---

## Overview

An end-to-end ELT pipeline ingesting the UC Berkeley **Berkeley Open MOS dataBase (BOMB)** —
96,600 transistor characterization data points in HDF5 format — into AWS S3, transformed via
dbt into a star schema analytical layer, and orchestrated by Apache Airflow running in Docker.

Built to surface thermal stability metrics across CMOS process variations and Monte Carlo
simulation profiles — mirroring real-world semiconductor QA workflows at companies like NVIDIA,
AMD, and Intel.

---

## Architecture

```
[BOMB HDF5 Files]
     │
     ▼
[Python Ingestion Script]  ──►  [AWS S3 Raw Zone]
     │                                │
     ▼                                ▼
[Apache Airflow DAG]         [AWS S3 Processed Zone]
     │                                │
     ▼                                ▼
[dbt Transformation]         [Parquet / Redshift]
     │
     ▼
[Star Schema Analytical Layer]
  ├── dim_device
  ├── dim_process_corner
  ├── dim_temperature
  └── fact_transistor_characterization
```

---

## Dataset Source

**Berkeley Open MOS dataBase (BOMB)**

- **Institution:** UC Berkeley, Department of Electrical Engineering and Computer Sciences (EECS)
- **Author:** Rohan Lageweg (2021), advised by Prof. Vladimir Stojanovic
- **Technical Report:** UCB/EECS-2021-192
- **Official Paper Page:** https://www2.eecs.berkeley.edu/Pubs/TechRpts/2021/EECS-2021-192.html
- **Full PDF:** https://www2.eecs.berkeley.edu/Pubs/TechRpts/2021/Archive/EECS-2021-192.pdf

> **Note on Dataset Access:** The BOMB dataset is referenced as open-source in the UC Berkeley
> technical report. The HDF5 data files are described in Section 4 ("BOMB Repository") of the PDF.
> Contact the EECS department at webteam@eecs.berkeley.edu if the direct data download is needed,
> or use the paper's SimData API framework to regenerate the dataset per Section 3 of the report.

**What the dataset contains:**
- 96,600 un-annotated transistor characterization data points
- Multi-dimensional arrays: I-V (current-voltage) and Y-V (admittance-voltage) parameters
- Dimensions: Monte Carlo variations × Temperature (-20°C, 27°C, 120°C) × Process corners × Device types × Terminal voltages (Vbs, Vgs, Vds)
- Format: HDF5 (`.hdf5`) files — loaded via the `SimData` Python API class provided in the paper

**Citation:**
```
@mastersthesis{Lageweg:EECS-2021-192,
    Author= {Lageweg, Rohan},
    Editor= {Stojanovic, Vladimir and Hakhamaneshi, Kourosh},
    Title= {Berkeley Open MOS dataBase (BOMB): A Dataset for Silicon Technology Representation Learning},
    School= {EECS Department, University of California, Berkeley},
    Year= {2021},
    Month= {Aug},
    Url= {http://www2.eecs.berkeley.edu/Pubs/TechRpts/2021/EECS-2021-192.html},
    Number= {UCB/EECS-2021-192}
}
```

---

## Tech Stack

| Layer | Tool |
|---|---|
| Orchestration | Apache Airflow 2.x |
| Containerization | Docker + Docker Compose |
| Cloud Storage | AWS S3 |
| Transformation | dbt (data build tool) |
| Data Format | HDF5 → Parquet |
| Language | Python 3.11 |
| Data Modeling | Star Schema |
| Data Quality | dbt tests (not_null, unique, accepted_values) |

---

## Folder Structure

```
project1_bomb_elt_pipeline/
├── README.md
├── .env.example
├── requirements.txt
├── data/
│   ├── raw/              # Raw HDF5 files from BOMB dataset
│   ├── processed/        # Intermediate cleaned files
│   └── parquet/          # Converted Parquet files for S3 upload
├── ingestion/
│   ├── download_bomb.py  # Script to load BOMB HDF5 files via SimData API
│   ├── hdf5_to_parquet.py
│   └── s3_uploader.py
├── dags/
│   ├── bomb_elt_dag.py   # Main Airflow DAG
│   └── utils.py
├── dbt_project/
│   ├── dbt_project.yml
│   ├── profiles.yml.example
│   ├── models/
│   │   ├── staging/
│   │   │   ├── stg_transistor_raw.sql
│   │   │   └── stg_process_corners.sql
│   │   └── marts/
│   │       ├── dim_device.sql
│   │       ├── dim_process_corner.sql
│   │       ├── dim_temperature.sql
│   │       └── fact_transistor_characterization.sql
│   ├── tests/
│   │   └── schema.yml    # dbt data quality tests
│   └── seeds/
│       └── thermal_thresholds.csv
├── docker/
│   ├── docker-compose.yml
│   └── Dockerfile.airflow
├── notebooks/
│   └── 01_eda_bomb_dataset.ipynb
├── scripts/
│   └── setup_aws.sh
├── docs/
│   └── architecture_diagram.png
└── tests/
    ├── test_ingestion.py
    └── test_transformations.py
```

---

## Getting Started

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/project1_bomb_elt_pipeline.git
cd project1_bomb_elt_pipeline

# 2. Copy environment variables
cp .env.example .env

# 3. Start Airflow + dependencies
docker-compose up -d

# 4. Download and ingest BOMB data
python ingestion/download_bomb.py
python ingestion/hdf5_to_parquet.py
python ingestion/s3_uploader.py

# 5. Run dbt transformations
cd dbt_project
dbt run
dbt test
```

---

## Key dbt Analytical Outputs

- **`fact_transistor_characterization`** — Core fact table with ibias, Y-parameters across all sweep dimensions
- **`dim_device`** — Device type dimension (low-voltage, high-voltage, normal)
- **`dim_process_corner`** — Process corner dimension (typical, fast, slow)
- **`dim_temperature`** — Temperature dimension with thermal threshold flags
- **Thermal Stability Metric** — Gold layer metric flagging which device/process combinations show highest variance under thermal stress

---

## Skills Demonstrated

`Apache Airflow` · `dbt` · `Docker` · `AWS S3` · `Python` · `SQL` · `HDF5` · `Parquet`
`Star Schema / Data Modeling` · `ELT Pipelines` · `Data Quality Testing` · `Semiconductor Domain`
