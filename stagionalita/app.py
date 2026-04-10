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
    initial_sidebar_state="collapsed"
)

# ═══════════════════════════════════════════════════════════════
# CUSTOM CSS — HIGH CONTRAST NEON TERMINAL
# ═══════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&display=swap');

/* ─── GLOBAL ─── */
.stApp { background: #050810 !important; }
* { -webkit-font-smoothing: antialiased; }

/* ─── ALL TEXT BRIGHTER ─── */
.stApp, .stApp p, .stApp span, .stApp label, .stApp div {
    color: #f1f5f9 !important;
}
.stMarkdown p { color: #f1f5f9 !important; font-size: 16px !important; line-height: 1.6 !important; }
.stMarkdown strong, .stMarkdown b { color: #ffffff !important; }

/* ─── HERO ─── */
.hero-box {
    background: linear-gradient(145deg, #080c1c 0%, #0f1a3d 40%, #0a1230 100%);
    border: 1px solid rgba(204,255,0,0.15);
    border-radius: 20px;
    padding: clamp(20px, 5vw, 40px);
    margin-bottom: 24px;
    position: relative;
    overflow: hidden;
}
.hero-box::before {
    content: '';
    position: absolute;
    top: -40%;
    right: -15%;
    width: 500px;
    height: 500px;
    background: radial-gradient(circle, rgba(204,255,0,0.06) 0%, transparent 65%);
    pointer-events: none;
}
.hero-box::after {
    content: '';
    position: absolute;
    bottom: -30%;
    left: -10%;
    width: 400px;
    height: 400px;
    background: radial-gradient(circle, rgba(88,136,255,0.05) 0%, transparent 65%);
    pointer-events: none;
}
.flag-row { display: flex; gap: 12px; margin-bottom: 8px; }
.flag { font-size: clamp(32px, 5vw, 44px); filter: drop-shadow(0 0 8px rgba(255,255,255,0.15)); }
.hero-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: clamp(28px, 6vw, 48px);
    font-weight: 700;
    letter-spacing: -1px;
    margin: 0 0 8px 0;
    color: #ffffff !important;
    line-height: 1.1;
}
.hero-title .yl { 
    color: #ccff00 !important;
    text-shadow: 0 0 20px rgba(204,255,0,0.35), 0 0 60px rgba(204,255,0,0.1);
}
.hero-title .bl { 
    color: #6ea8ff !important;
    text-shadow: 0 0 20px rgba(110,168,255,0.3);
}
.hero-title .wh {
    color: #ffffff !important;
    text-shadow: 0 0 10px rgba(255,255,255,0.15);
}
.hero-sub {
    font-family: 'Space Grotesk', sans-serif;
    font-size: clamp(14px, 2.5vw, 18px);
    color: #94a3b8 !important;
    margin: 0;
    line-height: 1.5;
}

/* ─── METRICS (st.metric override) ─── */
div[data-testid="stMetric"] {
    background: linear-gradient(145deg, #0d1425, #111d38) !important;
    border: 1px solid rgba(88,136,255,0.15) !important;
    border-radius: 14px !important;
    padding: 18px 16px !important;
}
div[data-testid="stMetric"] label {
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: clamp(12px, 2vw, 15px) !important;
    font-weight: 600 !important;
    color: #94a3b8 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.8px !important;
}
div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: clamp(26px, 5vw, 38px) !important;
    font-weight: 800 !important;
    color: #ffffff !important;
    text-shadow: 0 0 15px rgba(255,255,255,0.1);
}

/* ─── FILTER BAR ─── */

/* ─── EXPANDERS (pattern rows) ─── */
div[data-testid="stExpander"] {
    background: linear-gradient(145deg, #0a1020, #0f1730) !important;
    border: 1px solid #1a2a50 !important;
    border-radius: 14px !important;
    margin-bottom: 10px !important;
    overflow: hidden;
    transition: border-color 0.2s;
}
div[data-testid="stExpander"]:hover {
    border-color: rgba(204,255,0,0.25) !important;
}
div[data-testid="stExpander"] summary {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: clamp(14px, 2.5vw, 17px) !important;
    font-weight: 600 !important;
    color: #f1f5f9 !important;
    padding: 16px 20px !important;
    line-height: 1.5 !important;
}
div[data-testid="stExpander"] summary span {
    color: #f1f5f9 !important;
}
div[data-testid="stExpander"] div[data-testid="stExpanderDetails"] {
    padding: 12px 20px 20px !important;
    border-top: 1px solid #1a2a50 !important;
}

/* ─── INFO BOX (cause) ─── */
div[data-testid="stAlert"] {
    background: linear-gradient(135deg, rgba(204,255,0,0.06), rgba(88,136,255,0.04)) !important;
    border: 1px solid rgba(204,255,0,0.15) !important;
    border-radius: 10px !important;
    font-size: 15px !important;
    color: #e2e8f0 !important;
}

/* ─── BUTTONS ─── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #ccff00, #99cc00) !important;
    color: #050810 !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700 !important;
    font-size: 16px !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 12px 24px !important;
    text-shadow: none !important;
    box-shadow: 0 0 20px rgba(204,255,0,0.2);
    transition: box-shadow 0.2s, transform 0.1s;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 0 30px rgba(204,255,0,0.35) !important;
    transform: translateY(-1px);
}

/* ─── SELECTBOX ─── */
div[data-testid="stSelectbox"] > div > div {
    background: #0d1425 !important;
    border: 1px solid #1a2a50 !important;
    border-radius: 10px !important;
    color: #f1f5f9 !important;
    font-size: 15px !important;
}

/* ─── SORT DROPDOWN ─── */
.stSelectbox { margin-bottom: 16px; }

/* ─── MARKDOWN HEADERS ─── */
.stMarkdown h3 {
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: clamp(20px, 3.5vw, 26px) !important;
    font-weight: 700 !important;
    color: #ffffff !important;
    text-shadow: 0 0 10px rgba(255,255,255,0.08);
}
.stMarkdown h1, .stMarkdown h2 {
    color: #ffffff !important;
}

/* ─── DIVIDER ─── */
hr { border-color: #1a2545 !important; }

/* ─── PROGRESS BAR ─── */
.stProgress > div > div > div {
    background: linear-gradient(90deg, #ccff00, #88ff44) !important;
}

/* ─── MOBILE RESPONSIVE ─── */
@media (max-width: 768px) {
    .hero-box { padding: 18px !important; border-radius: 14px; }
    div[data-testid="stMetric"] { padding: 12px 10px !important; }
    div[data-testid="stExpander"] summary { padding: 12px 14px !important; font-size: 14px !important; }
    .stMarkdown p { font-size: 15px !important; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] { font-size: 24px !important; }
    div[data-testid="column"] { min-width: 48% !important; }
}

/* ─── HIDE STREAMLIT CHROME ─── */
#MainMenu, footer, header { visibility: hidden; }
div[data-testid="stDecoration"] { display: none; }
section[data-testid="stSidebar"] { display: none !important; }

/* ─── FOOTER ─── */
.app-footer {
    text-align: center;
    padding: 24px;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 13px;
    color: #475569;
    line-height: 1.8;
    border-top: 1px solid #1a2545;
    margin-top: 20px;
}
.app-footer b { color: #94a3b8; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════
st.markdown("""
<div class="hero-box">
    <div class="flag-row"><span class="flag">🇮🇹</span><span class="flag">🇺🇸</span></div>
    <h1 class="hero-title"><span class="yl">STAGIONALITÀ</span> <span class="wh">—</span> <span class="bl">Milano</span> <span class="wh">&</span> <span class="wh">NASDAQ</span></h1>
    <p class="hero-sub">Pattern mensili statisticamente significativi · Dati reali da Yahoo Finance · Zero dati inventati</p>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# FILTERS — In main area (works on EVERY device, no sidebar)
# ═══════════════════════════════════════════════════════════════
st.markdown("""
<div style="background:linear-gradient(145deg,#0c1225,#101d35);border:1px solid #1a2a50;border-radius:14px;padding:16px 20px 8px;margin-bottom:16px;">
<div style="font-family:'Space Grotesk',sans-serif;font-size:clamp(15px,2.5vw,18px);font-weight:700;color:#ffffff;margin-bottom:10px;">⚙️ FILTRI</div>
</div>
""", unsafe_allow_html=True)

fc1, fc2, fc3, fc4, fc5 = st.columns([1.2, 1.2, 1.2, 1.5, 1])

MESI_FULL = ['','Gennaio','Febbraio','Marzo','Aprile','Maggio','Giugno',
             'Luglio','Agosto','Settembre','Ottobre','Novembre','Dicembre']
sectors = sorted(set(s["sector"] for s in STOCKS.values()))

with fc1:
    market_filter = st.selectbox("MERCATO", ["Tutti", "Milano", "NASDAQ"])
with fc2:
    direction_filter = st.selectbox("DIREZIONE", ["Tutti", "▲ Rialzo", "▼ Ribasso"])
with fc3:
    month_filter = st.selectbox("MESE", ["Tutti"] + [f"{i} - {MESI_FULL[i]}" for i in range(1, 13)])
with fc4:
    sector_filter = st.selectbox("SETTORE", ["Tutti"] + sectors)
with fc5:
    st.markdown("<div style='height:26px'></div>", unsafe_allow_html=True)
    if st.button("🔄 AGGIORNA", type="primary", use_container_width=True):
        st.session_state.force_refresh = True
        st.session_state.pop('data_loaded', None)
        st.rerun()

# Update info
last_update = get_last_update_time()
if last_update:
    st.caption(f"📡 Ultimo aggiornamento: {last_update.strftime('%d/%m/%Y %H:%M')} · Fonti: Yahoo Finance, Stooq · Cache: 1h")

MN_LIST = ['','Gen','Feb','Mar','Apr','Mag','Giu','Lug','Ago','Set','Ott','Nov','Dic']

# ═══════════════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════════════

# Force refresh if button pressed
if st.session_state.get('force_refresh'):
    st.cache_data.clear()
    st.session_state.force_refresh = False

@st.cache_data(ttl=3600, show_spinner=False)
def load_data():
    """Load or refresh all seasonal data."""
    df, errors = run_full_analysis(progress_callback=None)
    return df, errors

# Show big visible loading message in MAIN area (not sidebar)
loading_container = st.empty()
if 'data_loaded' not in st.session_state:
    with loading_container.container():
        st.markdown("""
        <div style="text-align:center;padding:60px 20px;">
            <div style="font-size:48px;margin-bottom:16px;">⏳</div>
            <div style="font-family:'Space Grotesk',sans-serif;font-size:22px;font-weight:700;color:#ccff00;margin-bottom:8px;">
                Caricamento dati in corso...
            </div>
            <div style="font-size:15px;color:#94a3b8;">
                Scarico 10 anni di dati per 65+ titoli da Yahoo Finance.<br>
                Il primo caricamento può richiedere <b style="color:#ffffff;">1-3 minuti</b>. I successivi saranno istantanei.
            </div>
        </div>
        """, unsafe_allow_html=True)

with st.spinner(""):
    df, errors = load_data()

loading_container.empty()
st.session_state.data_loaded = True

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
# LEGEND
# ═══════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("""
<div style="background:linear-gradient(145deg,#0c1225,#111d38);border:1px solid #1a2a50;border-radius:16px;padding:clamp(16px,3vw,28px);margin:8px 0 20px 0;">
<h3 style="font-family:'Space Grotesk',sans-serif;font-size:clamp(18px,3vw,22px);font-weight:700;color:#ffffff;margin:0 0 16px 0;">
📖 Come leggere i dati
</h3>

<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px;">

<div style="background:#0a0f1e;border:1px solid #1a2545;border-radius:12px;padding:16px;">
<div style="font-family:'Space Grotesk',sans-serif;font-size:15px;font-weight:700;color:#ccff00;margin-bottom:8px;">🟢 Pallino Verde = Rialzo</div>
<div style="font-size:14px;color:#cbd5e1;line-height:1.6;">
Il titolo in quel mese è <b style="color:#22d98c;">salito in media</b> negli ultimi 10 anni.<br>
Es: <code style="color:#22d98c;">+4.86%</code> = in media il titolo è salito del 4.86% in quel mese.
</div>
</div>

<div style="background:#0a0f1e;border:1px solid #1a2545;border-radius:12px;padding:16px;">
<div style="font-family:'Space Grotesk',sans-serif;font-size:15px;font-weight:700;color:#f75c5c;margin-bottom:8px;">🔴 Pallino Rosso = Ribasso</div>
<div style="font-size:14px;color:#cbd5e1;line-height:1.6;">
Il titolo in quel mese è <b style="color:#f75c5c;">sceso in media</b> negli ultimi 10 anni.<br>
Es: <code style="color:#f75c5c;">-7.08%</code> = in media il titolo è sceso del 7.08% in quel mese.
</div>
</div>

<div style="background:#0a0f1e;border:1px solid #1a2545;border-radius:12px;padding:16px;">
<div style="font-family:'Space Grotesk',sans-serif;font-size:15px;font-weight:700;color:#6ea8ff;margin-bottom:8px;">📊 P-value = Quanto è affidabile</div>
<div style="font-size:14px;color:#cbd5e1;line-height:1.6;">
Misura la probabilità che il pattern sia dovuto al <b>caso</b>.<br>
<span style="color:#22d98c;">★★ p &lt; 0.05</span> → forte (meno del 5% di probabilità sia caso)<br>
<span style="color:#ffc83a;">★ p &lt; 0.10</span> → moderato (meno del 10%)<br>
<b>Più basso = più affidabile.</b>
</div>
</div>

<div style="background:#0a0f1e;border:1px solid #1a2545;border-radius:12px;padding:16px;">
<div style="font-family:'Space Grotesk',sans-serif;font-size:15px;font-weight:700;color:#ffc83a;margin-bottom:8px;">📈 Consistenza = Quante volte si ripete</div>
<div style="font-size:14px;color:#cbd5e1;line-height:1.6;">
Percentuale di anni in cui il titolo si è mosso nella <b>stessa direzione</b>.<br>
Es: <code>90%</code> = in 9 anni su 10 il titolo è salito (o sceso) in quel mese.<br>
<b>Più alto = più regolare.</b>
</div>
</div>

<div style="background:#0a0f1e;border:1px solid #1a2545;border-radius:12px;padding:16px;">
<div style="font-family:'Space Grotesk',sans-serif;font-size:15px;font-weight:700;color:#ffffff;margin-bottom:8px;">💡 Come usare questi dati</div>
<div style="font-size:14px;color:#cbd5e1;line-height:1.6;">
Cerca pattern con <b style="color:#22d98c;">p-value basso</b> (★★) e <b style="color:#ffc83a;">consistenza alta</b> (&gt;80%).<br>
Clicca su ogni riga per vedere il <b>grafico anno per anno</b> e verificare se il pattern è stabile o distorto da un singolo anno anomalo.
</div>
</div>

<div style="background:#0a0f1e;border:1px solid #1a2545;border-radius:12px;padding:16px;">
<div style="font-family:'Space Grotesk',sans-serif;font-size:15px;font-weight:700;color:#ffffff;margin-bottom:8px;">⚠️ Attenzione</div>
<div style="font-size:14px;color:#cbd5e1;line-height:1.6;">
I pattern stagionali sono <b>tendenze storiche</b>, non previsioni certe.<br>
Un evento imprevisto (crisi, guerra, pandemia) può rompere qualsiasi pattern.<br>
<b>Mai investire solo sulla base di stagionalità.</b>
</div>
</div>

</div>
</div>
""", unsafe_allow_html=True)

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
                marker_line_width=0,
                text=[f"{v:+.1f}%" if v != 0 else "—" for v in vals],
                textposition='outside',
                textfont=dict(family='JetBrains Mono', size=14, color='#ffffff'),
            ))
            fig.update_layout(
                title=dict(text=f"📊 {row['ticker']} — {row['month_name']} — Anno per anno",
                           font=dict(family='Space Grotesk', size=18, color='#ffffff')),
                plot_bgcolor='#050810',
                paper_bgcolor='#050810',
                font=dict(family='JetBrains Mono', size=13, color='#cbd5e1'),
                xaxis=dict(gridcolor='#1a2545', title=None, tickfont=dict(size=13, color='#e2e8f0')),
                yaxis=dict(gridcolor='#1a2545', title="Rendimento %", zeroline=True, 
                          zerolinecolor='#2a3a5a', zerolinewidth=2,
                          tickfont=dict(size=12, color='#cbd5e1')),
                height=360,
                margin=dict(l=60, r=20, t=60, b=50),
                showlegend=False,
                bargap=0.2,
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
                [0, '#991b1b'], [0.35, '#7f1d1d'], [0.45, '#1a2035'],
                [0.55, '#1a2035'], [0.65, '#065f46'], [1, '#059669']
            ],
            zmid=0,
            text=[[f"{v:+.1f}%" if v != 0 else "" for v in row] for row in heat_data.values],
            texttemplate="%{text}",
            textfont=dict(size=12, family='JetBrains Mono', color='#ffffff'),
            hovertemplate="<b>%{y}</b><br>Mese: %{x}<br>Rendimento: %{z:+.1f}%<extra></extra>",
            colorbar=dict(title=dict(text="Rend.%", font=dict(color='#cbd5e1', size=13)),
                         tickfont=dict(color='#cbd5e1', size=11)),
        ))
        fig_heat.update_layout(
            plot_bgcolor='#050810', paper_bgcolor='#050810',
            font=dict(family='JetBrains Mono', size=13, color='#e2e8f0'),
            height=max(350, len(heat_data) * 32),
            margin=dict(l=130, r=40, t=30, b=40),
            xaxis=dict(side='top', tickfont=dict(size=14, color='#ffffff')),
            yaxis=dict(tickfont=dict(size=12, color='#e2e8f0')),
        )
        st.plotly_chart(fig_heat, use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("""
<div class="app-footer">
⚠️ <b>NOTA METODOLOGICA</b> — Rendimenti calcolati su prezzi di chiusura mensili.<br>
Significatività statistica via t-test (H₀: μ=0). Soglia: p &lt; 0.10 e consistenza ≥ 60%.<br>
Dati forniti da Yahoo Finance / Stooq. <b>Nessun dato è inventato o approssimato.</b><br>
Non costituisce consiglio finanziario. I rendimenti passati non sono garanzia di risultati futuri.
</div>
""", unsafe_allow_html=True)
