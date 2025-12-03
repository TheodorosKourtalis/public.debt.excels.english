import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import textwrap
import sys
import re  # Imported for cleaning text
import matplotlib.patheffects as pe  # Import for the white halo effect
import os

# -----------------------------------------------------------------------------
# 1. SETUP & STYLE: "CLASSIC LUXURY"
# -----------------------------------------------------------------------------
plt.style.use('default')

CLASSIC_COLORS = {
    'navy': '#002E5D',
    'burgundy': '#800020',
    'gold': '#C5A059',
    'forest': '#2E4600',
    'slate': '#4B5358',
    'teal': '#006666',
    'rust': '#8B3A3A',
    'olive': '#556B2F',
    'sand': '#E6DCC3',
    'bg': '#FDFBF7',
    'grid': '#DCDCDC',
    'highlight': '#FF0000'
}

plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'DejaVu Serif', 'Garamond'],
    'font.size': 14,
    'axes.facecolor': CLASSIC_COLORS['bg'],
    'figure.facecolor': CLASSIC_COLORS['bg'],
    'axes.edgecolor': 'black',
    'axes.grid': True,
    'grid.alpha': 0.5,
    'grid.color': CLASSIC_COLORS['grid'],
    'grid.linestyle': '--',
    'axes.titlesize': 22,
    'axes.titleweight': 'bold',
    'axes.labelsize': 14,
    'text.color': 'black',
    'axes.labelcolor': 'black',
    'xtick.color': 'black',
    'ytick.color': 'black',
    'lines.linewidth': 2.5
})

# -----------------------------------------------------------------------------
# 2. DATA LOADING
# -----------------------------------------------------------------------------
GITHUB_URL = "https://github.com/TheodorosKourtalis/public.debt.excels.english/raw/main/combined_wide_by_freq.xlsx"
FILE_NAME = 'combined_wide_by_freq.xlsx'

print(f"Attempting to load data...")
try:
    if os.path.exists(FILE_NAME):
        df = pd.read_excel(FILE_NAME, sheet_name='Annual', engine='openpyxl')
        print("Local data loaded successfully.")
    else:
        raise FileNotFoundError("Local file not found.")
except Exception:
    try:
        df = pd.read_excel(GITHUB_URL, sheet_name='Annual', engine='openpyxl')
        print("Data loaded successfully from GitHub.")
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit()

if 'Date' in df.columns:
    try:
        df['Date'] = pd.to_datetime(df['Date'])
    except:
        df['Date'] = pd.to_datetime(df['Date'], format='%Y')
    df = df.sort_values('Date')
else:
    sys.exit("Error: 'Date' column not found.")

# -----------------------------------------------------------------------------
# 3. MAPPING
# -----------------------------------------------------------------------------
cols = df.columns.tolist()

def get_col(keywords):
    matches = [c for c in cols if all(k.lower() in c.lower() for k in keywords)]
    return matches[0] if matches else None

# --- Existing Macros ---
col_nom_gdp = get_col(['Nominal Gross Domestic Product'])
col_real_gdp = get_col(['Real Gross Domestic Product'])
col_budget_bal_gdp = get_col(['Budget balance', 'GDP share'])
col_debt_gdp = get_col(['General Government Consolidated Debt', 'GDP share'])
if not col_debt_gdp: col_debt_gdp = get_col(['General government', 'GDP share', 'debt'])

# --- Granular Revenue ---
col_rev_total_gdp = get_col(['Government_revenues', 'Total', 'GDP share'])
col_tax_vat_gdp = get_col(['Value added taxes', 'GDP share'])
col_tax_inc_gdp = get_col(['Taxes on individual income', 'GDP share'])
col_tax_corp_gdp = get_col(['Taxes on corporate profits', 'GDP share'])
col_tax_prop_gdp = get_col(['Taxes on land and buildings', 'GDP share'])
col_soc_cont_gdp = get_col(['Total social contributions', 'GDP share'])
if not col_soc_cont_gdp: col_soc_cont_gdp = get_col(['Social contributions', 'GDP share'])

# --- Sectors ---
col_con_ind = get_col(['Contribution_to_real_annual_growth', 'Industry (except construction)'])
col_con_const = get_col(['Contribution_to_real_annual_growth', 'Construction'])
col_con_trade = get_col(['Contribution_to_real_annual_growth', 'Trade'])
col_con_fin = get_col(['Contribution_to_real_annual_growth', 'Financial services'])
col_con_pub = get_col(['Contribution_to_real_annual_growth', 'Public administration'])
col_con_info = get_col(['Contribution_to_real_annual_growth', 'Information'])
col_con_real = get_col(['Contribution_to_real_annual_growth', 'Real estate'])
col_con_prof = get_col(['Contribution_to_real_annual_growth', 'Professional services'])
col_con_agri = get_col(['Contribution_to_real_annual_growth', 'Primary'])
col_con_arts = get_col(['Contribution_to_real_annual_growth', 'Arts'])

# --- Other Existing ---
col_int_pay_gdp = get_col(['Interest payments', 'GDP share'])
col_pub_inv_gdp = get_col(['Public investment', 'GDP share'])
col_debt_euro = get_col(['General government', 'Euros', 'debt'])
if not col_debt_euro: col_debt_euro = get_col(['General Government Consolidated Debt', 'Euros'])
col_rev_total_euro = get_col(['Government_revenues', 'Total', 'Euros'])

# --- NEW MAPPINGS FOR EXPENDITURE ANALYSIS ---
# 1. Function (COFOG)
col_cofog_soc = get_col(['Government_expenditures_by_function', 'Social protection', 'GDP'])
col_cofog_health = get_col(['Government_expenditures_by_function', 'Health', 'GDP'])
col_cofog_gen = get_col(['Government_expenditures_by_function', 'General public services', 'GDP'])
col_cofog_edu = get_col(['Government_expenditures_by_function', 'Education', 'GDP'])
col_cofog_def = get_col(['Government_expenditures_by_function', 'Defence', 'GDP'])
col_cofog_eco = get_col(['Government_expenditures_by_function', 'Economic affairs', 'GDP'])

# 2. Economic Type (Rigidities)
col_use_soc_ben = get_col(['Government_expenditures_by_use', 'Social benefits', 'GDP'])
col_use_wages = get_col(['Government_expenditures_by_use', 'Compensation of employees', 'GDP'])
col_use_int = get_col(['Government_expenditures_by_use', 'Interest payments', 'GDP'])
# col_pub_inv_gdp is already defined above

# 3. Capital Stock
col_cap_stock_govt = get_col(['Capital_stock_of_General_Government', 'Total fixed assets', 'GDP share'])

# --- Calculations ---
data = df.copy()
if col_real_gdp:
    data['GDP_Growth'] = data[col_real_gdp].pct_change() * 100
if col_debt_euro and col_rev_total_euro:
    data['Debt_Revenue_Ratio'] = data[col_debt_euro] / data[col_rev_total_euro]
if col_rev_total_gdp and col_tax_vat_gdp and col_tax_inc_gdp and col_tax_corp_gdp and col_soc_cont_gdp:
    known_taxes = data[[col_tax_vat_gdp, col_tax_inc_gdp, col_tax_corp_gdp, col_soc_cont_gdp]].sum(axis=1)
    if col_tax_prop_gdp:
        known_taxes += data[col_tax_prop_gdp]
    data['Rev_Other_GDP'] = data[col_rev_total_gdp] - known_taxes

# -----------------------------------------------------------------------------
# 4. CLEANING & CITATION LOGIC (FIXED FOR -1 and NEGATIVE PARENS)
# -----------------------------------------------------------------------------

def clean_series_name(name):
    """
    Robust cleaning for citation strings.
    1. Removes metadata like (annual data...).
    2. Removes artifacts like .1 
    3. Removes specific suffix '-1' if at the end or before a pipe.
    4. Removes numeric values in parentheses (e.g., (-0.19))
    """
    if not name or not isinstance(name, str):
        return ""
    
    # 1. Normalize underscores to spaces
    name = name.replace('_', ' ')
    name = name.strip()

    # 2. Remove Pandas duplicates (Variable.1, Variable.2) at the end
    name = re.sub(r'\.\d+$', '', name)

    # 3. Remove "annual data" metadata specific to this dataset
    name = re.sub(r'\s*\(annual[ _]data[^)]*\)', '', name, flags=re.IGNORECASE)

    # 4. Remove NUMERIC values in parentheses
    # Matches: (123), (123.4), (-0.19), (-123.45)
    name = re.sub(r'\s*\(\s*-?[\d.]+\s*\)', '', name)

    # 5. Remove "-1" artifact
    # Matches "-1" if it is followed by a Pipe or the End of String
    # This handles "Direct taxes-1" AND "Category-1 | Subcategory"
    name = re.sub(r'-1(?=\s*\||$)', '', name)

    # 6. Remove trailing pipe if strictly at end
    name = re.sub(r'\|\s*$', '', name)

    # 7. Format formatting (Spaces around pipes)
    if '|' in name:
        name = name.replace('|', ' | ')
    
    # 8. Final collapse of multiple spaces
    name = re.sub(r'\s+', ' ', name).strip()
    
    return name

def build_citation(col_names) -> str:
    if not isinstance(col_names, list):
        col_names = [col_names]
    
    # Generate clean names
    clean_names = [clean_series_name(c) for c in col_names if c]
    
    # Remove duplicates while preserving order
    unique_names = list(dict.fromkeys(clean_names))
    
    series_str = ", ".join(unique_names)
    return f"Source: Greece in Numbers; Series: {series_str}; Author’s calculations by Theodoros Kourtalis."

def place_citation(fig, wrapped_citation):
    citation_top_y = 0.17
    fig.text(0.1, citation_top_y, wrapped_citation, ha="left", va="top", fontsize=10, 
             color='#333333', fontfamily='serif')

def finalize_plot(fig, ax, title, series_names, xlabel='', ylabel=''):
    ax.set_title(title, fontsize=24, fontfamily='serif', fontweight='bold', pad=30, color='black')
    ax.set_xlabel(xlabel, fontsize=14, style='italic', labelpad=10)
    ax.set_ylabel(ylabel, fontsize=14, style='italic', labelpad=10)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_linewidth(1.5)
    ax.spines['left'].set_linewidth(1.5)
    ax.grid(axis='y', visible=True, linestyle=':', alpha=0.7)
    
    full_citation = build_citation(series_names)
    wrapped_cit = "\n".join(textwrap.wrap(full_citation, width=130))
    place_citation(fig, wrapped_cit)

# -----------------------------------------------------------------------------
# 5. GENERATE PLOTS
# -----------------------------------------------------------------------------
print("Generating clean charts...")
BOTTOM_MARGIN = 0.25

# -----------------------------------------------------------------------------
# 1. ECONOMIC OUTPUT (FINAL POLISH: Right-Side Annotations)
# -----------------------------------------------------------------------------
if col_nom_gdp and col_real_gdp:
    fig, ax = plt.subplots(figsize=(12, 8))
    
    dates = data['Date']
    # SCALING: Billions
    scale = 1000 
    y_nom = data[col_nom_gdp] / scale
    y_real = data[col_real_gdp] / scale
    
    # 1. THE INFLATION WEDGE (Smart Fill)
    ax.fill_between(dates, y_nom, y_real, where=(y_nom > y_real), 
                    color=CLASSIC_COLORS['gold'], alpha=0.2, interpolate=True, label='Inflation Effect')
    
    # 2. PLOT LINES
    ax.plot(dates, y_nom, color=CLASSIC_COLORS['navy'], linewidth=3, label='Nominal GDP')
    ax.plot(dates, y_real, color=CLASSIC_COLORS['burgundy'], linewidth=3.5, label='Real GDP')
    
    # 3. PRE-CRISIS PEAK
    peak_idx = y_real.idxmax()
    peak_val = y_real[peak_idx]
    peak_date = dates[peak_idx]
    
    # Dotted reference line
    ax.axhline(peak_val, color=CLASSIC_COLORS['slate'], linestyle=':', linewidth=1.5, alpha=0.7)
    # Peak Dot
    ax.scatter([peak_date], [peak_val], color=CLASSIC_COLORS['burgundy'], s=120, zorder=5, edgecolor='white', linewidth=2)
    # Peak Label
    ax.annotate(f'2008 Peak\n€{peak_val:.0f}B', 
                xy=(peak_date, peak_val), 
                xytext=(-10, 15), textcoords='offset points',
                ha='right', va='bottom', fontsize=11, fontweight='bold', color=CLASSIC_COLORS['burgundy'],
                bbox=dict(facecolor=CLASSIC_COLORS['bg'], alpha=0.9, edgecolor='none', pad=2))

    # 4. THE RECOVERY GAP (Moved to RIGHT)
    current_val = y_real.iloc[-1]
    current_date = dates.iloc[-1]
    
    if current_val < peak_val:
        # Solid vertical line (Bracket)
        ax.plot([current_date, current_date], [current_val, peak_val], color='red', linewidth=2)
        
        # Calculate %
        gap_pct = ((current_val - peak_val) / peak_val) * 100
        
        # ANNOTATION ON THE RIGHT
        # We place text 15 points to the RIGHT of the line
        ax.annotate(f'Recovery Gap\n{gap_pct:.1f}%', 
                    xy=(current_date, (current_val + peak_val)/2), # Center of the vertical line
                    xytext=(15, 0), textcoords='offset points',    # Shift Right
                    ha='left', va='center',                        # Align Left so text flows rightwards
                    fontsize=12, fontweight='bold', color='red',
                    arrowprops=dict(arrowstyle='-', color='red', lw=1.5, shrinkB=5))

    # 5. FORMATTING
    import matplotlib.ticker as ticker
    def billion_fmt(x, pos):
        return f'€{int(x)}B'
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(billion_fmt))
    
    # Legend: Solid Box for Clarity
    ax.legend(loc='upper left', frameon=True, facecolor='white', framealpha=1, edgecolor='none', fontsize=12, borderpad=1)

    # *** CRITICAL: Extend X-Axis to make room for the right-side label ***
    # We add ~3 years (approx 1000 days) of empty space on the right
    ax.set_xlim(right=dates.max() + pd.Timedelta(days=1200))

    finalize_plot(fig, ax, 'Real vs. Nominal GDP', [col_nom_gdp, col_real_gdp], ylabel='GDP (Billions)')
    plt.subplots_adjust(bottom=BOTTOM_MARGIN)
    plt.savefig('Chart_Output_Gap.png', dpi=300, bbox_inches='tight')

# -----------------------------------------------------------------------------
# 2. BUDGET BALANCE (CLEAN: No Annotations, RGBA Fix)
# -----------------------------------------------------------------------------
from matplotlib.colors import to_rgba

if col_budget_bal_gdp:
    fig, ax = plt.subplots(figsize=(12, 8))
    
    dates = data['Date']
    vals = data[col_budget_bal_gdp]
    
    # 1. COLOR & STYLE LOGIC
    # We maintain the visual highlighting (Dark 2009, Traffic Lights) 
    # but remove the text labels.
    bar_colors = []
    edges = []
    linewidths = []
    
    for i, row in data.iterrows():
        year = row['Date'].year
        v = row[col_budget_bal_gdp]
        
        # Style for 2009 (Darker & Solid)
        if year == 2009:
            c = '#660000'       # Dark Red
            a = 1.0             # Solid
            edges.append('black')
            linewidths.append(1.5)
        # Traffic Light Logic for others
        elif v >= 0:
            c = CLASSIC_COLORS['navy']
            a = 0.85
            edges.append('white')
            linewidths.append(0.5)
        elif v >= -3:
            c = CLASSIC_COLORS['gold'] # Compliant Deficit
            a = 0.85
            edges.append('white')
            linewidths.append(0.5)
        else:
            c = CLASSIC_COLORS['burgundy']
            a = 0.85
            edges.append('white')
            linewidths.append(0.5)
            
        bar_colors.append(to_rgba(c, alpha=a))
            
    # 2. PLOT BARS
    ax.bar(dates, vals, color=bar_colors, width=300, 
           edgecolor=edges, linewidth=linewidths, zorder=3)
    
    # 3. REFERENCE LINES
    ax.axhline(0, color='black', linewidth=2, zorder=4)
    
    # Maastricht Limit (-3%) - Keeping the line and small label as it's a threshold
    ax.axhline(-3, color='#CC0000', linestyle='--', linewidth=1.5, alpha=0.6, zorder=2)
    ax.text(dates.min(), -2.9, ' Maastricht Limit (-3%)', 
            color='#CC0000', fontsize=10, style='italic', fontweight='bold', va='bottom',
            bbox=dict(facecolor=CLASSIC_COLORS['bg'], alpha=0.85, edgecolor='none', pad=1))

    # 4. SHADING (Optional Context)
    # Keeping the grey background for the adjustment era as it is subtle
    try:
        ax.axvspan(pd.Timestamp('2010-01-01'), pd.Timestamp('2018-08-20'), 
                   color='gray', alpha=0.08, zorder=1)
        ax.text(pd.Timestamp('2014-06-01'), 1.5, 'Adjustment Era', 
                ha='center', va='bottom', fontsize=10, color='gray', style='italic')
    except:
        pass

    # No other annotations (2009, Pandemic, Surplus removed)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    finalize_plot(fig, ax, 'Fiscal Pulse: Budget Balance', [col_budget_bal_gdp], ylabel='% of GDP')
    plt.subplots_adjust(bottom=BOTTOM_MARGIN)
    plt.savefig('Chart_Balance.png', dpi=300, bbox_inches='tight')
    
# -----------------------------------------------------------------------------
# 3. DEBT (EXTREME POLISH: Combined Annotation - Down & Left)
# -----------------------------------------------------------------------------
col_debt_loans = get_col(['General_government_debt_by_debt_instrument', 'Loans', 'GDP share'])
col_debt_sec = get_col(['General_government_debt_by_debt_instrument', 'Debt securities', 'GDP share'])
col_debt_curr = get_col(['General_government_debt_by_debt_instrument', 'Currency and deposits', 'GDP share'])

if col_debt_loans and col_debt_sec and col_debt_curr:
    fig, ax = plt.subplots(figsize=(12, 8))
    
    dates = data['Date']
    y_curr = data[col_debt_curr].fillna(0)
    y_sec = data[col_debt_sec].fillna(0)
    y_loans = data[col_debt_loans].fillna(0)
    
    # 1. STACKPLOT
    labels = ['Currency & Deposits', 'Debt Securities (Bonds)', 'Official Loans (Bailouts)']
    colors = [CLASSIC_COLORS['gold'], CLASSIC_COLORS['navy'], CLASSIC_COLORS['burgundy']]
    
    ax.stackplot(dates, y_curr, y_sec, y_loans, labels=labels, colors=colors, alpha=0.9, edgecolor='white', linewidth=0.3)
    
    # 2. TOTAL DEBT LINE
    if col_debt_gdp:
        ax.plot(dates, data[col_debt_gdp], color='black', linewidth=2.5, linestyle='-', label='Total Debt')

    # 3. COMBINED ANNOTATION (Moved Down & Left)
    try:
        mask_2012 = dates.dt.year == 2012
        if mask_2012.any():
            d2012 = dates[mask_2012].iloc[0]
            
            # Anchor Point: The boundary between Blue (Securities) and Red (Loans)
            val_c = y_curr[mask_2012].values[0]
            val_s = y_sec[mask_2012].values[0]
            y_boundary = val_c + val_s
            
            # Combined Text
            ax.annotate('2012 THE GREAT SWAP\nPrivate Bonds → Official Loans\n(PSI & Haircut)', 
                        xy=(d2012, y_boundary), 
                        # UPDATED: (-90, 0) moves it significantly Left and Down relative to previous (0, 60)
                        xytext=(-90, 0), textcoords='offset points',
                        # UPDATED: ha='right' ensures the box sits to the left of the arrow tip
                        ha='right', va='center', fontsize=12, fontweight='bold', color='black',
                        bbox=dict(facecolor='white', alpha=0.95, edgecolor='black', boxstyle='round,pad=0.4'),
                        arrowprops=dict(arrowstyle='->', color='black', lw=2))
    except Exception as e:
        print(f"Annotation error: {e}")

    # 4. ANNOTATE PEAK
    peak_idx = data[col_debt_gdp].idxmax()
    peak_val = data[col_debt_gdp].iloc[peak_idx]
    peak_date = dates.iloc[peak_idx]
    
    ax.annotate(f'Peak Debt\n{peak_val:.0f}% GDP', 
                xy=(peak_date, peak_val), 
                xytext=(0, 20), textcoords='offset points',
                ha='center', va='bottom', fontsize=11, fontweight='bold', color='black',
                bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=1),
                arrowprops=dict(arrowstyle='-', color='black', lw=1))

    # 5. LEGEND & FORMATTING
    ax.legend(loc='upper left', frameon=True, facecolor='white', framealpha=0.95, fontsize=11)
    
    finalize_plot(fig, ax, 'The Anatomy of Greek Debt', 
                  [col_debt_loans, col_debt_sec, col_debt_curr], ylabel='% of GDP')
    plt.subplots_adjust(bottom=BOTTOM_MARGIN)
    plt.savefig('Chart_Debt.png', dpi=300, bbox_inches='tight')

elif col_debt_gdp:
    # FALLBACK
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.fill_between(data['Date'], data[col_debt_gdp], color=CLASSIC_COLORS['slate'], alpha=0.3)
    ax.plot(data['Date'], data[col_debt_gdp], color=CLASSIC_COLORS['slate'], linewidth=3)
    finalize_plot(fig, ax, 'The Debt Mountain', [col_debt_gdp], ylabel='% GDP')
    plt.subplots_adjust(bottom=BOTTOM_MARGIN)
    plt.savefig('Chart_Debt.png', dpi=300, bbox_inches='tight')
# -----------------------------------------------------------------------------
# 4. REVENUE DECOMPOSITION (CLEAN: Improved Structure, No Text)
# -----------------------------------------------------------------------------

# 1. SETUP ORDER (Base to Top)
# We keep Social Contributions and VAT at the bottom as the "Engines" of revenue
ordered_rev_setup = [
    (col_soc_cont_gdp, 'Social Contributions', CLASSIC_COLORS['burgundy']), # Base Labor Cost
    (col_tax_vat_gdp, 'VAT', CLASSIC_COLORS['navy']),                       # Consumption
    (col_tax_inc_gdp, 'Income Tax', CLASSIC_COLORS['gold']),                # Labor Income
    (col_tax_prop_gdp, 'Property Tax', CLASSIC_COLORS['forest']),           # Wealth (ENFIA)
    (col_tax_corp_gdp, 'Corporate Tax', CLASSIC_COLORS['teal']),            # Profit
    ('Rev_Other_GDP', 'Other/Transfers', CLASSIC_COLORS['slate'])           # Residual
]

# Filter for columns that actually exist
valid_rev = [(c, l, col) for c, l, col in ordered_rev_setup if c in data.columns]

if valid_rev:
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Data Prep
    dates = data['Date']
    bottom = np.zeros(len(dates))
    bar_width = 300 # Approx annual width
    
    # 2. PLOT STACKED BARS
    for col, label, color in valid_rev:
        vals = data[col].fillna(0).values
        vals_plot = np.maximum(vals, 0)
        
        # Add bars with white edges for clarity
        ax.bar(dates, vals_plot, bottom=bottom, label=label, color=color, 
               alpha=0.9, width=bar_width, edgecolor='white', linewidth=0.5)
            
        bottom += vals_plot

    # 3. TOTAL REVENUE LINE (The "Burden" Envelope)
    # We use a thick black line to show the overall size of the state
    ax.plot(dates, bottom, color='black', linewidth=2.5, linestyle='-', marker='o', 
            markersize=5, markerfacecolor='white', markeredgewidth=2, label='Total Revenue')

    # 4. LEGEND ORGANIZATION
    # "ncol=3" organizes the 6 items into 2 neat rows
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.08), 
              frameon=False, fontsize=11, ncol=3)

    # 5. CITATION & FINALIZE
    cit_cols = [x[0] for x in valid_rev if x[0] != 'Rev_Other_GDP']
    if col_rev_total_gdp: cit_cols.append(col_rev_total_gdp)
        
    finalize_plot(fig, ax, 'State Revenue: The Tax Mix', cit_cols, ylabel='% of GDP')
    
    plt.subplots_adjust(bottom=BOTTOM_MARGIN)
    plt.savefig('Chart_Revenue_Decomp.png', dpi=300, bbox_inches='tight')
# -----------------------------------------------------------------------------
# 5. GDP SECTOR CONTRIB (FINAL: Adjusted Axis & Trimmed Start)
# -----------------------------------------------------------------------------

# 1. STRATEGIC ORDERING
sectors = [
    (col_con_const, 'Construction', CLASSIC_COLORS['rust']),       # The Bubble
    (col_con_trade, 'Trade & Tourism', CLASSIC_COLORS['gold']),    # The Engine
    (col_con_ind, 'Industry', CLASSIC_COLORS['navy']),             # The Base
    (col_con_real, 'Real Estate', CLASSIC_COLORS['teal']),
    (col_con_fin, 'Finance', CLASSIC_COLORS['slate']),
    (col_con_pub, 'Public Admin', CLASSIC_COLORS['forest']),
    (col_con_prof, 'Prof. Services', CLASSIC_COLORS['olive']),
    (col_con_info, 'Info & Comms', CLASSIC_COLORS['burgundy'])
]
valid_sectors = [s for s in sectors if s[0] in data.columns]

if valid_sectors:
    fig, ax = plt.subplots(figsize=(12, 8))
    
    pos_bottom = np.zeros(len(data))
    neg_bottom = np.zeros(len(data))
    dates = data['Date']
    
    # 2. PLOT BARS
    for col, label, color in valid_sectors:
        vals = data[col].fillna(0).values
        pos_vals = np.maximum(vals, 0)
        neg_vals = np.minimum(vals, 0)
        
        # Positive Stack
        ax.bar(dates, pos_vals, bottom=pos_bottom, label=label, color=color, 
               width=300, alpha=0.9, edgecolor='white', linewidth=0.4)
        pos_bottom += pos_vals
        
        # Negative Stack
        ax.bar(dates, neg_vals, bottom=neg_bottom, color=color, 
               width=300, alpha=0.9, edgecolor='white', linewidth=0.4)
        neg_bottom += neg_vals

    # 3. ZERO LINE
    ax.axhline(0, color='black', linewidth=1.5, zorder=3)

    # 4. FIX TOTAL LINE (Trimmed First Year)
    sector_cols = [s[0] for s in valid_sectors]
    net_growth_calculated = data[sector_cols].fillna(0).sum(axis=1)
    
    # REMOVE THE FIRST YEAR VALUE (Set to NaN)
    # This prevents the line from starting at an awkward point if data is noisy
    if len(net_growth_calculated) > 0:
        net_growth_calculated.iloc[0] = np.nan

    # Plot Net Growth with Halo
    line, = ax.plot(dates, net_growth_calculated, color='black', linewidth=3, 
                    linestyle='-', marker='o', markersize=5, label='Net Growth', zorder=10)
    line.set_path_effects([pe.withStroke(linewidth=5, foreground='white')])

    # 5. ADJUST Y-AXIS (Add breathing room)
    # Find the lowest point of the negative bars
    min_y_val = neg_bottom.min()
    # Extend the limit by 2 percentage points downwards
    ax.set_ylim(bottom=min_y_val - 2)

    # 6. LEGEND & FINALIZATION
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.08), 
              frameon=False, fontsize=10, ncol=4)
    
    finalize_plot(fig, ax, 'Sectoral Drivers of GDP', [s[0] for s in valid_sectors], ylabel='Contribution (pp)')
    plt.subplots_adjust(bottom=BOTTOM_MARGIN)
    plt.savefig('Chart_GDP_Contrib.png', dpi=300, bbox_inches='tight')
    
# 6. PHASE (DEBT vs GROWTH)
if col_debt_gdp and 'GDP_Growth' in data.columns:
    fig, ax = plt.subplots(figsize=(16, 10))
    df_clean = data.dropna(subset=[col_debt_gdp, 'GDP_Growth'])
    
    if len(df_clean) > 1:
        x = df_clean[col_debt_gdp].values
        y = df_clean['GDP_Growth'].values
        dates = df_clean['Date'].dt.year.values
        n = len(x)

        import matplotlib.colors as mcolors
        cmap = mcolors.LinearSegmentedColormap.from_list("TimeFlow", [CLASSIC_COLORS['gold'], CLASSIC_COLORS['navy']])
        
        for i in range(n - 1):
            fraction = i / (n - 1)
            seg_color = cmap(fraction)
            ax.annotate('', 
                        xy=(x[i+1], y[i+1]), 
                        xytext=(x[i], y[i]),
                        arrowprops=dict(arrowstyle="->", color=seg_color, lw=2, alpha=0.8, connectionstyle="arc3,rad=0.15"),
                        va='center')

        ax.scatter(x, y, c=np.linspace(0, 1, n), cmap=cmap, s=80, zorder=2, edgecolors='none')
        
        def add_label(ix, text, color, ax, offset_x, offset_y):
            txt = ax.annotate(text, 
                              xy=(x[ix], y[ix]), 
                              xytext=(offset_x, offset_y),
                              textcoords='offset points',
                              fontsize=14, 
                              fontweight='bold', 
                              color=color,
                              ha='center', va='center')
            txt.set_path_effects([pe.withStroke(linewidth=4, foreground='white')])

        add_label(0, str(dates[0]), CLASSIC_COLORS['gold'], ax, -16, 18)
        
        dx = x[-1] - x[-2]
        dy = y[-1] - y[-2]
        dist = np.sqrt(dx**2 + dy**2)
        if dist == 0: dist = 1
        end_off_x = (dx / dist) * 20
        end_off_y = (dy / dist) * 20
        add_label(-1, str(dates[-1]), CLASSIC_COLORS['navy'], ax, end_off_x, end_off_y)

        finalize_plot(fig, ax, 'Debt vs Growth Path', [col_debt_gdp, col_real_gdp], xlabel='Debt (% GDP)', ylabel='Growth (%)')
        plt.subplots_adjust(bottom=BOTTOM_MARGIN)
        plt.savefig('Chart_Phase.png', dpi=300, bbox_inches='tight')

# -----------------------------------------------------------------------------
# 7. CROWDING (IMPROVED: The Investment Squeeze)
# -----------------------------------------------------------------------------
if col_int_pay_gdp and col_pub_inv_gdp:
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # 1. Plot Lines
    ax.plot(data['Date'], data[col_int_pay_gdp], color=CLASSIC_COLORS['burgundy'], 
            label='Interest Payments', linewidth=3.5)
    ax.plot(data['Date'], data[col_pub_inv_gdp], color=CLASSIC_COLORS['navy'], 
            linestyle='--', label='Public Investment', linewidth=3.5)
    
    # 2. Fill Logic (The "Squeeze")
    # Red Zone: Money flowing to creditors instead of infrastructure
    ax.fill_between(data['Date'], data[col_int_pay_gdp], data[col_pub_inv_gdp], 
                    where=(data[col_int_pay_gdp] > data[col_pub_inv_gdp]),
                    interpolate=True, color=CLASSIC_COLORS['burgundy'], alpha=0.15)
    
    # Blue Zone: Healthy investment surplus
    ax.fill_between(data['Date'], data[col_int_pay_gdp], data[col_pub_inv_gdp], 
                    where=(data[col_int_pay_gdp] <= data[col_pub_inv_gdp]),
                    interpolate=True, color=CLASSIC_COLORS['navy'], alpha=0.15)

    # 3. CALCULATE AND ANNOTATE THE "MAX SQUEEZE"
    # Create a temporary series to find the gap
    gap_series = data[col_int_pay_gdp] - data[col_pub_inv_gdp]
    max_gap_val = gap_series.max()
    
    # Only annotate if there is a positive gap (Interest > Investment)
    if max_gap_val > 0:
        max_gap_date = gap_series.idxmax() # Getting the index
        # If index is not date, we need to locate the row
        if not isinstance(max_gap_date, pd.Timestamp):
             # Fallback if idxmax returns an integer index
             max_gap_row = data.loc[data[col_int_pay_gdp] - data[col_pub_inv_gdp] == max_gap_val].iloc[0]
             max_gap_date = max_gap_row['Date']
        
        # Get the Y-values at that date for arrow placement
        y_int = data.loc[data['Date'] == max_gap_date, col_int_pay_gdp].values[0]
        y_inv = data.loc[data['Date'] == max_gap_date, col_pub_inv_gdp].values[0]
        
        # Add a double-headed arrow to show the gap
        ax.annotate('', xy=(max_gap_date, y_int), xytext=(max_gap_date, y_inv),
                    arrowprops=dict(arrowstyle='<->', color='black', lw=1.5))
        
        # Add text label next to the arrow
        ax.text(max_gap_date, (y_int + y_inv)/2, f' Peak Squeeze\n {max_gap_val:.1f}% GDP', 
                fontsize=11, fontweight='bold', ha='left', va='center', color=CLASSIC_COLORS['burgundy'],
                bbox=dict(facecolor=CLASSIC_COLORS['bg'], alpha=0.8, edgecolor='none', pad=2))

    # 4. DIRECT LABELING (Instead of Legend)
    # Get last values
    last_date = data['Date'].iloc[-1]
    last_int = data[col_int_pay_gdp].iloc[-1]
    last_inv = data[col_pub_inv_gdp].iloc[-1]
    
    # Offset labels slightly to the right
    ax.text(last_date, last_int, '  Interest Payments', color=CLASSIC_COLORS['burgundy'], 
            fontsize=12, fontweight='bold', va='center')
    ax.text(last_date, last_inv, '  Public Investment', color=CLASSIC_COLORS['navy'], 
            fontsize=12, fontweight='bold', va='center')

    # Final Polish
    finalize_plot(fig, ax, 'Crowding Out: The Cost of Debt', [col_int_pay_gdp, col_pub_inv_gdp], ylabel='% of GDP')
    
    # Extend X-axis slightly to fit the direct labels
    ax.set_xlim(right=data['Date'].max() + pd.Timedelta(days=700)) 
    
    plt.subplots_adjust(bottom=BOTTOM_MARGIN)
    plt.savefig('Chart_Crowding.png', dpi=300, bbox_inches='tight')


# -----------------------------------------------------------------------------
# NEW CHART 1: Expenditure by Function (COFOG) - SORTED STACK (Big -> Small)
# -----------------------------------------------------------------------------

# 1. MAPPING
col_cofog_order = get_col(['Government_expenditures_by_function', 'Public order', 'GDP'])
col_cofog_env = get_col(['Government_expenditures_by_function', 'Environmental protection', 'GDP'])
col_cofog_house = get_col(['Government_expenditures_by_function', 'Housing', 'GDP'])
col_cofog_rec = get_col(['Government_expenditures_by_function', 'Recreation', 'GDP'])

# 2. DEFINING VARIABLES & COLORS
# We define the mapping here, but the ORDER will be determined by data magnitude below.
cofog_vars_unsorted = [
    (col_cofog_soc, 'Social Protection (Pensions)', '#800020'),  # Burgundy
    (col_cofog_health, 'Health', '#008080'),                     # Teal
    (col_cofog_gen, 'General Public Services', '#404040'),       # Dark Grey
    (col_cofog_edu, 'Education', '#000080'),                     # Navy
    (col_cofog_order, 'Public Order & Safety', '#000000'),       # Black
    (col_cofog_def, 'Defence', '#556B2F'),                       # Olive
    (col_cofog_eco, 'Economic Affairs', '#FFD700'),              # Gold
    (col_cofog_env, 'Environment', '#228B22'),                   # Forest Green
    (col_cofog_house, 'Housing', '#D2691E'),                     # Chocolate
    (col_cofog_rec, 'Recreation & Culture', '#BA55D3')           # Medium Orchid
]

# 3. OVERRIDE CITATION POSITION
def place_citation_custom(fig, text):
    # CHANGED Y to 0.001 (Absolute bottom edge)
    fig.text(0.1, 0.001, text, ha="left", va="bottom", fontsize=10, 
             color='#333333', fontfamily='serif')

original_place_citation = place_citation
place_citation = place_citation_custom

# Filter for columns that actually exist
valid_cofog_unsorted = [v for v in cofog_vars_unsorted if v[0] in data.columns]

if valid_cofog_unsorted:
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # --- DATA PROCESSING & SORTING ---
    # 1. Clean Data
    stack_cols = [v[0] for v in valid_cofog_unsorted]
    valid_rows_mask = data[stack_cols].sum(axis=1) > 1.0 
    plot_data = data.loc[valid_rows_mask].copy()
    
    # 2. CALCULATE SIZES TO SORT STACK
    # We sum the entire series to find the "Biggest" over the whole period
    # Sort Descending: Largest Sum gets index 0 -> plotted at Bottom
    valid_cofog_sorted = sorted(valid_cofog_unsorted, 
                                key=lambda x: plot_data[x[0]].sum(), 
                                reverse=True)

    # 3. Prepare Plot Lists based on Sorted Order
    x = plot_data['Date']
    ys = [plot_data[v[0]].fillna(0).values for v in valid_cofog_sorted]
    labels = [v[1] for v in valid_cofog_sorted]
    colors = [v[2] for v in valid_cofog_sorted]
    
    # --- PLOT ---
    # stackplot plots the first item in the list at the bottom.
    # Since we sorted Descending, the Biggest is now at the Bottom.
    stacks = ax.stackplot(x, *ys, labels=labels, colors=colors, alpha=1.0, 
                          edgecolor='white', linewidth=0.5)

    # Annotate Bank Bailouts (Gold)
    if col_cofog_eco in plot_data.columns:
        eco_series = plot_data[col_cofog_eco]
        peak_idx = eco_series.idxmax()
        if isinstance(peak_idx, (int, pd.Timestamp)):
             try:
                 peak_date = plot_data.loc[peak_idx, 'Date']
                 # We need the cumulative height *at* the Economic Affairs layer
                 # Since order changed, we must find where Eco Affairs is in the stack
                 eco_idx = [v[0] for v in valid_cofog_sorted].index(col_cofog_eco)
                 
                 # Sum all layers up to and including Economic Affairs
                 relevant_cols = [v[0] for v in valid_cofog_sorted[:eco_idx+1]]
                 stack_height_at_eco = plot_data.loc[peak_idx, relevant_cols].sum()
                 
                 ax.annotate('Bank Recapitalization\n(One-off Costs)', 
                             xy=(peak_date, stack_height_at_eco), 
                             # CHANGED: Moved up from 30 to 50
                             xytext=(0, 50), textcoords='offset points',
                             ha='center', va='bottom', fontsize=10, style='italic', fontweight='bold',
                             arrowprops=dict(arrowstyle='->', color='black', lw=1.5))
             except:
                 pass

    # --- LEGEND ---
    # The handles/labels are already sorted Big->Small because we plotted them that way.
    # We just display them.
    handles, labels = ax.get_legend_handles_labels()
    
    # Display Legend
    ax.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, -0.08), 
              frameon=False, fontsize=11, ncol=3)
    
    finalize_plot(fig, ax, 'The Cost of the State: Expenditure by Function', 
                  [v[0] for v in valid_cofog_sorted], ylabel='% of GDP')
    
    plt.subplots_adjust(bottom=0.25) 
    plt.savefig('Chart_Expenditure_Function.png', dpi=300, bbox_inches='tight')

place_citation = original_place_citation
# -----------------------------------------------------------------------------
# NEW CHART 2: Expenditure by Economic Type 
# -----------------------------------------------------------------------------
# Compares Rigidities (Wages, Benefits, Interest) vs Investment
eco_vars = [
    (col_use_soc_ben, 'Social Benefits', CLASSIC_COLORS['burgundy'], '-'),
    (col_use_wages, 'Wages', CLASSIC_COLORS['navy'], '-'),
    (col_use_int, 'Interest', CLASSIC_COLORS['slate'], ':'),
    (col_pub_inv_gdp, 'Investment', CLASSIC_COLORS['gold'], '--') # Make Investment distinct
]
valid_eco = [v for v in eco_vars if v[0] in data.columns]

if valid_eco:
    fig, ax = plt.subplots(figsize=(12, 8))
    
    for col, label, color, style in valid_eco:
        ax.plot(data['Date'], data[col], label=label, color=color, linestyle=style, linewidth=3)
        
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), frameon=False, fontsize=12, ncol=4)
    
    finalize_plot(fig, ax, 'Budget Rigidities vs Investment', [v[0] for v in valid_eco], ylabel='% of GDP')
    plt.subplots_adjust(bottom=BOTTOM_MARGIN)
    plt.savefig('Chart_Expenditure_Economic.png', dpi=300, bbox_inches='tight')
# -----------------------------------------------------------------------------
# NEW CHART 3: Public Assets (The Depreciation Trap) - NO PEAK LABEL
# -----------------------------------------------------------------------------
if col_pub_inv_gdp and col_cap_stock_govt:
    fig, ax1 = plt.subplots(figsize=(12, 8))
    
    dates = data['Date']
    
    # --- AXIS 1: THE FLOW (Bars) ---
    color_flow = CLASSIC_COLORS['navy']
    bars = ax1.bar(dates, data[col_pub_inv_gdp], color=color_flow, alpha=0.3, 
                   width=300, label='Public Investment (Flow, Left)')
    
    # Highlight "Crisis Lows" (Red Bars)
    threshold = 3.0 
    for bar, val in zip(bars, data[col_pub_inv_gdp]):
        if val < threshold:
            bar.set_color(CLASSIC_COLORS['burgundy'])
            bar.set_alpha(0.5)

    ax1.set_ylabel('Annual Investment (% of GDP)', color=color_flow, fontsize=12, fontweight='bold')
    ax1.tick_params(axis='y', labelcolor=color_flow)
    ax1.set_ylim(bottom=0)

    # --- AXIS 2: THE STOCK (Line) ---
    ax2 = ax1.twinx()
    color_stock = '#333333' # Dark Charcoal
    
    line, = ax2.plot(dates, data[col_cap_stock_govt], color=color_stock, 
                     linewidth=4, label='Public Capital Stock (Asset Value, Right)')
    
    # Glowing Halo
    line.set_path_effects([pe.withStroke(linewidth=6, foreground='white', alpha=0.7)])

    ax2.set_ylabel('Total Public Assets (% of GDP)', color=color_stock, fontsize=12, fontweight='bold', rotation=270, labelpad=20)
    ax2.tick_params(axis='y', labelcolor=color_stock)
    
    # --- ANNOTATIONS ---
    # We calculate peak internally just for the "Depreciation" logic, but do NOT plot the label.
    peak_idx = data[col_cap_stock_govt].idxmax()
    peak_val = data.loc[peak_idx, col_cap_stock_govt]

    # Annotate "Net Depreciation" (Only if stock is currently lower than its peak)
    if data[col_cap_stock_govt].iloc[-1] < peak_val:
        # Arrow pointing down roughly from the middle of the decline
        mid_point_idx = int((len(data) + data.index.get_loc(peak_idx)) / 2)
        mid_date = data.iloc[mid_point_idx]['Date']
        mid_val = data.iloc[mid_point_idx][col_cap_stock_govt]
        
        ax2.annotate('Net Depreciation\n(Assets Wearing Out)', 
                     xy=(mid_date, mid_val), xytext=(20, 20), textcoords='offset points',
                     ha='left', fontsize=10, style='italic', color=CLASSIC_COLORS['burgundy'],
                     arrowprops=dict(arrowstyle='->', color=CLASSIC_COLORS['burgundy'], lw=1.5))

    # --- CLEANUP ---
    ax1.set_title('Public Wealth: Investment vs. Accumulated Assets', 
                  fontsize=24, fontfamily='serif', fontweight='bold', pad=30, color='black')
    
    ax1.spines['top'].set_visible(False)
    ax2.spines['top'].set_visible(False)
    ax1.grid(False)
    ax2.grid(True, linestyle=':', alpha=0.5)
    
    # Unified Legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=CLASSIC_COLORS['navy'], alpha=0.3, label='Normal Investment'),
        Patch(facecolor=CLASSIC_COLORS['burgundy'], alpha=0.5, label='Low Investment (<3% GDP)'),
        line
    ]
    ax1.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, 1.08), 
               frameon=False, ncol=3, fontsize=11)

    # Citation
    full_citation = build_citation([col_pub_inv_gdp, col_cap_stock_govt])
    wrapped_cit = "\n".join(textwrap.wrap(full_citation, width=130))
    place_citation(fig, wrapped_cit)
    
    plt.subplots_adjust(bottom=BOTTOM_MARGIN)
    plt.savefig('Chart_Investment_vs_Stock.png', dpi=300, bbox_inches='tight')
    
print("All charts (including new expenditure series) generated.")