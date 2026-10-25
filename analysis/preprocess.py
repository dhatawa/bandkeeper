"""
preprocess.py — Bersihkan dataset panitia EIT Water Hackathon jadi data siap-demo.
Pakai:  python preprocess.py --zip datasetEITwater.zip --out data_clean
Output:
  arda_daily_2017.csv     operasi harian 3 bendungan kaskade Arda + status band MOEW
  iskar_daily_2025.csv    debit harian S. Iskar (Novi Iskar = Sofia, Oreshovitsa = hilir)
  danube_levels_2021.csv  muka air Danube (dedup) — konteks regional
  raster_monthly_stats.csv  presipitasi & soil moisture 2024 per region (Arda, Sofia, Bulgaria)
  overlays/*.png + overlays/index.json  raster berwarna untuk Leaflet ImageOverlay
"""
import argparse, json, os, re, zipfile, glob
import numpy as np, pandas as pd, rasterio
from rasterio.windows import from_bounds
from parse_arda import parse_all

REGIONS = {  # bbox (lon_min, lat_min, lon_max, lat_max) — perkiraan, sesuaikan dgn batas DAS resmi
    'arda_basin': (24.6, 41.2, 26.4, 41.95),
    'sofia_iskar': (23.0, 42.4, 23.8, 42.95),
    'bulgaria': (22.2, 41.2, 28.7, 44.3),
}
STATIONS = {  # koordinat perkiraan — WAJIB dicek di OSM sebelum demo
    'Kardzhali':        dict(lat=41.645, lon=25.330, type='dam'),
    'Studen Kladenets': dict(lat=41.620, lon=25.640, type='dam'),
    'Ivaylovgrad':      dict(lat=41.575, lon=26.105, type='dam'),
    'Iskar_NoviIskar':  dict(lat=42.805, lon=23.350, type='gauge'),
    'Iskar_Oreshovitsa':dict(lat=43.590, lon=24.370, type='gauge'),
}

def decode(name):  # nama file Cyrillic di zip ter-encode sbg #UXXXX
    return re.sub(r'#U([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), name)

def extract(zip_path, dest):
    with zipfile.ZipFile(zip_path) as z:
        for i in z.infolist():
            n = decode(i.filename)
            if '..' in n: continue
            p = os.path.join(dest, n)
            if n.endswith('/'): os.makedirs(p, exist_ok=True); continue
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, 'wb') as f: f.write(z.read(i))
    return os.path.join(dest, 'Share')

def iskar(root):
    out = []
    for f, st in [('Искър_Нови_Искър_2025.csv', 'Iskar_NoviIskar'), ('Искър_Ореховица_2025.csv', 'Iskar_Oreshovitsa')]:
        d = pd.read_csv(os.path.join(root, f), parse_dates=['date']).rename(columns={'discharge(m3/s)': 'q_m3s'})
        d = d.set_index('date').asfreq('D')                       # ada gap s/d 18 hari -> tandai
        d['gap'] = d.q_m3s.isna()
        d['q_m3s'] = d.q_m3s.interpolate(limit=3)                 # isi gap pendek saja
        med = d.q_m3s.median()
        d['q_ratio_median'] = d.q_m3s / med                       # indeks banjir sederhana
        d['alert'] = pd.cut(d.q_ratio_median, [-np.inf, 3, 6, np.inf], labels=['normal', 'watch', 'warning'])
        d['station'] = st; out.append(d.reset_index())
    return pd.concat(out)

def danube(root):
    f = glob.glob(os.path.join(root, 'Danube', 'Бюлетин*.csv'))[0]
    d = pd.read_csv(f).dropna(subset=['станция']).drop_duplicates()
    d.columns = ['date', 'country', 'station', 'river_km', 'level_cm', 'delta24h_cm']
    d['delta24h_cm'] = pd.to_numeric(d.delta24h_cm.astype(str).str.replace('+', '', regex=False), errors='coerce')
    return d

def raster_stats_and_overlays(root, out_dir):
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    os.makedirs(os.path.join(out_dir, 'overlays'), exist_ok=True)
    rows, index = [], []
    for f in sorted(glob.glob(os.path.join(root, 'gee_output', '*', '*.tif'))):
        var = f.split(os.sep)[-2]
        m = re.search(r'(\d{4}-\d{2}-\d{2})_(\d{4}-\d{2}-\d{2})', f); start, end = m.groups()
        if (pd.Timestamp(end) - pd.Timestamp(start)).days < 25: continue   # skip potongan 3/15 hari
        with rasterio.open(f) as r:
            a = r.read(1).astype(float)
            if var == 'soil_moisture': a[a <= 0] = np.nan                   # 0 = nodata (laut/luar batas)
            for reg, bb in REGIONS.items():
                w = from_bounds(*bb, transform=r.transform)
                sub = r.read(1, window=w, boundless=True, fill_value=np.nan).astype(float)
                if var == 'soil_moisture': sub[sub <= 0] = np.nan
                rows.append(dict(var=var, month=start[:7], region=reg, mean=np.nanmean(sub), p10=np.nanpercentile(sub, 10)))
            b = r.bounds
            cmap = 'Blues' if var == 'precipitation' else 'RdYlBu'
            vmin, vmax = (0, 150) if var == 'precipitation' else (0.05, 0.40)
            png = f'{var}_{start[:7]}.png'
            plt.imsave(os.path.join(out_dir, 'overlays', png), np.ma.masked_invalid(a), cmap=cmap, vmin=vmin, vmax=vmax)
            index.append(dict(var=var, month=start[:7], file=png, bounds=[[b.bottom, b.left], [b.top, b.right]], vmin=vmin, vmax=vmax))
    st = pd.DataFrame(rows)
    # anomali soil moisture thd rata-rata tahunan 2024 (proxy kekeringan; idealnya pakai klimatologi 30 thn)
    sm = st[st['var'] == 'soil_moisture'].copy()
    sm['anom_pct'] = 100 * (sm['mean'] / sm.groupby('region')['mean'].transform('mean') - 1)
    st = st.merge(sm[['month', 'region', 'anom_pct']], on=['month', 'region'], how='left')
    json.dump(index, open(os.path.join(out_dir, 'overlays', 'index.json'), 'w'), indent=1)
    return st

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--zip', default='datasetEITwater.zip'); ap.add_argument('--out', default='data_clean')
    ap.add_argument('--raw', default='data_raw')
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    root = extract(a.zip, a.raw)
    parse_all(os.path.join(root, 'Cascade Arda')).to_csv(f'{a.out}/arda_daily_2017.csv', index=False)
    iskar(root).to_csv(f'{a.out}/iskar_daily_2025.csv', index=False)
    danube(root).to_csv(f'{a.out}/danube_levels_2021.csv', index=False)
    raster_stats_and_overlays(root, a.out).to_csv(f'{a.out}/raster_monthly_stats.csv', index=False)
    json.dump(STATIONS, open(f'{a.out}/stations.json', 'w'), indent=1)
    print('Selesai ->', a.out)
