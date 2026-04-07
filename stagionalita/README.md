# 🇮🇹🇺🇸 STAGIONALITÀ — Milano & NASDAQ

> Pattern stagionali statisticamente significativi sui mercati Milano e NASDAQ.  
> Dati reali da Yahoo Finance. **Nessun dato inventato. Mai.**

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.37+-red)
![Data](https://img.shields.io/badge/Dati-Yahoo%20Finance-green)

---

## 🚀 Deploy su Streamlit Cloud (GRATIS — 3 minuti)

### Passo 1: Fork su GitHub
1. Vai su [github.com](https://github.com) e accedi (o crea un account)
2. Clicca **"New repository"**
3. Nome: `stagionalita`
4. **Pubblico** ✅
5. Carica tutti i file di questa cartella nel repo

### Passo 2: Deploy su Streamlit Cloud
1. Vai su [share.streamlit.io](https://share.streamlit.io)
2. Accedi con GitHub
3. Clicca **"New app"**
4. Seleziona il repo `stagionalita`
5. Main file: `app.py`
6. Clicca **"Deploy!"**

### Passo 3: Aggiungi alla Home del telefono
L'app avrà un URL tipo `https://tuonome-stagionalita.streamlit.app`

**Su Redmi Note 13 Pro:**
1. Apri l'URL in **Chrome**
2. Tocca i **tre puntini ⋮** in alto a destra
3. Tocca **"Aggiungi a schermata Home"** ← questa volta FUNZIONA perché è https://
4. Dai il nome "Stagionalità"
5. Tocca **Aggiungi**

---

## 📊 Funzionalità

- **65+ titoli** analizzati tra FTSE MIB e NASDAQ
- **Rendimenti mensili anno per anno** (espandibili con click)
- **Heatmap stagionalità** interattiva
- **Filtri** per mercato, direzione, mese, settore
- **Aggiornamento automatico** ogni ora (cache TTL=3600s)
- **3 fonti dati** con fallback: Yahoo Finance → Stooq → Cache locale
- **Zero dati inventati**: se una fonte fallisce, il pattern non viene mostrato

## 🔧 Architettura

```
app.py              ← UI Streamlit
data_fetcher.py     ← Engine dati (Yahoo Finance + Stooq + cache)
requirements.txt    ← Dipendenze Python
.streamlit/
  config.toml       ← Tema scuro + configurazione
data_cache/         ← Cache locale JSON (auto-generata)
assets/
  icon.png          ← Icona app
```

## 📡 Fonti Dati

| Priorità | Fonte | Tipo | Affidabilità |
|----------|-------|------|-------------|
| 1️⃣ | Yahoo Finance | API Python (yfinance) | ★★★★★ |
| 2️⃣ | Stooq.com | CSV endpoint | ★★★★☆ |
| 3️⃣ | Cache locale | JSON file | ★★★☆☆ (stale) |

Se tutte le fonti falliscono per un ticker, quel ticker viene escluso con un warning. **Non viene mai inventato un numero.**

## 🧮 Metodologia Statistica

- Rendimenti mensili = (Close_fine_mese / Close_fine_mese_precedente - 1) × 100
- Test: **t-test a un campione** (H₀: μ = 0)
- Soglia significatività: **p-value < 0.10**
- Soglia consistenza: **≥ 60%** degli anni nella stessa direzione
- Finestra: **ultimi 10 anni** (escluso mese corrente se incompleto)

---

**⚠️ Disclaimer:** Non costituisce consiglio finanziario. I rendimenti passati non sono garanzia di risultati futuri.
