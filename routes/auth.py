from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_user, logout_user
from models import User
from app import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Add login logic
    return render_template('login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    # Add signup logic
    return render_template('signup.html')

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.home'))