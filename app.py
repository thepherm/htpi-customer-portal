"""HTPI Customer Portal - Flask Application with Socket.IO Server"""

import os
import logging
import asyncio
from datetime import timedelta
from flask import Flask, render_template, redirect, url_for, request, session, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from functools import wraps
import nats
from nats.aio.client import Client as NATS
import json

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if os.environ.get('ENV') == 'development' else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('ENV', 'development') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Enable CORS
CORS(app, supports_credentials=True)

# Initialize Socket.IO
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)

# NATS configuration
NATS_URL = os.environ.get('NATS_URL', 'nats://localhost:4222')
STANDALONE_MODE = os.environ.get('STANDALONE_MODE', 'true').lower() == 'true'
nc = None  # NATS client will be initialized on startup

# Connected clients tracking
connected_clients = {}

# Log startup mode
if STANDALONE_MODE:
    logger.warning("Running in STANDALONE MODE - No NATS/microservices required")
    logger.warning("Set STANDALONE_MODE=false when NATS and services are deployed")
else:
    logger.info("Running in MICROSERVICES MODE - Connecting to NATS")

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Tenant context decorator
def tenant_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if 'current_tenant' not in session:
            return redirect(url_for('select_tenant'))
        return f(*args, **kwargs)
    return decorated_function

# Routes - Only serve pages
@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login')
def login():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/select-tenant')
@login_required
def select_tenant():
    return render_template('select_tenant.html',
                         user=session.get('user'))

@app.route('/switch-tenant/<tenant_id>')
@login_required
def switch_tenant(tenant_id):
    # This will be updated via Socket.IO
    return redirect(url_for('select_tenant'))

@app.route('/dashboard')
@tenant_required
def dashboard():
    # Mock stats for development
    mock_stats = {
        'appointments_today': 5,
        'upcoming_appointments': 12,
        'recent_claims': 3,
        'pending_authorizations': 2
    }
    
    return render_template('dashboard.html', 
                         user=session.get('user'), 
                         tenant=session.get('current_tenant'),
                         stats=mock_stats)

@app.route('/patients')
@tenant_required
def patients():
    return render_template('patients.html', 
                         user=session.get('user'), 
                         tenant=session.get('current_tenant'))

# Session management endpoint (called from client-side after Socket.IO auth)
@app.route('/auth/session', methods=['POST'])
def set_session():
    try:
        data = request.get_json()
        if data.get('authenticated'):
            session['user'] = data.get('user')
            session['token'] = data.get('token')
            if data.get('current_tenant'):
                session['current_tenant'] = data.get('current_tenant')
            session.permanent = True
            logger.info(f"Session created for user: {session['user'].get('email')}")
            return jsonify({'success': True})
        else:
            session.clear()
            return jsonify({'success': False}), 401
    except Exception as e:
        logger.error(f"Session error: {str(e)}")
        return jsonify({'success': False, 'error': 'Server error'}), 500

# Socket.IO event handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    client_id = request.sid
    logger.info(f"Client connected: {client_id}")
    connected_clients[client_id] = {
        'sid': client_id,
        'authenticated': False
    }
    emit('connected', {'message': 'Connected to customer portal'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    client_id = request.sid
    logger.info(f"Client disconnected: {client_id}")
    if client_id in connected_clients:
        del connected_clients[client_id]

@socketio.on('auth:login')
def handle_login(data):
    """Handle login authentication"""
    client_id = request.sid
    email = data.get('email')
    password = data.get('password')
    
    logger.info(f"Login attempt for email: {email}")
    
    try:
        if STANDALONE_MODE:
            # Standalone mode - use mock authentication
            if email == 'demo@htpi.com' and password == 'demo123':
                # Create mock user
                user_data = {
                    'id': 'user-001',
                    'email': email,
                    'name': 'Demo User',
                    'role': 'user'
                }
                token = 'dev-token-' + os.urandom(16).hex()
                
                # Update connected client info
                connected_clients[client_id]['authenticated'] = True
                connected_clients[client_id]['user'] = user_data
                connected_clients[client_id]['token'] = token
                
                # Join user-specific room
                join_room(f"user:{user_data['id']}")
                
                emit('auth:login:response', {
                    'success': True,
                    'user': user_data,
                    'token': token
                })
                
                logger.info(f"[STANDALONE] User authenticated: {email}")
            else:
                emit('auth:login:response', {
                    'success': False,
                    'error': 'Invalid credentials. Use demo@htpi.com / demo123'
                })
        else:
            # Production mode - NATS auth
            if nc and nc.is_connected:
                auth_request = {
                    'email': email,
                    'password': password,
                    'portal': 'customer'
                }
                
                # In sync mode, we can't use await
                logger.info("NATS auth not available in sync mode")
                emit('auth:login:response', {
                    'success': False,
                    'error': 'Authentication service temporarily unavailable'
                })
            else:
                logger.error("NATS not connected")
                emit('auth:login:response', {
                    'success': False,
                    'error': 'Authentication service unavailable'
                })
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        emit('auth:login:response', {
            'success': False,
            'error': 'Authentication failed'
        })

@socketio.on('user:tenants:list')
def handle_list_tenants():
    """Get list of tenants for authenticated user"""
    client_id = request.sid
    client = connected_clients.get(client_id)
    
    if not client or not client.get('authenticated'):
        emit('error', {'message': 'Not authenticated'})
        return
    
    try:
        if STANDALONE_MODE:
            # Mock tenants for demo user
            mock_tenants = [
                {
                    'id': 'tenant-001',
                    'name': 'Demo Clinic',
                    'domain': 'demo.htpi.com',
                    'status': 'Active',
                    'role': 'User'
                },
                {
                    'id': 'tenant-002',
                    'name': 'Test Hospital',
                    'domain': 'test.htpi.com',
                    'status': 'Active',
                    'role': 'Viewer'
                }
            ]
            
            emit('user:tenants:list:response', {
                'tenants': mock_tenants
            })
            
            logger.info(f"[STANDALONE] Sent mock tenants to user")
        else:
            # Production mode
            user_id = client['user']['id']
            if nc and nc.is_connected:
                # In sync mode, can't use await
                logger.info("NATS tenant list not available in sync mode")
                emit('user:tenants:list:response', {
                    'tenants': []
                })
            else:
                emit('error', {'message': 'Service unavailable'})
    except Exception as e:
        logger.error(f"Error listing tenants: {str(e)}")
        emit('error', {'message': 'Failed to load tenants'})

@socketio.on('user:tenant:select')
def handle_select_tenant(data):
    """Handle tenant selection"""
    client_id = request.sid
    client = connected_clients.get(client_id)
    tenant_id = data.get('tenantId')
    
    if not client or not client.get('authenticated'):
        emit('error', {'message': 'Not authenticated'})
        return
    
    try:
        # Verify user has access to this tenant
        if nc and nc.is_connected:
            verify_request = {
                'user_id': client['user']['id'],
                'tenant_id': tenant_id
            }
            
            response = await nc.request('tenants.verify_access', 
                                      json.dumps(verify_request).encode(), 
                                      timeout=5)
            result = json.loads(response.data.decode())
            
            if result.get('has_access'):
                # Join tenant-specific room
                join_room(f"tenant:{tenant_id}")
                connected_clients[client_id]['tenant_id'] = tenant_id
                
                emit('user:tenant:select:response', {
                    'success': True,
                    'tenant_id': tenant_id
                })
                
                logger.info(f"User {client['user']['email']} selected tenant {tenant_id}")
            else:
                emit('user:tenant:select:response', {
                    'success': False,
                    'error': 'Access denied to this tenant'
                })
    except Exception as e:
        logger.error(f"Error selecting tenant: {str(e)}")
        emit('user:tenant:select:response', {
            'success': False,
            'error': 'Failed to select tenant'
        })

@socketio.on('dashboard:subscribe')
def handle_dashboard_subscribe(data):
    """Subscribe to dashboard updates for a tenant"""
    client_id = request.sid
    client = connected_clients.get(client_id)
    tenant_id = data.get('tenantId')
    
    if not client or not client.get('authenticated'):
        emit('error', {'message': 'Not authenticated'})
        return
    
    try:
        # Join dashboard room for this tenant
        room = f"dashboard:{tenant_id}"
        join_room(room)
        
        # Request initial dashboard data via NATS
        if nc and nc.is_connected:
            request_data = {
                'tenant_id': tenant_id,
                'user_id': client['user']['id']
            }
            
            response = await nc.request('dashboard.get_stats', 
                                      json.dumps(request_data).encode(), 
                                      timeout=5)
            stats = json.loads(response.data.decode())
            
            emit('dashboard:stats', stats)
            
            # Get recent activity
            activity_response = await nc.request('dashboard.get_activity', 
                                               json.dumps(request_data).encode(), 
                                               timeout=5)
            activities = json.loads(activity_response.data.decode())
            
            emit('dashboard:activity', activities.get('activities', []))
            
            logger.info(f"User subscribed to dashboard for tenant {tenant_id}")
    except Exception as e:
        logger.error(f"Error subscribing to dashboard: {str(e)}")
        emit('error', {'message': 'Failed to load dashboard data'})

@socketio.on('patients:subscribe')
def handle_patients_subscribe(data):
    """Subscribe to patient updates for a tenant"""
    client_id = request.sid
    client = connected_clients.get(client_id)
    tenant_id = data.get('tenantId')
    
    if not client or not client.get('authenticated'):
        emit('error', {'message': 'Not authenticated'})
        return
    
    try:
        # Join patients room for this tenant
        room = f"patients:{tenant_id}"
        join_room(room)
        
        # Request patient list via NATS
        if nc and nc.is_connected:
            request_data = {
                'tenant_id': tenant_id,
                'user_id': client['user']['id']
            }
            
            response = await nc.request('patients.list', 
                                      json.dumps(request_data).encode(), 
                                      timeout=5)
            patients = json.loads(response.data.decode())
            
            emit('patients:list', patients.get('patients', []))
            
            logger.info(f"User subscribed to patients for tenant {tenant_id}")
    except Exception as e:
        logger.error(f"Error subscribing to patients: {str(e)}")
        emit('error', {'message': 'Failed to load patients'})

@socketio.on('patients:add')
def handle_add_patient(data):
    """Add a new patient"""
    client_id = request.sid
    client = connected_clients.get(client_id)
    
    if not client or not client.get('authenticated'):
        emit('error', {'message': 'Not authenticated'})
        return
    
    try:
        # Add user context to patient data
        patient_data = {
            **data,
            'created_by': client['user']['id'],
            'created_by_name': client['user']['name']
        }
        
        # Send to patient service via NATS
        if nc and nc.is_connected:
            response = await nc.request('patients.create', 
                                      json.dumps(patient_data).encode(), 
                                      timeout=5)
            result = json.loads(response.data.decode())
            
            if result.get('success'):
                # Broadcast to all users in the tenant
                socketio.emit('patients:new', result['patient'], 
                            room=f"patients:{data['tenantId']}")
                
                emit('patients:add:response', {
                    'success': True,
                    'patient': result['patient']
                })
            else:
                emit('patients:add:response', {
                    'success': False,
                    'error': result.get('error', 'Failed to add patient')
                })
    except Exception as e:
        logger.error(f"Error adding patient: {str(e)}")
        emit('patients:add:response', {
            'success': False,
            'error': 'Failed to add patient'
        })

# NATS message handlers
async def handle_dashboard_update(msg):
    """Handle dashboard updates from NATS"""
    try:
        data = json.loads(msg.data.decode())
        tenant_id = data.get('tenant_id')
        update_type = data.get('type')
        
        if update_type == 'stats':
            socketio.emit('dashboard:stat:update', data['stats'], 
                        room=f"dashboard:{tenant_id}")
        elif update_type == 'activity':
            socketio.emit('dashboard:activity:new', data['activity'], 
                        room=f"dashboard:{tenant_id}")
    except Exception as e:
        logger.error(f"Error handling dashboard update: {str(e)}")

async def handle_patient_update(msg):
    """Handle patient updates from NATS"""
    try:
        data = json.loads(msg.data.decode())
        tenant_id = data.get('tenant_id')
        update_type = data.get('type')
        
        if update_type == 'update':
            socketio.emit('patients:update', data['patient'], 
                        room=f"patients:{tenant_id}")
        elif update_type == 'delete':
            socketio.emit('patients:delete', data['patient_id'], 
                        room=f"patients:{tenant_id}")
    except Exception as e:
        logger.error(f"Error handling patient update: {str(e)}")

# Initialize NATS connection
async def init_nats():
    """Initialize NATS connection and subscriptions"""
    global nc
    
    try:
        nc = await nats.connect(NATS_URL)
        logger.info(f"Connected to NATS at {NATS_URL}")
        
        # Subscribe to relevant topics
        await nc.subscribe("customer.dashboard.updates", cb=handle_dashboard_update)
        await nc.subscribe("customer.patients.updates", cb=handle_patient_update)
        
        logger.info("NATS subscriptions established")
    except Exception as e:
        logger.error(f"Failed to connect to NATS: {str(e)}")

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Only initialize NATS if not in standalone mode
    if not STANDALONE_MODE:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(init_nats())
        except Exception as e:
            logger.error(f"NATS initialization failed: {str(e)}")
            logger.warning("Starting without NATS connection")
    else:
        logger.info("Skipping NATS initialization in STANDALONE MODE")
    
    # Start Flask-SocketIO server
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting customer portal on port {port}")
    socketio.run(app, host='0.0.0.0', port=port, 
                 debug=os.environ.get('ENV') != 'production')