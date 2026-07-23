"""
Step 5 — KMeans Clustering (k=4 HCP Segments)
Output: data/processed/hcp_segmented.parquet
"""
import sys, os
sys.path.append(os.path.dirname(__file__))
import config
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("STEP 5 — KMeans Clustering (k=4 HCP Segments)")
print("=" * 60)

hcp = pd.read_parquet(config.HCP_RFM)
X   = hcp[['R_norm','F_norm','V_norm']].values

print(f"Running KMeans on {len(hcp):,} HCPs...")
km = KMeans(n_clusters=4, random_state=42, n_init=10, max_iter=300)
hcp['cluster'] = km.fit_predict(X)

idx = np.random.RandomState(42).choice(len(X), size=10000, replace=False)
sil = silhouette_score(X[idx], hcp['cluster'].values[idx])
print(f"Silhouette Score: {sil:.4f}  (benchmark: >0.35 = actionable)")

cluster_rfm = hcp.groupby('cluster')['RFM_score'].mean()
label_map   = cluster_rfm.rank(ascending=False).astype(int).map({
    1:'High Priority', 2:'Growth', 3:'Maintenance', 4:'Dormant'
})
hcp['segment'] = hcp['cluster'].map(label_map)

summary = hcp.groupby('segment').agg(
    count=('npi','count'), avg_RFM=('RFM_score','mean'), avg_vol=('volume','mean')
).round(2)
print(f"\nSegment Summary:")
print(summary.sort_values('avg_RFM', ascending=False).to_string())

order = summary['avg_RFM'].sort_values(ascending=False).index.tolist()
ok = order == ['High Priority','Growth','Maintenance','Dormant']
print(f"\nRFM hierarchy correct: {'✅' if ok else '❌'}")

hcp.to_parquet(config.HCP_SEGMENTED, index=False)
print(f"\n✅ Saved → {config.HCP_SEGMENTED}")