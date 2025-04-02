# app.py
import os
import uuid
import pandas as pd
import openai
from flask import Flask, render_template_string, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from io import BytesIO

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///site.db').replace('postgres://', 'postgresql://')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Set OpenAI API key
openai.api_key = os.environ.get('OPENAI_API_KEY')

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password_hash = db.Column(db.String(200))

class Guest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# HTML Templates
BASE_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .chat-container {{ height: 500px; overflow-y: auto; }}
        .message {{ margin: 10px; padding: 10px; border-radius: 5px; }}
        .user-message {{ background-color: #e3f2fd; }}
        .bot-message {{ background-color: #f5f5f5; }}
        .temperature-slider {{ width: 200px; }}
    </style>
</head>
<body>
    {navbar}
    <div class="container mt-4">
        {content}
    </div>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script>{scripts}</script>
</body>
</html>
'''

NAVBAR = '''
<nav class="navbar navbar-expand-lg navbar-dark bg-dark">
    <div class="container">
        <a class="navbar-brand" href="/">ChatBot</a>
        <div class="d-flex">
            %s
            <button class="btn btn-danger" onclick="logout()">Logout</button>
        </div>
    </div>
</nav>
'''

LOGIN_HTML = BASE_HTML % {
    'content': '''
    <div class="row justify-content-center">
        <div class="col-md-6">
            <h2>Login</h2>
            <form id="loginForm" onsubmit="return false;">
                <div class="mb-3">
                    <input type="text" class="form-control" id="username" placeholder="Username">
                </div>
                <div class="mb-3">
                    <input type="password" class="form-control" id="password" placeholder="Password">
                </div>
                <button class="btn btn-primary" onclick="submitForm('login')">Login</button>
                <button class="btn btn-link" onclick="window.location.href='/signup'">Sign Up</button>
            </form>
        </div>
    </div>
    ''',
    'scripts': '''
    function submitForm(action) {
        const username = $('#username').val();
        const password = $('#password').val();
        fetch('/' + action, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username, password})
        }).then(res => res.json()).then(data => {
            if (data.success) window.location.href = '/dashboard';
            else alert(data.error || 'Error');
        });
    }
    function logout() { window.location.href = '/logout'; }
    '''
}

DASHBOARD_HTML = BASE_HTML % {
    'navbar': NAVBAR % '<input type="range" class="form-range temperature-slider" min="0" max="1" step="0.1" value="0.7">',
    'content': '''
    <div class="row">
        <div class="col-md-8">
            <div class="card">
                <div class="card-header">Chat</div>
                <div class="card-body chat-container" id="chatContainer"></div>
                <div class="card-footer">
                    <input type="text" class="form-control" id="messageInput" placeholder="Type your message...">
                    <button class="btn btn-primary mt-2" onclick="sendMessage()">Send</button>
                </div>
            </div>
            <div class="mt-3">
                <input type="file" id="fileUpload" class="form-control">
                <button class="btn btn-secondary mt-2" onclick="uploadFile()">Analyze File</button>
                <div id="fileAnalysis" class="mt-2"></div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card">
                <div class="card-header">Guest List</div>
                <div class="card-body">
                    <div id="guestList"></div>
                    <input type="text" class="form-control mt-2" id="guestName" placeholder="Name">
                    <input type="email" class="form-control mt-2" id="guestEmail" placeholder="Email">
                    <button class="btn btn-success mt-2" onclick="addGuest()">Add Guest</button>
                </div>
            </div>
        </div>
    </div>
    ''',
    'scripts': '''
    let conversation = [];
    
    function appendMessage(message, isUser) {
        const container = $('#chatContainer');
        container.append(`<div class="message ${isUser ? 'user-message' : 'bot-message'}">${message}</div>`);
        container.scrollTop(container[0].scrollHeight);
    }

    async function sendMessage() {
        const message = $('#messageInput').val();
        const temperature = $('.temperature-slider').val();
        conversation.push({ role: 'user', content: message });
        appendMessage(message, true);
        
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ messages: conversation, temperature })
            });
            const data = await response.json();
            if (data.message) {
                conversation.push({ role: 'assistant', content: data.message });
                appendMessage(data.message, false);
            }
        } catch (error) {
            console.error('Error:', error);
        }
        $('#messageInput').val('');
    }

    async function loadGuests() {
        const response = await fetch('/api/guests');
        const guests = await response.json();
        $('#guestList').html(guests.map(g => `
            <div class="d-flex justify-content-between mb-2">
                <div>${g.name} &lt;${g.email}&gt;</div>
                <button class="btn btn-sm btn-danger" onclick="deleteGuest(${g.id})">X</button>
            </div>
        `).join(''));
    }

    async function addGuest() {
        const name = $('#guestName').val();
        const email = $('#guestEmail').val();
        await fetch('/api/guests', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email })
        });
        loadGuests();
        $('#guestName, #guestEmail').val('');
    }

    async function deleteGuest(id) {
        await fetch(`/api/guests/${id}`, { method: 'DELETE' });
        loadGuests();
    }

    async function uploadFile() {
        const file = $('#fileUpload')[0].files[0];
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        if (data.summary) {
            $('#fileAnalysis').html(data.summary);
        }
    }

    $(document).ready(() => {
        loadGuests();
        $('#messageInput').keypress(e => e.which === 13 && sendMessage());
    });
    '''
}

# Routes
@app.route('/')
def home():
    return render_template_string(BASE_HTML % {
        'title': 'Home',
        'navbar': '',
        'content': '<h1>Welcome to ChatBot</h1><div class="mt-3"><a href="/login" class="btn btn-primary">Login</a></div>',
        'scripts': ''
    })

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        user = User.query.filter_by(username=data['username']).first()
        if user and check_password_hash(user.password_hash, data['password']):
            login_user(user)
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Invalid credentials'})
    return render_template_string(LOGIN_HTML)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.get_json()
        hashed_password = generate_password_hash(data['password'])
        new_user = User(username=data['username'], password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return jsonify({'success': True})
    return render_template_string(LOGIN_HTML.replace('Login', 'Sign Up').replace('submitForm(\'login\')', 'submitForm(\'signup\')'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template_string(DASHBOARD_HTML)

# API Endpoints
@app.route('/api/chat', methods=['POST'])
@login_required
def chat():
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=request.json['messages'],
            temperature=float(request.json.get('temperature', 0.7))
        return jsonify({'message': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/guests', methods=['GET', 'POST'])
@login_required
def guests():
    if request.method == 'GET':
        guests = Guest.query.filter_by(user_id=current_user.id).order_by(Guest.name).all()
        return jsonify([{'id': g.id, 'name': g.name, 'email': g.email} for g in guests])
    elif request.method == 'POST':
        data = request.get_json()
        new_guest = Guest(name=data['name'], email=data['email'], user_id=current_user.id)
        db.session.add(new_guest)
        db.session.commit()
        return jsonify({'message': 'Guest added'})

@app.route('/api/guests/<int:id>', methods=['DELETE'])
@login_required
def delete_guest(id):
    guest = Guest.query.filter_by(id=id, user_id=current_user.id).first()
    if guest:
        db.session.delete(guest)
        db.session.commit()
        return jsonify({'message': 'Guest deleted'})
    return jsonify({'error': 'Guest not found'}), 404

@app.route('/api/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file.stream)
        else:
            df = pd.read_excel(file.stream)
        
        return jsonify({
            'summary': df.describe().to_html(),
            'columns': df.columns.tolist(),
            'row_count': len(df)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Initialization
def create_app():
    with app.app_context():
        db.create_all()
    return app

if __name__ == '__main__':
    create_app().run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))