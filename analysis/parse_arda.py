"""Parser laporan harian Kaskade Arda (Kardzhali, Studen Kladenets, Ivaylovgrad) -> tidy CSV."""
import pandas as pd, glob, re, sys
DAMS = {'Кърджали': 'Kardzhali', 'Ст. Кладенец': 'Studen Kladenets', 'Ивайловград': 'Ivaylovgrad'}

def find_col(hdr, pattern, start=0):
    for c in range(start, len(hdr)):
        if re.search(pattern, hdr[c], re.I): return c
    return None

def parse_sheet(df):
    hdr = [' '.join(str(df.iat[i, c]) for i in range(0, min(6, len(df)))) for c in range(df.shape[1])]
    c_vol = find_col(hdr, r'наличен');  c_in = find_col(hdr, r'ПРИТОК'); c_out = find_col(hdr, r'РАЗХОД')
    c_lvl = find_col(hdr, r'\bВН\b');    c_nv = find_col(hdr, r'НВРВН')
    c_lo  = find_col(hdr, r'МОСВ|над');  c_stat = find_col(hdr, r'Статус'); c_dev = find_col(hdr, r'Отклонение')
    c_pct = find_col(hdr, r'общия обем'); c_tot = find_col(hdr, r'общ\b'); c_use = find_col(hdr, r'полезен')
    out = []
    for _, r in df.iterrows():
        dam = str(r.get(2, '')).strip()
        if dam not in DAMS: continue
        g = lambda c: r.iat[c] if c is not None and c < len(r) else None
        out.append(dict(date=str(r.iat[1]).strip(), dam=DAMS[dam], vol_total_mcm=g(c_tot), vol_useful_mcm=g(c_use),
                        vol_mcm=g(c_vol), pct_full=g(c_pct), inflow_m3s=g(c_in), outflow_m3s=g(c_out),
                        level_m=g(c_lvl), nvrvn_m=g(c_nv),
                        band_low_mcm=g(c_lo), band_high_mcm=g(c_lo + 1) if c_lo is not None else None,
                        status_raw=g(c_stat), deviation_mcm=g(c_dev)))
    return out

def parse_all(folder):
    rows = []
    for f in sorted(glob.glob(f'{folder}/*.xls')):
        for name, df in pd.read_excel(f, sheet_name=None, header=None, engine='xlrd').items():
            if re.match(r'\s*\d{2}\.\d{2}\.\d{4}', str(name)): rows += parse_sheet(df)
    d = pd.DataFrame(rows)
    d['date'] = pd.to_datetime(d['date'], format='%d.%m.%Y', errors='coerce')
    num = [c for c in d.columns if c not in ('date', 'dam', 'status_raw')]
    d[num] = d[num].apply(pd.to_numeric, errors='coerce')
    # --- cleaning ---
    d = d[d.date.between('2017-01-01', '2017-12-31')]                # buang typo tanggal (mis. 2015-09-30)
    d = d.drop_duplicates(['date', 'dam'], keep='last').sort_values(['dam', 'date'])
    for c in ('inflow_m3s', 'outflow_m3s'): d.loc[d[c] < 0, c] = pd.NA  # debit negatif = error input
    # status dihitung ulang dari band (lebih andal daripada teks manual operator)
    d['status'] = 'OK'
    d.loc[d.vol_mcm > d.band_high_mcm, 'status'] = 'ABOVE_BAND'   # ЗАВИШЕН: ruang tampung banjir terpakai
    d.loc[d.vol_mcm < d.band_low_mcm,  'status'] = 'BELOW_BAND'   # ЗАНИЖЕН: cadangan kekeringan kurang
    d['flood_buffer_mcm'] = d.vol_total_mcm - d.vol_mcm           # sisa ruang sebelum penuh
    return d.reset_index(drop=True)

if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/data/Share/Cascade Arda'
    d = parse_all(src)
    d.to_csv("arda_daily_2017.csv", index=False)
    print(len(d), d.date.min().date(), d.date.max().date())
    print(d.groupby(['dam', 'status']).size().unstack(fill_value=0))
    print(d.groupby('dam')[['inflow_m3s', 'outflow_m3s', 'pct_full', 'band_low_mcm', 'band_high_mcm']].agg(['min', 'max']).round(1).to_string())
    print('mismatch status operator vs hitung:', (d.status_raw.map({'OK':'OK','ЗАВИШЕН':'ABOVE_BAND','ЗАНИЖЕН':'BELOW_BAND'}) != d.status).sum())
