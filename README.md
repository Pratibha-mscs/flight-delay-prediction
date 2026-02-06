# Flight Delay Prediction (BTS On-Time Performance)

Predict whether a flight will arrive **15+ minutes late** (ArrDel15) using the U.S. BTS On-Time Performance dataset.

## Dataset
Source: BTS On-Time Performance (1987–present).
This repo does **not** include raw/processed data files (too large).  
Download instructions will be added.

## What’s done so far
- Converted monthly BTS CSV files to Parquet for faster loading
- Built EDA:
  - Monthly seasonality (summer peaks)
  - Origin and route delay hotspots
  - Delay increases for later departure blocks
- Trained LightGBM on full dataset (2023 train, 2024 validation/test)
  - Baseline AUC ~0.72–0.73

## Repo Structure
- `notebooks/` : EDA + model training notebooks
- `scripts/` : helper scripts (conversion / training)
- `processed/` : (ignored) local Parquet files

## Next steps
- Add more feature engineering (interaction rolling features)
- Threshold tuning + business metrics (top-K delay capture)
- Final model evaluation + plots
