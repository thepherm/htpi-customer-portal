# HTPI Customer Portal Architecture

## Overview

The Customer Portal is a **pure event-driven MVC layer** that communicates exclusively through NATS. It has NO business logic and acts as a bridge between:
- **Frontend**: Socket.IO events from customer browsers
- **Backend**: NATS messages to/from microservices

## Architecture Flow

```
Browser → Socket.IO → Customer Portal → NATS → Microservices → MongoDB
                            ↑                          ↓
                            ← ← ← ← ← ← ← ← ← ← ← ← ← ←
```

## NATS Integration

### Publishing Subjects
- `htpi.auth.login` - User authentication
- `htpi.tenant.list.for.user` - Get user's accessible tenants
- `htpi.tenant.verify.access` - Verify user access to tenant
- `htpi.patient.list` - Get patient list
- `htpi.dashboard.get.stats` - Get dashboard statistics
- `htpi.insurance.list.for.patient` - Get patient's insurance
- `htpi.claims.list.for.patient` - Get patient's claims

### Subscription Channels
- `customer.auth.response.*` - Authentication responses
- `customer.tenants.response.*` - Tenant list responses
- `customer.patients.response.*` - Patient data responses
- `customer.dashboard.response.*` - Dashboard data responses
- `customer.broadcast.dashboard.*` - Real-time dashboard updates
- `customer.broadcast.patients.*` - Real-time patient updates

## Key Differences from Admin Portal

1. **Access Control**: 
   - Customers can only see tenants they've been granted access to
   - All requests include user context for authorization

2. **Limited Actions**:
   - Mostly read-only operations
   - Can view but not create/modify most data
   - Can add their own patients in some cases

3. **Filtered Data**:
   - Services filter responses based on user permissions
   - Only see data relevant to their role in each tenant

## Example Flow: User Login

### 1. Browser sends Socket.IO event:
```javascript
socket.emit('auth:login', {
    email: 'user@example.com',
    password: 'password123'
});
```

### 2. Customer Portal forwards to NATS:
```python
@socketio.on('auth:login')
def handle_login(data):
    # Only forward to NATS, no business logic
    auth_message = {
        'email': data['email'],
        'password': data['password'],
        'portal': 'customer',  # Important: identifies customer portal
        'clientId': request.sid,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    publish_to_nats('auth.login', auth_message)
```

### 3. Auth Service handles authentication:
```python
# In htpi-auth-service
async def handle_customer_login(msg):
    data = json.loads(msg.data.decode())
    
    # Authenticate user
    user = authenticate(data['email'], data['password'])
    
    # Check portal access
    if user and user.can_access_customer_portal:
        # Generate token
        token = generate_jwt(user)
        
        # Respond to customer portal
        await publish('customer.auth.response.' + data['clientId'], {
            'success': True,
            'user': user.to_dict(),
            'token': token
        })
```

### 4. Customer Portal receives response and emits to browser:
```python
async def handle_auth_response(msg):
    data = json.loads(msg.data.decode())
    
    # Forward to specific client
    socketio.emit('auth:login:response', {
        'success': data['success'],
        'user': data.get('user'),
        'token': data.get('token')
    }, room=data['clientId'])
```

## Multi-Tenant Access

Unlike the admin portal where admins can see all tenants, customers:
1. Only see tenants where they have been assigned access
2. Must select a tenant before accessing data
3. All subsequent requests are filtered by selected tenant + user permissions

## Security Considerations

1. **Portal Separation**: Customer portal has its own Socket.IO server
2. **Event Isolation**: Customer events use different NATS subjects
3. **Permission Checking**: Every service validates user access
4. **No Cross-Portal Events**: Admin and customer portals can't see each other's events

## Required Environment Variables

```bash
# NATS Connection (Required)
NATS_URL=nats://htpi-nats.railway.internal:4222

# Flask Configuration
SECRET_KEY=your-secure-secret-key
PORT=5000
ENV=production
```

## Deployment Notes

1. **NATS is Required**: Portal will exit if NATS is not available
2. **No Standalone Mode**: Unlike development, production requires full microservice stack
3. **Session Management**: Uses Flask sessions for maintaining user state
4. **Real-time Updates**: Socket.IO rooms isolate tenant/user data