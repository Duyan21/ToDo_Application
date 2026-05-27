import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def app():
    from src.app.app import create_app
    from src.database.models import db

    with patch('src.app.app.BackgroundScheduler', return_value=MagicMock()):
        test_app = create_app()

    test_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SECRET_KEY': 'test-secret-key',
    })

    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()
