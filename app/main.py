# app/main.py

# app/main.py

from flask import Flask, jsonify
from flask_cors import CORS
from app.database import db_session
from app.routes.auth_routes import auth_bp
from app.routes.admin_routes import admin_bp
from app.routes.ticket_routes import ticket_bp
from app.ai.ai_routes import ai_bp

def create_app():
    app = Flask(__name__)
    CORS(app)

    # Register Blueprints - Updated to match frontend expectations
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(ticket_bp, url_prefix="/api/tickets")
    app.register_blueprint(ai_bp, url_prefix="/api/ai")
    
    from app.routes.team_lead_routes import team_lead_bp
    from app.routes.agent_routes import agent_bp
    app.register_blueprint(team_lead_bp, url_prefix="/api/team-lead")
    app.register_blueprint(agent_bp, url_prefix="/api/agent")

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()

    @app.route("/")
    def root():
        """Root endpoint - API information"""
        return jsonify({
            "message": "Welcome to ResolveIQ API (Flask)",
            "version": "1.0",
            "health_check": "/api/v1/health"
        })

    @app.route("/api/v1/health")
    def health():
        return jsonify({"status": "ok", "service": "ResolveIQ API (Flask)"})

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
# main.pya