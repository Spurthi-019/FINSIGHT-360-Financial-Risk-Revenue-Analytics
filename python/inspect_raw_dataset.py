import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np

def find_raw_file():
    """Locate the target raw CSV file."""
    # Check command-line argument if provided
    if len(sys.argv) > 1:
        custom_path = Path(sys.argv[1])
        if custom_path.exists():
            return custom_path

    # Default candidates
    candidates = [
        Path("data/raw/transactions_train.csv"),
        Path("../data/raw/transactions_train.csv"),
        Path(__file__).resolve().parent.parent / "data" / "raw" / "transactions_train.csv",
    ]
    for p in candidates:
        if p.exists():
            return p.resolve()

    # Fallback: find any csv in data/raw
    raw_dir_candidates = [
        Path("data/raw"),
        Path("../data/raw"),
        Path(__file__).resolve().parent.parent / "data" / "raw",
    ]
    for raw_dir in raw_dir_candidates:
        if raw_dir.exists():
            csv_files = list(raw_dir.glob("*.csv"))
            if csv_files:
                return csv_files[0].resolve()

    raise FileNotFoundError("Could not locate raw CSV file in data/raw/.")

def profile_dataset(file_path: Path):
    lines = []
    
    def log(msg=""):
        lines.append(str(msg))
        print(msg)

    log("=" * 80)
    log("           FINsight 360 - RAW DATASET PROFILE REPORT")
    log("=" * 80)
    log()

    # 1. File Metadata
    file_size_bytes = os.path.getsize(file_path)
    file_size_mb = file_size_bytes / (1024 * 1024)
    log("1. FILE INFORMATION")
    log("-" * 80)
    log(f"File Name      : {file_path.name}")
    log(f"Absolute Path  : {file_path}")
    log(f"File Size      : {file_size_mb:.2f} MB ({file_size_bytes:,} bytes)")
    log()

    # Load dataset
    log("Loading dataset with pandas...")
    df = pd.read_csv(file_path)
    total_rows, total_cols = df.shape
    log(f"Dataset successfully loaded. Total Rows: {total_rows:,}, Total Columns: {total_cols}")
    log()

    # 2. Dimensions & Structure
    log("2. DATASET DIMENSIONS & SCHEMA OVERVIEW")
    log("-" * 80)
    log(f"Total Row Count    : {total_rows:,}")
    log(f"Total Column Count : {total_cols}")
    log()
    log(f"{'No.':<4} {'Column Name':<35} {'Detected dtype':<18}")
    log("-" * 60)
    for idx, (col_name, dtype) in enumerate(df.dtypes.items(), 1):
        log(f"{idx:<4} {col_name:<35} {str(dtype):<18}")
    log()

    # 3. Missing Values
    log("3. MISSING (NULL) VALUES ANALYSIS")
    log("-" * 80)
    null_counts = df.isnull().sum()
    null_pcts = (null_counts / total_rows) * 100
    has_nulls = False
    log(f"{'Column Name':<35} {'Null Count':<12} {'Null Percentage':<15}")
    log("-" * 65)
    for col in df.columns:
        cnt = null_counts[col]
        pct = null_pcts[col]
        if cnt > 0:
            has_nulls = True
        log(f"{col:<35} {cnt:<12,} {pct:>6.2f}%")
    if not has_nulls:
        log("\n[Summary] No missing values detected across all columns (100% complete).")
    log()

    # 4. Duplicate Rows
    log("4. DUPLICATE ROWS ANALYSIS")
    log("-" * 80)
    exact_duplicates = df.duplicated().sum()
    dup_pct = (exact_duplicates / total_rows) * 100 if total_rows > 0 else 0.0
    log(f"Total Exact Duplicate Rows : {exact_duplicates:,} ({dup_pct:.2f}%)")
    log()

    # Identify column types
    date_cols = [
        c for c in df.columns 
        if any(keyword in c.lower() for keyword in ["time", "date", "ts"])
    ]
    numeric_cols = list(df.select_dtypes(include=[np.number]).columns)
    # Exclude date cols from numeric if any, though usually dates are object or datetime
    numeric_cols = [c for c in numeric_cols if c not in date_cols]
    text_categorical_cols = [
        c for c in df.columns 
        if c not in numeric_cols and c not in date_cols
    ]

    # 5. Date / Timestamp Columns
    log("5. DATE & TIMESTAMP COLUMNS ANALYSIS")
    log("-" * 80)
    if not date_cols:
        log("No date/timestamp columns identified by name pattern.")
    else:
        for col in date_cols:
            log(f"Column: '{col}' (Original dtype: {df[col].dtype})")
            try:
                # Attempt conversion
                dt_series = pd.to_datetime(df[col], errors='coerce')
                valid_count = dt_series.notnull().sum()
                invalid_count = dt_series.isnull().sum() - df[col].isnull().sum()
                min_date = dt_series.min()
                max_date = dt_series.max()
                date_range_days = (max_date - min_date).total_seconds() / 86400.0 if pd.notnull(min_date) and pd.notnull(max_date) else None
                
                log(f"  Valid Parsed Timestamps : {valid_count:,} / {total_rows:,}")
                if invalid_count > 0:
                    log(f"  Failed to Parse         : {invalid_count:,}")
                log(f"  Earliest Date (Min)     : {min_date}")
                log(f"  Latest Date (Max)       : {max_date}")
                if date_range_days is not None:
                    log(f"  Date Range in Days      : {date_range_days:.2f} days (~{date_range_days / 30.4375:.1f} months)")
            except Exception as e:
                log(f"  Error parsing dates in '{col}': {e}")
            log()

    # 6. Text / Categorical Columns
    log("6. TEXT & CATEGORICAL COLUMNS ANALYSIS")
    log("-" * 80)
    if not text_categorical_cols:
        log("No non-numeric, non-date categorical columns found.")
    else:
        for col in text_categorical_cols:
            cardinality = df[col].nunique(dropna=False)
            log(f"Column: '{col}'")
            log(f"  Cardinality (Unique Values): {cardinality:,}")
            log("  Top 5 Most Frequent Values :")
            val_counts = df[col].value_counts(dropna=False).head(5)
            for rank, (val, cnt) in enumerate(val_counts.items(), 1):
                pct = (cnt / total_rows) * 100
                display_val = "<NULL>" if pd.isna(val) else repr(val)
                log(f"    {rank}. {display_val:<25} Count: {cnt:>8,} ({pct:>5.2f}%)")
            log()

    # 7. Numeric Columns Summary Statistics
    log("7. NUMERIC COLUMNS SUMMARY STATISTICS")
    log("-" * 80)
    if not numeric_cols:
        log("No numeric columns found.")
    else:
        stats_header = f"{'Column Name':<35} {'Min':<14} {'Max':<14} {'Mean':<14} {'Median':<14}"
        log(stats_header)
        log("-" * 95)
        for col in numeric_cols:
            col_min = df[col].min()
            col_max = df[col].max()
            col_mean = df[col].mean()
            col_median = df[col].median()
            
            # Format numbers intelligently (integer vs float)
            def fmt_num(val):
                if pd.isna(val):
                    return "N/A"
                if isinstance(val, (int, np.integer)) or (isinstance(val, float) and val.is_integer() and abs(val) < 1e9):
                    return f"{val:,.0f}" if abs(val) >= 1000 else f"{val:.0f}"
                return f"{val:,.4f}" if abs(val) >= 1000 else f"{val:.4f}"

            log(f"{col:<35} {fmt_num(col_min):<14} {fmt_num(col_max):<14} {fmt_num(col_mean):<14} {fmt_num(col_median):<14}")
        log()

    log("=" * 80)
    log("                     END OF DATASET PROFILE REPORT")
    log("=" * 80)

    # Save to report file
    report_candidates = [
        Path("reports/raw_data_profile.txt"),
        Path(__file__).resolve().parent.parent / "reports" / "raw_data_profile.txt"
    ]
    report_path = report_candidates[0]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    
    print(f"\n[SUCCESS] Profile report saved to: {report_path.resolve()}")

if __name__ == "__main__":
    raw_csv = find_raw_file()
    profile_dataset(raw_csv)
