# HTPI Customer Portal

Flask-based customer portal for the HTPI healthcare system.

## Features

- Multi-tenant support (customers can access multiple organizations)
- Patient viewing
- Claims tracking
- Insurance information
- Real-time updates via Socket.IO

## Deployment

### Environment Variables

```bash
# Required
PORT=5000
SECRET_KEY=your-secret-key-here

# Standalone Mode (for testing without microservices)
STANDALONE_MODE=true

# Production Mode (when microservices are deployed)
STANDALONE_MODE=false
NATS_URL=nats://htpi-nats.railway.internal:4222
```

### Testing Credentials (Standalone Mode)

- Email: `demo@htpi.com`
- Password: `demo123`

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
