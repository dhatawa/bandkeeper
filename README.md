# Bandkeeper

**Smart dam release planning for floods and droughts.**
Built by Team Reika for the EIT Water Hackathon Sofia 2026, Track 3 (Strengthen Europe’s resilience to water-driven disasters), topic 03: dam release planning.

**Live demo:** https://dhatawa.github.io/bandkeeper/ (runs in the browser, no install)

---

## What it does

Bandkeeper gives a dam operator one number each morning: how much water to release today, and why.

It reads the daily operating report the operator already files, takes an inflow forecast for the next one to seven days, and plans releases so the reservoir:

- keeps room under the ministry’s **upper fill schedule** for the next flood,
- holds water above the **lower fill schedule** for the dry season,
- never releases faster than the dam already has (its 2017 maximum),
- stays inside the ministry’s **monthly water quota**.

## Results on 2017 data

Day-by-day replay on the organisers’ Arda cascade reports, 15 November to 31 December 2017, with releases capped at each dam’s 2017 maximum.

| Measure | As operated | Bandkeeper |
|---|---|---|
| Studen Kladenets, days above upper schedule (3-day forecast) | 28 | 5 |
| Same, 5-day forecast | 28 | 2 |
| Same, forecast 30% too low | 28 | 6 |
| Studen Kladenets, peak release (m³/s) | 160.5 | 160.5 |
| Studen Kladenets, December quota used | 84% | 92% |
| Ivaylovgrad, days above upper schedule | 14 | 0 |
| Ivaylovgrad, peak release (m³/s) | 252 | about 146 |

Our water balance (tomorrow’s volume = today’s volume + inflow − release − losses) matches the reported volumes with a correlation of 1.00 on all three dams.

## How the planner works

1. **Read the daily report:** volume, inflow, release, upper and lower schedule, monthly quota.
2. **Take the inflow forecast:** one to seven days ahead. The replay uses observed inflow with 5% noise.
3. **Find the strictest day:** for each forecast day, compute the release that keeps the reservoir 5 million m³ under the upper schedule, and keep the largest.
4. **Respect the river and the quota:** cap the release at the dam’s 2017 maximum, stay inside the monthly quota, and with no flood ahead, hold water above the lower schedule.

The same logic runs in two places: `js/script.js` for the website and `analysis/ops_sim.py` for the Python replay.

## Repository structure

```
index.html              Website and interactive replay
css/style.css           Styles (light and dark theme)
js/data.js              Cleaned 2017 Arda data, release caps and monthly quotas
js/script.js            Planner, charts and controls
assets/img/             Team photos
analysis/
  parse_arda.py         Parses the Bulgarian daily dam reports (.xls) into a tidy table
  preprocess.py         Cleans the organisers' dataset (dams, Iskar, Danube, rasters)
  ops_sim.py            Release planner and replay in Python
  data_clean/           Cleaned Arda daily data, 2017
  requirements.txt
```

## Run it yourself

**Website:** open `index.html` in a browser. No build step.

**Python replay:**

```bash
cd analysis
pip install -r requirements.txt
python ops_sim.py data_clean/arda_daily_2017.csv
```

**Rebuild the cleaned data** from the organisers’ zip (not included in this repo):

```bash
python preprocess.py --zip datasetEITwater.zip --out data_clean
```

## Data

From the organisers’ shared dataset: Arda cascade daily operating reports (2017), Iskar discharge at Novi Iskar and Oreshovitsa (2025), Danube water levels (2021), and monthly precipitation and soil moisture for Bulgaria (2024). The repo contains only the cleaned Arda table derived from it.

## What we changed after sector feedback

During the hackathon we asked a water-sector mentor three questions.

| We asked | A mentor answered | We changed |
|---|---|---|
| How do operators set daily releases? | From manual and automatic measurement stations | Bandkeeper adds the forecast those readings lack |
| What is the safe downstream flow? | It depends on the river; no regulation fixes it | Releases capped at each dam’s 2017 maximum, editable per river |
| Are there fines for leaving the band? | No; the ministry sets monthly water quotas | Every plan is checked against the monthly quota |

## Limitations

- The replay forecast is observed inflow plus noise, so it shows a best case. A rainfall-to-inflow model on ERA5-Land data is the next step.
- The dam reports cover one year, 2017. A live pilot with an operator is the real test.
- Topic 03 also names urban stormwater surge control. We focused on dam release planning because the organisers’ data supports it; the same planning rule can drive urban storm tanks once city data is available.

## Team

- **Dyka Hatawa:** data, simulator and product. Informatics, Institut Teknologi Nasional Bandung.
- **Reisya Putri Ramadhani:** customers and business case.
