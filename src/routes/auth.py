from flask import Blueprint, render_template, request, jsonify, session
from src.database.models import db, User
from werkzeug.security import check_password_hash, generate_password_hash
from src.utils.decorators.validate_input import validate_input

from src.utils.decorators.require_auth import require_auth

auth_bp = Blueprint('auth', __name__, template_folder='../../templates')

@auth_bp.route("/register")
def register_page():
    return render_template("register.html")

# vào /signin hoặc / sẽ hiển thị trang đăng nhập
@auth_bp.route("/")
@auth_bp.route("/signin")
def signin_page():
    return render_template("signin.html")

@auth_bp.route('/api/register', methods=['POST'])
@validate_input(
    required_fields=['name', 'email', 'password'],
    field_types={'name': str, 'email': str, 'password': str}
)
def register():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email đã tồn tại"}), 400

    new_user = User(
        name=name,
        email=email,
        password_hash=generate_password_hash(password)
    )
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "Đăng ký thành công"})

@auth_bp.route('/api/signin', methods=['POST'])
@validate_input(
    required_fields=['email', 'password'],
    field_types={'email': str, 'password': str}
)
def signin():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Email hoặc mật khẩu không đúng"}), 400

    session['user_id'] = user.id
    return jsonify({"message": "Đăng nhập thành công"})

@auth_bp.route('/api/logout', methods=['POST'])
@require_auth
def logout():
    session.clear()
    return jsonify({"message": "Đã đăng xuất"})
