import pytest
from unittest.mock import patch
from werkzeug.security import generate_password_hash
from sqlalchemy.pool import StaticPool


@pytest.fixture(scope="session")
def app():
    with patch("src.app.app.BackgroundScheduler"):
        from src.app.app import create_app
        application = create_app()

    application.config.update({
        "TESTING": True,
        "SECRET_KEY": "test-secret",
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SQLALCHEMY_ENGINE_OPTIONS": {
            "connect_args": {"check_same_thread": False},
            "poolclass": StaticPool,
        },
    })
    return application


@pytest.fixture
def db(app):
    """Fresh DB for each test — creates all tables, tears down after."""
    from src.database.models import db as _db
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app, db):
    with app.test_client() as c:
        yield c


# ── Shared domain objects ─────────────────────────────────────────────────────

@pytest.fixture
def user(db):
    from src.database.models import User
    u = User(
        name="Test User",
        email="test@example.com",
        password_hash=generate_password_hash("password123"),
    )
    db.session.add(u)
    db.session.commit()
    db.session.refresh(u)
    return u


@pytest.fixture
def other_user(db):
    from src.database.models import User
    u = User(
        name="Other User",
        email="other@example.com",
        password_hash=generate_password_hash("password123"),
    )
    db.session.add(u)
    db.session.commit()
    db.session.refresh(u)
    return u


@pytest.fixture
def auth_client(client, user):
    with client.session_transaction() as sess:
        sess["user_id"] = user.id
    yield client


@pytest.fixture
def task(db, user):
    from src.database.models import Task, Priority, TaskStatus
    from datetime import datetime, timedelta
    t = Task(
        user_id=user.id,
        title="Test Task",
        priority=Priority.medium,
        status=TaskStatus.pending,
        deadline=datetime.now() + timedelta(hours=2),
        reminder_minutes=30,
    )
    db.session.add(t)
    db.session.commit()
    db.session.refresh(t)
    return t


@pytest.fixture
def overdue_task(db, user):
    from src.database.models import Task, Priority, TaskStatus
    from datetime import datetime, timedelta
    t = Task(
        user_id=user.id,
        title="Overdue Task",
        priority=Priority.high,
        status=TaskStatus.pending,
        deadline=datetime.now() - timedelta(hours=3),
        reminder_minutes=0,
    )
    db.session.add(t)
    db.session.commit()
    db.session.refresh(t)
    return t


@pytest.fixture
def notification(db, user, task):
    from src.database.models import Notification, NotificationType
    from datetime import datetime
    n = Notification(
        task_id=task.id,
        user_id=user.id,
        type=NotificationType.OVERDUE,
        message="Test overdue",
        notify_time=datetime.now(),
        is_read=False,
    )
    db.session.add(n)
    db.session.commit()
    db.session.refresh(n)
    return n
