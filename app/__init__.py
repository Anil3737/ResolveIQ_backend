import logging
from flask import Flask, jsonify
from app.config import Config
from app.extensions import db, migrate, jwt, cors, limiter
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, origins=[
        "http://localhost:5173",  # Vite (Local)
        "http://localhost:3000",  # React (Local)
        "https://resolveiq.com"   # Production (Proposed)
    ])
    limiter.init_app(app)

    logger.info("[App] Registering blueprints...")
    from app.routes.auth_routes import auth_bp
    from app.routes.admin_routes import admin_bp
    from app.routes.ticket_routes import ticket_bp
    from app.routes.sla_routes import sla_bp
    from app.routes.ai_routes import ai_bp
    from app.routes.analytics_routes import analytics_bp
    from app.routes.team_lead_routes import team_lead_bp
    from app.routes.agent_routes import agent_bp
    from app.routes.activity_routes import activity_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(ticket_bp, url_prefix='/api/tickets')
    app.register_blueprint(sla_bp, url_prefix='/api/sla')
    app.register_blueprint(ai_bp, url_prefix='/api/ai')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    app.register_blueprint(team_lead_bp, url_prefix='/api/team-lead')
    app.register_blueprint(agent_bp, url_prefix='/api/agent')
    app.register_blueprint(activity_bp, url_prefix='/api')
    logger.info("[App] Blueprints registered.")
    
    # Initialize background scheduler
    logger.info("[App] Starting scheduler...")
    from app.scheduler import init_scheduler
    init_scheduler(app)

    # JWT Identity/Lookup Loaders
    logger.info("[App] Configuring JWT loaders...")
    from app.models import User

    @jwt.user_identity_loader
    def user_identity_lookup(user):
        # identity MUST be a string for JWT "sub" field
        if hasattr(user, 'id'):
            return str(user.id)
        if isinstance(user, dict):
            return str(user.get('id'))
        return str(user)

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data["sub"]
        return db.session.get(User, int(identity))

    # JWT Error Handlers for Debugging
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        logger.error(f"❌ JWT INVALID: {error}")
        return jsonify({"success": False, "message": f"Invalid token: {error}"}), 422

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        logger.error(f"❌ JWT MISSING: {error}")
        return jsonify({"success": False, "message": "Missing Authorization Header"}), 401

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_data):
        logger.error(f"❌ JWT EXPIRED: {jwt_data}")
        return jsonify({"success": False, "message": "Token has expired"}), 401

    # Create tables if they don't exist.
    # Wrapped in try/except — a DB connection failure does NOT crash the server.
    logger.info("[App] Connecting to database...")
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables verified/created.")
        except Exception as e:
            logger.warning("WARNING: Could not connect to database!")
            logger.warning(f"   Error: {e}")
            logger.warning("   ->  Open Workbench and check if MySQL is running.")
            logger.warning("   ->  Then check DB_PASSWORD in your .env file.")
            logger.warning("   ->  The Flask server will start, but API calls will fail.")

    logger.info("[App] create_app() complete. Starting Flask server...")
    return app
