import logging
from flask import Flask
from src.routes.auth import auth_bp
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
    app.secret_key = '656664296eaf2a66f9c6d6c527e586c849ad9f68cf519f191095e1f596d77cda'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydb.sqlite'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    app.register_blueprint(auth_bp)

    return app