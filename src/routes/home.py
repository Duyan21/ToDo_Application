from flask import Blueprint, render_template, redirect, url_for, session
from src.database.models import User

home_bp = Blueprint('home', __name__, template_folder='../../templates')

@home_bp.route('/home')
def home():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.signin_page'))
    user = User.query.get(user_id)
    return render_template('home.html', user_name=user.name)
