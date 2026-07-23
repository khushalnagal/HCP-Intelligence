"""
Step 1 — Generate 1M+ CMS-mirrored Medicare Part D Records
Output: data/raw/cms_raw.parquet
"""
import sys, os
sys.path.append(os.path.dirname(__file__))
import config
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

np.random.seed(42)
N = 1_000_000

print("=" * 60)
print("STEP 1 — Generating 1M+ CMS Medicare Part D Records")
print("=" * 60)

states = ['CA','TX','FL','NY','PA','IL','OH','GA','NC','MI',
          'NJ','VA','WA','AZ','MA','TN','IN','MO','MD','WI',
          'CO','MN','SC','AL','LA','KY','OR','OK','CT','UT',
          'NV','AR','MS','KS','NM','NE','WV','ID','HI','NH',
          'ME','RI','MT','DE','SD','ND','AK','VT','WY','DC']
state_weights = np.array([
    120,110,100,95,70,65,60,55,52,50,48,45,43,40,38,35,33,30,28,27,
    25,24,22,21,20,19,18,17,16,15,14,13,12,11,10,9,8,7,6,5,
    4,4,3,3,2,2,2,2,1,1], dtype=float)
state_weights /= state_weights.sum()

raw_specialties = [
    'Cardiology','CARDIOLOGY','Cardiologist','cardiology',
    'Internal Medicine','INTERNAL MEDICINE','Int. Medicine','internal medicine',
    'Family Practice','Family Medicine','FAMILY PRACTICE','family practice',
    'Endocrinology','ENDOCRINOLOGY','Endocrinologist','endocrinology',
    'Geriatric Medicine','Geriatrics','GERIATRICS','geriatric medicine',
    'Nephrology','NEPHROLOGY','nephrologist',
    'Neurology','NEUROLOGY','Neurologist',
    'General Practice','GENERAL PRACTICE','general practice',
    'Nurse Practitioner','NURSE PRACTITIONER','NP',
    'Physician Assistant','PA','PHYSICIAN ASSISTANT',
    None, None, None
]
spec_weights = np.array([
    8,6,5,4, 9,7,5,4, 8,7,6,4, 6,5,4,3, 4,3,2,2,
    3,2,2,   3,2,2,   3,2,2,   4,3,2,   3,2,2,   2,2,1
], dtype=float)
spec_weights /= spec_weights.sum()

cardio_drugs = [
    ('Lisinopril','generic'),('LISINOPRIL','generic'),
    ('Atorvastatin','generic'),('ATORVASTATIN','generic'),
    ('Metoprolol Succinate','generic'),('METOPROLOL SUCCINATE','generic'),
    ('Amlodipine','generic'),('AMLODIPINE','generic'),
    ('Losartan Potassium','generic'),('Carvedilol','generic'),
    ('Lipitor','brand'),('LIPITOR','brand'),
    ('Crestor','brand'),('CRESTOR','brand'),
    ('Entresto','brand'),('Eliquis','brand'),
    ('Xarelto','brand'),('Jardiance','brand'),
    ('Farxiga','brand'),('Repatha','brand'),('Praluent','brand'),
]
drug_names = [d[0] for d in cardio_drugs]
drug_types = [d[1] for d in cardio_drugs]
drug_w     = np.array([10,8,9,7,8,6,7,5,6,5,6,5,5,4,4,5,4,3,2,2,2], dtype=float)
drug_w    /= drug_w.sum()

null_mask         = np.random.choice([True,False], size=N, p=[0.03,0.97])
years             = np.random.choice([2019,2020,2021,2022], size=N, p=[0.15,0.20,0.30,0.35])
total_claim_count = np.random.lognormal(4.5,1.2,N).astype(int)+1
total_drug_cost   = total_claim_count * np.random.lognormal(4.0,0.8,N)
bene_count        = (total_claim_count * np.random.uniform(0.3,0.9,N)).astype(int)+1

# Intentional dirty data
bad_cost          = np.random.choice(N, size=int(N*0.005), replace=False)
bad_claim         = np.random.choice(N, size=int(N*0.003), replace=False)
total_drug_cost[bad_cost]    = -total_drug_cost[bad_cost]
total_claim_count[bad_claim] = 0

valid_npis = np.random.randint(1000000000,1999999999, size=int(N*0.97))
full_npis  = np.random.choice(valid_npis, size=N)
npi_vals   = [None if null_mask[i] else int(full_npis[i]) for i in range(N)]

drug_idx      = np.random.choice(len(drug_names), size=N, p=drug_w)
drugs_col     = np.array(drug_names)[drug_idx]
drug_type_col = np.array(drug_types)[drug_idx]

print("Building DataFrame... (takes ~20s)")
df = pd.DataFrame({
    'npi'                          : npi_vals,
    'nppes_provider_last_org_name' : [f"DR_{np.random.randint(1000,9999)}" for _ in range(N)],
    'nppes_provider_first_name'    : np.random.choice(['JAMES','MARY','ROBERT','PATRICIA','JOHN',
                                     'JENNIFER','MICHAEL','LINDA',None], size=N,
                                     p=[.13,.12,.12,.11,.11,.10,.10,.10,.11]),
    'nppes_provider_state'         : np.random.choice(states, size=N, p=state_weights),
    'nppes_provider_country'       : np.where(np.random.random(N)>0.01,'US','XX'),
    'specialty_description'        : np.random.choice(raw_specialties, size=N, p=spec_weights),
    'drug_name'                    : drugs_col,
    'drug_type'                    : drug_type_col,
    'year'                         : years,
    'total_claim_count'            : total_claim_count,
    'total_30_day_fill_count'      : (total_claim_count*np.random.uniform(0.7,1.0,N)).astype(int),
    'total_drug_cost'              : np.round(total_drug_cost,2),
    'total_day_supply'             : (total_claim_count*np.random.randint(20,90,N)),
    'bene_count'                   : bene_count,
    'ge65_suppress_flag'           : np.random.choice(['','#',None], size=N, p=[0.88,0.10,0.02]),
})

print(f"Raw shape      : {df.shape}")
print(f"Null NPIs      : {df['npi'].isna().sum():,}")
print(f"Null specs     : {df['specialty_description'].isna().sum():,}")
print(f"Negative costs : {(df['total_drug_cost']<0).sum():,}")
print(f"Zero claims    : {(df['total_claim_count']==0).sum():,}")

df.to_parquet(config.RAW_DATA, index=False)
print(f"\n✅ Saved → {config.RAW_DATA}")