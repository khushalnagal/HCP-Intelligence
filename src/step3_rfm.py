"""
Step 3 — RFM Feature Engineering per HCP
Output: data/processed/hcp_rfm.parquet
"""
import sys, os
sys.path.append(os.path.dirname(__file__))
import config
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("STEP 3 — RFM Feature Engineering per HCP")
print("=" * 60)

df = pd.read_parquet(config.CLEAN_DATA)
print(f"Loaded: {len(df):,} records | {df['npi'].nunique():,} unique HCPs")

brand_df = (df[df['drug_type']=='brand'].groupby('npi')['total_claim_count']
              .sum().rename('brand_claims'))

hcp = df.groupby('npi').agg(
    last_name=('last_name','first'), first_name=('first_name','first'),
    state=('state','first'), territory=('territory','first'),
    specialty=('specialty','first'), recency_year=('year','max'),
    frequency=('total_claim_count','sum'), volume=('total_drug_cost','sum'),
    unique_drugs=('drug_name','nunique'), patient_count=('bene_count','sum'),
    years_active=('year','nunique'),
).reset_index()

hcp = hcp.merge(brand_df, on='npi', how='left')
hcp['brand_claims'] = hcp['brand_claims'].fillna(0)
hcp['brand_sov']    = (hcp['brand_claims']/hcp['frequency']).clip(0,1).round(4)

year_to_r = {2019:1, 2020:2, 2021:3, 2022:4}
hcp['R_score'] = hcp['recency_year'].map(year_to_r).fillna(1).astype(int)
hcp['F_score'] = pd.qcut(hcp['frequency'].rank(method='first'), q=4, labels=[1,2,3,4]).astype(int)
hcp['V_score'] = pd.qcut(hcp['volume'].rank(method='first'), q=4, labels=[1,2,3,4]).astype(int)

hcp['RFM_score'] = (hcp['R_score']*0.25 + hcp['F_score']*0.35 + hcp['V_score']*0.40).round(3)

scaler = StandardScaler()
hcp[['R_norm','F_norm','V_norm']] = scaler.fit_transform(hcp[['R_score','F_score','V_score']])

print(f"\nRFM Sanity Checks:")
print(f"  R_score range : {hcp['R_score'].min()} – {hcp['R_score'].max()}  ← must be 1-4")
print(f"  RFM_score max : {hcp['RFM_score'].max()}  ← must be 4.0")
print(f"  Duplicate NPIs: {hcp['npi'].duplicated().sum()}  ← must be 0")

hcp.to_parquet(config.HCP_RFM, index=False)
print(f"\n✅ Saved → {config.HCP_RFM} — {len(hcp):,} HCPs")