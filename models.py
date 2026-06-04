from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class NewsEvent(db.Model):
    __tablename__ = 'news_events'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    source = db.Column(db.String(200))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    country = db.Column(db.String(100))
    industry = db.Column(db.String(100))
    shock_type = db.Column(db.String(100))
    severity = db.Column(db.Float, default=0.0)
    probability = db.Column(db.Float, default=0.0)
    url = db.Column(db.String(1000))
    description = db.Column(db.Text)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'source': self.source,
            'date': self.date.isoformat() if self.date else None,
            'country': self.country,
            'industry': self.industry,
            'shock_type': self.shock_type,
            'severity': self.severity,
            'probability': self.probability,
            'url': self.url,
            'description': self.description
        }

class ShockSimulation(db.Model):
    __tablename__ = 'shock_simulations'
    id = db.Column(db.Integer, primary_key=True)
    shock_type = db.Column(db.String(100))
    severity = db.Column(db.Float)
    country = db.Column(db.String(100))
    duration = db.Column(db.Integer)
    revenue_impact = db.Column(db.Float)
    risk_score = db.Column(db.Float)
    price_increase = db.Column(db.Float)
    affected_industries = db.Column(db.Text)
    affected_products = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'shock_type': self.shock_type,
            'severity': self.severity,
            'country': self.country,
            'duration': self.duration,
            'revenue_impact': self.revenue_impact,
            'risk_score': self.risk_score,
            'price_increase': self.price_increase,
            'affected_industries': self.affected_industries,
            'affected_products': self.affected_products,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Alert(db.Model):
    __tablename__ = 'alerts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500))
    message = db.Column(db.Text)
    severity = db.Column(db.String(50))  # low, medium, high, critical
    alert_type = db.Column(db.String(100))
    status = db.Column(db.String(50), default='unread')  # unread, read, dismissed
    country = db.Column(db.String(100))
    industry = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'severity': self.severity,
            'alert_type': self.alert_type,
            'status': self.status,
            'country': self.country,
            'industry': self.industry,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class ForecastResult(db.Model):
    __tablename__ = 'forecast_results'
    id = db.Column(db.Integer, primary_key=True)
    forecast_type = db.Column(db.String(100))
    horizon_days = db.Column(db.Integer)
    forecast_data = db.Column(db.Text)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'forecast_type': self.forecast_type,
            'horizon_days': self.horizon_days,
            'forecast_data': self.forecast_data,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class CountryRisk(db.Model):
    __tablename__ = 'country_risk'
    id = db.Column(db.Integer, primary_key=True)
    country = db.Column(db.String(100), unique=True)
    country_code = db.Column(db.String(10))
    risk_score = db.Column(db.Float)
    trade_exposure = db.Column(db.Float)
    dependency_score = db.Column(db.Float)
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'country': self.country,
            'country_code': self.country_code,
            'risk_score': self.risk_score,
            'trade_exposure': self.trade_exposure,
            'dependency_score': self.dependency_score,
            'lat': self.lat,
            'lon': self.lon
        }
