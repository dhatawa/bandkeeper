"""
ops_sim.py — Simulator "Smart Dam & Surge-to-Storage" untuk kaskade Arda.
Ide: dengan prakiraan inflow L hari ke depan, lepaskan air LEBIH AWAL (pre-release) secukupnya
agar volume tidak menembus batas atas band MOEW (ruang banjir), TAPI jangan sampai di bawah batas
bawah band (cadangan kekeringan). Dibandingkan dengan operasi aktual 2017.
Neraca massa: V[t+1] = V[t] + (Qin - Qout) * 0.0864 - losses   (juta m3; tervalidasi korelasi ~1.0 di data)
"""
import numpy as np, pandas as pd
K = 0.0864  # m3/s selama 1 hari -> juta m3

def simulate(g, start, end, lead_days=3, q_safe=None, q_env=2.0, margin_mcm=5.0,
             forecast_err=0.0, losses_mcm=0.1, seed=0):
    """g: data 1 bendungan (kolom date, vol_mcm, inflow_m3s, outflow_m3s, band_low_mcm, band_high_mcm).
    q_safe: batas rilis (m3/s). Default None = rilis tertinggi bendungan itu sepanjang data 2017
            (masukan mentor: tidak ada batas debit hilir yang diatur, tergantung sungai).
    forecast_err: bias relatif prakiraan (mis. -0.2 = prakiraan 20% terlalu rendah)."""
    rng = np.random.default_rng(seed)
    if q_safe is None: q_safe = float(g.outflow_m3s.max())
    g = g.sort_values('date').set_index('date').loc[start:end].copy()
    g[['band_low_mcm', 'band_high_mcm']] = g[['band_low_mcm', 'band_high_mcm']].ffill().bfill()
    qin = g.inflow_m3s.fillna(0).to_numpy()
    hi = g.band_high_mcm.to_numpy(); lo = g.band_low_mcm.fillna(0).to_numpy()
    n = len(g); V = np.empty(n + 1); V[0] = g.vol_mcm.iloc[0]; Q = np.empty(n)
    for t in range(n):
        fc = qin[t:t + lead_days + 1] * (1 + forecast_err + rng.normal(0, 0.05, len(qin[t:t + lead_days + 1])))
        # proyeksi volume jika hanya lepas aliran lingkungan
        proj = V[t] + np.cumsum((fc - q_env) * K - losses_mcm)
        # kebutuhan pelepasan tambahan: ambil kendala paling ketat di tiap hari k dalam horizon
        need = (proj - (hi[t] - margin_mcm)) / (K * np.arange(1, len(proj) + 1))
        excess = max(0.0, need.max()) * K            # >0 berarti proyeksi menembus batas atas
        q = q_env + max(0.0, need.max())
        q = min(q, q_safe)
        # jangan kuras di bawah band bawah (cadangan kekeringan) kecuali proyeksi tetap melewati batas atas
        floor_q = (V[t] + (qin[t] * K) - losses_mcm - lo[t]) / K
        if excess == 0: q = min(q, max(q_env, floor_q))
        Q[t] = max(q, 0.0)
        V[t + 1] = V[t] + (qin[t] - Q[t]) * K - losses_mcm
    g['vol_smart'] = V[1:]; g['out_smart'] = Q
    g['vol_actual'] = g.vol_mcm
    return g.reset_index()

def kpi(sim):
    above = lambda v: int((v > sim.band_high_mcm).sum())
    below = lambda v: int((v < sim.band_low_mcm).sum())
    return pd.DataFrame({
        'aktual': [sim.vol_actual.max(), above(sim.vol_actual), below(sim.vol_actual), sim.outflow_m3s.max(), sim.vol_actual.iloc[-1]],
        'smart':  [sim.vol_smart.max(),  above(sim.vol_smart),  below(sim.vol_smart),  sim.out_smart.max(),   sim.vol_smart.iloc[-1]],
    }, index=['puncak volume (jt m3)', 'hari di atas band', 'hari di bawah band', 'puncak outflow (m3/s)', 'volume akhir (jt m3)']).round(1)

if __name__ == '__main__':
    import sys
    d = pd.read_csv(sys.argv[1] if len(sys.argv) > 1 else 'data_clean/arda_daily_2017.csv', parse_dates=['date'])
    for dam in ['Studen Kladenets', 'Kardzhali', 'Ivaylovgrad']:
        g = d[d.dam == dam]
        if g.band_high_mcm.isna().all(): continue
        for lead in (1, 3, 5):
            s = simulate(g, '2017-11-15', '2017-12-31', lead_days=lead)
            print(f'\n== {dam} | Nov-Des 2017 | lead {lead} hari'); print(kpi(s).to_string())
