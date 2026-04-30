import logging
import os
from flask import Flask
import urllib
from src.routes.auth import auth_bp
from src.routes.task import task_bp
from src.routes.notification import noti_bp
from src.database.models import db
from apscheduler.schedulers.background import BackgroundScheduler
from src.services.notification_service import NotificationService

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
    app.secret_key = os.getenv('SECRET_KEY', 'replace-with-a-secure-secret')
    
    # Database configuration from .env
    DB_HOST = os.getenv("DB_HOST")
    DB_NAME = os.getenv("DB_NAME")
    DB_DRIVER = os.getenv("DB_DRIVER")
    
    if DB_HOST and DB_NAME and DB_DRIVER:
        # SQL Server configuration
        params = urllib.parse.quote_plus(
            f"DRIVER={DB_DRIVER};"
            f"SERVER={DB_HOST};"
            f"DATABASE={DB_NAME};"
            "Trusted_Connection=yes;"
        )
        app.config["SQLALCHEMY_DATABASE_URI"] = f"mssql+pyodbc:///?odbc_connect={params}"
    else:
        # Fallback to SQLite for development
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydb.sqlite'
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(task_bp)
    app.register_blueprint(noti_bp)

    # Initialize background scheduler for notifications
    def start_scheduler():
        scheduler = BackgroundScheduler()
        
        def run_notification_check():
            with app.app_context():
                NotificationService.check_and_create_notifications()
        
        scheduler.add_job(
            func=run_notification_check,
            trigger="interval",
            seconds=3,  # Run every 3 seconds
            id='notification_check_job'
        )
        scheduler.start()
        print("Background scheduler started for notifications")
        return scheduler
    
    # Start scheduler after app is created
    scheduler = start_scheduler()
    
    # Shutdown scheduler when app exits
    import atexit
    atexit.register(lambda: scheduler.shutdown())

    return app