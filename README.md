# HTPI Customer Portal

Flask-based customer portal for the HTPI healthcare system with full NATS integration.

## Features

- Multi-tenant support (customers can access multiple organizations)
- Patient viewing with real-time updates
- Claims tracking
- Insurance information
- 100% event-driven architecture via NATS
- Real-time updates via Socket.IO

## Architecture

This portal is a pure MVC layer with NO business logic:
- Receives Socket.IO events from browsers
- Forwards all requests to NATS
- Microservices handle all business logic
- Responses flow back through NATS to Socket.IO

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed flow.

## Deployment

### Required Environment Variables

```bash
# NATS Connection (REQUIRED - portal won't start without it)
NATS_URL=nats://htpi-nats.railway.internal:4222

# Flask Configuration
PORT=5000
SECRET_KEY=your-secret-key-here
ENV=production
```

### Railway Deployment

The portal requires these services to be running:
1. `htpi-nats` - Message broker
2. `htpi-auth-service` - For user authentication
3. `htpi-tenant-service` - For multi-tenant access
4. `htpi-patients-service` - For patient data
5. `htpi-mongodb-service` - For data persistence

## Architecture

The customer portal is designed to:
- Allow customers to view their healthcare data
- Access multiple tenant organizations they belong to
- View patient records, claims, and insurance information
- Receive real-time updates through Socket.IO

Unlike the admin portal, customers:
- Can only see tenants they have been granted access to
- Have read-only access to most data
- Cannot create or modify system-wide settings
- Have restricted access based on their role within each tenant

## Socket.IO Events

Customer-specific events:
- `auth:login` - User authentication
- `user:tenants:list` - Get user's accessible tenants
- `user:tenant:select` - Select active tenant
- `dashboard:subscribe` - Subscribe to dashboard updates
- `patients:subscribe` - Subscribe to patient list
- `patients:view` - View patient details

## Running Locally

```bash
pip install -r requirements.txt
python app.py
```

## Docker Deployment

```bash
docker build -t htpi-customer-portal .
docker run -p 5000:5000 -e STANDALONE_MODE=true htpi-customer-portal
```
