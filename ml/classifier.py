import pandas as pd
import numpy as np
import joblib
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

MODEL_DIR = os.path.join(os.path.dirname(__file__), '..', 'ml', 'saved_models')
os.makedirs(MODEL_DIR, exist_ok=True)

# ─────────────────────────────────────────────
# SHOCK KEYWORD RULES (no model needed for MVP)
# ─────────────────────────────────────────────
SHOCK_KEYWORDS = {
    'Oil Shock': ['oil', 'crude', 'petroleum', 'opec', 'brent', 'wti', 'gas price', 'fuel'],
    'Semiconductor Shortage': ['semiconductor', 'chip', 'wafer', 'tsmc', 'intel', 'nvidia', 'fab', 'microchip'],
    'Trade Restriction': ['tariff', 'sanction', 'ban', 'embargo', 'trade war', 'restriction', 'export control', 'import duty'],
    'Shipping Crisis': ['port', 'shipping', 'container', 'freight', 'suez', 'logistics delay', 'vessel', 'cargo'],
    'Climate Event': ['flood', 'earthquake', 'hurricane', 'drought', 'wildfire', 'tsunami', 'storm', 'climate'],
    'Currency Volatility': ['currency', 'exchange rate', 'devaluation', 'inflation', 'forex', 'dollar', 'yuan', 'rupee']
}

INDUSTRY_MAP = {
    'Oil Shock': 'Energy',
    'Semiconductor Shortage': 'Electronics',
    'Trade Restriction': 'Manufacturing',
    'Shipping Crisis': 'Logistics',
    'Climate Event': 'Agriculture',
    'Currency Volatility': 'Banking'
}

COUNTRY_KEYWORDS = {
    'China': ['china', 'chinese', 'beijing', 'shanghai'],
    'USA': ['united states', 'american', 'washington', 'federal reserve'],
    'Taiwan': ['taiwan', 'taiwanese', 'taipei'],
    'Russia': ['russia', 'russian', 'moscow', 'kremlin'],
    'India': ['india', 'indian', 'mumbai', 'delhi'],
    'Germany': ['germany', 'german', 'berlin', 'bundesbank'],
    'Japan': ['japan', 'japanese', 'tokyo', 'yen'],
    'Saudi Arabia': ['saudi', 'riyadh', 'opec', 'aramco'],
    'South Korea': ['south korea', 'korean', 'seoul', 'samsung'],
    'UK': ['britain', 'uk', 'london', 'sterling'],
}

def classify_shock_type(text: str) -> tuple[str, float]:
    """Rule-based shock classification"""
    text_lower = text.lower()
    scores = {}
    for shock, keywords in SHOCK_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[shock] = score

    if not scores:
        return 'Trade Restriction', 0.3

    best = max(scores, key=scores.get)
    total = sum(scores.values())
    prob = min(scores[best] / max(total, 1), 1.0)
    return best, round(prob, 2)

def detect_country(text: str) -> str:
    """Detect country from text"""
    text_lower = text.lower()
    for country, keywords in COUNTRY_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return country
    return 'Global'

def compute_severity(text: str, shock_type: str) -> float:
    """Compute severity score 0-10"""
    HIGH_WORDS = ['critical', 'severe', 'major', 'significant', 'crisis', 'collapse', 'emergency', 'catastrophic']
    MED_WORDS = ['disruption', 'shortage', 'impact', 'concern', 'risk', 'decline', 'fall', 'drop']
    LOW_WORDS = ['minor', 'slight', 'small', 'limited', 'modest']

    text_lower = text.lower()
    score = 5.0  # base
    score += sum(1.5 for w in HIGH_WORDS if w in text_lower)
    score += sum(0.8 for w in MED_WORDS if w in text_lower)
    score -= sum(1.0 for w in LOW_WORDS if w in text_lower)
    return min(max(round(score, 1), 1.0), 10.0)

# ─────────────────────────────────────────────
# SHOCK SIMULATOR MODELS
# ─────────────────────────────────────────────

SHOCK_TYPE_ENCODING = {
    'Oil Shock': 0, 'Semiconductor Shortage': 1, 'Trade Restriction': 2,
    'Shipping Crisis': 3, 'Climate Event': 4, 'Currency Volatility': 5
}

COUNTRY_ENCODING = {
    'China': 0, 'USA': 1, 'Taiwan': 2, 'Russia': 3,
    'India': 4, 'Germany': 5, 'Japan': 6, 'Saudi Arabia': 7,
    'South Korea': 8, 'UK': 9, 'Global': 5
}

def simulate_shock(shock_type: str, severity: float, country: str, duration: int) -> dict:
    """
    Simulate economic impact of a supply chain shock.
    Uses rule-based formulas augmented by ML-style coefficients.
    """
    st_enc = SHOCK_TYPE_ENCODING.get(shock_type, 2)
    ct_enc = COUNTRY_ENCODING.get(country, 5)

    # Base impact factors per shock type
    base_factors = {
        'Oil Shock':              {'revenue': 0.12, 'price': 0.15, 'risk_base': 65},
        'Semiconductor Shortage': {'revenue': 0.18, 'price': 0.22, 'risk_base': 72},
        'Trade Restriction':      {'revenue': 0.10, 'price': 0.08, 'risk_base': 58},
        'Shipping Crisis':        {'revenue': 0.08, 'price': 0.12, 'risk_base': 55},
        'Climate Event':          {'revenue': 0.14, 'price': 0.18, 'risk_base': 60},
        'Currency Volatility':    {'revenue': 0.09, 'price': 0.20, 'risk_base': 50},
    }

    factors = base_factors.get(shock_type, {'revenue': 0.10, 'price': 0.10, 'risk_base': 55})

    # Duration multiplier (log scale)
    dur_mult = 1 + np.log1p(duration / 30) * 0.5

    revenue_impact = -(factors['revenue'] * severity * dur_mult * 100)
    price_increase = factors['price'] * severity * dur_mult * 100
    risk_score = min(factors['risk_base'] + severity * 3 + duration * 0.1, 100)

    # Affected industries
    industry_impact_map = {
        'Oil Shock': ['Energy', 'Logistics', 'Airlines', 'Petrochemicals', 'Plastics'],
        'Semiconductor Shortage': ['Electronics', 'Automotive', 'Telecom', 'Defense', 'Consumer Tech'],
        'Trade Restriction': ['Manufacturing', 'Agriculture', 'Steel', 'Chemicals', 'Textiles'],
        'Shipping Crisis': ['Logistics', 'Retail', 'FMCG', 'Automotive', 'Electronics'],
        'Climate Event': ['Agriculture', 'Insurance', 'Construction', 'Tourism', 'Utilities'],
        'Currency Volatility': ['Banking', 'Imports/Exports', 'Tourism', 'Commodities', 'Real Estate']
    }

    product_impact_map = {
        'Oil Shock': ['Fuel', 'Plastics', 'Fertilizers', 'Airline Tickets', 'Heating Oil'],
        'Semiconductor Shortage': ['Smartphones', 'Cars', 'Laptops', 'Gaming Consoles', 'Medical Devices'],
        'Trade Restriction': ['Steel Products', 'Agricultural Goods', 'Electronics', 'Textiles', 'Chemicals'],
        'Shipping Crisis': ['Consumer Goods', 'Raw Materials', 'Food Products', 'Industrial Parts', 'Furniture'],
        'Climate Event': ['Food Commodities', 'Insurance Premiums', 'Building Materials', 'Crops', 'Water'],
        'Currency Volatility': ['Imported Goods', 'Foreign Travel', 'Commodities', 'Luxury Items', 'Electronics']
    }

    return {
        'revenue_impact': round(revenue_impact, 2),
        'risk_score': round(risk_score, 1),
        'price_increase': round(price_increase, 2),
        'affected_industries': ', '.join(industry_impact_map.get(shock_type, ['General Manufacturing'])),
        'affected_products': ', '.join(product_impact_map.get(shock_type, ['General Products']))
    }

# ─────────────────────────────────────────────
# INVESTMENT SCORING
# ─────────────────────────────────────────────

def score_sectors(shock_events: list) -> dict:
    """Score investment sectors based on current shock events"""
    sectors = {
        'Energy': {'score': 50, 'action': 'Hold'},
        'EV': {'score': 50, 'action': 'Hold'},
        'Banking': {'score': 50, 'action': 'Hold'},
        'Telecom': {'score': 50, 'action': 'Hold'},
        'FMCG': {'score': 50, 'action': 'Hold'},
        'Electronics': {'score': 50, 'action': 'Hold'},
        'Logistics': {'score': 50, 'action': 'Hold'},
        'Semiconductor': {'score': 50, 'action': 'Hold'},
    }

    for event in shock_events:
        shock = event.get('shock_type', '')
        sev = event.get('severity', 5)

        if shock == 'Oil Shock':
            sectors['Energy']['score'] += sev * 3
            sectors['EV']['score'] += sev * 2
            sectors['Logistics']['score'] -= sev * 2
        elif shock == 'Semiconductor Shortage':
            sectors['Semiconductor']['score'] += sev * 3
            sectors['Electronics']['score'] -= sev * 2
            sectors['EV']['score'] -= sev * 1.5
        elif shock == 'Trade Restriction':
            sectors['Banking']['score'] -= sev * 1.5
            sectors['Logistics']['score'] -= sev * 2
        elif shock == 'Shipping Crisis':
            sectors['Logistics']['score'] += sev * 2
            sectors['FMCG']['score'] -= sev * 1.5
        elif shock == 'Currency Volatility':
            sectors['Banking']['score'] -= sev * 2
            sectors['FMCG']['score'] -= sev * 1

    for sector in sectors:
        s = min(max(sectors[sector]['score'], 0), 100)
        sectors[sector]['score'] = round(s, 1)
        if s >= 65:
            sectors[sector]['action'] = 'Buy'
        elif s <= 35:
            sectors[sector]['action'] = 'Sell'
        else:
            sectors[sector]['action'] = 'Hold'

    return sectors

# ─────────────────────────────────────────────
# CONSUMER IMPACT
# ─────────────────────────────────────────────

PRODUCT_BASE_PRICES = {
    'Smartphone': 699, 'Laptop': 999, 'Electric Vehicle': 45000,
    'Fuel (per litre)': 1.5, 'Wheat (per kg)': 0.8, 'Steel (per ton)': 800,
    'Semiconductor Chip': 50, 'Solar Panel': 300, 'Natural Gas': 4.5,
    'Container Shipping (TEU)': 2000
}

def predict_consumer_impact(shock_events: list) -> list:
    """Predict price and availability impact on consumer products"""
    results = []
    for product, base_price in PRODUCT_BASE_PRICES.items():
        price_increase_pct = 0
        shortage_risk = 0
        delay_days = 0
        confidence = 0.7

        for event in shock_events:
            shock = event.get('shock_type', '')
            sev = event.get('severity', 5) / 10

            relevant = False
            if 'Semiconductor' in product and shock == 'Semiconductor Shortage':
                price_increase_pct += sev * 25; shortage_risk += sev * 80; delay_days += sev * 60; relevant = True
            elif product in ['Fuel (per litre)', 'Natural Gas'] and shock == 'Oil Shock':
                price_increase_pct += sev * 30; shortage_risk += sev * 40; delay_days += sev * 10; relevant = True
            elif 'Shipping' in product and shock == 'Shipping Crisis':
                price_increase_pct += sev * 40; shortage_risk += sev * 30; delay_days += sev * 30; relevant = True
            elif 'Wheat' in product and shock == 'Climate Event':
                price_increase_pct += sev * 20; shortage_risk += sev * 50; delay_days += sev * 20; relevant = True

            if relevant:
                confidence = min(0.95, confidence + 0.05)

        predicted_price = base_price * (1 + price_increase_pct / 100)
        results.append({
            'product': product,
            'current_price': base_price,
            'predicted_price': round(predicted_price, 2),
            'price_increase_pct': round(min(price_increase_pct, 100), 1),
            'shortage_risk': round(min(shortage_risk, 100), 1),
            'delay_days': round(min(delay_days, 180), 0),
            'confidence': round(confidence, 2)
        })

    return results
