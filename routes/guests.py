from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app import db
from models import Guest

guest_bp = Blueprint('guest', __name__, url_prefix='/guests')

@guest_bp.route('/')
@login_required
def manage():
    guests = Guest.query.filter_by(user_id=current_user.id).all()
    return render_template('guests/manage.html', guests=guests)

@guest_bp.route('/add', methods=['POST'])
@login_required
def add():
    name = request.form.get('name')
    email = request.form.get('email')
    
    new_guest = Guest(
        name=name,
        email=email,
        user_id=current_user.id
    )
    db.session.add(new_guest)
    db.session.commit()
    flash('Guest added successfully')
    return redirect(url_for('guest.manage'))

@guest_bp.route('/delete/<int:id>')
@login_required
def delete(id):
    guest = Guest.query.get_or_404(id)
    if guest.user_id != current_user.id:
        flash('Unauthorized action')
        return redirect(url_for('guest.manage'))
    
    db.session.delete(guest)
    db.session.commit()
    flash('Guest removed successfully')
    return redirect(url_for('guest.manage'))