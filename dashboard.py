"""
Dashboard: India's 20 Years of GDP Misestimation (WP26-3)
Recreates paper figures with Fisher's z-transformation statistical tests.
Supports toggling between Old/New GVA series, non-agri vs full GDP, and custom correlations.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats
import openpyxl
import os
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(page_title="India GDP: A Statistical Review", layout="wide")

# --- Data Loading ---
BASE = os.path.join(os.path.dirname(__file__),
    "Replication Package wo CMIE", "Replication Package wo CMIE", "Replication Package wo CMIE")
DATA_FILE = os.path.join(BASE, "Data1.xlsx")


@st.cache_data
def load_master_dataframe():
    """Load Figure 2 as base (all indicators + non-agri GVA), then add
    full GVA Old (2004-05 base, GDP at Factor Cost) from 'Macro Indicators & GVA (2)'."""
    wb = openpyxl.load_workbook(DATA_FILE, data_only=True)

    def clean(v):
        try:
            f = float(v)
            return f if np.isfinite(f) else np.nan
        except (TypeError, ValueError):
            return np.nan

    # --- Figure 2: all indicators, Real Sales, Direct Taxes, non-agri GVA ---
    ws_f2 = wb["Figure 2"]
    rows_f2 = list(ws_f2.iter_rows(values_only=True))
    headers_f2 = list(rows_f2[0])
    headers_f2[0] = "Year"
    records_f2 = [r for r in rows_f2[1:] if r[0] is not None]
    df = pd.DataFrame(records_f2, columns=headers_f2)

    # --- Macro Indicators & GVA (2): full GVA Old (2004-05 base) ---
    # Col 0 = Year, Col 10 = Real GVA Old (GDP at Factor Cost, 2004-05 base)
    # This is the genuine full-economy GVA including agriculture; distinct from
    # Real GDP (market prices) by the net-taxes-on-products wedge.
    # For the new base (2011-12), GVA ≈ GDP so we use Real GDP from Figure 2.
    ws_gva2 = wb["Macro Indicators & GVA (2)"]
    rows_gva2 = list(ws_gva2.iter_rows(values_only=True))
    df_full_gva = pd.DataFrame([
        {"Year": str(r[0]).strip(), "Real Full GVA Old": clean(r[10])}
        for r in rows_gva2[1:]
        if r[0] is not None and isinstance(r[0], str) and "-" in str(r[0])
    ])

    wb.close()

    # Merge: Figure 2 as base, add full GVA Old column
    df = df.merge(df_full_gva, on="Year", how="left")

    # Deduplicate column names (e.g. two "Real Imports" columns)
    seen = {}
    new_headers = []
    for h in df.columns:
        if h in seen:
            new_headers.append(f"{h}_{seen[h]}")
            seen[h] += 1
        else:
            new_headers.append(h)
            seen[h] = 1
    df.columns = new_headers

    df["Year"] = df["Year"].astype(str).str.strip()

    # Parse numeric year
    def year_to_int(y):
        s = str(y).strip()
        if "-" in s and len(s) >= 7:
            return int(s[:4])
        try:
            return int(float(s))
        except:
            return None

    df["YearInt"] = df["Year"].apply(year_to_int)
    df = df.dropna(subset=["YearInt"])
    df["YearInt"] = df["YearInt"].astype(int)

    # Convert all data columns to numeric
    for col in df.columns:
        if col not in ("Year", "YearInt"):
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


@st.cache_data
def load_gdp_discrepancies():
    wb = openpyxl.load_workbook(DATA_FILE, data_only=True)
    ws = wb["GDP Discripancies"]
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    headers = list(rows[0])
    headers[0] = "Year"
    records = [r for r in rows[1:] if r[0] is not None and isinstance(r[1], (int, float))]
    df = pd.DataFrame(records, columns=headers)
    for col in df.columns[1:]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


# --- Statistical Functions ---
def fisher_z_transform(r, n):
    """Compute Fisher's z-transformation with CI and p-value."""
    if abs(r) >= 1.0:
        r = np.sign(r) * 0.9999
    z = np.arctanh(r)
    se = 1.0 / np.sqrt(max(n - 3, 1))
    z_lower = z - 1.96 * se
    z_upper = z + 1.96 * se
    r_lower = np.tanh(z_lower)
    r_upper = np.tanh(z_upper)
    t_stat = r * np.sqrt((n - 2) / (1 - r**2)) if abs(r) < 1 else np.inf
    p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df=max(n - 2, 1)))
    return {
        "r": r, "n": n, "fisher_z": z, "se_z": se,
        "ci_lower_r": r_lower, "ci_upper_r": r_upper,
        "t_stat": t_stat, "p_value": p_value
    }


def compute_correlation_with_stats(x, y):
    """Compute Pearson r and full Fisher's z stats from arrays."""
    mask = np.isfinite(x) & np.isfinite(y)
    x_clean, y_clean = x[mask], y[mask]
    n = len(x_clean)
    if n < 4:
        return None
    r, _ = stats.pearsonr(x_clean, y_clean)
    result = fisher_z_transform(r, n)
    slope, intercept = np.polyfit(x_clean, y_clean, 1)
    result["slope"] = slope
    result["intercept"] = intercept
    result["x_clean"] = x_clean
    result["y_clean"] = y_clean
    return result


def significance_label(p):
    if p < 0.001: return "***"
    elif p < 0.01: return "**"
    elif p < 0.05: return "*"
    return "n.s."


def format_stats(s):
    if s is None:
        return "Insufficient data"
    sig = significance_label(s["p_value"])
    return (f"r = {s['r']:.3f}{sig}, n = {s['n']}, "
            f"Fisher z = {s['fisher_z']:.3f}, "
            f"95% CI [{s['ci_lower_r']:.3f}, {s['ci_upper_r']:.3f}], "
            f"p = {s['p_value']:.4f}")


# --- Core Plotting ---
def get_y_values(df, y_mode, gva_series_mode, period_mask_1, period_mask_2):
    """
    Build y-series depending on user's GVA toggle.
    Returns (y1_array, y2_array) for period 1 and period 2 respectively.

    y_mode: which dependent variable column set to use
    gva_series_mode: how to pick old vs new series
    """
    # Determine column names based on y_mode
    if y_mode == "Full GVA (incl. Agriculture)":
        # Old base (2004-05): genuine full GVA = GDP at Factor Cost, distinct from GDP.
        # New base (2011-12): GVA ≈ GDP in this dataset, so use Real GDP.
        y1_col = "Real Full GVA Old"
        y2_col = "Real GDP"
    elif y_mode == "Real GDP":
        y1_col = "Real GDP"
        y2_col = "Real GDP"
    else:  # Non-Agri GVA (Paper Default)
        # Paper methodology: Old series for pre-2012, New series for post-2012
        y1_col = "Real non agri GVA Old"
        y2_col = "Real non agri GVA New"

    return y1_col, y2_col


def split_and_compute(df, x_col, y1_col, y2_col, period1, period2, exclude_pandemic=True):
    """Split data into two periods, compute correlation stats for each."""
    df = df.copy()
    if exclude_pandemic:
        df = df[~df["YearInt"].isin([2020, 2021])]

    m1 = (df["YearInt"] >= period1[0]) & (df["YearInt"] <= period1[1])
    m2 = (df["YearInt"] >= period2[0]) & (df["YearInt"] <= period2[1])

    def extract(sub, xc, yc):
        s = sub[[xc, yc]].dropna()
        return s[xc].values.astype(float), s[yc].values.astype(float)

    x1, y1 = extract(df[m1], x_col, y1_col)
    x2, y2 = extract(df[m2], x_col, y2_col)

    s1 = compute_correlation_with_stats(x1, y1)
    s2 = compute_correlation_with_stats(x2, y2)
    return x1, y1, x2, y2, s1, s2


def make_correlation_figure(x1, y1, x2, y2, s1, s2, x_label, y_label, title,
                            p1_label="1995-11", p2_label="2012-24"):
    """Create a correlation scatter plot with two periods, regression lines, and Fisher stats."""
    fig = go.Figure()

    # Period 1
    fig.add_trace(go.Scatter(x=x1, y=y1, mode="markers",
        marker=dict(color="#1f77b4", size=8), name=p1_label,
        hovertemplate=f"{x_label}: %{{x:.1f}}<br>{y_label}: %{{y:.1f}}"))
    if s1 and len(x1) > 1:
        xr = np.linspace(min(x1), max(x1), 50)
        fig.add_trace(go.Scatter(x=xr, y=s1["slope"] * xr + s1["intercept"],
            mode="lines", line=dict(color="#1f77b4", dash="dash"), showlegend=False))

    # Period 2
    fig.add_trace(go.Scatter(x=x2, y=y2, mode="markers",
        marker=dict(color="#d62728", size=8, symbol="diamond"), name=p2_label,
        hovertemplate=f"{x_label}: %{{x:.1f}}<br>{y_label}: %{{y:.1f}}"))
    if s2 and len(x2) > 1:
        xr = np.linspace(min(x2), max(x2), 50)
        fig.add_trace(go.Scatter(x=xr, y=s2["slope"] * xr + s2["intercept"],
            mode="lines", line=dict(color="#d62728", dash="dash"), showlegend=False))

    # Stat annotations — stacked at bottom-right, clear of data
    annotations = []
    if s1:
        sig1 = significance_label(s1["p_value"])
        annotations.append(dict(x=0.99, y=0.34, xref="paper", yref="paper",
            text=f"<b>{p1_label}</b>: r={s1['r']:.2f} {sig1}<br>"
                 f"CI [{s1['ci_lower_r']:.2f}, {s1['ci_upper_r']:.2f}]<br>"
                 f"Fisher z={s1['fisher_z']:.3f}, p={s1['p_value']:.4f}",
            showarrow=False, font=dict(size=10, color="#1f77b4"),
            bgcolor="rgba(255,255,255,0.88)", bordercolor="#1f77b4", borderwidth=1,
            xanchor="right", yanchor="top"))
    if s2:
        sig2 = significance_label(s2["p_value"])
        annotations.append(dict(x=0.99, y=0.01, xref="paper", yref="paper",
            text=f"<b>{p2_label}</b>: r={s2['r']:.2f} {sig2}<br>"
                 f"CI [{s2['ci_lower_r']:.2f}, {s2['ci_upper_r']:.2f}]<br>"
                 f"Fisher z={s2['fisher_z']:.3f}, p={s2['p_value']:.4f}",
            showarrow=False, font=dict(size=10, color="#d62728"),
            bgcolor="rgba(255,255,255,0.88)", bordercolor="#d62728", borderwidth=1,
            xanchor="right", yanchor="bottom"))

    fig.update_layout(
        title=title, xaxis_title=x_label, yaxis_title=y_label,
        annotations=annotations, height=480, template="plotly_white",
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            xanchor="right", x=1,
            bgcolor="rgba(255,255,255,0.8)", bordercolor="lightgrey", borderwidth=1
        ),
        margin=dict(t=80)   # extra top margin so horizontal legend clears the title
    )
    return fig


def make_forest_plot(stats_pairs, labels, title="Fisher's z: Correlation Comparison (95% CI)"):
    """Forest plot comparing pre vs post correlations."""
    fig = go.Figure()
    for i, (s1, s2) in enumerate(stats_pairs):
        if s1:
            fig.add_trace(go.Scatter(
                x=[s1["r"]], y=[i - 0.13],
                error_x=dict(type="data",
                    array=[s1["ci_upper_r"] - s1["r"]],
                    arrayminus=[s1["r"] - s1["ci_lower_r"]]),
                mode="markers", marker=dict(color="#1f77b4", size=10),
                name="Pre-2012" if i == 0 else None, showlegend=(i == 0)))
        if s2:
            fig.add_trace(go.Scatter(
                x=[s2["r"]], y=[i + 0.13],
                error_x=dict(type="data",
                    array=[s2["ci_upper_r"] - s2["r"]],
                    arrayminus=[s2["r"] - s2["ci_lower_r"]]),
                mode="markers", marker=dict(color="#d62728", size=10, symbol="diamond"),
                name="Post-2012" if i == 0 else None, showlegend=(i == 0)))
    fig.add_vline(x=0, line_dash="dash", line_color="gray")
    fig.update_layout(
        title=title,
        xaxis_title="Pearson r (back-transformed from Fisher z)",
        yaxis=dict(tickvals=list(range(len(labels))), ticktext=labels),
        height=max(400, len(labels) * 65), template="plotly_white")
    return fig


def build_diff_table(stats_pairs, dep_labels, ind_labels):
    """Build table testing whether each correlation significantly changed across periods."""
    rows = []
    for (s1, s2), dep, ind in zip(stats_pairs, dep_labels, ind_labels):
        if s1 and s2:
            z1, z2 = s1["fisher_z"], s2["fisher_z"]
            se_diff = np.sqrt(1 / max(s1["n"] - 3, 1) + 1 / max(s2["n"] - 3, 1))
            z_stat = (z1 - z2) / se_diff
            p_diff = 2 * (1 - stats.norm.cdf(abs(z_stat)))
            rows.append({
                "Dependent": dep, "Indicator": ind,
                "r (pre)": round(s1["r"], 3), "r (post)": round(s2["r"], 3),
                "Δr": round(s1["r"] - s2["r"], 3),
                "z₁": round(z1, 3), "z₂": round(z2, 3),
                "Z-stat": round(z_stat, 3),
                "p (diff)": round(p_diff, 4),
                "Sig": significance_label(p_diff),
                "Direction": "Weakened" if s1["r"] > s2["r"] else "Strengthened"
            })
    return pd.DataFrame(rows)


# ========================
# LOAD DATA
# ========================
df_master = load_master_dataframe()

# ========================
# SIDEBAR CONTROLS
# ========================
st.sidebar.title("Dashboard Controls")

st.sidebar.header("GVA Series Selection")
y_mode = st.sidebar.radio("Dependent variable",
    ["Non-Agri GVA (Paper Default)", "Full GVA (incl. Agriculture)", "Real GDP"],
    help="Paper uses non-agri GVA (excludes agriculture and public admin). "
         "'Full GVA' uses 2004-05 base GDP at Factor Cost pre-2012 (genuinely distinct from GDP) "
         "and Real GDP post-2012 (where GVA ≈ GDP in the 2011-12 base series). "
         "'Real GDP' uses Real GDP at market prices for both periods.")

# Always use paper methodology: Old series pre-2012, New series post-2012
gva_series_mode = "Paper: Old pre-2012, New post-2012"

st.sidebar.header("Period Selection")
col_p1, col_p2 = st.sidebar.columns(2)
with col_p1:
    p1_start = st.number_input("Period 1 start", 1993, 2024, 1995)
    p1_end = st.number_input("Period 1 end", 1993, 2024, 2011)
with col_p2:
    p2_start = st.number_input("Period 2 start", 1993, 2025, 2012)
    p2_end = st.number_input("Period 2 end", 1993, 2025, 2024)

period1 = (p1_start, p1_end)
period2 = (p2_start, p2_end)
p1_label = f"{p1_start}-{str(p1_end)[-2:]}"
p2_label = f"{p2_start}-{str(p2_end)[-2:]}"

exclude_pandemic = st.sidebar.checkbox("Exclude 2020-21 & 2021-22 (pandemic years)", value=True)

# Determine y columns based on user selection
y1_col, y2_col = get_y_values(df_master, y_mode, gva_series_mode, None, None)
if y_mode == "Full GVA (incl. Agriculture)":
    y_label_short = "Real Full GVA Growth"
elif y_mode == "Real GDP":
    y_label_short = "Real GDP Growth"
else:
    y_label_short = "Real Non-Agri GVA Growth"


# All available indicator columns
INDICATOR_COLS = {
    "Real Exports": "Real Exports",
    "IIP": "IIP",
    "Real Bank Credit": "Real Bank Credit",
    "Real Direct Taxes": "Real Direct Taxes",
    "Electricity Consumption": "Electricity Consumption growth",
    "Real Imports": "Real Imports",
    "Real Sales": "Real Sales",
    "Real GDP": "Real GDP",
    "IIP Consumption": "IIP Consumption",
    "IIP Capital": "IIP Capital",
}

# ========================
# MAIN TITLE
# ========================
st.title("India GDP: A Statistical Review")
st.markdown("**Reproducing and extending the analysis from WP26-3 (Anand, Felman & Subramanian, March 2026) with statistical tests**")
st.markdown(f"*Current settings*: **{y_mode}** | "
            f"Periods: {p1_label} vs {p2_label} | "
            f"{'Excl.' if exclude_pandemic else 'Incl.'} pandemic years")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Fig 2: GVA vs Indicators",
    "Fig 3: Sales vs Indicators",
    "Fig 4: GVA vs Sales",
    "Fig 10: CPI-WPI Wedge",
    "Fisher z Summary",
    "Custom Correlations"])


# ========================
# Helper: run a standard set of correlation plots
# ========================
def run_correlation_panel(indicator_list, dep_y1_col, dep_y2_col, dep_label, tab_container):
    """Generate correlation scatter plots + forest plot + table for a set of indicators."""
    all_stats = []
    df = df_master.copy()
    if exclude_pandemic:
        df = df[~df["YearInt"].isin([2020, 2021])]

    cols = tab_container.columns(2)
    for idx, (nice_name, col_name) in enumerate(indicator_list):
        x1, y1, x2, y2, s1, s2 = split_and_compute(
            df_master, col_name, dep_y1_col, dep_y2_col,
            period1, period2, exclude_pandemic)
        fig = make_correlation_figure(x1, y1, x2, y2, s1, s2,
            nice_name, dep_label,
            f"{dep_label.split(' Growth')[0]} and {nice_name}",
            p1_label, p2_label)
        with cols[idx % 2]:
            st.plotly_chart(fig, use_container_width=True)
        all_stats.append((s1, s2))

    # Forest plot
    tab_container.subheader("Fisher's z-Transformation Summary")
    labels = [name for name, _ in indicator_list]
    fig_forest = make_forest_plot(all_stats, labels)
    tab_container.plotly_chart(fig_forest, use_container_width=True)

    # Detailed table
    tab_container.subheader("Detailed Statistical Tests")
    table_rows = []
    for (s1, s2), (nice_name, _) in zip(all_stats, indicator_list):
        for period_lbl, s in [(p1_label, s1), (p2_label, s2)]:
            if s:
                table_rows.append({
                    "Indicator": nice_name, "Period": period_lbl,
                    "n": s["n"], "r": round(s["r"], 3),
                    "Fisher z": round(s["fisher_z"], 3),
                    "SE(z)": round(s["se_z"], 3),
                    "95% CI lower": round(s["ci_lower_r"], 3),
                    "95% CI upper": round(s["ci_upper_r"], 3),
                    "t-stat": round(s["t_stat"], 3),
                    "p-value": round(s["p_value"], 4),
                    "Sig": significance_label(s["p_value"])
                })
    if table_rows:
        tab_container.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

    # Difference-in-correlation table
    tab_container.subheader("Test: Did Correlations Change Across Periods?")
    df_diff = build_diff_table(
        all_stats,
        [dep_label.split(" Growth")[0]] * len(indicator_list),
        [name for name, _ in indicator_list])
    if not df_diff.empty:
        tab_container.dataframe(df_diff, use_container_width=True, hide_index=True)
        sig_count = (df_diff["p (diff)"] < 0.05).sum()
        tab_container.info(f"**{sig_count}/{len(df_diff)}** correlations changed significantly (p < 0.05).")

    return all_stats


# ============================================================
# TAB 1: Figure 2 - GVA and core macro indicators
# ============================================================
with tab1:
    st.header("Figure 2: Correlation between GVA and Core Macro Indicators")
    st.markdown(f"Using **{y_mode}** with **{gva_series_mode}**. Pandemic years "
                f"{'excluded' if exclude_pandemic else 'included'}.")

    gva_indicators = [
        ("Real Exports", "Real Exports"),
        ("IIP", "IIP"),
        ("Real Bank Credit", "Real Bank Credit"),
        ("Real Direct Taxes", "Real Direct Taxes"),
        ("Electricity Consumption", "Electricity Consumption growth"),
        ("Real Imports", "Real Imports"),
    ]
    all_stats_gva = run_correlation_panel(gva_indicators, y1_col, y2_col, y_label_short, st.container())


# ============================================================
# TAB 2: Figure 3 - Sales and core macro indicators
# ============================================================
with tab2:
    st.header("Figure 3: Correlation between Sales and Core Macro Indicators")
    st.markdown("Sales is an independent check — it doesn't depend on official GVA methodology.")

    sales_indicators = [
        ("Real Exports", "Real Exports"),
        ("IIP", "IIP"),
        ("Real Bank Credit", "Real Bank Credit"),
        ("Real Direct Taxes", "Real Direct Taxes"),
        ("Electricity Consumption", "Electricity Consumption growth"),
        ("Real Imports", "Real Imports"),
    ]
    # For Sales, y-col is always "Real Sales" — no old/new distinction
    all_stats_sales = run_correlation_panel(
        sales_indicators, "Real Sales", "Real Sales", "Real Sales Growth", st.container())


# ============================================================
# TAB 3: Figure 4 - GVA vs Sales
# ============================================================
with tab3:
    st.header("Figure 4: Correlation between GVA and Sales")
    st.markdown("Agriculture and public administration excluded from GVA (per paper). "
                "Uses your selected GVA series toggle.")

    x1, y1_arr, x2, y2_arr, s1, s2 = split_and_compute(
        df_master, y1_col if y1_col == y2_col else y1_col,  # GVA as x
        "Real Sales", "Real Sales" if y1_col == y2_col else "Real Sales",
        period1, period2, exclude_pandemic)

    # Actually: GVA on x-axis, Sales on y-axis (matching Fig 4)
    # Need to handle the old/new split properly
    df_work = df_master.copy()
    if exclude_pandemic:
        df_work = df_work[~df_work["YearInt"].isin([2020, 2021])]

    m1 = (df_work["YearInt"] >= period1[0]) & (df_work["YearInt"] <= period1[1])
    m2 = (df_work["YearInt"] >= period2[0]) & (df_work["YearInt"] <= period2[1])

    sub1 = df_work[m1][[y1_col, "Real Sales"]].dropna()
    sub2 = df_work[m2][[y2_col, "Real Sales"]].dropna()

    gva1_x = sub1[y1_col].values.astype(float)
    sales1_y = sub1["Real Sales"].values.astype(float)
    gva2_x = sub2[y2_col].values.astype(float)
    sales2_y = sub2["Real Sales"].values.astype(float)

    s1 = compute_correlation_with_stats(gva1_x, sales1_y)
    s2 = compute_correlation_with_stats(gva2_x, sales2_y)

    fig = make_correlation_figure(gva1_x, sales1_y, gva2_x, sales2_y, s1, s2,
        y_label_short, "Real Sales Growth", "GVA vs Sales", p1_label, p2_label)
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**{p1_label}**: {format_stats(s1)}")
    with col2:
        st.warning(f"**{p2_label}**: {format_stats(s2)}")

    # Difference test
    if s1 and s2:
        z1, z2 = s1["fisher_z"], s2["fisher_z"]
        se_d = np.sqrt(1 / max(s1["n"] - 3, 1) + 1 / max(s2["n"] - 3, 1))
        z_d = (z1 - z2) / se_d
        p_d = 2 * (1 - stats.norm.cdf(abs(z_d)))
        st.success(f"**Difference test** (Fisher z): z₁−z₂ = {z1 - z2:.3f}, "
                   f"Z = {z_d:.3f}, p = {p_d:.4f} {significance_label(p_d)}")


# ============================================================
# TAB 4: Figure 10 - CPI-WPI Wedge
# ============================================================
with tab4:
    st.header("Figure 10: CPI-WPI Wedge and GDP Discrepancies")

    df_disc = load_gdp_discrepancies()
    df_plot = df_disc.dropna(subset=["CPI minus WPI", "Discripancies"]).copy()

    if len(df_plot) > 3:
        x_vals = df_plot["CPI minus WPI"].values.astype(float)
        y_vals = df_plot["Discripancies"].values.astype(float)
        s = compute_correlation_with_stats(x_vals, y_vals)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode="markers+text",
            text=df_plot["Year"].astype(str).values, textposition="top center",
            marker=dict(color="#2ca02c", size=9), showlegend=False))

        if s:
            xr = np.linspace(np.nanmin(x_vals), np.nanmax(x_vals), 50)
            fig.add_trace(go.Scatter(x=xr, y=s["slope"] * xr + s["intercept"],
                mode="lines", line=dict(color="#2ca02c", dash="dash"), showlegend=False))
            sig = significance_label(s["p_value"])
            fig.add_annotation(x=0.99, y=0.01, xref="paper", yref="paper",
                text=f"r = {s['r']:.2f} {sig}<br>"
                     f"95% CI [{s['ci_lower_r']:.2f}, {s['ci_upper_r']:.2f}]<br>"
                     f"Fisher z = {s['fisher_z']:.3f}, p = {s['p_value']:.4f}",
                showarrow=False, font=dict(size=11), bgcolor="rgba(255,255,255,0.88)",
                bordercolor="#2ca02c", borderwidth=1, xanchor="right", yanchor="bottom")

        fig.update_layout(
            title="Expenditure-Production GDP Discrepancy vs CPI-WPI Wedge",
            xaxis_title="CPI minus WPI", yaxis_title="GDP Discrepancy (%)",
            template="plotly_white", height=520)
        st.plotly_chart(fig, use_container_width=True)
        if s:
            st.info(f"**Correlation**: {format_stats(s)}")


# ============================================================
# TAB 5: Fisher z Summary
# ============================================================
with tab5:
    st.header("Fisher's z-Transformation: Full Summary & Difference Tests")
    st.markdown(r"""
    For each correlation pair (pre vs post), we test whether the correlation
    **significantly changed** using Fisher's z-test for independent correlations:
    $$Z = \frac{z_1 - z_2}{\sqrt{\frac{1}{n_1-3} + \frac{1}{n_2-3}}}$$
    where $z_i = \text{arctanh}(r_i)$ is the Fisher transformation.
    """)

    # Re-compute all stats for GVA indicators
    all_pairs = []
    gva_ind = [("Real Exports", "Real Exports"), ("IIP", "IIP"),
               ("Real Bank Credit", "Real Bank Credit"),
               ("Real Direct Taxes", "Real Direct Taxes"),
               ("Electricity", "Electricity Consumption growth"),
               ("Real Imports", "Real Imports")]
    for nice, col in gva_ind:
        _, _, _, _, s1, s2 = split_and_compute(
            df_master, col, y1_col, y2_col, period1, period2, exclude_pandemic)
        all_pairs.append(("GVA", nice, s1, s2))

    sales_ind = gva_ind.copy()
    for nice, col in sales_ind:
        _, _, _, _, s1, s2 = split_and_compute(
            df_master, col, "Real Sales", "Real Sales", period1, period2, exclude_pandemic)
        all_pairs.append(("Sales", nice, s1, s2))

    stats_for_table = [(s1, s2) for _, _, s1, s2 in all_pairs]
    dep_labels = [dep for dep, _, _, _ in all_pairs]
    ind_labels = [ind for _, ind, _, _ in all_pairs]

    df_diff = build_diff_table(stats_for_table, dep_labels, ind_labels)
    if not df_diff.empty:
        st.dataframe(df_diff, use_container_width=True, hide_index=True)
        sig_count = (df_diff["p (diff)"] < 0.05).sum()
        st.info(f"**{sig_count}/{len(df_diff)}** correlations changed significantly (p < 0.05).")

    # Forest plot
    st.subheader("Forest Plot: All Correlation Changes")
    combined_labels = [f"{d} vs {i}" for d, i in zip(dep_labels, ind_labels)]
    fig_forest = make_forest_plot(stats_for_table, combined_labels,
        "All Correlations: Pre vs Post (with 95% CI)")
    st.plotly_chart(fig_forest, use_container_width=True)


# ============================================================
# TAB 6: Custom Correlations
# ============================================================
with tab6:
    st.header("Custom Correlation Explorer")
    st.markdown("Build your own scatter plots with any pair of variables. "
                "All Fisher z-tests are computed automatically.")

    available_y = {
        "Non-Agri GVA Old (2004-05 base)": "Real non agri GVA Old",
        "Non-Agri GVA New (2011-12 base)": "Real non agri GVA New",
        "Non-Agri GVA (paper blend: Old pre-2012, New post-2012)": "__BLEND_NONAGRI__",
        "Full GVA incl. Agri — Old (2004-05 base)": "Real Full GVA Old",
        "Full GVA incl. Agri (paper blend: Old pre-2012, GDP post-2012)": "__BLEND_FULL__",
        "Real GDP": "Real GDP",
        "Real Sales": "Real Sales",
    }
    available_x = {
        "Real Exports": "Real Exports",
        "IIP": "IIP",
        "Real Bank Credit": "Real Bank Credit",
        "Real Direct Taxes": "Real Direct Taxes",
        "Electricity Consumption": "Electricity Consumption growth",
        "Real Imports": "Real Imports",
        "Real Sales": "Real Sales",
        "Real GDP": "Real GDP",
        "Non-Agri GVA Old": "Real non agri GVA Old",
        "Non-Agri GVA New": "Real non agri GVA New",
        "IIP Consumption": "IIP Consumption",
        "IIP Capital": "IIP Capital",
    }

    c1, c2 = st.columns(2)
    with c1:
        y_choice = st.selectbox("Y-axis (dependent)", list(available_y.keys()), index=0)
    with c2:
        x_choices = st.multiselect("X-axis indicators (select one or more)",
            list(available_x.keys()),
            default=["Real Exports", "IIP", "Real Bank Credit"])

    custom_p1 = (st.session_state.get("p1_start", p1_start),
                 st.session_state.get("p1_end", p1_end))
    custom_p2 = (st.session_state.get("p2_start", p2_start),
                 st.session_state.get("p2_end", p2_end))

    if x_choices:
        custom_stats = []
        cols_disp = st.columns(min(2, len(x_choices)))

        for idx, x_name in enumerate(x_choices):
            x_col = available_x[x_name]
            y_val = available_y[y_choice]

            # Handle blended GVA options
            if y_val == "__BLEND_NONAGRI__":
                cy1 = "Real non agri GVA Old"
                cy2 = "Real non agri GVA New"
            elif y_val == "__BLEND_FULL__":
                cy1 = "Real Full GVA Old"   # 2004-05 base for pre-2012
                cy2 = "Real GDP"             # new base ≈ GDP for post-2012
            else:
                cy1 = y_val
                cy2 = y_val

            x1, y1_arr, x2, y2_arr, s1, s2 = split_and_compute(
                df_master, x_col, cy1, cy2, period1, period2, exclude_pandemic)

            fig = make_correlation_figure(x1, y1_arr, x2, y2_arr, s1, s2,
                x_name, y_choice,
                f"{y_choice} vs {x_name}",
                p1_label, p2_label)

            with cols_disp[idx % len(cols_disp)]:
                st.plotly_chart(fig, use_container_width=True)
            custom_stats.append((s1, s2))

        # Summary table
        if len(custom_stats) > 0:
            st.subheader("Custom Correlation Results")
            df_custom = build_diff_table(
                custom_stats,
                [y_choice] * len(x_choices),
                x_choices)
            if not df_custom.empty:
                st.dataframe(df_custom, use_container_width=True, hide_index=True)

            # Forest plot
            fig_f = make_forest_plot(custom_stats, x_choices,
                f"Custom: {y_choice} vs selected indicators")
            st.plotly_chart(fig_f, use_container_width=True)
    else:
        st.warning("Select at least one X-axis indicator above.")


# ========================
# FOOTER
# ========================
st.markdown("---")
st.caption("Data: Replication Package from Anand, Felman & Subramanian (WP26-3, March 2026). "
           "Statistical tests use Fisher's z-transformation with 95% CIs. "
           "Significance: *** p<0.001, ** p<0.01, * p<0.05, n.s. not significant.")
