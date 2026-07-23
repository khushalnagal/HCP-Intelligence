"""
config.py — Central path config for the entire project.
All scripts import from here so paths never break.
"""
import os

# Root = this project folder on your system
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Data paths
RAW_DATA      = os.path.join(ROOT, 'data', 'raw',       'cms_raw.parquet')
CLEAN_DATA    = os.path.join(ROOT, 'data', 'processed', 'cms_clean.parquet')
HCP_RFM       = os.path.join(ROOT, 'data', 'processed', 'hcp_rfm.parquet')
HCP_SEGMENTED = os.path.join(ROOT, 'data', 'processed', 'hcp_segmented.parquet')
HCP_FINAL     = os.path.join(ROOT, 'data', 'processed', 'hcp_final.parquet')
WINBACK       = os.path.join(ROOT, 'data', 'processed', 'dormant_winback.parquet')
DATABASE      = os.path.join(ROOT, 'data', 'processed', 'pharma.db')

# Output paths
OUT_TOP_STATES    = os.path.join(ROOT, 'data', 'outputs', 'top_states.csv')
OUT_BRAND_GENERIC = os.path.join(ROOT, 'data', 'outputs', 'brand_generic_sov.csv')
OUT_SPECIALTY     = os.path.join(ROOT, 'data', 'outputs', 'specialty_territory.csv')
OUT_RANKED        = os.path.join(ROOT, 'data', 'outputs', 'hcp_ranked_targets.csv')
OUT_SUMMARY       = os.path.join(ROOT, 'data', 'outputs', 'business_insight_summary.txt')

# Charts
CHARTS_DIR = os.path.join(ROOT, 'charts')

if __name__ == '__main__':
    print("Project root :", ROOT)
    print("Raw data     :", RAW_DATA)
    print("Charts dir   :", CHARTS_DIR)