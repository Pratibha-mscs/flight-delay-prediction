# Flight Delay Prediction (BTS On-Time Performance)

This project predicts whether a U.S. domestic flight will arrive **15+ minutes late** using the BTS TranStats On-Time Performance dataset. The goal is to build a realistic model that can be used **before departure** (so I avoid columns that would leak the answer, like actual departure/arrival times).

---

## What I’m Predicting

**Target:** `ArrDel15`

- `1` = arrival delay is **15 minutes or more**
- `0` = not delayed by that definition

---

## Dataset (Real-World, Large)

**Source:** U.S. DOT / BTS TranStats  
**Database:** On-Time Reporting Carrier On-Time Performance (1987–present)

### Scope used in this project
- Time range used: **Jan 2023 – Dec 2024**
- Total rows loaded: **13,708,650**
- Positive class rate (ArrDel15 = 1): **20.69%**

### Time-based split (more realistic than random split)
- Train (2023): **6,743,403** rows  
- Validation (2024 Jan–Jun): **3,403,465** rows  
- Test (2024 Jul–Dec): **3,561,782** rows  

### Local storage size (not committed to GitHub)
Raw monthly CSVs (local only):
- 2023: ~**2.9 GB**
- 2024: ~**3.0 GB**
- Total raw CSV size: ~**5.9 GB**

Processed Parquet (local only):
- processed/2023: ~**62 MB**
- processed/2024: ~**67 MB**
- Total parquet size: ~**129 MB**

Note: Raw CSV and Parquet files are excluded from GitHub via `.gitignore` because they are too large.

---

## How to Download the Data (Reproducible)

This repo does not include raw data files. To reproduce the dataset:

1. Open BTS TranStats for:
   On-Time Reporting Carrier On-Time Performance (1987–present)

2. Use the **Download** workflow (individual flight data download).

3. Select:
   - Years: **2023** and **2024**
   - Period: **Monthly**
   - Format: **Pre-zipped file** (recommended)

4. Download each month and extract the CSV.

5. Rename monthly CSVs to short names:
   - `2023_01.csv`, `2023_02.csv`, …, `2023_12.csv`
   - `2024_01.csv`, `2024_02.csv`, …, `2024_12.csv`

6. Convert CSV → Parquet locally (faster + smaller). This project expects:
   - `processed/2023/*.parquet`
   - `processed/2024/*.parquet`

---

## Repository Structure


---

## Data Cleaning + Preparation

Even though most of the columns I kept have very low missingness, I still do a few important steps:

- Parse `FlightDate` as a proper date.
- Extract scheduled time features from `CRSDepTime` and `CRSArrTime` (hour/minute).
- Create `route = Origin -> Dest`.
- Verify/clean invalid scheduled times (example: make sure times are 0–2359).
- Keep the feature set “pre-departure safe” to avoid leakage.

---

## Leakage Rules (What I Avoid Using)

To keep the prediction setting realistic (information known before the flight leaves), I avoid columns like:

- Actual departure/arrival timestamps (DepTime, ArrTime, WheelsOff, WheelsOn)
- Actual delay values (DepDelay, ArrDelay, DepDelayMinutes, ArrDelayMinutes)
- Cause-of-delay fields (CarrierDelay, WeatherDelay, NASDelay, etc.)
- Diversion details (Div1…Div5 fields)
- Any post-event operational columns that wouldn’t exist at prediction time

---

## Features Used (Leakage-Safe)

### Schedule and routing (available before departure)
- Calendar: Month, DayOfMonth, DayOfWeek, weekend flag
- Scheduled times: features derived from CRSDepTime and CRSArrTime (hour/minute)
- Airline: Reporting_Airline
- Route: Origin, Dest, and route string
- Flight characteristics: Distance, CRSElapsedTime
- Time blocks: DepTimeBlk, ArrTimeBlk

### Historical behavior features (safe rolling aggregates)
These are computed using rolling averages on *past* flights and use a shift so the current flight’s label is not included.

- origin_delay_rate_200: last 200 flights at the same origin airport
- route_delay_rate_200: last 200 flights on the same route
- carrier_delay_rate_500: last 500 flights for the same airline
- depblk_delay_rate_500: last 500 flights for the same departure time block

---

## Model

### Model used
LightGBM (gradient boosted decision trees)

### Why LightGBM
- Works well on large tabular datasets
- Handles non-linear interactions
- Fast enough to train on millions of rows
- Good baseline for operational prediction problems

### Class imbalance
Delays are about 20.69% of the data, so the classes are imbalanced.  
I handle this with `scale_pos_weight` during training.

---

## Results (Current Best)

- Validation AUC: **~0.7216**
- Test AUC: **~0.7257**

I also export evaluation artifacts to `notebooks/outputs/`:
- model metrics summary
- ROC and PR curve points
- top-K delay capture table (business-style view)
- feature importance
- a 100k sample of test predictions (so GitHub stays light)

---

## How to Run

1. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

2. Open and run the notebook:

notebooks/01_sanity_check.ipynb 