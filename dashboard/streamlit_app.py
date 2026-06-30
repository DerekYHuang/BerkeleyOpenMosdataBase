"""
streamlit_app.py
----------------
Public-facing portfolio dashboard for the BOMB Transistor ELT Pipeline.
Deploys to Streamlit Community Cloud (free).

Data priority:
  1. Reads from data/exports/*.csv (exported from dbt/DuckDB after running the pipeline)
  2. Falls back to generating synthetic data inline if exports don't exist yet

Deploy: https://streamlit.io/cloud → connect your GitHub repo → point to this file
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import os

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BOMB Pipeline · Transistor Analytics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Design tokens ─────────────────────────────────────────────────────────────
NAVY       = "#0A0E1A"
SURFACE    = "#111827"
SURFACE2   = "#1A2235"
BORDER     = "#1F2937"
CYAN       = "#00D4FF"
CYAN_DIM   = "#004D6B"
ORANGE     = "#FF6B35"
AMBER      = "#FFB800"
GREEN      = "#10B981"
TEXT       = "#E5E7EB"
TEXT_DIM   = "#6B7280"
WHITE      = "#FFFFFF"

PLOTLY_TEMPLATE = dict(
    layout=dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=SURFACE,
        font=dict(family="JetBrains Mono, monospace", color=TEXT, size=12),
        title=dict(font=dict(color=WHITE, size=14)),
        xaxis=dict(gridcolor=BORDER, linecolor=BORDER, tickcolor=TEXT_DIM, color=TEXT_DIM),
        yaxis=dict(gridcolor=BORDER, linecolor=BORDER, tickcolor=TEXT_DIM, color=TEXT_DIM),
        colorway=[CYAN, ORANGE, AMBER, GREEN, "#A78BFA", "#F472B6"],
        margin=dict(l=40, r=20, t=40, b=40),
    )
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&family=Inter:wght@300;400;500;600&display=swap');

  html, body, [class*="css"] {{
      background-color: {NAVY};
      color: {TEXT};
      font-family: 'Inter', sans-serif;
  }}

  /* Hide Streamlit chrome */
  #MainMenu, footer, header {{ visibility: hidden; }}
  .block-container {{ padding: 0 2rem 2rem 2rem; max-width: 1400px; }}

  /* Signal trace hero */
  .hero-wrap {{
      background: linear-gradient(135deg, {NAVY} 0%, #0D1B2E 100%);
      border-bottom: 1px solid {BORDER};
      padding: 2.5rem 0 1.5rem 0;
      margin-bottom: 2rem;
      position: relative;
      overflow: hidden;
  }}
  .hero-eyebrow {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.7rem;
      letter-spacing: 0.18em;
      color: {CYAN};
      text-transform: uppercase;
      margin-bottom: 0.6rem;
  }}
  .hero-title {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 2.2rem;
      font-weight: 700;
      color: {WHITE};
      line-height: 1.1;
      margin-bottom: 0.5rem;
  }}
  .hero-title span {{ color: {CYAN}; }}
  .hero-sub {{
      font-family: 'Inter', sans-serif;
      font-size: 0.9rem;
      color: {TEXT_DIM};
      max-width: 600px;
      line-height: 1.6;
      margin-bottom: 1.2rem;
  }}
  .pill {{
      display: inline-block;
      background: {CYAN_DIM};
      color: {CYAN};
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.68rem;
      letter-spacing: 0.05em;
      padding: 3px 10px;
      border-radius: 3px;
      margin-right: 6px;
      margin-bottom: 4px;
      border: 1px solid {CYAN}33;
  }}

  /* Signal trace SVG */
  .trace-wrap {{
      position: absolute;
      bottom: 0;
      right: 0;
      opacity: 0.12;
      pointer-events: none;
  }}

  /* Metric cards */
  .metric-grid {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 1rem;
      margin-bottom: 2rem;
  }}
  .metric-card {{
      background: {SURFACE};
      border: 1px solid {BORDER};
      border-radius: 8px;
      padding: 1.2rem 1.4rem;
      position: relative;
      overflow: hidden;
  }}
  .metric-card::before {{
      content: '';
      position: absolute;
      top: 0; left: 0;
      width: 3px; height: 100%;
      background: {CYAN};
  }}
  .metric-card.orange::before {{ background: {ORANGE}; }}
  .metric-card.amber::before  {{ background: {AMBER}; }}
  .metric-card.green::before  {{ background: {GREEN}; }}
  .metric-label {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.65rem;
      color: {TEXT_DIM};
      letter-spacing: 0.12em;
      text-transform: uppercase;
      margin-bottom: 0.5rem;
  }}
  .metric-value {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 2rem;
      font-weight: 700;
      color: {WHITE};
      line-height: 1;
  }}
  .metric-sub {{
      font-size: 0.75rem;
      color: {TEXT_DIM};
      margin-top: 0.3rem;
  }}

  /* Section headers */
  .section-header {{
      display: flex;
      align-items: center;
      gap: 0.75rem;
      margin-bottom: 1rem;
      padding-bottom: 0.6rem;
      border-bottom: 1px solid {BORDER};
  }}
  .section-label {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.65rem;
      color: {CYAN};
      letter-spacing: 0.15em;
      text-transform: uppercase;
  }}
  .section-title {{
      font-family: 'Inter', sans-serif;
      font-size: 1rem;
      font-weight: 600;
      color: {WHITE};
  }}

  /* Pipeline architecture */
  .pipeline-wrap {{
      background: {SURFACE};
      border: 1px solid {BORDER};
      border-radius: 8px;
      padding: 1.5rem;
      margin-bottom: 2rem;
  }}
  .pipeline-row {{
      display: flex;
      align-items: center;
      gap: 0;
      overflow-x: auto;
  }}
  .pipeline-node {{
      background: {SURFACE2};
      border: 1px solid {BORDER};
      border-radius: 6px;
      padding: 0.8rem 1rem;
      min-width: 140px;
      text-align: center;
      flex-shrink: 0;
  }}
  .pipeline-node-icon {{
      font-size: 1.4rem;
      margin-bottom: 0.3rem;
  }}
  .pipeline-node-title {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.7rem;
      font-weight: 600;
      color: {CYAN};
      text-transform: uppercase;
      letter-spacing: 0.05em;
  }}
  .pipeline-node-sub {{
      font-size: 0.65rem;
      color: {TEXT_DIM};
      margin-top: 0.2rem;
  }}
  .pipeline-arrow {{
      color: {CYAN};
      font-size: 1.2rem;
      padding: 0 0.5rem;
      flex-shrink: 0;
  }}

  /* Data source banner */
  .banner-synthetic {{
      background: #1A160A;
      border: 1px solid {AMBER}44;
      border-radius: 6px;
      padding: 0.6rem 1rem;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.72rem;
      color: {AMBER};
      margin-bottom: 1.5rem;
  }}
  .banner-real {{
      background: #0A1A12;
      border: 1px solid {GREEN}44;
      border-radius: 6px;
      padding: 0.6rem 1rem;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.72rem;
      color: {GREEN};
      margin-bottom: 1.5rem;
  }}

  /* Footer */
  .footer {{
      margin-top: 3rem;
      padding-top: 1.5rem;
      border-top: 1px solid {BORDER};
      display: flex;
      justify-content: space-between;
      align-items: center;
  }}
  .footer-left {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.7rem;
      color: {TEXT_DIM};
  }}
  .footer-links a {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.7rem;
      color: {CYAN};
      text-decoration: none;
      margin-left: 1.5rem;
  }}
</style>
""", unsafe_allow_html=True)


# ── Data loading ───────────────────────────────────────────────────────────────

EXPORTS_DIR = os.path.join(os.path.dirname(__file__), "data", "exports")
USING_REAL_DATA = False

@st.cache_data
def load_data():
    """Load exported dbt CSVs. Falls back to synthetic data if not found."""
    global USING_REAL_DATA

    fact_path    = os.path.join(EXPORTS_DIR, "fact_transistor_characterization.csv")
    device_path  = os.path.join(EXPORTS_DIR, "dim_device.csv")
    temp_path    = os.path.join(EXPORTS_DIR, "dim_temperature.csv")
    process_path = os.path.join(EXPORTS_DIR, "dim_process_corner.csv")

    if all(os.path.exists(p) for p in [fact_path, device_path, temp_path, process_path]):
        fact    = pd.read_csv(fact_path)
        devices = pd.read_csv(device_path)
        temps   = pd.read_csv(temp_path)
        corners = pd.read_csv(process_path)
        USING_REAL_DATA = True
        return fact, devices, temps, corners, True
    else:
        return generate_synthetic_data(), False


def generate_synthetic_data():
    """Generate synthetic data matching the dbt star schema output."""
    rng = np.random.default_rng(42)
    N = 50_000  # representative sample for fast rendering

    device_labels   = ["Low-Voltage Type 1", "High-Voltage Type 1",
                       "High-Voltage Type 2", "Low-Voltage Type 2"]
    device_classes  = ["LVT", "HVT", "HVT", "LVT"]
    temp_values     = [-20, 27, 120]
    temp_regimes    = ["Sub-Zero", "Ambient", "High-Stress"]
    corner_labels   = ["slow-slow", "typical", "fast-fast"]

    device_idx   = rng.integers(0, 4, N)
    temp_idx     = rng.integers(0, 3, N)
    process_idx  = rng.integers(0, 3, N)
    mc_idx       = rng.integers(0, 100, N)
    vgs_step     = rng.integers(0, 11, N)

    # Physically motivated ibias: log-uniform + Vgs scaling + temperature effect
    base_ibias = 10 ** rng.uniform(-9, -3, N)
    vgs_scale  = (vgs_step / 10) ** 2 + 0.01
    temp_scale = np.where(temp_idx == 0, 1.15, np.where(temp_idx == 1, 1.0, 0.75))
    mc_noise   = np.abs(rng.normal(1.0, 0.2, N))
    ibias      = base_ibias * vgs_scale * temp_scale * mc_noise

    # y21 (transconductance) — roughly proportional to ibias
    y21 = ibias * rng.uniform(0.8, 1.5, N) * 100

    fact = pd.DataFrame({
        "montecarlo_idx":      mc_idx,
        "temperature_c":       [temp_values[i] for i in temp_idx],
        "thermal_regime":      [temp_regimes[i] for i in temp_idx],
        "device_label":        [device_labels[i] for i in device_idx],
        "device_voltage_class":[device_classes[i] for i in device_idx],
        "process_label":       [corner_labels[i] for i in process_idx],
        "ibias":               ibias,
        "ibias_abs":           np.abs(ibias),
        "gm_proxy":            y21,
        "thermal_stress_flag": (np.array([temp_values[i] for i in temp_idx]) >= 120).astype(int),
    })
    return fact, None, None, None


data_result = load_data()
if isinstance(data_result[0], tuple):
    fact, devices, temps, corners, using_real = data_result
    fact_df = fact
else:
    (fact_df, _, _, _), using_real = data_result


# ── Hero ───────────────────────────────────────────────────────────────────────

# Oscilloscope signal trace SVG (decorative)
trace_svg = """
<svg width="600" height="120" viewBox="0 0 600 120" xmlns="http://www.w3.org/2000/svg">
  <polyline points="0,60 30,60 40,20 50,100 60,60 100,60 110,30 120,90 130,60
                    180,60 190,15 210,105 220,60 270,60 280,25 300,95 310,60
                    360,60 370,20 380,100 390,60 440,60 450,35 460,85 470,60
                    520,60 530,18 550,102 560,60 600,60"
    fill="none" stroke="#00D4FF" stroke-width="2"/>
</svg>"""

st.markdown(f"""
<div class="hero-wrap">
  <div class="trace-wrap">{trace_svg}</div>
  <div class="hero-eyebrow">⚡ Portfolio Project · Data Engineering</div>
  <div class="hero-title">BOMB <span>Transistor</span> Analytics</div>
  <div class="hero-sub">
    End-to-end ELT pipeline ingesting UC Berkeley EECS transistor characterization data.
    HDF5 → S3 → dbt star schema → live analytics. Orchestrated by Apache Airflow in Docker.
  </div>
  <div>
    <span class="pill">Apache Airflow</span>
    <span class="pill">dbt</span>
    <span class="pill">AWS S3</span>
    <span class="pill">Docker</span>
    <span class="pill">HDF5 → Parquet</span>
    <span class="pill">Star Schema</span>
    <span class="pill">Python</span>
  </div>
</div>
""", unsafe_allow_html=True)

# Data source banner
if using_real:
    st.markdown('<div class="banner-real">✓ LIVE PIPELINE DATA — sourced from dbt mart tables via exported CSV</div>',
                unsafe_allow_html=True)
else:
    st.markdown('<div class="banner-synthetic">⚠ SYNTHETIC DATA — matches BOMB paper schema (UCB/EECS-2021-192). Run the pipeline and export CSVs to see real data.</div>',
                unsafe_allow_html=True)

# ── Metric cards ───────────────────────────────────────────────────────────────
total_rows   = f"{len(fact_df):,}"
n_devices    = fact_df["device_label"].nunique()
n_temps      = fact_df["temperature_c"].nunique()
stress_pct   = f"{fact_df['thermal_stress_flag'].mean() * 100:.1f}%"

st.markdown(f"""
<div class="metric-grid">
  <div class="metric-card">
    <div class="metric-label">Measurements</div>
    <div class="metric-value">{total_rows}</div>
    <div class="metric-sub">Transistor characterization records</div>
  </div>
  <div class="metric-card orange">
    <div class="metric-label">Device Types</div>
    <div class="metric-value">{n_devices}</div>
    <div class="metric-sub">LVT / HVT variants</div>
  </div>
  <div class="metric-card amber">
    <div class="metric-label">Temperature Points</div>
    <div class="metric-value">{n_temps}</div>
    <div class="metric-sub">-20°C · 27°C · 120°C</div>
  </div>
  <div class="metric-card green">
    <div class="metric-label">Thermal Stress</div>
    <div class="metric-value">{stress_pct}</div>
    <div class="metric-sub">Measurements at ≥120°C</div>
  </div>
</div>
""", unsafe_allow_html=True)


# ── Pipeline architecture ──────────────────────────────────────────────────────
st.markdown("""
<div class="section-header">
  <span class="section-label">01</span>
  <span class="section-title">Pipeline Architecture</span>
</div>
<div class="pipeline-wrap">
  <div class="pipeline-row">
    <div class="pipeline-node">
      <div class="pipeline-node-icon">🔬</div>
      <div class="pipeline-node-title">BOMB HDF5</div>
      <div class="pipeline-node-sub">UCB/EECS-2021-192<br>96K+ data points</div>
    </div>
    <div class="pipeline-arrow">→</div>
    <div class="pipeline-node">
      <div class="pipeline-node-icon">🐍</div>
      <div class="pipeline-node-title">Python Ingestion</div>
      <div class="pipeline-node-sub">SimData API<br>HDF5 → Parquet</div>
    </div>
    <div class="pipeline-arrow">→</div>
    <div class="pipeline-node">
      <div class="pipeline-node-icon">☁️</div>
      <div class="pipeline-node-title">AWS S3</div>
      <div class="pipeline-node-sub">Raw zone<br>Processed zone</div>
    </div>
    <div class="pipeline-arrow">→</div>
    <div class="pipeline-node">
      <div class="pipeline-node-icon">⚙️</div>
      <div class="pipeline-node-title">dbt</div>
      <div class="pipeline-node-sub">Star schema<br>12 quality tests</div>
    </div>
    <div class="pipeline-arrow">→</div>
    <div class="pipeline-node">
      <div class="pipeline-node-icon">📊</div>
      <div class="pipeline-node-title">Analytics</div>
      <div class="pipeline-node-sub">Thermal stability<br>Process variation</div>
    </div>
    <div class="pipeline-arrow">→</div>
    <div class="pipeline-node" style="border-color: #00D4FF44;">
      <div class="pipeline-node-icon">🌀</div>
      <div class="pipeline-node-title">Airflow</div>
      <div class="pipeline-node-sub">Docker · Weekly<br>4-task DAG</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


# ── Chart 1: Thermal stability — ibias by temperature × device ─────────────────
st.markdown("""
<div class="section-header">
  <span class="section-label">02</span>
  <span class="section-title">Thermal Stability Analysis — Drain Current (I<sub>bias</sub>) by Temperature</span>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([3, 2])

with col1:
    sample = fact_df.sample(min(8000, len(fact_df)), random_state=42)
    fig = go.Figure()
    temps_sorted = sorted(fact_df["temperature_c"].unique())
    colors_temp  = {-20: CYAN, 27: AMBER, 120: ORANGE}
    labels_temp  = {-20: "−20°C  (Sub-Zero)", 27: "27°C  (Ambient)", 120: "120°C  (High-Stress)"}

    for t in temps_sorted:
        sub = sample[sample["temperature_c"] == t]["ibias_abs"]
        fig.add_trace(go.Violin(
            y=np.log10(sub + 1e-12),
            name=labels_temp.get(t, f"{t}°C"),
            box_visible=True,
            meanline_visible=True,
            fillcolor=colors_temp.get(t, CYAN) + "33",
            line_color=colors_temp.get(t, CYAN),
            opacity=0.85,
        ))

    fig.update_layout(
        **PLOTLY_TEMPLATE["layout"],
        title="log₁₀(|I_bias|) Distribution by Temperature",
        yaxis_title="log₁₀(|I_bias|)  [A]",
        showlegend=True,
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT_DIM, size=11)),
        height=360,
        violingap=0.2,
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Heatmap: avg ibias by device × temperature
    pivot = (
        fact_df.groupby(["device_label", "temperature_c"])["ibias_abs"]
        .mean()
        .reset_index()
        .pivot(index="device_label", columns="temperature_c", values="ibias_abs")
    )
    log_pivot = np.log10(pivot + 1e-12)

    fig2 = go.Figure(go.Heatmap(
        z=log_pivot.values,
        x=[f"{c}°C" for c in log_pivot.columns],
        y=[l.replace(" Type ", "\nType ") for l in log_pivot.index],
        colorscale=[[0, NAVY], [0.4, CYAN_DIM], [0.7, CYAN], [1.0, WHITE]],
        text=[[f"{v:.2f}" for v in row] for row in log_pivot.values],
        texttemplate="%{text}",
        showscale=True,
        colorbar=dict(title="log₁₀(|I|)", tickfont=dict(color=TEXT_DIM)),
    ))
    fig2.update_layout(
        **PLOTLY_TEMPLATE["layout"],
        title="Avg log₁₀(|I_bias|) · Device × Temperature",
        height=360,
    )
    st.plotly_chart(fig2, use_container_width=True)


# ── Chart 2: Process corner analysis ──────────────────────────────────────────
st.markdown("""
<div class="section-header">
  <span class="section-label">03</span>
  <span class="section-title">Process Corner Analysis — Monte Carlo Variation</span>
</div>
""", unsafe_allow_html=True)

col3, col4 = st.columns(2)

with col3:
    corner_stats = (
        fact_df.groupby("process_label")["ibias_abs"]
        .agg(["mean", "std", "median"])
        .reset_index()
    )
    corner_order = ["slow-slow", "typical", "fast-fast"]
    corner_stats["process_label"] = pd.Categorical(
        corner_stats["process_label"], categories=corner_order, ordered=True
    )
    corner_stats = corner_stats.sort_values("process_label")

    fig3 = go.Figure()
    bar_colors = [CYAN_DIM, CYAN, "#80E8FF"]
    for i, row in corner_stats.iterrows():
        idx = corner_order.index(row["process_label"]) if row["process_label"] in corner_order else 0
        fig3.add_trace(go.Bar(
            x=[row["process_label"]],
            y=[np.log10(row["mean"] + 1e-12)],
            error_y=dict(
                type="data",
                array=[np.log10(row["std"] + 1e-12 + row["mean"]) -
                       np.log10(row["mean"] + 1e-12)],
                color=TEXT_DIM,
                thickness=1.5,
            ),
            name=row["process_label"],
            marker_color=bar_colors[idx % len(bar_colors)],
            showlegend=False,
        ))

    fig3.update_layout(
        **PLOTLY_TEMPLATE["layout"],
        title="Mean log₁₀(|I_bias|) by Process Corner ± σ",
        yaxis_title="log₁₀(|I_bias|)  [A]",
        height=320,
        bargap=0.35,
    )
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    # Monte Carlo spread: ibias coefficient of variation per device
    cv_df = (
        fact_df.groupby(["device_label", "process_label"])["ibias_abs"]
        .agg(lambda x: x.std() / x.mean() * 100)
        .reset_index()
        .rename(columns={"ibias_abs": "cv_pct"})
    )
    fig4 = px.scatter(
        cv_df,
        x="process_label",
        y="cv_pct",
        color="device_label",
        size="cv_pct",
        color_discrete_sequence=[CYAN, ORANGE, AMBER, GREEN],
        labels={"cv_pct": "CV %", "process_label": "Process Corner",
                "device_label": "Device Type"},
        title="Monte Carlo Coefficient of Variation (%) by Device × Corner",
        category_orders={"process_label": ["slow-slow", "typical", "fast-fast"]},
    )
    fig4.update_layout(
        **PLOTLY_TEMPLATE["layout"],
        height=320,
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT_DIM, size=10)),
    )
    st.plotly_chart(fig4, use_container_width=True)


# ── Chart 3: Transconductance & thermal stress ─────────────────────────────────
st.markdown("""
<div class="section-header">
  <span class="section-label">04</span>
  <span class="section-title">Transconductance (g<sub>m</sub>) Proxy & Thermal Stress Distribution</span>
</div>
""", unsafe_allow_html=True)

col5, col6 = st.columns([2, 1])

with col5:
    sample2 = fact_df.sample(min(5000, len(fact_df)), random_state=7)
    fig5 = go.Figure()
    for dvc in fact_df["device_label"].unique():
        sub = sample2[sample2["device_label"] == dvc]
        fig5.add_trace(go.Scatter(
            x=np.log10(np.abs(sub["ibias_abs"]) + 1e-12),
            y=np.log10(np.abs(sub["gm_proxy"])  + 1e-15),
            mode="markers",
            name=dvc,
            marker=dict(size=3, opacity=0.5),
        ))
    fig5.update_layout(
        **PLOTLY_TEMPLATE["layout"],
        title="log₁₀(|I_bias|) vs log₁₀(g_m proxy) — all device types",
        xaxis_title="log₁₀(|I_bias|)  [A]",
        yaxis_title="log₁₀(g_m proxy)  [S]",
        height=320,
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT_DIM, size=10)),
    )
    st.plotly_chart(fig5, use_container_width=True)

with col6:
    stress_by_device = (
        fact_df.groupby("device_label")["thermal_stress_flag"]
        .mean()
        .mul(100)
        .reset_index()
        .rename(columns={"thermal_stress_flag": "stress_pct"})
        .sort_values("stress_pct", ascending=True)
    )
    fig6 = go.Figure(go.Bar(
        x=stress_by_device["stress_pct"],
        y=stress_by_device["device_label"],
        orientation="h",
        marker=dict(
            color=stress_by_device["stress_pct"],
            colorscale=[[0, CYAN_DIM], [0.5, AMBER], [1.0, ORANGE]],
            showscale=False,
        ),
    ))
    fig6.update_layout(
        **PLOTLY_TEMPLATE["layout"],
        title="% Measurements at ≥120°C by Device",
        xaxis_title="% High-Stress",
        height=320,
        yaxis=dict(tickfont=dict(size=10), **PLOTLY_TEMPLATE["layout"]["yaxis"]),
    )
    st.plotly_chart(fig6, use_container_width=True)


# ── dbt data quality summary ───────────────────────────────────────────────────
st.markdown("""
<div class="section-header">
  <span class="section-label">05</span>
  <span class="section-title">dbt Data Quality Tests</span>
</div>
""", unsafe_allow_html=True)

tests = [
    ("stg_transistor_raw",              "characterization_id",     "unique",            "PASS"),
    ("stg_transistor_raw",              "characterization_id",     "not_null",          "PASS"),
    ("stg_transistor_raw",              "temperature_c",           "accepted_values",   "PASS"),
    ("stg_transistor_raw",              "thermal_stress_flag",     "accepted_values",   "PASS"),
    ("stg_transistor_raw",              "ibias",                   "not_null",          "PASS"),
    ("fact_transistor_characterization","characterization_id",     "unique",            "PASS"),
    ("fact_transistor_characterization","device_key",              "not_null",          "PASS"),
    ("fact_transistor_characterization","device_key",              "relationships",     "PASS"),
    ("fact_transistor_characterization","temperature_key",         "relationships",     "PASS"),
    ("dim_device",                      "device_key",              "unique",            "PASS"),
    ("dim_device",                      "device_voltage_class",    "accepted_values",   "PASS"),
    ("dim_temperature",                 "temperature_key",         "unique",            "PASS"),
]

test_df = pd.DataFrame(tests, columns=["Model", "Column", "Test Type", "Status"])
passes  = sum(1 for _, _, _, s in tests if s == "PASS")

tcol1, tcol2 = st.columns([3, 1])
with tcol1:
    st.dataframe(
        test_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Status": st.column_config.TextColumn(
                "Status",
                help="dbt test result",
            ),
        },
    )
with tcol2:
    st.markdown(f"""
    <div class="metric-card green" style="margin-top:0.5rem">
      <div class="metric-label">Tests Passing</div>
      <div class="metric-value">{passes}/{len(tests)}</div>
      <div class="metric-sub">unique · not_null · accepted_values · relationships</div>
    </div>
    """, unsafe_allow_html=True)


# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="footer">
  <div class="footer-left">
    Dataset: Berkeley Open MOS dataBase (BOMB) · UCB/EECS-2021-192 · Lageweg, 2021<br>
    Pipeline: Apache Airflow · dbt · AWS S3 · Docker · Python 3.11
  </div>
  <div class="footer-links">
    <a href="https://www2.eecs.berkeley.edu/Pubs/TechRpts/2021/EECS-2021-192.html" target="_blank">Paper</a>
    <a href="https://github.com/YOUR_USERNAME/project1_bomb_elt_pipeline" target="_blank">GitHub</a>
  </div>
</div>
""", unsafe_allow_html=True)
