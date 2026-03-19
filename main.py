from app import create_app

app = create_app()

if __name__ == "__main__":
    # use_reloader=False prevents Werkzeug from spawning a second process
    # which would create a second APScheduler instance and cause the
    # "maximum number of running instances reached" warning.
    import os
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug_mode, host="0.0.0.0", port=5000, use_reloader=False)
