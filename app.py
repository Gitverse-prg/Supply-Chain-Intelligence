import os
from flask import Flask, render_template, send_from_directory
from models import db
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__)
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = \'sqlite:///' + os.path.join(BASE_DIR, 'database.db')

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'scsi-platform-2024')

    db.init_app(app)

    from routes.api import api
    app.register_blueprint(api)

    # Page routes
    @app.route('/')
    def index():
        return render_template('dashboard.html', page='dashboard')

    @app.route('/news')
    def news():
        return render_template('news.html', page='news')

    @app.route('/simulator')
    def simulator():
        return render_template('simulator.html', page='simulator')

    @app.route('/country-risk')
    def country_risk():
        return render_template('country_risk.html', page='country_risk')

    @app.route('/consumer-impact')
    def consumer_impact():
        return render_template('consumer_impact.html', page='consumer_impact')

    @app.route('/investment')
    def investment():
        return render_template('investment.html', page='investment')

    @app.route('/forecast')
    def forecast():
        return render_template('forecast.html', page='forecast')

    @app.route('/ceo-report')
    def ceo_report():
        return render_template('ceo_report.html', page='ceo_report')

    @app.route('/notifications')
    def notifications():
        return render_template('notifications.html', page='notifications')

    @app.route('/historical')
    def historical():
        return render_template('historical.html', page='historical')

    @app.route('/scenario')
    def scenario():
        return render_template('scenario.html', page='scenario')

    @app.route('/assistant')
    def assistant():
        return render_template('assistant.html', page='assistant')

    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    print("\n" + "="*55)
    print("  GLOBAL SUPPLY CHAIN SHOCK INTELLIGENCE PLATFORM")
    print("="*55)
    print("  Running at: http://127.0.0.1:5000")
    print("  Press CTRL+C to stop")
    print("="*55 + "\n")
    app.run(debug=True, port=5000)
