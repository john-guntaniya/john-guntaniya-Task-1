"""
DecodeLabs — Project 1: Data Cleaning & Preparation
=====================================================
Goal: Clean the raw e-commerce order dataset by handling missing values,
duplicates, and incorrect data — following the 3-phase process from the
project brief:

  Phase 1: Strategic Imputation   -> handle missing values (don't just delete)
  Phase 2: The Integrity Audit    -> remove duplicates, unique IDs must be unique
  Phase 3: Speak One Language     -> standardize formats (dates, text, numbers)

Verification Gate (must pass before "Project 2"):
  - 0% duplicate Order IDs
  - 0% incorrectly formatted dates

Every change is written to a Change Log so the transformation is fully
auditable ("If it isn't documented, it didn't happen").

Usage:
    python clean_data.py
"""

import pandas as pd
import numpy as np
from datetime import datetime

RAW_FILE = "Dataset_for_Data_Analytics.xlsx"
CLEAN_FILE = "Cleaned_Dataset.xlsx"

change_log = []  # list of dicts: Change ID, Description, Impact, Status


def log_change(change_id, description, impact, status="Resolved"):
    change_log.append(
        {"Change ID": change_id, "Description": description,
         "Impact": impact, "Status": status}
    )


def main():
    print("=" * 70)
    print("DECODELABS | PROJECT 1: DATA CLEANING & PREPARATION")
    print("=" * 70)

    # ------------------------------------------------------------------
    # STEP 0: LOAD & INSPECT
    # ------------------------------------------------------------------
    df = pd.read_excel(RAW_FILE)
    raw_rows = len(df)
    print(f"\n[STEP 0] Loaded raw dataset: {raw_rows} rows x {df.shape[1]} columns")
    print("\nColumn dtypes:")
    print(df.dtypes)

    print("\nMissing values per column:")
    missing = df.isnull().sum()
    print(missing[missing > 0] if missing.sum() else "  None found.")

    # ------------------------------------------------------------------
    # PHASE 1: STRATEGIC IMPUTATION — Handle the Gaps. Don't just delete.
    # ------------------------------------------------------------------
    print("\n[PHASE 1] Strategic Imputation")

    # CouponCode: a blank means "no coupon was applied at checkout" — this is
    # a legitimate business state, not a data-entry gap, so we impute with an
    # explicit label rather than dropping rows or using mean/median/mode
    # (which would be meaningless for a categorical code).
    n_missing_coupon = df["CouponCode"].isnull().sum()
    if n_missing_coupon:
        df["CouponCode"] = df["CouponCode"].fillna("No Coupon")
        log_change(
            "CR001",
            "Imputed missing 'CouponCode' values with explicit label 'No Coupon'",
            f"Preserved {n_missing_coupon} records (no rows deleted)",
        )
        print(f"  -> Filled {n_missing_coupon} missing CouponCode values with 'No Coupon'")
    else:
        print("  -> No missing CouponCode values found.")

    # Numeric columns: median imputation for any missing values (robust to outliers)
    numeric_cols = ["Quantity", "UnitPrice", "ItemsInCart", "TotalPrice"]
    for col in numeric_cols:
        n_missing = df[col].isnull().sum()
        if n_missing:
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
            log_change(
                f"CR-{col}",
                f"Imputed missing '{col}' values using column median ({median_val})",
                f"Preserved {n_missing} records",
            )
            print(f"  -> Filled {n_missing} missing '{col}' values with median ({median_val})")

    # Any remaining missing values in categorical/text columns -> "Unknown"
    for col in df.columns:
        n_missing = df[col].isnull().sum()
        if n_missing and col not in ["CouponCode"] + numeric_cols:
            df[col] = df[col].fillna("Unknown")
            log_change(
                f"CR-{col}",
                f"Imputed missing '{col}' values with placeholder 'Unknown'",
                f"Preserved {n_missing} records",
            )
            print(f"  -> Filled {n_missing} missing '{col}' values with 'Unknown'")

    if not any(c["Description"].startswith("Imputed missing '") for c in change_log) and n_missing_coupon == 0:
        print("  -> No further imputation required — dataset was already complete elsewhere.")

    # ------------------------------------------------------------------
    # PHASE 2: THE INTEGRITY AUDIT — One Truth, One Record.
    # ------------------------------------------------------------------
    print("\n[PHASE 2] Integrity Audit")

    # 2a. Exact full-row duplicates
    n_exact_dupes = df.duplicated().sum()
    if n_exact_dupes:
        df = df.drop_duplicates(keep="first")
        log_change("CR002", "Removed exact duplicate rows", f"Removed {n_exact_dupes} rows")
        print(f"  -> Removed {n_exact_dupes} exact duplicate rows")
    else:
        print("  -> No exact duplicate rows found.")

    # 2b. Duplicate unique identifiers (OrderID) — "GROUP BY Order_ID HAVING COUNT(*) > 1"
    dupe_order_mask = df.duplicated(subset=["OrderID"], keep="first")
    n_dupe_orders = dupe_order_mask.sum()
    if n_dupe_orders:
        df = df[~dupe_order_mask]
        log_change(
            "CR003",
            "Eliminated inflated transaction counts (duplicate OrderID retained first occurrence only)",
            f"Removed {n_dupe_orders} duplicate OrderID rows",
        )
        print(f"  -> Removed {n_dupe_orders} rows with duplicate OrderID")
    else:
        print("  -> OrderID is 100% unique. No duplicate identifiers found.")

    # ------------------------------------------------------------------
    # PHASE 3: SPEAK ONE LANGUAGE — Standardize formats
    # ------------------------------------------------------------------
    print("\n[PHASE 3] Format Standardization")

    # 3a. Dates -> ISO 8601 (YYYY-MM-DD)
    before_dtype = str(df["Date"].dtype)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    n_bad_dates = df["Date"].isnull().sum()
    if n_bad_dates:
        # Could not be parsed at all — flag rather than silently drop
        log_change(
            "CR004",
            "Flagged unparseable Date values (could not coerce to ISO 8601)",
            f"{n_bad_dates} rows flagged",
            status="Needs Review",
        )
        print(f"  -> WARNING: {n_bad_dates} Date values could not be parsed.")
    df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
    log_change("CR005", "Standardized 'Date' column to ISO 8601 (YYYY-MM-DD)",
               f"Applied to all {len(df)} rows (was {before_dtype})")
    print(f"  -> Standardized all dates to ISO 8601 (YYYY-MM-DD)")

    # 3b. Text columns -> trim whitespace + consistent title/proper case
    text_cols = ["Product", "ShippingAddress", "PaymentMethod",
                 "OrderStatus", "ReferralSource"]
    code_cols = ["CouponCode"]  # promo codes: trim only, never re-case (e.g. SAVE10 must stay SAVE10)
    id_cols = ["OrderID", "CustomerID", "TrackingNumber"]

    total_text_fixes = 0
    for col in text_cols:
        original = df[col].astype(str)
        cleaned = original.str.strip().str.replace(r"\s+", " ", regex=True)
        cleaned = cleaned.str.title()
        n_changed = (original != cleaned).sum()
        total_text_fixes += n_changed
        df[col] = cleaned
    if total_text_fixes:
        log_change("CR006", "Trimmed whitespace and applied consistent Title Case to text columns",
                    f"{total_text_fixes} cell values normalized across {len(text_cols)} columns")
        print(f"  -> Normalized casing/whitespace on {total_text_fixes} text cells")
    else:
        print("  -> Text columns already clean (no whitespace/case issues).")

    # Promo/coupon codes: trim only — never re-case (SAVE10 must stay SAVE10, not Save10)
    total_code_fixes = 0
    for col in code_cols:
        original = df[col].astype(str)
        cleaned = original.str.strip().str.replace(r"\s+", " ", regex=True)
        n_changed = (original != cleaned).sum()
        total_code_fixes += n_changed
        df[col] = cleaned
    if total_code_fixes:
        log_change("CR006b", "Trimmed whitespace on promo code column (case preserved)",
                    f"{total_code_fixes} cell values normalized")
        print(f"  -> Trimmed whitespace on {total_code_fixes} CouponCode cells")
    else:
        print("  -> CouponCode already clean.")

    # 3c. ID columns -> trim whitespace, uppercase (IDs are codes, not prose)
    total_id_fixes = 0
    for col in id_cols:
        original = df[col].astype(str)
        cleaned = original.str.strip().str.upper()
        n_changed = (original != cleaned).sum()
        total_id_fixes += n_changed
        df[col] = cleaned
    if total_id_fixes:
        log_change("CR007", "Trimmed whitespace and standardized casing on ID columns",
                    f"{total_id_fixes} cell values normalized across {len(id_cols)} columns")
        print(f"  -> Normalized {total_id_fixes} ID cells")
    else:
        print("  -> ID columns already clean.")

    # 3d. Numeric precision -> 2 decimal places for currency fields
    for col in ["UnitPrice", "TotalPrice"]:
        df[col] = df[col].astype(float).round(2)
    log_change("CR008", "Enforced 2-decimal numeric precision on 'UnitPrice' and 'TotalPrice'",
                f"Applied to all {len(df)} rows")
    print("  -> Rounded currency fields to 2 decimal places")

    # 3e. Recompute / validate TotalPrice = Quantity x UnitPrice
    expected_total = (df["Quantity"] * df["UnitPrice"]).round(2)
    mismatch_mask = (df["TotalPrice"] - expected_total).abs() > 0.02
    n_mismatch = mismatch_mask.sum()
    if n_mismatch:
        df.loc[mismatch_mask, "TotalPrice"] = expected_total[mismatch_mask]
        log_change("CR009", "Recalculated 'TotalPrice' where it did not equal Quantity x UnitPrice",
                    f"Corrected {n_mismatch} rows")
        print(f"  -> Corrected {n_mismatch} rows where TotalPrice != Quantity x UnitPrice")
    else:
        print("  -> TotalPrice consistent with Quantity x UnitPrice for all rows.")

    # 3f. Business-rule sanity checks: non-positive Quantity / UnitPrice
    bad_qty = (df["Quantity"] <= 0).sum()
    bad_price = (df["UnitPrice"] <= 0).sum()
    if bad_qty:
        log_change("CR010", "Flagged rows with non-positive Quantity", f"{bad_qty} rows flagged",
                    status="Needs Review")
        print(f"  -> WARNING: {bad_qty} rows have Quantity <= 0")
    if bad_price:
        log_change("CR011", "Flagged rows with non-positive UnitPrice", f"{bad_price} rows flagged",
                    status="Needs Review")
        print(f"  -> WARNING: {bad_price} rows have UnitPrice <= 0")
    if not bad_qty and not bad_price:
        print("  -> No non-positive Quantity/UnitPrice values found.")

    df = df.reset_index(drop=True)

    # ------------------------------------------------------------------
    # VERIFICATION GATE (per brief: "0% duplicate IDs, 0% bad date formats")
    # ------------------------------------------------------------------
    print("\n[VERIFICATION GATE]")
    dup_id_rate = df["OrderID"].duplicated().sum() / len(df) * 100
    bad_date_rate = df["Date"].apply(
        lambda x: True if not _is_iso_date(x) else False
    ).sum() / len(df) * 100
    print(f"  Duplicate OrderID rate : {dup_id_rate:.2f}%  {'PASS' if dup_id_rate == 0 else 'FAIL'}")
    print(f"  Bad date format rate   : {bad_date_rate:.2f}%  {'PASS' if bad_date_rate == 0 else 'FAIL'}")

    # ------------------------------------------------------------------
    # SAVE OUTPUTS
    # ------------------------------------------------------------------
    log_df = pd.DataFrame(change_log)
    with pd.ExcelWriter(CLEAN_FILE, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Cleaned_Data", index=False)
        log_df.to_excel(writer, sheet_name="Change_Log", index=False)

    print("\n" + "=" * 70)
    print(f"DONE. {raw_rows} raw rows -> {len(df)} clean rows.")
    print(f"Saved: {CLEAN_FILE}  (sheets: 'Cleaned_Data', 'Change_Log')")
    print("=" * 70)


def _is_iso_date(s):
    try:
        datetime.strptime(str(s), "%Y-%m-%d")
        return True
    except ValueError:
        return False


if __name__ == "__main__":
    main()
