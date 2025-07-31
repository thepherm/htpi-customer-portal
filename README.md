# HTPI Customer Portal

Modern React-based customer portal for the HTPI healthcare insurance claim processing system.

## Overview

The HTPI Customer Portal provides healthcare providers and billing staff with a user-friendly interface to:

- Manage patient information
- Verify insurance coverage
- Create and submit HCFA 1500 forms
- Track claim status
- View payment history
- Generate reports

## Features

- **Real-time Updates**: Socket.IO integration for instant updates
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Role-based Access**: Different views for providers, billers, and staff
- **Secure Authentication**: JWT-based authentication
- **Modern UI**: Material-UI components for a clean, professional interface

## Tech Stack

- React 18 with TypeScript
- Material-UI v5 for UI components
- Socket.IO Client for real-time communication
- React Query for server state management
- React Router v6 for navigation
- React Hook Form for form handling
- Date-fns for date manipulation

## Prerequisites

- Node.js 16+
- npm or yarn
- HTPI Gateway Service running

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/htpi-customer-portal.git
cd htpi-customer-portal
```

2. Install dependencies:
```bash
npm install
```

3. Create environment file:
```bash
cp .env.example .env
```

4. Update `.env` with your configuration:
```env
REACT_APP_GATEWAY_URL=http://localhost:8000
REACT_APP_API_URL=http://localhost:8000
```

## Development

Start the development server:
```bash
npm start
```

The app will open at [http://localhost:3000](http://localhost:3000)

## Building for Production

```bash
npm run build
```

This creates an optimized production build in the `build` folder.

## Deployment

### Deploy to Vercel
```bash
npm install -g vercel
vercel
```

### Deploy to Netlify
```bash
npm install -g netlify-cli
netlify deploy --prod --dir=build
```

### Deploy to Railway
```bash
railway login
railway link
railway up
```

## Project Structure

```
src/
├── components/       # Reusable UI components
├── contexts/        # React contexts (Auth, etc.)
├── hooks/           # Custom React hooks
├── pages/           # Page components
├── services/        # API and Socket.IO services
├── types/           # TypeScript type definitions
├── utils/           # Utility functions
├── App.tsx          # Main app component
└── index.tsx        # Entry point
```

## Available Pages

- **/login** - User authentication
- **/dashboard** - Main dashboard with statistics
- **/patients** - Patient management
- **/patients/new** - Create new patient
- **/patients/:id** - View patient details
- **/patients/:id/edit** - Edit patient
- **/insurance** - Insurance management
- **/forms** - HCFA form management
- **/forms/new** - Create new form
- **/forms/:id** - View/edit form
- **/claims** - Claim tracking
- **/claims/:id** - Claim details
- **/reports** - Reporting dashboard
- **/settings** - User settings
- **/profile** - User profile

## Authentication

The portal uses JWT tokens for authentication:

1. User logs in with email/password
2. Receives JWT token from gateway service
3. Token stored in localStorage
4. Token sent with all API requests
5. Token refreshed automatically

## Real-time Features

Socket.IO provides real-time updates for:

- New patient registrations
- Insurance verification results
- Claim status changes
- Payment notifications
- System alerts

## State Management

- **React Query**: Server state (patients, claims, etc.)
- **React Context**: Client state (auth, UI preferences)
- **Local Storage**: Auth tokens, user preferences

## Error Handling

- Network errors display user-friendly messages
- Form validation with helpful error messages
- Automatic retry for failed requests
- Offline detection and queuing

## Testing

Run tests:
```bash
npm test
```

Run tests with coverage:
```bash
npm test -- --coverage
```

## Code Quality

Lint code:
```bash
npm run lint
```

Format code:
```bash
npm run format
```

## Performance Optimization

- Code splitting for faster initial load
- Lazy loading of routes
- Image optimization
- Memoization of expensive operations
- Virtual scrolling for large lists

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Troubleshooting

### Connection Issues
- Verify gateway service is running
- Check REACT_APP_GATEWAY_URL in .env
- Look for CORS errors in console

### Authentication Problems
- Clear localStorage
- Check token expiration
- Verify JWT secret matches gateway

### Build Errors
- Delete node_modules and reinstall
- Clear npm/yarn cache
- Check for TypeScript errors

## Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create pull request

## License

MIT
