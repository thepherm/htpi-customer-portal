"""HTPI Customer Portal - Flask Application with Socket.IO Server"""

import os
import logging
import asyncio
from datetime import datetime, timedelta
from flask import Flask, render_template, redirect, url_for, request, session, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from functools import wraps
import nats
from nats.aio.client import Client as NATS
import json
import uuid

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

# Initialize Socket.IO with async mode
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True, async_mode='threading')

# NATS configuration
NATS_URL = os.environ.get('NATS_URL', 'nats://localhost:4222')
nc = None  # NATS client will be initialized on startup

# Connected clients tracking
connected_clients = {}

# NATS subjects mapping
NATS_SUBJECTS = {
    # Auth service
    'auth.login': 'htpi.auth.login',
    'auth.verify': 'htpi.auth.verify',
    
    # Tenant service
    'tenant.list.for.user': 'htpi.tenant.list.for.user',
    'tenant.verify.access': 'htpi.tenant.verify.access',
    
    # Patient service
    'patient.list': 'htpi.patient.list',
    'patient.get': 'htpi.patient.get',
    
    # Dashboard service
    'dashboard.get.stats': 'htpi.dashboard.get.stats',
    'dashboard.get.activity': 'htpi.dashboard.get.activity',
    
    # Insurance service
    'insurance.list.for.patient': 'htpi.insurance.list.for.patient',
    
    # Claims service
    'claims.list.for.patient': 'htpi.claims.list.for.patient',
    'claims.get': 'htpi.claims.get'
}

def publish_to_nats(subject_key, data):
    """
    Publish message to NATS
    This is a placeholder for sync mode - in production this would be async
    """
    if not nc or not nc.is_connected:
        logger.warning(f"NATS not connected, cannot publish to {subject_key}")
        return None
    
    try:
        subject = NATS_SUBJECTS.get(subject_key)
        if not subject:
            logger.error(f"Unknown NATS subject key: {subject_key}")
            return None
        
        message = json.dumps(data).encode()
        logger.info(f"Publishing to NATS {subject}: {data}")
        
        # In production, this would be async
        # response = await nc.request(subject, message, timeout=30)
        # return json.loads(response.data.decode())
        
        return None  # Sync mode limitation
    except Exception as e:
        logger.error(f"Error publishing to NATS: {str(e)}")
        return None

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
    return render_template('dashboard.html', 
                         user=session.get('user'), 
                         tenant=session.get('current_tenant'))

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
    """Forward login authentication to NATS"""
    client_id = request.sid
    email = data.get('email')
    password = data.get('password')
    
    logger.info(f"Login attempt for email: {email}")
    
    try:
        # Add context to auth request
        auth_message = {
            'email': email,
            'password': password,
            'portal': 'customer',
            'clientId': client_id,
            'requestId': data.get('requestId', str(uuid.uuid4())),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Publish to NATS
        result = publish_to_nats('auth.login', auth_message)
        
        if result:
            # Forward NATS response to client
            if result.get('success'):
                user_data = result.get('user')
                token = result.get('token')
                
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
                
                logger.info(f"User authenticated via NATS: {email}")
            else:
                emit('auth:login:response', {
                    'success': False,
                    'error': result.get('error', 'Invalid credentials')
                })
        else:
            # NATS not available
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
    """Forward tenant list request to NATS"""
    client_id = request.sid
    client = connected_clients.get(client_id)
    
    if not client or not client.get('authenticated'):
        emit('error', {'message': 'Not authenticated'})
        return
    
    try:
        # Publish to NATS to get user's tenants
        nats_message = {
            'userId': client['user']['id'],
            'userEmail': client['user']['email'],
            'clientId': client_id,
            'requestType': 'list',
            'responseChannel': f"customer.tenants.response.{client_id}"
        }
        
        # Publish to NATS
        result = publish_to_nats('tenant.list.for.user', nats_message)
        
        if result:
            # Forward NATS response
            emit('user:tenants:list:response', {
                'tenants': result.get('tenants', [])
            })
        else:
            # NATS not available - send empty list
            emit('user:tenants:list:response', {
                'tenants': [],
                'error': 'Service temporarily unavailable'
            })
        
        logger.info(f"User {client['user']['id']} requested tenant list")
        
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

# NATS Response Handlers
async def handle_auth_response(msg):
    """Handle authentication responses from NATS"""
    try:
        data = json.loads(msg.data.decode())
        client_id = data.get('clientId')
        
        if data.get('success'):
            user_data = data.get('user')
            token = data.get('token')
            
            # Update connected client
            if client_id in connected_clients:
                connected_clients[client_id]['authenticated'] = True
                connected_clients[client_id]['user'] = user_data
                connected_clients[client_id]['token'] = token
            
            # Send response to specific client
            socketio.emit('auth:login:response', {
                'success': True,
                'user': user_data,
                'token': token
            }, room=client_id)
        else:
            socketio.emit('auth:login:response', {
                'success': False,
                'error': data.get('error', 'Authentication failed')
            }, room=client_id)
            
    except Exception as e:
        logger.error(f"Error handling auth response: {str(e)}")

async def handle_tenant_response(msg):
    """Handle tenant list responses from NATS"""
    try:
        data = json.loads(msg.data.decode())
        client_id = data.get('clientId')
        
        socketio.emit('user:tenants:list:response', {
            'tenants': data.get('tenants', [])
        }, room=client_id)
        
    except Exception as e:
        logger.error(f"Error handling tenant response: {str(e)}")

async def handle_patient_response(msg):
    """Handle patient responses from NATS"""
    try:
        data = json.loads(msg.data.decode())
        response_type = data.get('responseType')
        
        if response_type == 'list':
            socketio.emit('patients:list', {
                'patients': data.get('patients', [])
            }, room=f"patients:{data['tenantId']}")
            
        elif response_type == 'created':
            # Notify specific client
            socketio.emit(f"patients:add:response:{data['requestId']}", {
                'success': True,
                'patient': data['patient']
            }, room=data.get('clientId'))
            
            # Broadcast to all users in tenant
            socketio.emit('patients:new', data['patient'], 
                        room=f"patients:{data['tenantId']}")
            
    except Exception as e:
        logger.error(f"Error handling patient response: {str(e)}")

async def handle_dashboard_update(msg):
    """Handle dashboard updates from NATS"""
    try:
        data = json.loads(msg.data.decode())
        tenant_id = data.get('tenantId')
        update_type = data.get('type')
        
        if update_type == 'stats':
            socketio.emit('dashboard:stats:update', data['stats'], 
                        room=f"dashboard:{tenant_id}")
        elif update_type == 'activity':
            socketio.emit('dashboard:activity:new', data['activity'], 
                        room=f"dashboard:{tenant_id}")
    except Exception as e:
        logger.error(f"Error handling dashboard update: {str(e)}")

# Initialize NATS connection
async def init_nats():
    """Initialize NATS connection and subscriptions"""
    global nc
    
    try:
        nc = await nats.connect(NATS_URL)
        logger.info(f"Connected to NATS at {NATS_URL}")
        
        # Subscribe to response channels from services
        await nc.subscribe("customer.auth.response.*", cb=handle_auth_response)
        await nc.subscribe("customer.tenants.response.*", cb=handle_tenant_response)
        await nc.subscribe("customer.patients.response.*", cb=handle_patient_response)
        await nc.subscribe("customer.dashboard.response.*", cb=handle_dashboard_update)
        
        # Subscribe to broadcast channels
        await nc.subscribe("customer.broadcast.dashboard.*", cb=handle_dashboard_update)
        await nc.subscribe("customer.broadcast.patients.*", cb=handle_patient_response)
        
        logger.info("Customer portal NATS subscriptions established")
    except Exception as e:
        logger.error(f"Failed to connect to NATS: {str(e)}")
        raise

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Run NATS initialization in event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(init_nats())
        logger.info("NATS connection established successfully")
    except Exception as e:
        logger.error(f"NATS initialization failed: {str(e)}")
        logger.error("Customer portal requires NATS to function properly")
        # Exit if NATS is not available
        import sys
        sys.exit(1)
    
    # Start Flask-SocketIO server
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting customer portal on port {port}")
    socketio.run(app, host='0.0.0.0', port=port, 
                 debug=os.environ.get('ENV') != 'production')