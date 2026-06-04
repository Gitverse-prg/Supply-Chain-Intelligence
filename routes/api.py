from flask import Blueprint, jsonify, request, send_file
from models import db, NewsEvent, ShockSimulation, Alert, ForecastResult, CountryRisk
from services.news_service import fetch_all_news, parse_date
from services.groq_service import generate_ceo_report, chat_assistant
from services.pdf_service import generate_pdf_report
from ml.classifier import classify_shock_type, detect_country, compute_severity, INDUSTRY_MAP, simulate_shock, score_sectors, predict_consumer_impact
from ml.forecaster import generate_forecast, generate_early_warnings
from datetime import datetime, timedelta
import json
import os

api = Blueprint('api', __name__, url_prefix='/api')

# ─────────────────────────────────────────────
# NEWS
# ─────────────────────────────────────────────

@api.route('/news/refresh', methods=['POST'])
def refresh_news():
    """Manually fetch and classify new articles"""
    articles = fetch_all_news()
    added = 0
    for a in articles:
        title = a.get('title', '')
        if not title or title == '[Removed]':
            continue
        exists = NewsEvent.query.filter_by(title=title).first()
        if exists:
            continue
        text = f"{title} {a.get('description', '')}"
        shock_type, prob = classify_shock_type(text)
        country = detect_country(text)
        severity = compute_severity(text, shock_type)
        industry = INDUSTRY_MAP.get(shock_type, 'General')
        event = NewsEvent(
            title=title,
            source=a.get('source', {}).get('name', 'Unknown'),
            date=parse_date(a.get('publishedAt', '')),
            country=country,
            industry=industry,
            shock_type=shock_type,
            severity=severity,
            probability=prob,
            url=a.get('url', ''),
            description=a.get('description', '')[:500] if a.get('description') else ''
        )
        db.session.add(event)
        added += 1
        # Auto-alert if high severity
        if severity >= 7.5:
            alert = Alert(
                title=f"High Severity: {shock_type}",
                message=f"{title[:200]} (Severity: {severity}/10)",
                severity='high' if severity < 9 else 'critical',
                alert_type='news_event',
                country=country,
                industry=industry
            )
            db.session.add(alert)

    db.session.commit()
    return jsonify({'status': 'ok', 'added': added, 'total_fetched': len(articles)})

@api.route('/news', methods=['GET'])
def get_news():
    limit = request.args.get('limit', 50, type=int)
    shock_type = request.args.get('shock_type', None)
    country = request.args.get('country', None)
    q = NewsEvent.query.order_by(NewsEvent.date.desc())
    if shock_type:
        q = q.filter(NewsEvent.shock_type == shock_type)
    if country:
        q = q.filter(NewsEvent.country == country)
    events = q.limit(limit).all()
    return jsonify([e.to_dict() for e in events])

@api.route('/news/stats', methods=['GET'])
def news_stats():
    total = NewsEvent.query.count()
    high_sev = NewsEvent.query.filter(NewsEvent.severity >= 7).count()
    from sqlalchemy import func
    shock_counts = db.session.query(NewsEvent.shock_type, func.count(NewsEvent.id)).group_by(NewsEvent.shock_type).all()
    country_counts = db.session.query(NewsEvent.country, func.count(NewsEvent.id)).group_by(NewsEvent.country).order_by(func.count(NewsEvent.id).desc()).limit(5).all()
    industry_counts = db.session.query(NewsEvent.industry, func.count(NewsEvent.id)).group_by(NewsEvent.industry).order_by(func.count(NewsEvent.id).desc()).limit(5).all()
    avg_sev = db.session.query(func.avg(NewsEvent.severity)).scalar() or 0

    return jsonify({
        'total': total,
        'high_severity': high_sev,
        'avg_severity': round(avg_sev, 2),
        'shock_distribution': dict(shock_counts),
        'top_countries': [{'country': c, 'count': n} for c, n in country_counts],
        'top_industries': [{'industry': i, 'count': n} for i, n in industry_counts]
    })

# ─────────────────────────────────────────────
# SHOCK SIMULATOR
# ─────────────────────────────────────────────

@api.route('/simulate', methods=['POST'])
def run_simulation():
    data = request.json
    shock_type = data.get('shock_type', 'Oil Shock')
    severity = float(data.get('severity', 5))
    country = data.get('country', 'Global')
    duration = int(data.get('duration', 30))

    result = simulate_shock(shock_type, severity, country, duration)

    sim = ShockSimulation(
        shock_type=shock_type, severity=severity,
        country=country, duration=duration,
        revenue_impact=result['revenue_impact'],
        risk_score=result['risk_score'],
        price_increase=result['price_increase'],
        affected_industries=result['affected_industries'],
        affected_products=result['affected_products']
    )
    db.session.add(sim)

    if result['risk_score'] >= 70:
        alert = Alert(
            title=f"Simulation Alert: {shock_type} in {country}",
            message=f"Simulation shows risk score {result['risk_score']:.0f}/100 with revenue impact {result['revenue_impact']:.1f}%",
            severity='high' if result['risk_score'] < 85 else 'critical',
            alert_type='simulation',
            country=country
        )
        db.session.add(alert)

    db.session.commit()
    return jsonify(result)

@api.route('/simulations/history', methods=['GET'])
def simulation_history():
    sims = ShockSimulation.query.order_by(ShockSimulation.created_at.desc()).limit(20).all()
    return jsonify([s.to_dict() for s in sims])

# ─────────────────────────────────────────────
# COUNTRY RISK MAP
# ─────────────────────────────────────────────

@api.route('/country-risk', methods=['GET'])
def get_country_risk():
    risks = CountryRisk.query.all()
    if not risks:
        _seed_country_risk()
        risks = CountryRisk.query.all()
    return jsonify([r.to_dict() for r in risks])

def _seed_country_risk():
    """Seed initial country risk data"""
    countries = [
        {'country': 'China', 'code': 'CN', 'risk': 72, 'trade': 85, 'dep': 78, 'lat': 35.86, 'lon': 104.19},
        {'country': 'USA', 'code': 'US', 'risk': 45, 'trade': 90, 'dep': 55, 'lat': 37.09, 'lon': -95.71},
        {'country': 'Russia', 'code': 'RU', 'risk': 82, 'trade': 60, 'dep': 70, 'lat': 61.52, 'lon': 105.31},
        {'country': 'India', 'code': 'IN', 'risk': 55, 'trade': 65, 'dep': 60, 'lat': 20.59, 'lon': 78.96},
        {'country': 'Germany', 'code': 'DE', 'risk': 40, 'trade': 80, 'dep': 50, 'lat': 51.16, 'lon': 10.45},
        {'country': 'Japan', 'code': 'JP', 'risk': 50, 'trade': 75, 'dep': 65, 'lat': 36.20, 'lon': 138.25},
        {'country': 'Taiwan', 'code': 'TW', 'risk': 78, 'trade': 70, 'dep': 82, 'lat': 23.69, 'lon': 120.96},
        {'country': 'South Korea', 'code': 'KR', 'risk': 58, 'trade': 72, 'dep': 68, 'lat': 35.90, 'lon': 127.77},
        {'country': 'Brazil', 'code': 'BR', 'risk': 62, 'trade': 55, 'dep': 48, 'lat': -14.23, 'lon': -51.92},
        {'country': 'Saudi Arabia', 'code': 'SA', 'risk': 65, 'trade': 68, 'dep': 72, 'lat': 23.88, 'lon': 45.08},
        {'country': 'UK', 'code': 'GB', 'risk': 38, 'trade': 78, 'dep': 45, 'lat': 55.37, 'lon': -3.43},
        {'country': 'France', 'code': 'FR', 'risk': 42, 'trade': 76, 'dep': 48, 'lat': 46.22, 'lon': 2.21},
        {'country': 'Australia', 'code': 'AU', 'risk': 35, 'trade': 62, 'dep': 40, 'lat': -25.27, 'lon': 133.77},
        {'country': 'Indonesia', 'code': 'ID', 'risk': 60, 'trade': 58, 'dep': 55, 'lat': -0.78, 'lon': 113.92},
        {'country': 'Mexico', 'code': 'MX', 'risk': 57, 'trade': 65, 'dep': 52, 'lat': 23.63, 'lon': -102.55},
        {'country': 'Ukraine', 'code': 'UA', 'risk': 88, 'trade': 45, 'dep': 65, 'lat': 48.37, 'lon': 31.16},
        {'country': 'Vietnam', 'code': 'VN', 'risk': 52, 'trade': 70, 'dep': 58, 'lat': 14.05, 'lon': 108.27},
        {'country': 'Canada', 'code': 'CA', 'risk': 33, 'trade': 73, 'dep': 42, 'lat': 56.13, 'lon': -106.34},
    ]
    for c in countries:
        cr = CountryRisk(
            country=c['country'], country_code=c['code'],
            risk_score=c['risk'], trade_exposure=c['trade'],
            dependency_score=c['dep'], lat=c['lat'], lon=c['lon']
        )
        db.session.add(cr)
    db.session.commit()

@api.route('/country-risk/update', methods=['POST'])
def update_country_risk():
    """Update risk scores from recent news"""
    from sqlalchemy import func
    country_risk_news = db.session.query(
        NewsEvent.country,
        func.avg(NewsEvent.severity)
    ).group_by(NewsEvent.country).all()

    for country, avg_sev in country_risk_news:
        cr = CountryRisk.query.filter_by(country=country).first()
        if cr:
            cr.risk_score = min(100, cr.risk_score * 0.7 + avg_sev * 10 * 0.3)
            cr.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'status': 'updated'})

# ─────────────────────────────────────────────
# CONSUMER IMPACT
# ─────────────────────────────────────────────

@api.route('/consumer-impact', methods=['GET'])
def get_consumer_impact():
    recent = NewsEvent.query.order_by(NewsEvent.date.desc()).limit(30).all()
    events = [e.to_dict() for e in recent]
    results = predict_consumer_impact(events)
    return jsonify(results)

# ─────────────────────────────────────────────
# INVESTMENT DASHBOARD
# ─────────────────────────────────────────────

@api.route('/investment', methods=['GET'])
def get_investment():
    recent = NewsEvent.query.order_by(NewsEvent.date.desc()).limit(50).all()
    events = [e.to_dict() for e in recent]
    sectors = score_sectors(events)
    return jsonify({
        'sectors': sectors,
        'buy': [s for s, v in sectors.items() if v['action'] == 'Buy'],
        'hold': [s for s, v in sectors.items() if v['action'] == 'Hold'],
        'sell': [s for s, v in sectors.items() if v['action'] == 'Sell'],
        'high_risk': [s for s, v in sectors.items() if v['score'] <= 40]
    })

# ─────────────────────────────────────────────
# FORECAST
# ─────────────────────────────────────────────

@api.route('/forecast', methods=['POST'])
def run_forecast():
    data = request.json
    forecast_type = data.get('type', 'Supply Chain Risk')
    horizon = int(data.get('horizon', 30))

    result = generate_forecast(forecast_type, horizon)

    fr = ForecastResult(
        forecast_type=forecast_type,
        horizon_days=horizon,
        forecast_data=json.dumps(result)
    )
    db.session.add(fr)

    warnings = generate_early_warnings([result])
    for w in warnings:
        alert = Alert(
            title=f"Forecast Warning: {w['type']}",
            message=w['message'],
            severity=w['severity'],
            alert_type='forecast_warning'
        )
        db.session.add(alert)

    db.session.commit()
    return jsonify(result)

# ─────────────────────────────────────────────
# CEO REPORT
# ─────────────────────────────────────────────

@api.route('/report/generate', methods=['POST'])
def generate_report():
    from sqlalchemy import func
    total_news = NewsEvent.query.count()
    high_sev = NewsEvent.query.filter(NewsEvent.severity >= 7).count()
    avg_risk = db.session.query(func.avg(NewsEvent.severity)).scalar() or 0
    active_alerts = Alert.query.filter_by(status='unread').count()

    top_countries = [r[0] for r in db.session.query(NewsEvent.country, func.count(NewsEvent.id)).group_by(NewsEvent.country).order_by(func.count(NewsEvent.id).desc()).limit(3).all()]
    top_industries = [r[0] for r in db.session.query(NewsEvent.industry, func.count(NewsEvent.id)).group_by(NewsEvent.industry).order_by(func.count(NewsEvent.id).desc()).limit(3).all()]
    shock_types = [r[0] for r in db.session.query(NewsEvent.shock_type, func.count(NewsEvent.id)).group_by(NewsEvent.shock_type).order_by(func.count(NewsEvent.id).desc()).limit(3).all()]

    context = {
        'total_news': total_news, 'high_severity': high_sev,
        'avg_risk': avg_risk * 10, 'active_alerts': active_alerts,
        'top_countries': top_countries, 'top_industries': top_industries,
        'shock_types': shock_types
    }

    report_text = generate_ceo_report(context)
    return jsonify({'report': report_text, 'context': context})

@api.route('/report/export', methods=['POST'])
def export_report():
    data = request.json
    report_text = data.get('report', '')
    if not report_text:
        return jsonify({'error': 'No report text provided'}), 400
    try:
        filepath = generate_pdf_report(report_text)
        return send_file(filepath, as_attachment=True,
                         download_name=os.path.basename(filepath),
                         mimetype='application/pdf')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ─────────────────────────────────────────────
# ALERTS / NOTIFICATIONS
# ─────────────────────────────────────────────

@api.route('/alerts', methods=['GET'])
def get_alerts():
    status = request.args.get('status', None)
    q = Alert.query.order_by(Alert.created_at.desc())
    if status:
        q = q.filter(Alert.status == status)
    alerts = q.limit(100).all()
    return jsonify([a.to_dict() for a in alerts])

@api.route('/alerts/<int:alert_id>/read', methods=['POST'])
def mark_alert_read(alert_id):
    alert = Alert.query.get_or_404(alert_id)
    alert.status = 'read'
    db.session.commit()
    return jsonify({'status': 'ok'})

@api.route('/alerts/<int:alert_id>/dismiss', methods=['POST'])
def dismiss_alert(alert_id):
    alert = Alert.query.get_or_404(alert_id)
    alert.status = 'dismissed'
    db.session.commit()
    return jsonify({'status': 'ok'})

@api.route('/alerts/stats', methods=['GET'])
def alert_stats():
    total = Alert.query.count()
    unread = Alert.query.filter_by(status='unread').count()
    critical = Alert.query.filter_by(severity='critical').count()
    high = Alert.query.filter_by(severity='high').count()
    return jsonify({'total': total, 'unread': unread, 'critical': critical, 'high': high})

# ─────────────────────────────────────────────
# HISTORICAL ANALYTICS
# ─────────────────────────────────────────────

@api.route('/historical', methods=['GET'])
def get_historical():
    days = request.args.get('days', 30, type=int)
    since = datetime.utcnow() - timedelta(days=days)
    events = NewsEvent.query.filter(NewsEvent.date >= since).order_by(NewsEvent.date).all()

    from collections import defaultdict
    daily = defaultdict(list)
    for e in events:
        key = e.date.strftime('%Y-%m-%d') if e.date else 'unknown'
        daily[key].append(e.severity)

    trend_data = [{'date': d, 'avg_risk': round(sum(v)/len(v)*10, 1), 'count': len(v)}
                  for d, v in sorted(daily.items())]

    from sqlalchemy import func
    industry_trend = db.session.query(NewsEvent.industry, func.count(NewsEvent.id), func.avg(NewsEvent.severity)).filter(NewsEvent.date >= since).group_by(NewsEvent.industry).all()
    country_trend = db.session.query(NewsEvent.country, func.count(NewsEvent.id), func.avg(NewsEvent.severity)).filter(NewsEvent.date >= since).group_by(NewsEvent.country).order_by(func.count(NewsEvent.id).desc()).limit(10).all()

    return jsonify({
        'risk_trend': trend_data,
        'industry_trend': [{'industry': i, 'count': c, 'avg_severity': round(a * 10, 1)} for i, c, a in industry_trend],
        'country_trend': [{'country': c, 'count': n, 'avg_severity': round(a * 10, 1)} for c, n, a in country_trend],
        'period_days': days
    })

# ─────────────────────────────────────────────
# SCENARIO COMPARISON
# ─────────────────────────────────────────────

@api.route('/scenario/compare', methods=['POST'])
def compare_scenarios():
    data = request.json
    scenario_a = data.get('scenario_a', {})
    scenario_b = data.get('scenario_b', {})

    result_a = simulate_shock(
        scenario_a.get('shock_type', 'Oil Shock'),
        float(scenario_a.get('severity', 5)),
        scenario_a.get('country', 'Global'),
        int(scenario_a.get('duration', 30))
    )
    result_b = simulate_shock(
        scenario_b.get('shock_type', 'Trade Restriction'),
        float(scenario_b.get('severity', 5)),
        scenario_b.get('country', 'Global'),
        int(scenario_b.get('duration', 30))
    )

    return jsonify({
        'scenario_a': {'params': scenario_a, 'result': result_a},
        'scenario_b': {'params': scenario_b, 'result': result_b},
        'comparison': {
            'risk_score_diff': round(result_a['risk_score'] - result_b['risk_score'], 2),
            'revenue_diff': round(result_a['revenue_impact'] - result_b['revenue_impact'], 2),
            'price_diff': round(result_a['price_increase'] - result_b['price_increase'], 2),
            'worse_scenario': 'A' if result_a['risk_score'] > result_b['risk_score'] else 'B'
        }
    })

# ─────────────────────────────────────────────
# AI CHAT ASSISTANT
# ─────────────────────────────────────────────

@api.route('/chat', methods=['POST'])
def chat():
    data = request.json
    question = data.get('question', '')
    if not question:
        return jsonify({'error': 'No question provided'}), 400

    from sqlalchemy import func
    recent_news = [e.to_dict() for e in NewsEvent.query.order_by(NewsEvent.date.desc()).limit(10).all()]
    high_risk = [r.to_dict() for r in CountryRisk.query.filter(CountryRisk.risk_score >= 65).order_by(CountryRisk.risk_score.desc()).limit(5).all()]
    alerts = [a.to_dict() for a in Alert.query.filter_by(status='unread').limit(5).all()]
    shock_types = [r[0] for r in db.session.query(NewsEvent.shock_type, func.count(NewsEvent.id)).group_by(NewsEvent.shock_type).order_by(func.count(NewsEvent.id).desc()).limit(5).all()]
    industries = [r[0] for r in db.session.query(NewsEvent.industry, func.count(NewsEvent.id)).group_by(NewsEvent.industry).order_by(func.count(NewsEvent.id).desc()).limit(5).all()]

    context = {
        'recent_news': [{'title': n['title'], 'shock_type': n['shock_type'], 'severity': n['severity']} for n in recent_news],
        'high_risk_countries': [{'country': r['country'], 'risk_score': r['risk_score']} for r in high_risk],
        'alerts': [{'title': a['title'], 'severity': a['severity']} for a in alerts],
        'shock_types': shock_types,
        'industries': industries
    }

    answer = chat_assistant(question, context)
    return jsonify({'answer': answer, 'question': question})

# ─────────────────────────────────────────────
# DASHBOARD SUMMARY
# ─────────────────────────────────────────────

@api.route('/dashboard/summary', methods=['GET'])
def dashboard_summary():
    from sqlalchemy import func
    total_news = NewsEvent.query.count()
    high_sev = NewsEvent.query.filter(NewsEvent.severity >= 7).count()
    active_alerts = Alert.query.filter_by(status='unread').count()
    avg_sev = db.session.query(func.avg(NewsEvent.severity)).scalar() or 0
    avg_risk = round(avg_sev * 10, 1)

    recent = NewsEvent.query.order_by(NewsEvent.date.desc()).limit(5).all()
    top_risks = CountryRisk.query.order_by(CountryRisk.risk_score.desc()).limit(5).all()
    recent_alerts = Alert.query.filter_by(status='unread').order_by(Alert.created_at.desc()).limit(3).all()

    return jsonify({
        'total_news': total_news,
        'high_severity_events': high_sev,
        'active_alerts': active_alerts,
        'global_risk_score': avg_risk,
        'recent_news': [e.to_dict() for e in recent],
        'top_risk_countries': [r.to_dict() for r in top_risks],
        'recent_alerts': [a.to_dict() for a in recent_alerts],
        'last_updated': datetime.utcnow().isoformat()
    })
