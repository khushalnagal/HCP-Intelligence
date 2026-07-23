"""
Step 2 — Clean & Normalize CMS Data
Output: data/processed/cms_clean.parquet
"""
import sys, os
sys.path.append(os.path.dirname(__file__))
import config
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("STEP 2 — Data Cleaning & Normalization")
print("=" * 60)

df = pd.read_parquet(config.RAW_DATA)
print(f"\n[RAW]  Rows: {len(df):,}")

before = len(df)
df = df.dropna(subset=['npi'])
df['npi'] = df['npi'].astype(np.int64)
print(f"[1] Dropped null NPIs       : -{before-len(df):>7,}  →  {len(df):,} remain")

before = len(df)
df = df[df['nppes_provider_country'] == 'US']
print(f"[2] Dropped non-US records  : -{before-len(df):>7,}  →  {len(df):,} remain")

before = len(df)
df = df[df['ge65_suppress_flag'] != '#']
print(f"[3] Dropped suppressed (#)  : -{before-len(df):>7,}  →  {len(df):,} remain")

before = len(df)
df = df[df['total_claim_count'] > 0]
print(f"[4] Dropped zero claims     : -{before-len(df):>7,}  →  {len(df):,} remain")

before = len(df)
df = df[df['total_drug_cost'] > 0]
print(f"[5] Dropped negative costs  : -{before-len(df):>7,}  →  {len(df):,} remain")

SPECIALTY_MAP = {
    'cardiology':'Cardiology','cardiologist':'Cardiology',
    'internal medicine':'Internal Medicine','int. medicine':'Internal Medicine',
    'family practice':'Family Practice','family medicine':'Family Practice',
    'endocrinology':'Endocrinology','endocrinologist':'Endocrinology',
    'geriatric medicine':'Geriatric Medicine','geriatrics':'Geriatric Medicine',
    'nephrologist':'Nephrology','neurologist':'Neurology',
    'general practice':'General Practice',
    'np':'Nurse Practitioner','pa':'Physician Assistant',
}
DRUG_TO_SPECIALTY = {
    'Lisinopril':'Internal Medicine','Atorvastatin':'Internal Medicine',
    'Metoprolol Succinate':'Cardiology','Amlodipine':'Internal Medicine',
    'Losartan Potassium':'Internal Medicine','Carvedilol':'Cardiology',
    'Lipitor':'Cardiology','Crestor':'Internal Medicine','Entresto':'Cardiology',
    'Eliquis':'Cardiology','Xarelto':'Cardiology','Jardiance':'Endocrinology',
    'Farxiga':'Endocrinology','Repatha':'Cardiology','Praluent':'Cardiology',
}

df['specialty_description'] = (
    df['specialty_description'].fillna('').str.strip().str.lower()
    .map(lambda x: SPECIALTY_MAP.get(x, x.title() if x else None))
)
null_spec = df['specialty_description'].isna() | (df['specialty_description']=='')
df.loc[null_spec,'specialty_description'] = (
    df.loc[null_spec,'drug_name'].str.title().map(DRUG_TO_SPECIALTY).fillna('General Practice')
)
print(f"\n[6] Specialty normalized — unique values: {df['specialty_description'].nunique()}")
print(f"    Unknown remaining: {(df['specialty_description']=='Unknown').sum()}  ← must be 0")

df['drug_name_clean'] = df['drug_name'].str.strip().str.title()

TERRITORY_MAP = {
    'CA':'West','WA':'West','OR':'West','NV':'West','AZ':'West','CO':'West',
    'UT':'West','MT':'West','ID':'West','WY':'West',
    'TX':'South','FL':'South','GA':'South','NC':'South','SC':'South','AL':'South',
    'TN':'South','MS':'South','LA':'South','AR':'South','OK':'South','VA':'South',
    'WV':'South','KY':'South','DC':'South',
    'NY':'Northeast','PA':'Northeast','NJ':'Northeast','MA':'Northeast','CT':'Northeast',
    'RI':'Northeast','NH':'Northeast','VT':'Northeast','ME':'Northeast','DE':'Northeast','MD':'Northeast',
    'IL':'Midwest','OH':'Midwest','MI':'Midwest','IN':'Midwest','WI':'Midwest','MN':'Midwest',
    'MO':'Midwest','IA':'Midwest','KS':'Midwest','NE':'Midwest','ND':'Midwest','SD':'Midwest',
    'NM':'Southwest','HI':'Pacific','AK':'Pacific',
}
df['territory'] = df['nppes_provider_state'].map(TERRITORY_MAP).fillna('Other')
df['nppes_provider_first_name'] = df['nppes_provider_first_name'].fillna('UNKNOWN')

df_clean = df[[
    'npi','nppes_provider_last_org_name','nppes_provider_first_name',
    'nppes_provider_state','territory','specialty_description',
    'drug_name_clean','drug_type','year',
    'total_claim_count','total_drug_cost','bene_count'
]].rename(columns={
    'nppes_provider_last_org_name':'last_name',
    'nppes_provider_first_name':'first_name',
    'nppes_provider_state':'state',
    'specialty_description':'specialty',
    'drug_name_clean':'drug_name',
})

df_clean.to_parquet(config.CLEAN_DATA, index=False)
print(f"\nClean records  : {len(df_clean):,}")
print(f"Unique HCPs    : {df_clean['npi'].nunique():,}")
print(f"✅ Saved → {config.CLEAN_DATA}")