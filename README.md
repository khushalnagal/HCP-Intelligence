# Pharma HCP Prescriber Intelligence and Targeting System

identifying which doctors (HCPs) are high-priority targets for a sales rep using Medicare Part D prescribing data.

## Project Structure

    pharma_hcp_intelligence/
        src/            Python scripts for each pipeline stage
        data/
            raw/        Generated CMS-mirrored records (not tracked in git)
            processed/  Intermediate files (not tracked in git)
            outputs/    Final CSVs and business summary
        charts/         Matplotlib/Seaborn visualizations
        sql/            SQL queries used for analysis
        run_all.py      Runs full pipeline in one command

## Setup

    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt
    python run_all.py

## Pipeline

1. Generate 1M+ CMS-mirrored Medicare Part D records
2. Clean and normalize (null handling, specialty mapping, territory assignment)
3. Engineer RFM features per HCP (Recency, Frequency, Volume)
4. SQL analysis (top prescribers, brand vs generic share of voice)
5. KMeans clustering into 4 segments (High Priority / Growth / Maintenance / Dormant)
6. YoY trend classification plus win-back recovery model
7. Charts and ranked target list output

## Stack

Python - Pandas - NumPy - Scikit-learn - Matplotlib - Seaborn - SQL
