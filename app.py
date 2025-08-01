"""HTPI Customer Portal - Flask Application (Event-Driven)"""

import os
import logging
from datetime import timedelta
from flask import Flask, render_template, redirect, url_for, request, session
from flask_cors import CORS
from functools import wraps

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('ENV', 'development') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Enable CORS
CORS(app, supports_credentials=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gateway service URL for Socket.IO
GATEWAY_URL = os.environ.get('GATEWAY_URL', 'http://localhost:8000')

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Routes - Only serve pages, no API calls
@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login')
def login():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html', gateway_url=GATEWAY_URL)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', 
                         user=session.get('user'), 
                         gateway_url=GATEWAY_URL,
                         session_token=session.get('token'))

@app.route('/patients')
@login_required
def patients():
    return render_template('patients.html', 
                         user=session.get('user'), 
                         gateway_url=GATEWAY_URL,
                         session_token=session.get('token'))

# Session management endpoint (called from client-side after Socket.IO auth)
@app.route('/auth/session', methods=['POST'])
def set_session():
    try:
        data = request.get_json()
        if data.get('authenticated'):
            session['user'] = data.get('user')
            session['token'] = data.get('token')
            session.permanent = True
            return {'success': True}
        else:
            session.clear()
            return {'success': False}, 401
    except Exception as e:
        logger.error(f"Session error: {str(e)}")
        return {'success': False, 'error': 'Server error'}, 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('ENV') != 'production')