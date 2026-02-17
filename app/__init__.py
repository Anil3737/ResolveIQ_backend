from flask import Flask, jsonify
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

    # JWT Identity/Lookup Loaders
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
        return User.query.get(int(identity))

    # JWT Error Handlers for Debugging
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        print(f"❌ JWT INVALID: {error}")
        return jsonify({"success": False, "message": f"Invalid token: {error}"}), 422

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        print(f"❌ JWT MISSING: {error}")
        return jsonify({"success": False, "message": "Missing Authorization Header"}), 401

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_data):
        print(f"❌ JWT EXPIRED: {jwt_data}")
        return jsonify({"success": False, "message": "Token has expired"}), 401

    return app
