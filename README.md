# 🌐 Global Supply Chain Shock Intelligence Platform (SCSI)

An AI-powered platform that monitors global supply chain disruptions, predicts risks,
analyzes impacts, and generates executive insights.

---

## 🚀 Quick Start (Local Setup)

### 1. Prerequisites
- Python 3.10+
- pip

### 2. Extract & Navigate
```bash
unzip supply-chain-shock-platform.zip
cd supply-chain-shock-platform
```

### 3. Create Virtual Environment
```bash
python -m venv venv

# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

> **Note on Prophet**: If Prophet fails to install, run:
> ```bash
> pip install prophet --no-build-isolation
> ```
> Prophet requires `pystan` and may need Visual C++ Build Tools on Windows.
> The platform works without Prophet using a built-in fallback forecaster.

### 5. Configure API Keys
```bash
cp .env.example .env
```
Edit `.env` and add your keys:
```
GROQ_API_KEY=your_groq_api_key_here      ← Required for AI features
NEWS_API_KEY=your_newsapi_key_here        ← For live news (optional)
GNEWS_API_KEY=your_gnews_api_key_here     ← Fallback news (optional)
```

**Get free API keys:**
- Groq: https://console.groq.com (free tier available)
- NewsAPI: https://newsapi.org (100 req/day free)
- GNews: https://gnews.io (100 req/day free)

### 6. Run the Application
```bash
python app.py
```

Open your browser: **http://127.0.0.1:5000**

---

## 📋 Platform Modules

| # | Module | Description |
|---|--------|-------------|
| 1 | News Monitor | Fetch & classify supply chain news |
| 2 | Shock Simulator | Simulate economic impact of shocks |
| 3 | Country Risk Map | Interactive Leaflet world risk map |
| 4 | Consumer Impact | Product price & shortage predictions |
| 5 | Investment Dashboard | Sector buy/hold/sell signals |
| 6 | Forecast Center | Prophet 30/60/90-day forecasts |
| 7 | CEO Report | AI executive report + PDF export |
| 8 | Notifications | Alert center with severity tracking |
| 9 | Historical Analytics | 30/90/365-day trend analysis |
| 10 | Scenario Comparison | A vs B scenario comparison |
| 11 | AI Assistant | Groq-powered supply chain Q&A |

---

## 📊 Datasets (Create Your Own)

See `datasets/DATASETS_README.md` for exact column schemas for:
- `industry_dependency.csv`
- `country_dependency.csv`
- `product_dependency.csv`
- `historical_shocks.csv`
- `sector_performance.csv`
- `news_training_dataset.csv`

The platform runs without these CSVs using built-in intelligence models.

---

## 🧠 ML Models Used

| Model | Algorithm | Purpose |
|-------|-----------|---------|
| News Classifier | TF-IDF + Rule Engine | Shock type & country detection |
| Shock Simulator | Rule-based Regression | Revenue, risk, price impact |
| Sector Scorer | Weighted Rule Model | Investment signals |
| Consumer Impact | Formula Model | Price & shortage prediction |
| Forecaster | Prophet / Trend Model | 30/60/90-day forecasting |

---

## 🗂 Project Structure

```
supply-chain-shock-platform/
├── app.py                    ← Flask entry point
├── models.py                 ← SQLAlchemy DB models
├── requirements.txt
├── .env.example
├── README.md
├── routes/
│   └── api.py                ← All REST API endpoints
├── services/
│   ├── news_service.py       ← NewsAPI / GNews fetcher
│   ├── groq_service.py       ← Groq AI integration
│   └── pdf_service.py        ← ReportLab PDF export
├── ml/
│   ├── classifier.py         ← News classification + simulation
│   └── forecaster.py         ← Prophet forecasting
├── templates/                ← Jinja2 HTML templates
│   ├── base.html
│   ├── dashboard.html
│   ├── news.html
│   ├── simulator.html
│   ├── country_risk.html
│   ├── consumer_impact.html
│   ├── investment.html
│   ├── forecast.html
│   ├── ceo_report.html
│   ├── notifications.html
│   ├── historical.html
│   ├── scenario.html
│   └── assistant.html
├── static/
│   ├── css/main.css
│   └── js/main.js
├── datasets/
│   └── DATASETS_README.md    ← Column schemas for your CSVs
├── reports/                  ← Generated PDF reports saved here
└── database.db               ← Auto-created SQLite database
```

---

## 🔧 Troubleshooting

**Prophet not installing?**
```bash
pip install pystan==3.7.0
pip install prophet
```

**Port already in use?**
```bash
python app.py --port 5001
# or edit app.py: app.run(port=5001)
```

**No news loading?**
- Add NewsAPI or GNews key in `.env`
- Platform runs in demo mode without news API keys

**Groq AI not responding?**
- Verify `GROQ_API_KEY` in `.env`
- Check https://console.groq.com for key validity

---

## 📦 Tech Stack

**Frontend:** HTML5 · CSS3 · Bootstrap 5 · Chart.js · Plotly.js · Leaflet.js
**Backend:** Flask · SQLAlchemy · Pandas · NumPy · Scikit-Learn · Prophet
**Database:** SQLite
**AI:** Groq (LLaMA 3 8B)
**News:** NewsAPI + GNews fallback

---

Built for final-year project & placement portfolio.
Run locally with `python app.py` — no Docker, no Redis, no cloud required.
