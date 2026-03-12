from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
import datetime
from app.models.guest import Guest
from app.models.event import Event
from app.models.rsvp import RSVP
from app.extensions import db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@main_bp.route('/chat')
@login_required
def dashboard():
    return render_template('chat.html')

@main_bp.route('/guests')
@login_required
def guests():
    if current_user.is_admin:
        all_guests = Guest.query.all()
    else:
        all_guests = Guest.query.filter_by(owner_id=current_user.id).all()
    return render_template('guests.html', guests=all_guests)

@main_bp.route('/events')
@login_required
def events():
    if current_user.is_admin:
        all_events = Event.query.all()
    else:
        all_events = Event.query.filter_by(owner_id=current_user.id).all()
    
    # We pass events, search, location defaults logic
    search_location = request.args.get('location', '')
    return render_template('events.html', events=all_events, search_location=search_location)

@main_bp.route('/rsvps')
@login_required
def rsvps():
    if current_user.is_admin:
        all_rsvps = RSVP.query.all()
        user_events = Event.query.all()
        user_guests = Guest.query.all()
    else:
        all_rsvps = RSVP.query.join(Event).filter(Event.owner_id == current_user.id).all()
        user_events = Event.query.filter_by(owner_id=current_user.id).all()
        user_guests = Guest.query.filter_by(owner_id=current_user.id).all()
        
    return render_template('rsvps.html', rsvps=all_rsvps, events=user_events, guests=user_guests)

@main_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if not current_user.is_admin:
        flash('Access denied. Administrator privileges required.', 'error')
        return redirect(url_for('main.profile'))
        
    import json
    from app.extensions import db
    
    if request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
            
        try:
            current_user.settings_json = json.dumps(data)
            db.session.commit()
            return jsonify({'status': 'success', 'message': 'Settings saved successfully!'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'status': 'error', 'message': str(e)}), 500
        
    # GET request
    default_settings = {
        'dark_mode': False,
        'email_notifications': True,
        'audio_alerts': False,
        'daily_summary': True,
        'accent_color': '#3b82f6',
        'language': 'en',
        'timezone': 'IST',
        'currency': 'INR'
    }
    
    try:
        if current_user.settings_json:
            user_settings = json.loads(current_user.settings_json)
            # Merge with defaults
            current_settings = {**default_settings, **user_settings}
        else:
            current_settings = default_settings
    except json.JSONDecodeError:
        current_settings = default_settings
    
    return render_template('settings.html', settings=current_settings)

@main_bp.route('/settings/action', methods=['POST'])
@login_required
def settings_action():
    if not current_user.is_admin:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
        
    data = request.get_json()
    action_type = data.get('action_type')
    
    if action_type == 'revoke_session':
        # Simulated session teardown
        return jsonify({'status': 'success', 'message': f"Successfully revoked {data.get('device', 'session')}."})
        
    elif action_type == 'toggle_integration':
        # Simulated integration OAuth flow
        target = data.get('target', 'Integration')
        return jsonify({'status': 'success', 'message': f"A connect request for {target} has been securely initiated."})
        
    return jsonify({'status': 'error', 'message': 'Unknown action'}), 400

@main_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        from app.extensions import db
        username = request.form.get('username')
        email = request.form.get('email')
        
        current_user.username = username
        current_user.email = email
        
        # Optionally handle password change if provided
        password = request.form.get('password')
        if password:
            current_user.set_password(password)
            
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'error')
            
        return redirect(url_for('main.profile'))
        
    return render_template('profile.html', user=current_user)

@main_bp.route('/sentiment')
@login_required
def sentiment():
    return render_template('sentiment.html')

@main_bp.route('/about')
def about():
    return render_template('about.html')

@main_bp.route('/contact')
def contact():
    return render_template('contact.html')

# Guest Routes Additions

@main_bp.route('/guests/new', methods=['GET', 'POST'])
@login_required
def new_guest():
    if request.method == 'POST':
        guest = Guest(
            name=request.form.get('name'),
            email=request.form.get('email'),
            phone=request.form.get('phone'),
            notes=request.form.get('notes'),
            dietary_needs=request.form.get('dietary_needs'),
            owner_id=current_user.id
        )
        db.session.add(guest)
        try:
            db.session.commit()
            flash('Guest added successfully!', 'success')
            return redirect(url_for('main.guests'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding guest: {str(e)}', 'error')
    
    return render_template('guest_form.html', guest=None)

@main_bp.route('/guests/<int:guest_id>')
@login_required
def view_guest(guest_id):
    query = Guest.query.get_or_404(guest_id)
    if not current_user.is_admin and query.owner_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('main.guests'))
    return render_template('guest_detail.html', guest=query, rsvps=query.rsvps)

@main_bp.route('/guests/<int:guest_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_guest(guest_id):
    guest = Guest.query.get_or_404(guest_id)
    if not current_user.is_admin and guest.owner_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('main.guests'))
    
    if request.method == 'POST':
        guest.name = request.form.get('name')
        guest.email = request.form.get('email')
        guest.phone = request.form.get('phone')
        guest.notes = request.form.get('notes')
        guest.dietary_needs = request.form.get('dietary_needs')
        
        try:
            db.session.commit()
            flash('Guest updated successfully!', 'success')
            return redirect(url_for('main.view_guest', guest_id=guest.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating guest: {str(e)}', 'error')
    
    return render_template('guest_form.html', guest=guest)

@main_bp.route('/guests/<int:guest_id>/delete', methods=['POST'])
@login_required
def delete_guest(guest_id):
    guest = Guest.query.get_or_404(guest_id)
    if not current_user.is_admin and guest.owner_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('main.guests'))
        
    db.session.delete(guest)
    db.session.commit()
    flash('Guest deleted successfully!', 'success')
    return redirect(url_for('main.guests'))

# APIs for Search and Delete
@main_bp.route('/find-guest', methods=['POST'])
@login_required
def find_guest():
    data = request.get_json()
    search_term = data.get('search_term', '').strip()
    
    if not search_term:
        return jsonify({'error': 'No search term provided'}), 400
        
    try:
        from sqlalchemy import or_
        query = Guest.query.filter(or_(Guest.name.ilike(f'%{search_term}%'), Guest.email.ilike(f'%{search_term}%')))
        if not current_user.is_admin:
            query = query.filter_by(owner_id=current_user.id)
            
        guests_found = query.all()
        if not guests_found:
            return jsonify({'message': 'No guests found matching your search.'})
            
        result_html = """
        <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50 dark:bg-gray-700">
                <tr>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Name</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Email</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Phone</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Actions</th>
                </tr>
            </thead>
            <tbody class="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
        """
        
        for guest in guests_found:
            result_html += f"""
                <tr>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">{guest.name}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">{guest.email}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">{guest.phone or ''}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <button onclick="removeGuest('{guest.id}')" class="text-red-600 hover:text-red-900">Remove</button>
                    </td>
                </tr>
            """
        
        result_html += """
            </tbody>
        </table>
        </div>
        """
        
        return jsonify({
            'html': result_html,
            'count': len(guests_found)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/remove-guest', methods=['POST'])
@login_required
def remove_guest():
    data = request.get_json()
    # Handle both old 'registration_number' usage and new 'id' usage from our frontend script
    guest_id = data.get('registration_number') or data.get('id')
    
    if not guest_id:
        return jsonify({'error': 'No guest identifier provided'}), 400
        
    try:
        guest = Guest.query.get(guest_id)
        if not guest:
            return jsonify({'error': 'Guest not found'}), 404
            
        if not current_user.is_admin and guest.owner_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
            
        db.session.delete(guest)
        db.session.commit()
        
        return jsonify({
            'message': f'Guest {guest.name} has been removed successfully.'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Event Routes Additions

@main_bp.route('/events/new', methods=['GET', 'POST'])
@login_required
def new_event():
    if request.method == 'POST':
        date_str = request.form.get('date')
        try:
            date_obj = datetime.datetime.fromisoformat(date_str) if 'T' in date_str else datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                date_obj = datetime.datetime.now()
                
        event = Event(
            name=request.form.get('name'),
            date=date_obj,
            location=request.form.get('location'),
            description=request.form.get('description'),
            max_guests=request.form.get('max_guests', type=int) or 0,
            owner_id=current_user.id
        )
        db.session.add(event)
        try:
            db.session.commit()
            flash('Event created successfully!', 'success')
            return redirect(url_for('main.events'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating event: {str(e)}', 'error')
            
    return render_template('event_form.html', event=None)

@main_bp.route('/events/<int:event_id>')
@login_required
def view_event(event_id):
    event = Event.query.get_or_404(event_id)
    if not current_user.is_admin and event.owner_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('main.events'))
    return render_template('event_detail.html', event=event, rsvps=event.rsvps)

@main_bp.route('/events/<int:event_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    if not current_user.is_admin and event.owner_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('main.events'))
        
    if request.method == 'POST':
        date_str = request.form.get('date')
        try:
            date_obj = datetime.datetime.fromisoformat(date_str) if 'T' in date_str else datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                date_obj = datetime.datetime.now()
                
        event.name = request.form.get('name')
        event.date = date_obj
        event.location = request.form.get('location')
        event.description = request.form.get('description')
        event.max_guests = request.form.get('max_guests', type=int) or 0
        
        try:
            db.session.commit()
            flash('Event updated successfully!', 'success')
            return redirect(url_for('main.view_event', event_id=event.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating event: {str(e)}', 'error')
            
    return render_template('event_form.html', event=event)

@main_bp.route('/events/<int:event_id>/delete', methods=['POST'])
@login_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    if not current_user.is_admin and event.owner_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('main.events'))
        
    db.session.delete(event)
    db.session.commit()
    flash('Event deleted successfully!', 'success')
    return redirect(url_for('main.events'))

# RSVP Routes Additions

@main_bp.route('/rsvps/new', methods=['GET', 'POST'])
@login_required
def new_rsvp():
    if request.method == 'POST':
        rsvp = RSVP(
            guest_id=request.form.get('guest_id'),
            event_id=request.form.get('event_id'),
            status=request.form.get('status'),
            plus_ones_count=request.form.get('plus_ones', type=int) or 0,
            notes=request.form.get('dietary_restrictions')
        )
        
        db.session.add(rsvp)
        try:
            db.session.commit()
            flash('RSVP recorded successfully!', 'success')
            return redirect(url_for('main.rsvps'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error recording RSVP: {str(e)}', 'error')
            
    guests = Guest.query.filter_by(owner_id=current_user.id).all() if not current_user.is_admin else Guest.query.all()
    events = Event.query.filter_by(owner_id=current_user.id).all() if not current_user.is_admin else Event.query.all()
    return render_template('rsvp_form.html', guests=guests, events=events, rsvp=None)

@main_bp.route('/rsvps/<int:rsvp_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_rsvp(rsvp_id):
    rsvp = RSVP.query.get_or_404(rsvp_id)
    if not current_user.is_admin and rsvp.event.owner_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('main.rsvps'))
        
    if request.method == 'POST':
        rsvp.status = request.form.get('status')
        rsvp.plus_ones_count = request.form.get('plus_ones', type=int) or 0
        rsvp.notes = request.form.get('dietary_restrictions')
        
        try:
            db.session.commit()
            flash('RSVP updated successfully!', 'success')
            return redirect(url_for('main.rsvps'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating RSVP: {str(e)}', 'error')
            
    guests = Guest.query.filter_by(owner_id=current_user.id).all() if not current_user.is_admin else Guest.query.all()
    events = Event.query.filter_by(owner_id=current_user.id).all() if not current_user.is_admin else Event.query.all()
    return render_template('rsvp_form.html', guests=guests, events=events, rsvp=rsvp)

@main_bp.route('/rsvps/<int:rsvp_id>/delete', methods=['POST'])
@login_required
def delete_rsvp(rsvp_id):
    rsvp = RSVP.query.get_or_404(rsvp_id)
    if not current_user.is_admin and rsvp.event.owner_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('main.rsvps'))
        
    db.session.delete(rsvp)
    db.session.commit()
    flash('RSVP deleted successfully!', 'success')
    return redirect(url_for('main.rsvps'))

@main_bp.route('/notifications/mark-read', methods=['POST'])
@login_required
def mark_notifications_read():
    return jsonify({'success': True, 'message': 'Notifications marked as read'})

@main_bp.route('/upload-excel', methods=['POST'])
@login_required
def upload_excel():
    import os
    import pandas as pd
    from werkzeug.utils import secure_filename
    from flask import current_app
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        return jsonify({'error': 'Invalid file format'}), 400
    
    try:
        upload_folder = os.path.join(current_app.root_path, '..', 'temp_uploads')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
            
        filename = secure_filename(file.filename)
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        
        df = pd.read_excel(filepath)
        os.remove(filepath)
        
        added_count = 0
        for idx, row in df.iterrows():
            name = str(row.get('Name', '')).strip()
            email = str(row.get('Email', '')).strip()
            
            if name and name != 'nan':
                existing = Guest.query.filter_by(email=email, owner_id=current_user.id).first()
                if not existing:
                    guest = Guest(
                        name=name,
                        email=email if email and email != 'nan' else f"guest_{idx}@example.com",
                        phone=str(row.get('Phone', '')).strip() if str(row.get('Phone', '')) != 'nan' else '',
                        owner_id=current_user.id
                    )
                    db.session.add(guest)
                    added_count += 1
        
        db.session.commit()
        return jsonify({
            'success': True, 
            'message': f'Successfully imported {added_count} guests from Excel file.'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

