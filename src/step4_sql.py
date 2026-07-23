"""
Step 4 — SQL Analysis (SQLite / MySQL-compatible syntax)
Output: data/processed/pharma.db + CSVs in data/outputs/
"""
import sys, os
sys.path.append(os.path.dirname(__file__))
import config
import pandas as pd
import sqlite3
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("STEP 4 — SQL Analysis")
print("=" * 60)

hcp = pd.read_parquet(config.HCP_RFM)
df  = pd.read_parquet(config.CLEAN_DATA)

conn = sqlite3.connect(config.DATABASE)
hcp.to_sql('hcp_master', conn, if_exists='replace', index=False)
df.to_sql('prescriptions', conn, if_exists='replace', index=False)
print("Tables loaded: hcp_master, prescriptions")

queries = {
"Q1 — Top 10 Prescribers by Volume": """
    SELECT npi, last_name, specialty, state, territory,
           ROUND(volume,2) AS total_drug_cost, frequency AS total_claims,
           ROUND(RFM_score,3) AS rfm_score
    FROM hcp_master ORDER BY volume DESC LIMIT 10
""",
"Q2 — Top 10 States by Drug Spend": """
    SELECT state, COUNT(DISTINCT npi) AS hcp_count,
           SUM(frequency) AS total_claims,
           ROUND(SUM(volume),0) AS total_drug_cost,
           ROUND(AVG(RFM_score),3) AS avg_rfm
    FROM hcp_master GROUP BY state ORDER BY total_drug_cost DESC LIMIT 10
""",
"Q3 — Brand vs Generic SoV by Territory": """
    SELECT territory, drug_type, COUNT(DISTINCT npi) AS hcp_count,
           SUM(total_claim_count) AS total_claims,
           ROUND(100.0*SUM(total_claim_count)/
             SUM(SUM(total_claim_count)) OVER (PARTITION BY territory),2) AS sov_pct
    FROM prescriptions GROUP BY territory, drug_type ORDER BY territory, drug_type DESC
""",
"Q4 — Specialty Breakdown by Territory": """
    SELECT territory, specialty, COUNT(DISTINCT npi) AS hcp_count,
           SUM(frequency) AS total_claims, ROUND(AVG(RFM_score),3) AS avg_rfm
    FROM hcp_master
    WHERE specialty IN ('Cardiology','Internal Medicine','Endocrinology')
    GROUP BY territory, specialty ORDER BY territory, total_claims DESC
""",
"Q5 — High-Value Dormant HCPs": """
    SELECT npi, last_name, specialty, state, territory, recency_year,
           frequency, ROUND(volume,0) AS volume, ROUND(RFM_score,3) AS rfm
    FROM hcp_master WHERE V_score=4 AND R_score=1 ORDER BY volume DESC LIMIT 10
""",
}

results = {}
for title, sql in queries.items():
    print(f"\n{'='*60}\n  {title}\n{'='*60}")
    r = pd.read_sql(sql, conn)
    print(r.to_string(index=False))
    results[title] = r

results["Q2 — Top 10 States by Drug Spend"].to_csv(config.OUT_TOP_STATES, index=False)
results["Q3 — Brand vs Generic SoV by Territory"].to_csv(config.OUT_BRAND_GENERIC, index=False)
results["Q4 — Specialty Breakdown by Territory"].to_csv(config.OUT_SPECIALTY, index=False)

conn.close()
print("\n✅ SQL analysis complete. CSVs saved.")