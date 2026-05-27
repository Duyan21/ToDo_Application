from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for

from src.dto.user_dto import UserLoginDTO, UserRegisterDTO
from src.services.auth_service import AuthError, EmailAlreadyExistsError, InvalidCredentialsError, AuthService
from src.utils.decorators.require_auth import require_auth
from src.utils.decorators.validate_input import validate_input

auth_bp = Blueprint('auth', __name__, template_folder='../../templates')


@auth_bp.route("/register")
def register_page():
    if session.get('user_id'):
        return redirect(url_for('home.home'))
    return redirect(url_for('auth.signin_page', tab='register'))


@auth_bp.route("/")
@auth_bp.route("/signin")
def signin_page():
    if session.get('user_id'):
        return redirect(url_for('home.home'))
    return render_template("signin.html")


@auth_bp.route('/api/register', methods=['POST'])
@validate_input(
    required_fields=['name', 'email', 'password'],
    field_types={'name': str, 'email': str, 'password': str},
    email_fields=['email'],
    min_length={'name': 1, 'password': 8}
)
def register():
    data = request.get_json()
    dto = UserRegisterDTO(name=data['name'], email=data['email'], password=data['password'])
    try:
        user_dto = AuthService.register(dto)
    except EmailAlreadyExistsError as e:
        return jsonify({"error": str(e)}), 409
    except AuthError as e:
        return jsonify({"error": str(e)}), 400
    session['user_id'] = user_dto.id
    return jsonify({"message": "Đăng ký thành công"}), 201


@auth_bp.route('/api/signin', methods=['POST'])
@validate_input(
    required_fields=['email', 'password'],
    field_types={'email': str, 'password': str},
    email_fields=['email']
)
def signin():
    data = request.get_json()
    dto = UserLoginDTO(email=data['email'], password=data['password'])
    try:
        user_dto = AuthService.signin(dto)
    except InvalidCredentialsError as e:
        return jsonify({"error": str(e)}), 401
    except AuthError as e:
        return jsonify({"error": str(e)}), 400
    session['user_id'] = user_dto.id
    return jsonify({"message": "Đăng nhập thành công"})


@auth_bp.route('/api/logout', methods=['POST'])
@require_auth(api=True)
def logout():
    # Cross-origin form posts cannot set X-Requested-With; reject them to mitigate CSRF.
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return jsonify({"error": "Yêu cầu không hợp lệ"}), 403
    session.clear()
    return jsonify({"message": "Đã đăng xuất"})
