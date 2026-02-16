from flask import Flask
from app.config import Config
from app.extensions import db, migrate, jwt, cors

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app)

    # Register Blueprints
    from app.routes.auth_routes import auth_bp
    from app.routes.admin_routes import admin_bp
    from app.routes.ticket_routes import ticket_bp
    from app.routes.sla_routes import sla_bp
    from app.routes.ai_routes import ai_bp
    from app.routes.analytics_routes import analytics_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(ticket_bp, url_prefix='/api/tickets')
    app.register_blueprint(sla_bp, url_prefix='/api/sla')
    app.register_blueprint(ai_bp, url_prefix='/api/ai')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')

    return app
