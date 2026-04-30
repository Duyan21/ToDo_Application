import logging
from flask import Flask
from src.routes.auth import auth_bp
from src.routes.task import task_bp
from src.database.models import db

def create_app():
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(levelname)s %(name)s %(message)s'
        )

    app = Flask(
        __name__,
        template_folder='../templates',
        static_folder='../static'
    )
    app.secret_key = 'replace-with-a-secure-secret'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydb.sqlite'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(task_bp)

    return app