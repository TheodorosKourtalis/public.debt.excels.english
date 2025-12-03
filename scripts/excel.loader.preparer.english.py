# -*- coding: utf-8 -*-
"""
MASTER GITHUB EXCEL LOADER (Final Robust Version + Deduplication)
Output Directory: /Users/thodoreskourtales/dyn.macro/project.1/
"""

import urllib.parse
import urllib.request
import pandas as pd
import io
import time
import os
import re
import hashlib
from datetime import datetime

# --- 1. SETUP OUTPUT DIRECTORY ---
OUTPUT_DIR = "/Users/thodoreskourtales/dyn.macro/project.1/"
os.makedirs(OUTPUT_DIR, exist_ok=True)
print(f"📂 Output directory set to: {OUTPUT_DIR}")

# --- 2. CONFIGURATION ---
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36)"
)
RETRIES = 3

# Flags
WRITE_COMBINED = True
WRITE_WIDE = True
WRITE_WIDE_BY_FREQ = True

# Output Paths
COMBINED_OUT = os.path.join(OUTPUT_DIR, "combined_cleaned.xlsx")
WIDE_OUT = os.path.join(OUTPUT_DIR, "combined_wide.xlsx")
WIDE_BY_FREQ_OUT = os.path.join(OUTPUT_DIR, "combined_wide_by_freq.xlsx")

# --- 3. URLS ---
REPO_BASE = "https://github.com/TheodorosKourtalis/public.debt.excels.english/blob/main/"
FILENAMES = [
    "Annual_deflator_of_GDP_and_expenditure_components.xlsx",
    "Average_duration_of_Central_Government_debt.xlsx",
    "Budget_balance_primary_budget_balance_and_interest_payments_(annual_data_1995-present)-1.xlsx",
    "Budget_balance_primary_budget_balance_and_interest_payments_(annual_data_1995-present).xlsx",
    "Capital_stock_by_economic_sector.xlsx",
    "Capital_stock_decomposed_by_asset_type.xlsx",
    "Capital_stock_of_Financial_Corporations.xlsx",
    "Capital_stock_of_General_Government.xlsx",
    "Capital_stock_of_Households.xlsx",
    "Capital_stock_of_Non-Financial_Corporations.xlsx",
    "Capital_stock_of_institutional_sectors.xlsx",
    "Central_Government_Debt_by_duration.xlsx",
    "Consumption_per_capita.xlsx",
    "Contribution_to_real_annual_growth_.xlsx",
    "Contribution_to_real_quarterly_growth_seasonally_adjusted.xlsx",
    "Contributions_to_real_annual_growth.xlsx",
    "Direct_taxes_by_source-1.xlsx",
    "Direct_taxes_by_source.xlsx",
    "Fixed_Investment_and_Inventories_not_seasonally_adjusted.xlsx",
    "Fixed_Investment_and_Inventories_seasonally_adjusted.xlsx",
    "Fixed_investment_breakdown_by_sector.xlsx",
    "Fixed_investment_by_asset_type_not_seasonally_adjusted.xlsx",
    "Fixed_investment_by_asset_type_seasonally_adjusted.xlsx",
    "GDP_not_seasonally_adjusted_.xlsx",
    "GDP_per_capita.xlsx",
    "GDP_seasonally_adjusted-1.xlsx",
    "GDP_seasonally_adjusted-2.xlsx",
    "General_Government_Debt_(annual_data_1995-present)-1.xlsx",
    "General_Government_Debt_(annual_data_1995-present).xlsx",
    "General_government_debt_by_debt_instrument_(annual_data_1995-present).xlsx",
    "General_government_debt_by_debt_instrument_(quarterly_data_2000-present).xlsx",
    "Government_Expenditures_Revenues_and_Budget_Balance_(annual_data_1995-present).xlsx",
    "Government_Expenditures_Revenues_and_Budget_Balance_(quarterly_data_1999-present).xlsx",
    "Government_Spending_Consumption_and_Investment_not_seasonally_adjusted.xlsx",
    "Government_Spending_Consumption_and_Investment_seasonally_adjusted.xlsx",
    "Government_and_Private_Fixed_Investment_not_seasonally_adjusted.xlsx",
    "Government_and_Private_Fixed_Investment_seasonally_adjusted.xlsx",
    "Government_and_private_consumption_not_seasonally_adjusted.xlsx",
    "Government_and_private_consumption_seasonally_adjusted_.xlsx",
    "Government_expenditures_by_function-1.xlsx",
    "Government_expenditures_by_function.xlsx",
    "Government_expenditures_by_use_(annual_data_1995-present).xlsx",
    "Government_expenditures_by_use_(quarterly_data_1999-present).xlsx",
    "Government_revenues_by_source_(annual_data_1995-present).xlsx",
    "Government_revenues_by_source_(quarterly_data_1999-present)_.xlsx",
    "Gross_Value_Added_not_seasonally_adjusted.xlsx",
    "Gross_Value_Added_seasonally_adjusted.xlsx",
    "Growth_rate_in_nominal_and_real_GDP.xlsx",
    "Indirect_taxes_by_source-1.xlsx",
    "Indirect_taxes_by_source.xlsx",
    "Net_exports_not_seasonally_adjusted.xlsx",
    "Net_exports_seasonally_adjusted.xlsx",
    "Nominal_GDP.xlsx",
    "Public_debt_for_different_levels_of_government_(annual_data_1995-present).xlsx",
    "Public_debt_for_different_levels_of_government_(quarterly_data_2000-present).xlsx",
    "Quarterly_deflator_of_GDP_and_expenditure_components.xlsx",
    "Real_GDP.xlsx",
    "Social_contributions_by_contributor-1.xlsx",
    "Social_contributions_by_contributor.xlsx",
    "Social_contributions_by_type_of_contribution.xlsx"
]
URLS = [REPO_BASE + f for f in FILENAMES]

# === 4. HELPERS ===

def normalize_url(url: str) -> str:
    url = url.replace("/blob/", "/raw/")
    parsed = urllib.parse.urlparse(url)
    q = urllib.parse.parse_qs(parsed.query)
    q["raw"] = ["1"]
    return urllib.parse.quote(urllib.parse.urlunparse(parsed._replace(query=urllib.parse.urlencode(q, doseq=True))), safe=':/?=&%')

def check_url(url: str) -> int:
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=10) as resp: return resp.status
    except: return 200 

def fetch_bytes(url: str) -> bytes:
    for _ in range(RETRIES):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=30) as resp: return resp.read()
        except: time.sleep(1)
    raise RuntimeError("Download failed")

# === 5. EXCEL PARSING LOGIC ===

KNOWN_PLACEHOLDERS = [
    "Τιμές Στήλης", "Column Values", "Values", "Columns", 
    "Metric", "Variables", "Indicators"
]
POSSIBLE_DATE_COLS = ["Date", "Year", "Quarter", "Ημερομηνία", "Έτος"]

def _clean_txt(x):
    return re.sub(r"\s+", " ", str(x).strip()) if pd.notna(x) else ""

def _parse_date_col(df):
    df = df.copy()
    found_col = None
    
    for col in df.columns:
        if str(col).strip() in POSSIBLE_DATE_COLS:
            found_col = col
            break
            
    if not found_col and len(df.columns) > 0:
        first_col = df.columns[0]
        sample = df[first_col].dropna().head(5).astype(str)
        if sample.str.match(r'^\d{4}$').all() or sample.str.match(r'^\d{4}-\d{2}$').all():
            found_col = first_col

    if found_col:
        df.rename(columns={found_col: "Date"}, inplace=True)
        try:
            date_vals = df["Date"].astype(str)
            df["Date"] = pd.to_datetime(date_vals, errors='coerce')
        except: pass
        return df[~df["Date"].isna()]
    return df

def _coerce_numeric(df):
    for c in df.columns:
        if c == "Date": continue
        if df[c].dtype.kind in 'biufc': continue
        
        s = df[c].astype(str).str.replace(r"[^\d,\.-]", "", regex=True)
        if s.str.match(r'.*,\d{1,2}$').any():
            s = s.str.replace(".", "").str.replace(",", ".")
        else:
            s = s.str.replace(",", "")
        df[c] = pd.to_numeric(s, errors='coerce')
    return df

def flatten_excel(xl, sheet_name, fname):
    try:
        df = pd.read_excel(xl, sheet_name=sheet_name, header=[0, 1])
        new_cols = []
        for cat, unit in df.columns:
            c_txt = _clean_txt(cat)
            u_txt = _clean_txt(unit)
            if c_txt in KNOWN_PLACEHOLDERS or "Unnamed" in c_txt:
                if "Date" in u_txt or "Year" in u_txt: new_cols.append("Date")
                elif u_txt: new_cols.append(f"{fname} | {u_txt}")
                else: new_cols.append(f"{fname} | {c_txt}")
            else:
                new_cols.append(f"{fname} | {c_txt} ({u_txt})")
        df.columns = new_cols
        if len(df) > 0:
            first_val = str(df.iloc[0,0])
            if "Date" in first_val or "Year" in first_val: df = df.iloc[1:]
            elif first_val == "nan" and len(df) > 1 and ("Date" in str(df.iloc[1,0]) or str(df.iloc[1,0]).isdigit()): df = df.iloc[1:]
        return _coerce_numeric(_parse_date_col(df))
    except: pass

    try:
        df = pd.read_excel(xl, sheet_name=sheet_name, header=0)
        df = _parse_date_col(df)
        if "Date" in df.columns:
            non_date = [c for c in df.columns if c != "Date"]
            mapper = {c: f"{fname} | {c}" for c in non_date}
            df.rename(columns=mapper, inplace=True)
            return _coerce_numeric(df)
    except: pass
    return None

# === 6. MAIN EXECUTION + DEDUPLICATION ===

print("=== PROCESSING FILES ===")
BOOKS = {}
seen_hashes = set() # To store data hashes

for i, raw in enumerate(URLS, start=1):
    fname = raw.split('/')[-1].replace(".xlsx", "")
    normalized = normalize_url(raw)
    
    print(f"\n[{i}] 📥 {fname}")
    
    try:
        blob = fetch_bytes(normalized)
        xl = pd.ExcelFile(io.BytesIO(blob), engine="openpyxl")
        
        BOOKS[fname] = {}
        
        for sheet in xl.sheet_names:
            if any(x in sheet.lower() for x in ["info", "meta", "title", "back"]): continue
            
            df = flatten_excel(xl, sheet, fname)
            
            if df is not None and not df.empty and "Date" in df.columns:
                # --- DEDUPLICATION LOGIC ---
                # We hash the data content (excluding the filename part of columns)
                # to detect if the *numbers* are identical to a previous file.
                
                # Create a standardized version for hashing
                df_hash = df.copy().sort_values("Date").reset_index(drop=True)
                # Remove filename prefix from columns for pure content comparison
                df_hash.columns = [c.split('|')[-1].strip() if '|' in c else c for c in df_hash.columns]
                
                # Convert to string and hash
                data_str = df_hash.to_string()
                data_hash = hashlib.md5(data_str.encode('utf-8')).hexdigest()
                
                if data_hash in seen_hashes:
                    print(f"    🗑️  Duplicate data found in sheet '{sheet}'. Skipping.")
                    continue
                
                seen_hashes.add(data_hash)
                BOOKS[fname][sheet] = df
                
                cols = len(df.columns) - 1
                dates = df["Date"].sort_values()
                rng = f"{dates.iloc[0].date()} to {dates.iloc[-1].date()}"
                print(f"    ✅ Sheet '{sheet}': {rng}, {cols} metrics")
            else:
                if "info" not in sheet.lower():
                    print(f"    ⚠️  Sheet '{sheet}': Could not extract data.")

    except Exception as e:
        print(f"    ❌ Error: {e}")

# === 7. SAVING ===

if WRITE_WIDE:
    print("\n💾 Saving Wide Format...")
    all_dfs = []
    for fname, sheets in BOOKS.items():
        for sheet, df in sheets.items():
            if df is not None and "Date" in df.columns:
                df_grouped = df.groupby("Date").mean(numeric_only=True).reset_index()
                all_dfs.append(df_grouped.set_index("Date"))
    
    if all_dfs:
        wide_df = pd.concat(all_dfs, axis=1, join="outer").sort_index().reset_index()
        wide_df.to_excel(WIDE_OUT, index=False)
        print(f"✅ Saved: {WIDE_OUT}")

if WRITE_WIDE_BY_FREQ:
    print("\n💾 Saving Wide Format By Frequency...")
    freq_buckets = {"Annual": [], "Quarterly": [], "Monthly": [], "Other": []}
    
    for fname, sheets in BOOKS.items():
        for sheet, df in sheets.items():
            if df is not None and "Date" in df.columns and len(df) > 3:
                df = df.sort_values("Date")
                dates = df["Date"]
                delta = (dates.iloc[1] - dates.iloc[0]).days
                
                if 360 <= delta <= 366: key = "Annual"
                elif 88 <= delta <= 92: key = "Quarterly"
                elif 28 <= delta <= 31: key = "Monthly"
                else: key = "Other"
                
                df_grouped = df.groupby("Date").mean(numeric_only=True).reset_index().set_index("Date")
                freq_buckets[key].append(df_grouped)

    if any(freq_buckets.values()):
        with pd.ExcelWriter(WIDE_BY_FREQ_OUT, engine="openpyxl") as writer:
            for freq, dfs in freq_buckets.items():
                if dfs:
                    combined = pd.concat(dfs, axis=1, join="outer").sort_index().reset_index()
                    combined.to_excel(writer, sheet_name=freq, index=False)
                    print(f"   Saved sheet: {freq} ({len(combined)} rows)")
        print(f"✅ Saved: {WIDE_BY_FREQ_OUT}")

print("\n=== DONE ===")
