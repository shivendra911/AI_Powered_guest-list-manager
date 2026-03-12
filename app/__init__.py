from flask import Flask
from .config import Config
from .extensions import db, login_manager

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Flask extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.chatbot_api import chatbot_bp
    from app.routes.main import main_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(main_bp)

    # Import models so SQLAlchemy creates the tables
    from app import models
    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Context processors
    @app.context_processor
    def inject_settings():
        from app.models.guest import Guest
        from flask_login import current_user
        import json
        
        settings = {}
        if current_user.is_authenticated and hasattr(current_user, 'settings_json') and current_user.settings_json:
            try:
                settings = json.loads(current_user.settings_json)
            except json.JSONDecodeError:
                pass
                
        return {
            'notifications_count': 0, # Placeholder
            'app_version': '2.0',
            'get_guest_rsvps': lambda guest_id: Guest.query.get(guest_id).rsvps if Guest.query.get(guest_id) else [],
            'settings': settings
        }

    @app.template_filter('format_date')
    def format_date_filter(value, format="%b %d, %Y"):
        if value is None:
            return ""
        if isinstance(value, str):
            import datetime
            try:
                value = datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    value = datetime.datetime.strptime(value, "%Y-%m-%d")
                except ValueError:
                    return value
        return value.strftime(format)

    @app.template_filter('format_datetime_local')
    def format_datetime_local_filter(value):
        if value is None:
            return ""
        if isinstance(value, str):
            import datetime
            try:
                # Parse ISO format or standard datetime
                if 'T' in value:
                    value = datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))
                else:
                    value = datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return value
        # Format for datetime-local input
        return value.strftime("%Y-%m-%dT%H:%M")

    @app.template_filter('format_currency')
    def format_currency_filter(value, currency_setting='USD'):
        if value is None:
            return ""
        try:
            value = float(value)
        except (ValueError, TypeError):
            return value
            
        currency_map = {
            'USD': '${:,.2f}',
            'EUR': '€{:,.2f}',
            'GBP': '£{:,.2f}',
            'INR': '₹{:,.2f}'
        }
        
        formatter = currency_map.get(currency_setting, '${:,.2f}')
        return formatter.format(value)

    return app
