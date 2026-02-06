```md
# Flight Delay Prediction (BTS On-Time Performance)

Predict whether a U.S. domestic flight will arrive **15+ minutes late** using the official **BTS TranStats “On-Time Reporting Carrier On-Time Performance (1987–present)”** dataset.

---

## Project Goal

Build a **realistic, production-style** binary classifier to predict **ArrDel15** (1 = arrival delay ≥ 15 minutes, 0 = otherwise) using **only information that is available before the flight departs**, plus safe historical aggregates (no target leakage from actual departure/arrival timestamps).

---

## Dataset

### Source
U.S. Department of Transportation (DOT) / Bureau of Transportation Statistics (BTS) TranStats  
Database: **On-Time Reporting Carrier On-Time Performance (1987–present)**

### Scope used in this project
- Time range: **Jan 2023 – Dec 2024**
- Total rows loaded: **13,708,650**
- Positive class rate (ArrDel15 = 1): **20.69%**
- Time-based split (realistic for forecasting):
  - Train (2023): **6,743,403** rows
  - Validation (2024 Jan–Jun): **3,403,465** rows
  - Test (2024 Jul–Dec): **3,561,782** rows

### Local storage size (not committed to GitHub)
Raw monthly CSVs:
- 2023 CSVs: ~**2.9 GB**
- 2024 CSVs: ~**3.0 GB**
- Total raw CSV size: ~**5.9 GB**

Processed Parquet (after filtering/selecting columns):
- processed/2023: ~**62 MB**
- processed/2024: ~**67 MB**
- Total Parquet size: ~**129 MB**

> Note: Raw CSV and Parquet files are intentionally excluded from GitHub via `.gitignore` due to size.

---

## Data Download Instructions (Reproducible)

This repo does **not** include raw data files. To reproduce the dataset:

1. Open the BTS TranStats page for:  
   **On-Time Reporting Carrier On-Time Performance (1987–present)**

2. Use the **Download** workflow (individual flight data download).

3. Select:
   - **Years:** 2023 and 2024  
   - **Period:** Monthly  
   - **Format:** **Pre-zipped file** (recommended)

4. Download each month and extract the CSV locally.

5. Rename monthly CSVs to short, consistent names:
   - `2023_01.csv`, `2023_02.csv`, … `2023_12.csv`
   - `2024_01.csv`, `2024_02.csv`, … `2024_12.csv`

6. Convert CSV → Parquet locally (recommended for speed and size). This project expects:
   - `processed/2023/*.parquet`
   - `processed/2024/*.parquet`

---

## Repository Structure

```

flight-delay-prediction/
├── 2023/                         # local raw CSVs (ignored)
├── 2024/                         # local raw CSVs (ignored)
├── processed/                    # local parquet data (ignored)
│   ├── 2023/
│   └── 2024/
├── notebooks/
│   ├── 01_sanity_check.ipynb     # EDA + training workflow
│   └── outputs/                  # small exported results (tracked)
│       ├── model_metrics_summary.csv
│       ├── feature_importance.csv
│       ├── test_topk_delay_capture.csv
│       ├── test_roc_curve_points.csv
│       ├── test_pr_curve_points.csv
│       └── test_predictions_sample_100k.csv
├── scripts/                      # helper scripts (csv→parquet, etc.)
├── src/                          
├── requirements.txt
└── README.md

````

---

## Problem Definition

### Target
- **ArrDel15** ∈ {0,1}  
  - 1 = arrived **15+ minutes late**
  - 0 = not late by that definition

### Leakage Rules (what we avoid)
To keep the model legitimate for “pre-departure” prediction, we avoid using:
- Actual departure time (DepTime), arrival time (ArrTime)
- Actual delays (DepDelay, ArrDelay) and their group buckets
- Cause-of-delay fields (CarrierDelay, WeatherDelay, NASDelay, etc.)
- Diversion details (Div1…Div5 columns)
- Other post-event operational fields that would not exist at prediction time

---

## Features Used (Leakage-Safe)

### Schedule + routing features (available pre-departure)
- Calendar: `Month`, `DayofMonth`, `DayOfWeek`, `is_weekend`
- Planned schedule times: parsed from `CRSDepTime`, `CRSArrTime` → `dep_hour`, `dep_min`, `arr_hour`, `arr_min`
- Route basics: `Origin`, `Dest`, `route = Origin->Dest`
- Airline: `Reporting_Airline`
- Flight characteristics: `Distance`, `CRSElapsedTime`
- Time blocks: `DepTimeBlk`, `ArrTimeBlk`

### Historical behavior (safe rolling aggregates with shift to prevent leakage)
All rolling rates are computed as rolling means on past flights and use `shift(1)` so the current row’s label is never included.

- `origin_delay_rate_200` (last 200 flights at the same origin)
- `route_delay_rate_200` (last 200 flights on the same route)
- `carrier_delay_rate_500` (last 500 flights for the carrier)
- `depblk_delay_rate_500` (last 500 flights in the same departure time block)

---

## Modeling

### Model
- **LightGBM (gradient-boosted decision trees)**

### Why LightGBM
- Handles large datasets efficiently (millions of rows)
- Works well with mixed numeric + categorical inputs
- Strong baseline for tabular classification
- Supports class imbalance handling via `scale_pos_weight`

### Class imbalance handling
- Positive class ≈ **20.69%**
- Used: `scale_pos_weight = (neg / pos)` during training

### Train/Validation/Test split
Time-based split to mimic real forecasting:
- Train: 2023
- Validation: 2024 Jan–Jun
- Test: 2024 Jul–Dec

---

## Results (Current Best)

- Validation AUC: **~0.7216**
- Test AUC: **~0.7257**

Interpretation: the model ranks delayed flights above non-delayed flights with strong separation for a large-scale operational dataset using leakage-safe features.

Exports (tracked in GitHub under `notebooks/outputs/`):
- `model_metrics_summary.csv` (AUC + AP)
- `feature_importance.csv`
- `test_topk_delay_capture.csv` (business-friendly “top-K capture” table)
- `test_roc_curve_points.csv`, `test_pr_curve_points.csv`
- `test_predictions_sample_100k.csv` (small sample for review)

---

## How to Run Locally

### 1) Setup environment
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
````

### 2) Open the notebook

Open `notebooks/01_sanity_check.ipynb` in VS Code (or Jupyter) and run cells top-to-bottom:

* Load parquet files
* Create features (time parsing + rolling aggregates)
* Train LightGBM
* Export metrics and artifacts to `notebooks/outputs/`

---

## Next Steps

* Add interaction-based historical features (e.g., Origin × DepTimeBlk rolling rate)
* Threshold tuning for business objectives (precision/recall trade-offs)
* More visualizations and model interpretation (SHAP, calibration checks)
* Optional: incorporate external weather data for further lift (kept separate from the leakage-safe baseline)

---

## Notes

* Raw data is excluded from the repository due to size.
* All model features are selected to keep the prediction setting realistic and avoid leakage.

