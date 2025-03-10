from flask import Flask


def create_app():
    app = Flask(__name__)
    app.json.ensure_ascii = False

    # Register Blueprints
    from app.routes.odoo import odoo_bp
    from app.routes.excel import excel_bp

    app.register_blueprint(odoo_bp, url_prefix="/api/odoo")
    app.register_blueprint(excel_bp, url_prefix="/api/excel")

    return app
