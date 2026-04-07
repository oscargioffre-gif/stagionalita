"""
🇮🇹🇺🇸 STAGIONALITÀ — Milano & NASDAQ
Streamlit app for seasonal stock pattern analysis.

Data sources: Yahoo Finance (primary), Stooq (fallback), local cache (emergency).
NEVER fabricates data. Every number has a provenance.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import json
import os

from data_fetcher import (
    STOCKS, run_full_analysis, get_last_update_time,
    fetch_monthly_returns, analyze_ticker_seasonality
)

# ═══════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="STAGIONALITÀ — Milano & NASDAQ",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════════════════════════════
# CUSTOM CSS — Dark finance terminal aesthetic
# ═══════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=DM+Sans:wght@400;500;600;700&display=swap');

:root {
    --bg: #0a0e1a;
    --sf: #111827;
    --sf2: #1a2035;
    --bd: #1e2a4a;
    --tx: #e2e8f0;
    --dm: #64748b;
    --gn: #22d98c;
    --rd: #f75c5c;
    --yl: #ccff00;
    --bl: #5888ff;
    --gd: #ffc83a;
}

.stApp { background: var(--bg) !important; }

/* Hero header */
.hero-box {
    background: linear-gradient(135deg, #0a0e1a 0%, #111d3a 50%, #0a1628 100%);
    border: 1px solid #1e2a4a;
    border-radius: 16px;
    padding: 28px 32px;
    margin-bottom: 20px;
    position: relative;
    overflow: hidden;
}
.hero-box::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -20%;
    width: 400px;
    height: 400px;
    background: radial-gradient(circle, rgba(204,255,0,0.04) 0%, transparent 70%);
    pointer-events: none;
}
.hero-title {
    font-family: 'DM Sans', sans-serif;
    font-size: 32px;
    font-weight: 700;
    letter-spacing: -0.5px;
    margin: 0 0 4px 0;
    color: #e2e8f0;
}
.hero-title .yl { color: #ccff00; }
.hero-title .bl { color: #5888ff; }
.hero-sub {
    font-family: 'DM Sans', sans-serif;
    font-size: 14px;
    color: #64748b;
    margin: 0;
}
.flag-row { display: flex; gap: 10px; margin-top: 10px; }
.flag { font-size: 28px; }

/* Metric cards */
.metric-row { display: flex; gap: 12px; flex-wrap: wrap; margin: 16px 0; }
.metric-card {
    background: #111827;
    border: 1px solid #1e2a4a;
    border-radius: 10px;
    padding: 14px 18px;
    min-width: 120px;
    flex: 1;
}
.metric-card .label {
    font-family: 'DM Sans', sans-serif;
    font-size: 11px;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 4px;
}
.metric-card .value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 22px;
    font-weight: 700;
    color: #e2e8f0;
}
.metric-card .value.gn { color: #22d98c; }
.metric-card .value.rd { color: #f75c5c; }
.metric-card .value.yl { color: #ccff00; }
.metric-card .value.bl { color: #5888ff; }

/* Table styling */
.pattern-row {
    background: #111827;
    border: 1px solid #1e2a4a;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 14px;
    transition: background 0.15s;
    cursor: pointer;
}
.pattern-row:hover { background: #1a2035; border-color: #2a3a5a; }

.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 6px;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    font-size: 11px;
}
.badge.up { background: rgba(34,217,140,0.1); color: #22d98c; border: 1px solid rgba(34,217,140,0.25); }
.badge.dn { background: rgba(247,92,92,0.1); color: #f75c5c; border: 1px solid rgba(247,92,92,0.25); }
.badge.mi { background: rgba(255,200,58,0.1); color: #ffc83a; border: 1px solid rgba(255,200,58,0.25); }
.badge.nq { background: rgba(88,136,255,0.1); color: #5888ff; border: 1px solid rgba(88,136,255,0.25); }

.source-tag {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    padding: 2px 6px;
    border-radius: 4px;
}
.source-tag.ok { background: rgba(34,217,140,0.1); color: #22d98c; }
.source-tag.warn { background: rgba(255,200,58,0.1); color: #ffc83a; }
.source-tag.err { background: rgba(247,92,92,0.1); color: #f75c5c; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #0d1220 !important;
    border-right: 1px solid #1e2a4a !important;
}

/* Hide streamlit branding */
#MainMenu, footer, header { visibility: hidden; }
div[data-testid="stDecoration"] { display: none; }

/* Expander fix */
.streamlit-expanderHeader {
    background: #111827 !important;
    border: 1px solid #1e2a4a !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
}
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════
st.markdown("""
<div class="hero-box">
    <div class="flag-row"><span class="flag">🇮🇹</span><span class="flag">🇺🇸</span></div>
    <h1 class="hero-title"><span class="yl">STAGIONALITÀ</span> — <span class="bl">Milano</span> & NASDAQ</h1>
    <p class="hero-sub">Pattern mensili statisticamente significativi · Dati aggiornati da Yahoo Finance · Nessun dato inventato</p>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### ⚙️ Filtri")
    
    market_filter = st.selectbox("Mercato", ["Tutti", "Milano", "NASDAQ"])
    direction_filter = st.selectbox("Direzione", ["Tutti", "▲ Rialzo", "▼ Ribasso"])
    month_filter = st.selectbox("Mese", ["Tutti"] + [f"{i} - {MN[i]}" for i, MN in enumerate(
        ['','Gennaio','Febbraio','Marzo','Aprile','Maggio','Giugno',
         'Luglio','Agosto','Settembre','Ottobre','Novembre','Dicembre'], 0) if i > 0])
    
    sectors = sorted(set(s["sector"] for s in STOCKS.values()))
    sector_filter = st.selectbox("Settore", ["Tutti"] + sectors)
    
    st.markdown("---")
    st.markdown("### 📊 Dati")
    
    last_update = get_last_update_time()
    if last_update:
        st.info(f"Ultimo aggiornamento: {last_update.strftime('%d/%m/%Y %H:%M')}")
    
    if st.button("🔄 AGGIORNA DATI", type="primary", use_container_width=True):
        st.session_state.force_refresh = True
        st.rerun()
    
    st.markdown("---")
    st.markdown("""
    <div style="font-size:10px;color:#64748b;line-height:1.5">
    <b>Fonti dati:</b><br>
    1️⃣ Yahoo Finance (primaria)<br>
    2️⃣ Stooq.com (fallback)<br>
    3️⃣ Cache locale (emergenza)<br><br>
    <b>⚠️ Disclaimer:</b> Rendimenti passati non garantiscono risultati futuri. 
    Non costituisce consiglio finanziario. Significatività statistica: p-value < 0.10.
    </div>
    """, unsafe_allow_html=True)

MN_LIST = ['','Gen','Feb','Mar','Apr','Mag','Giu','Lug','Ago','Set','Ott','Nov','Dic']

# ═══════════════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600, show_spinner=False)
def load_data():
    """Load or refresh all seasonal data."""
    placeholder = st.empty()
    progress = st.progress(0, text="Avvio analisi...")
    
    def update_progress(pct, msg):
        progress.progress(pct, text=msg)
    
    df, errors = run_full_analysis(progress_callback=update_progress)
    progress.empty()
    placeholder.empty()
    return df, errors

# Force refresh if button pressed
if st.session_state.get('force_refresh'):
    st.cache_data.clear()
    st.session_state.force_refresh = False

df, errors = load_data()

if df is None or len(df) == 0:
    st.error("❌ Nessun dato disponibile. Verifica la connessione internet e riprova.")
    st.stop()


# ═══════════════════════════════════════════════════════════════
# APPLY FILTERS
# ═══════════════════════════════════════════════════════════════
filtered = df.copy()

if market_filter != "Tutti":
    filtered = filtered[filtered['market'] == market_filter]
if direction_filter == "▲ Rialzo":
    filtered = filtered[filtered['direction'] == 'up']
elif direction_filter == "▼ Ribasso":
    filtered = filtered[filtered['direction'] == 'down']
if month_filter != "Tutti":
    month_num = int(month_filter.split(' - ')[0])
    filtered = filtered[filtered['month'] == month_num]
if sector_filter != "Tutti":
    filtered = filtered[filtered['sector'] == sector_filter]


# ═══════════════════════════════════════════════════════════════
# METRICS
# ═══════════════════════════════════════════════════════════════
c1, c2, c3, c4, c5, c6 = st.columns(6)

n_total = len(filtered)
n_up = len(filtered[filtered['direction'] == 'up'])
n_down = len(filtered[filtered['direction'] == 'down'])
n_mi = len(filtered[filtered['market'] == 'Milano'])
n_nq = len(filtered[filtered['market'] == 'NASDAQ'])
avg_ret = filtered['mean_return'].abs().mean() if len(filtered) > 0 else 0

with c1:
    st.metric("Pattern", n_total)
with c2:
    st.metric("▲ Rialzo", n_up)
with c3:
    st.metric("▼ Ribasso", n_down)
with c4:
    st.metric("🇮🇹 Milano", n_mi)
with c5:
    st.metric("🇺🇸 NASDAQ", n_nq)
with c6:
    st.metric("|Rend.| medio", f"{avg_ret:.1f}%")


# Show errors if any
if errors:
    with st.expander(f"⚠️ {len(errors)} titoli con problemi di dati", expanded=False):
        for e in errors:
            st.markdown(f"- **{e['name']}** ({e['ticker']}): `{e['error']}`")


# ═══════════════════════════════════════════════════════════════
# MAIN TABLE
# ═══════════════════════════════════════════════════════════════
st.markdown("---")

# Sort options
sort_col = st.selectbox("Ordina per", ["P-value (significatività)", "Rendimento medio (abs)", "Consistenza", "Ticker"], 
                         label_visibility="collapsed")

if sort_col == "P-value (significatività)":
    filtered = filtered.sort_values('p_value')
elif sort_col == "Rendimento medio (abs)":
    filtered = filtered.sort_values('mean_return', key=abs, ascending=False)
elif sort_col == "Consistenza":
    filtered = filtered.sort_values('consistency', ascending=False)
else:
    filtered = filtered.sort_values('ticker')


for idx, row in filtered.iterrows():
    dir_icon = "▲" if row['direction'] == 'up' else "▼"
    dir_class = "up" if row['direction'] == 'up' else "dn"
    dir_label = "RIALZO" if row['direction'] == 'up' else "RIBASSO"
    mkt_class = "mi" if row['market'] == 'Milano' else "nq"
    ret_color = "#22d98c" if row['mean_return'] > 0 else "#f75c5c"
    ret_sign = "+" if row['mean_return'] > 0 else ""
    pv_stars = "★★" if row['p_value'] < 0.05 else "★" if row['p_value'] < 0.10 else ""
    
    src = row.get('source', 'unknown')
    src_class = "ok" if "yfinance" in str(src) else "warn" if "stooq" in str(src) or "cache" in str(src) else "err"
    
    with st.expander(
        f"**{row['ticker']}** · {row['name']} · {row['month_name']} · "
        f"{'🟢' if row['direction']=='up' else '🔴'} {ret_sign}{row['mean_return']}% · "
        f"p={row['p_value']:.3f}{pv_stars} · {row['consistency']:.0f}%"
    ):
        # Top info row
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.markdown(f"**Ticker:** `{row['ticker']}`")
            st.markdown(f"**Settore:** {row['sector']}")
        with c2:
            st.markdown(f"**Mercato:** {row['market']}")
            st.markdown(f"**Fonte:** `{src}`")
        with c3:
            st.markdown(f"**Direzione:** {dir_icon} {dir_label}")
            st.markdown(f"**Mese:** {row['month_name']}")
        with c4:
            st.markdown(f"**Rend. medio:** `{ret_sign}{row['mean_return']}%`")
            st.markdown(f"**Dev. std:** `{row['std']}%`")
        with c5:
            st.markdown(f"**P-value:** `{row['p_value']:.4f}` {pv_stars}")
            st.markdown(f"**Consistenza:** `{row['consistency']:.0f}%`")
        
        # Cause
        st.info(f"📌 **Causa:** {row['cause']}")
        
        # Year-by-year chart
        yearly = row.get('yearly', {})
        if yearly:
            years = sorted(yearly.keys())
            vals = []
            colors = []
            labels = []
            for y in years:
                info = yearly[y]
                if info['status'] == 'in_corso':
                    vals.append(0)
                    colors.append('#3b4a6b')
                    labels.append(f"{y}\n(in corso)")
                elif info['val'] is not None:
                    vals.append(info['val'])
                    colors.append('#22d98c' if info['val'] > 0 else '#f75c5c')
                    labels.append(str(y))
                
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=labels, y=vals,
                marker_color=colors,
                text=[f"{v:+.1f}%" if v != 0 else "—" for v in vals],
                textposition='outside',
                textfont=dict(family='JetBrains Mono', size=11, color='#e2e8f0'),
            ))
            fig.update_layout(
                title=f"{row['ticker']} — {row['month_name']} — Rendimento anno per anno",
                title_font=dict(family='DM Sans', size=14, color='#94a3b8'),
                plot_bgcolor='#0a0e1a',
                paper_bgcolor='#0a0e1a',
                font=dict(family='JetBrains Mono', color='#94a3b8'),
                xaxis=dict(gridcolor='#1e2a4a', title=None),
                yaxis=dict(gridcolor='#1e2a4a', title="Rendimento %", zeroline=True, zerolinecolor='#2a3a5a'),
                height=320,
                margin=dict(l=50, r=20, t=50, b=40),
                showlegend=False,
            )
            # Add mean line
            mean_val = row['mean_return']
            fig.add_hline(y=mean_val, line_dash="dash",
                         line_color="#ccff00", annotation_text=f"Media: {mean_val:+.1f}%",
                         annotation_font_color="#ccff00")
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Stats row
            real_vals = [yearly[y]['val'] for y in years if yearly[y]['val'] is not None]
            if real_vals:
                sc1, sc2, sc3, sc4, sc5 = st.columns(5)
                with sc1:
                    st.metric("Media", f"{np.mean(real_vals):+.1f}%")
                with sc2:
                    st.metric("Mediana", f"{np.median(real_vals):+.1f}%")
                with sc3:
                    st.metric("Migliore", f"{max(real_vals):+.1f}%")
                with sc4:
                    st.metric("Peggiore", f"{min(real_vals):+.1f}%")
                with sc5:
                    st.metric("Anni", str(len(real_vals)))


# ═══════════════════════════════════════════════════════════════
# HEATMAP — Monthly returns overview
# ═══════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 🗓️ Heatmap Stagionalità — Pattern per mese")

if len(filtered) > 0:
    heat_data = filtered.pivot_table(
        values='mean_return', 
        index='ticker', 
        columns='month', 
        aggfunc='mean'
    ).fillna(0)
    
    if len(heat_data) > 0:
        month_labels = [MN_LIST[i] if i <= 12 else '' for i in heat_data.columns]
        
        fig_heat = go.Figure(data=go.Heatmap(
            z=heat_data.values,
            x=month_labels,
            y=heat_data.index,
            colorscale=[
                [0, '#7f1d1d'], [0.3, '#991b1b'], [0.45, '#1e2a4a'],
                [0.55, '#1e2a4a'], [0.7, '#065f46'], [1, '#047857']
            ],
            zmid=0,
            text=[[f"{v:+.1f}%" if v != 0 else "" for v in row] for row in heat_data.values],
            texttemplate="%{text}",
            textfont=dict(size=10, family='JetBrains Mono'),
            hovertemplate="Ticker: %{y}<br>Mese: %{x}<br>Rendimento: %{z:+.1f}%<extra></extra>",
            colorbar=dict(title="Rend.%", tickfont=dict(color='#94a3b8')),
        ))
        fig_heat.update_layout(
            plot_bgcolor='#0a0e1a', paper_bgcolor='#0a0e1a',
            font=dict(family='JetBrains Mono', color='#94a3b8'),
            height=max(300, len(heat_data) * 28),
            margin=dict(l=120, r=40, t=20, b=40),
            xaxis=dict(side='top'),
        )
        st.plotly_chart(fig_heat, use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("""
<div style="text-align:center;padding:16px;font-size:11px;color:#475569;line-height:1.7">
⚠️ <b>NOTA METODOLOGICA</b> — Tutti i rendimenti sono calcolati su prezzi di chiusura mensili.<br>
Significatività statistica via t-test a una coda (H₀: μ=0). Soglia: p < 0.10 e consistenza ≥ 60%.<br>
Dati forniti da Yahoo Finance / Stooq. Nessun dato è inventato o approssimato.<br>
<b>Non costituisce consiglio finanziario.</b> I rendimenti passati non sono garanzia di risultati futuri.
</div>
""", unsafe_allow_html=True)
