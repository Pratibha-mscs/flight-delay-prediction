import os
import glob
import duckdb

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

RAW_2023 = os.path.join(ROOT, "2023")
RAW_2024 = os.path.join(ROOT, "2024")
OUT_2023 = os.path.join(ROOT, "processed", "2023")
OUT_2024 = os.path.join(ROOT, "processed", "2024")

os.makedirs(OUT_2023, exist_ok=True)
os.makedirs(OUT_2024, exist_ok=True)

# Pre-departure features + filters + label
KEEP_COLS = [
    "Year", "Month", "DayofMonth", "DayOfWeek", "FlightDate",
    "Reporting_Airline", "DOT_ID_Reporting_Airline", "Flight_Number_Reporting_Airline",
    "OriginAirportID", "OriginCityMarketID", "OriginState", "Origin",
    "DestAirportID", "DestCityMarketID", "DestState", "Dest",
    "CRSDepTime", "DepTimeBlk", "CRSArrTime", "ArrTimeBlk",
    "Distance", "DistanceGroup", "CRSElapsedTime",
    "Cancelled", "Diverted",
    "ArrDel15"
]
SELECT_SQL = ", ".join([f'"{c}"' for c in KEEP_COLS])

def convert_year(raw_dir: str, out_dir: str, year: str):
    csv_files = sorted(glob.glob(os.path.join(raw_dir, f"{year}_*.csv")))
    if not csv_files:
        raise SystemExit(f"No CSV files found in: {raw_dir}")

    for csv_path in csv_files:
        base = os.path.basename(csv_path)         
        month = base.split("_")[1].split(".")[0]  
        out_path = os.path.join(out_dir, f"{year}_{month}.parquet")

        print(f"Converting {base} -> {os.path.basename(out_path)}")

        con = duckdb.connect(database=":memory:")
        con.execute(f"""
            COPY (
                SELECT {SELECT_SQL}
                FROM read_csv_auto('{csv_path}', sample_size=-1)
                WHERE "Cancelled" = 0 AND "Diverted" = 0 AND "ArrDel15" IS NOT NULL
            )
            TO '{out_path}' (FORMAT PARQUET);
        """)
        con.close()

    print(f"Done writing {year} parquet files to {out_dir}")

if __name__ == "__main__":
    convert_year(RAW_2023, OUT_2023, "2023")
    convert_year(RAW_2024, OUT_2024, "2024")
