# john-guntaniya-Task-1
# Data Cleaning & Preparation — DecodeLabs Project 1

Cleans a raw e-commerce order dataset (1,200 records) by handling missing
values, duplicates, and inconsistent formatting — turning it into a
reliable, analysis-ready source of truth.

## Overview

This project follows a 3-phase cleaning process:

| Phase | What it does |
|---|---|
| **1. Strategic Imputation** | Fills missing values sensibly instead of dropping rows (e.g. blank `CouponCode` → `"No Coupon"`, numeric gaps → column median) |
| **2. Integrity Audit** | Removes exact duplicate rows and duplicate `OrderID` records, keeping the first occurrence |
| **3. Speak One Language** | Standardizes dates to ISO 8601, trims/normalizes text and ID casing, rounds currency to 2 decimals, and recalculates `TotalPrice` where it doesn't match `Quantity × UnitPrice` |

Every change made to the data is written to an auditable **Change Log**
(Change ID, Description, Impact, Status) so the transformation can be
reviewed end to end.

Before finishing, the script runs a **verification gate** and reports:
- Duplicate `OrderID` rate (must be 0%)
- Incorrectly formatted date rate (must be 0%)

## Repository Structure

```
.
├── clean_data.py               # Main cleaning script
├── Dataset_for_Data_Analytics.xlsx   # Raw input dataset (not tracked if private)
├── Cleaned_Dataset.xlsx        # Output: cleaned data + change log
└── README.md
```

Install dependencies:

```bash
pip install pandas openpyxl
```

## Usage

1. Place `Dataset_for_Data_Analytics.xlsx` in the same directory as
   `clean_data.py`.
2. Run the script:

```bash
python clean_data.py
```

3. Output is written to `Cleaned_Dataset.xlsx`, containing two sheets:
   - **Cleaned_Data** — the fully cleaned dataset
   - **Change_Log** — a record of every transformation applied, with row-level impact counts

## Sample Output

```
======================================================================
DECODELABS | PROJECT 1: DATA CLEANING & PREPARATION
======================================================================

[STEP 0] Loaded raw dataset: 1200 rows x 14 columns

[PHASE 1] Strategic Imputation
  -> Filled 309 missing CouponCode values with 'No Coupon'

[PHASE 2] Integrity Audit
  -> No exact duplicate rows found.
  -> OrderID is 100% unique. No duplicate identifiers found.

[PHASE 3] Format Standardization
  -> Standardized all dates to ISO 8601 (YYYY-MM-DD)
  -> Rounded currency fields to 2 decimal places
  -> TotalPrice consistent with Quantity x UnitPrice for all rows.

[VERIFICATION GATE]
  Duplicate OrderID rate : 0.00%  PASS
  Bad date format rate   : 0.00%  PASS

======================================================================
DONE. 1200 raw rows -> 1200 clean rows.
Saved: Cleaned_Dataset.xlsx  (sheets: 'Cleaned_Data', 'Change_Log')
======================================================================
```

## Dataset Fields

| Column | Description |
|---|---|
| `OrderID` | Unique order identifier |
| `Date` | Order date (standardized to `YYYY-MM-DD`) |
| `CustomerID` | Unique customer identifier |
| `Product` | Product name |
| `Quantity` | Units ordered |
| `UnitPrice` | Price per unit (USD) |
| `ShippingAddress` | Delivery address |
| `PaymentMethod` | Payment type used |
| `OrderStatus` | Current order status |
| `TrackingNumber` | Shipment tracking code |
| `ItemsInCart` | Total items in cart at checkout |
| `CouponCode` | Promo code applied, if any |
| `ReferralSource` | Marketing channel that drove the order |
| `TotalPrice` | `Quantity × UnitPrice` (validated/recalculated) |

