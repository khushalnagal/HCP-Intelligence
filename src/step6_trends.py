"""
Step 6 — YoY Trend Classification + Win-Back Model
Output: data/processed/hcp_final.parquet + dormant_winback.parquet
"""
import sys, os
sys.path.append(os.path.dirname(__file__))
import config
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("STEP 6 — YoY Trend + Win-Back Model")
print("=" * 60)

df  = pd.read_parquet(config.CLEAN_DATA)
hcp = pd.read_parquet(config.HCP_SEGMENTED)

annual = (df.groupby(['npi','year'])['total_claim_count']
            .sum().reset_index().sort_values(['npi','year']))

multi_year = annual.groupby('npi')['year'].count()
multi_year = multi_year[multi_year >= 2].index
annual_multi = annual[annual['npi'].isin(multi_year)]
print(f"HCPs with 2+ years: {len(multi_year):,}")
print(f"Single-year HCPs  : {len(hcp)-len(multi_year):,}  → trend='Single Year', slope=NaN")

def compute_slope(grp):
    x, y = grp['year'].values, grp['total_claim_count'].values
    slope = np.polyfit(x, y, 1)[0]
    return round(slope/(y.mean()+1e-9)*100, 2)

print("Computing slopes...")
slopes = annual_multi.groupby('npi').apply(compute_slope, include_groups=False).reset_index()
slopes.columns = ['npi','yoy_slope_pct']

def classify(pct):
    if pct >= 10: return 'Growing'
    if pct <= -10: return 'Declining'
    return 'Stable'
slopes['trend'] = slopes['yoy_slope_pct'].map(classify)

hcp = hcp.merge(slopes[['npi','yoy_slope_pct','trend']], on='npi', how='left')
hcp['trend'] = hcp['trend'].fillna('Single Year')
hcp['yoy_slope_pct'] = hcp.apply(
    lambda r: np.nan if r['trend']=='Single Year' else r['yoy_slope_pct'], axis=1)

print(f"\nTrend distribution:")
print(hcp['trend'].value_counts().to_string())

dormant_hp = hcp[(hcp['V_score']==4) & (hcp['R_score']==1)].copy()
SPEC_MOD = {'Cardiology':1.15,'Endocrinology':1.15,'Internal Medicine':1.05,'Family Practice':1.05}

def recovery_rate(row):
    gap = 2022 - row['recency_year']
    base = 0.28 if gap<=2 else (0.20 if gap==3 else 0.14)
    mod  = SPEC_MOD.get(row['specialty'], 0.90)
    return min(round(base*mod,4), 0.35)

dormant_hp['recovery_rate'] = dormant_hp.apply(recovery_rate, axis=1)
dormant_hp['recoverable_volume'] = (dormant_hp['volume']*dormant_hp['recovery_rate']).round(0)
dormant_hp.to_parquet(config.WINBACK, index=False)

print(f"\nWin-Back Summary:")
print(f"  Dormant high-value HCPs   : {len(dormant_hp):,}")
print(f"  Realistic recoverable vol : ${dormant_hp['recoverable_volume'].sum()/1e6:.0f}M")
print(f"  Avg recovery rate         : {dormant_hp['recovery_rate'].mean()*100:.1f}%")

print(f"\nSanity Checks:")
print(f"  Single Year slope=NaN     : {hcp[hcp['trend']=='Single Year']['yoy_slope_pct'].isna().all()} ← must be True")
print(f"  Multi-year slope not NaN  : {hcp[hcp['trend']!='Single Year']['yoy_slope_pct'].isna().sum()} ← must be 0")

hcp.to_parquet(config.HCP_FINAL, index=False)
print(f"\n✅ Saved → {config.HCP_FINAL}")