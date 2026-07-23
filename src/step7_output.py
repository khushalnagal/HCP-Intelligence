"""
Step 7 - Power BI Data Export, Ranked Target List, Business Summary
"""
import sys, os
sys.path.append(os.path.dirname(__file__))
import config
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("STEP 7 - Power BI Export, Ranked List, Business Summary")
print("=" * 60)

hcp     = pd.read_parquet(config.HCP_FINAL)
df      = pd.read_parquet(config.CLEAN_DATA)
dormant = pd.read_parquet(config.WINBACK)

SEG_ORDER = ['High Priority','Growth','Maintenance','Dormant']

# Ranked Target List (top 5 per segment per territory)
ranked_all = []
for territory in hcp['territory'].unique():
    for segment in SEG_ORDER:
        top5 = hcp[(hcp['territory']==territory)&(hcp['segment']==segment)].nlargest(5,'RFM_score').copy()
        top5['rank_in_segment'] = range(1, len(top5)+1)
        ranked_all.append(top5)
ranked = pd.concat(ranked_all, ignore_index=True)[[
    'territory','segment','rank_in_segment','npi','last_name','first_name',
    'specialty','state','trend','yoy_slope_pct','recency_year',
    'frequency','volume','brand_sov','RFM_score']]
ranked['volume'] = ranked['volume'].round(0)
ranked['brand_sov'] = (ranked['brand_sov']*100).round(1).astype(str)+'%'
ranked.to_csv(config.OUT_RANKED, index=False)
print(f"Ranked list: {len(ranked)} rows")

# Full HCP export for Power BI (all 569K rows)
hcp_export = hcp[[
    'npi','last_name','first_name','state','territory','specialty',
    'recency_year','frequency','volume','brand_sov',
    'R_score','F_score','V_score','RFM_score',
    'segment','trend','yoy_slope_pct'
]].copy()
hcp_export['volume'] = hcp_export['volume'].round(2)
hcp_export.to_csv(os.path.join(os.path.dirname(config.OUT_RANKED), 'hcp_full_export.csv'), index=False)
print(f"Full HCP export: {len(hcp_export)} rows")

# Annual trend table for Power BI line charts
annual_export = (df.groupby(['npi','year'])['total_claim_count']
                    .sum().reset_index()
                    .rename(columns={'total_claim_count':'annual_claims'}))
annual_export = annual_export.merge(
    hcp[['npi','segment','trend','specialty','territory']], on='npi', how='left')
annual_export.to_csv(os.path.join(os.path.dirname(config.OUT_RANKED), 'hcp_annual_trend.csv'), index=False)
print(f"Annual trend export: {len(annual_export)} rows")

# Business Summary
hp_vol = hcp[hcp['segment']=='High Priority']['volume'].sum()
total_vol = hcp['volume'].sum()
grow_hp = ((hcp['segment']=='High Priority')&(hcp['trend']=='Growing')).sum()
decl_hp = ((hcp['segment']=='High Priority')&(hcp['trend']=='Declining')).sum()
clean_pct = (1-len(df)/1000000)*100
hp_count = (hcp['segment']=='High Priority').sum()
grow_count = (hcp['segment']=='Growth').sum()
maint_count = (hcp['segment']=='Maintenance').sum()
dorm_count = (hcp['segment']=='Dormant').sum()
hp_pct_base = hp_count/len(hcp)*100
hp_pct_spend = hp_vol/total_vol*100
winback_m = dormant['recoverable_volume'].sum()/1e6

lines = []
lines.append("PHARMA HCP PRESCRIBER INTELLIGENCE - BUSINESS INSIGHT SUMMARY")
lines.append("=" * 70)
lines.append("")
lines.append("OVERVIEW")
lines.append(f"This analysis segments {len(hcp):,} cardiovascular prescribers from")
lines.append(f"{len(df):,} cleaned Medicare Part D records to identify high-priority")
lines.append("sales targets across 6 territories.")
lines.append("")
lines.append("DATASET")
lines.append("  Raw records ingested   : 1,000,000")
lines.append(f"  Records after cleaning : {len(df):,} ({clean_pct:.1f}% removed - nulls, suppressed, invalid)")
lines.append(f"  Unique HCPs analyzed   : {len(hcp):,}")
lines.append("")
lines.append("SEGMENTATION (KMeans, k=4, silhouette=0.40)")
lines.append(f"  High Priority : {hp_count:,} HCPs - ${hp_vol/1e9:.1f}B ({hp_pct_spend:.0f}% of spend)")
lines.append(f"  Growth        : {grow_count:,} HCPs")
lines.append(f"  Maintenance   : {maint_count:,} HCPs")
lines.append(f"  Dormant       : {dorm_count:,} HCPs")
lines.append("")
lines.append("FINDINGS")
lines.append(f"  1. Revenue concentration: the High Priority segment ({hp_count:,} doctors,")
lines.append(f"     {hp_pct_base:.0f}% of the base) accounts for {hp_pct_spend:.0f}% of total spend.")
lines.append("     Sales effort should concentrate here first.")
lines.append("")
lines.append(f"  2. Within High Priority, {grow_hp:,} doctors show a growing prescribing trend")
lines.append(f"     and {decl_hp:,} show a declining trend. These require different rep actions -")
lines.append("     accelerate visits for growing accounts, protect relationships for declining ones.")
lines.append("")
lines.append(f"  3. Win-back opportunity: {len(dormant):,} dormant high-value doctors represent")
lines.append(f"     ${winback_m:.0f}M in realistic recoverable volume, based on a")
lines.append("     specialty- and recency-adjusted recovery rate (not raw historical volume).")
lines.append("")
lines.append("RECOMMENDATION")
lines.append("  Prioritize territory call plans using the High Priority segment first,")
lines.append(f"  layering in trend direction to decide cadence. Route the {len(dormant):,} win-back")
lines.append("  candidates to a separate re-engagement track rather than standard rep visits.")

summary = "\n".join(lines)
print(summary)

with open(config.OUT_SUMMARY, "w", encoding="utf-8") as f:
    f.write(summary)

print("")
print("Step 7 complete - all outputs saved.")