import React from 'react';
import {
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  CardActions,
  Button,
  LinearProgress
} from '@mui/material';
import {
  People as PeopleIcon,
  Assignment as AssignmentIcon,
  Description as DescriptionIcon,
  TrendingUp as TrendingUpIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
  action?: () => void;
  actionText?: string;
}

const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  icon,
  color,
  action,
  actionText
}) => (
  <Card>
    <CardContent>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <Box
          sx={{
            backgroundColor: color,
            borderRadius: 2,
            p: 1,
            mr: 2,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
        >
          {icon}
        </Box>
        <Typography color="text.secondary" gutterBottom>
          {title}
        </Typography>
      </Box>
      <Typography variant="h4" component="div">
        {value}
      </Typography>
    </CardContent>
    {action && actionText && (
      <CardActions>
        <Button size="small" onClick={action}>
          {actionText}
        </Button>
      </CardActions>
    )}
  </Card>
);

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  
  // Mock data - in real app, this would come from API
  const stats = {
    totalPatients: 156,
    activeInsurance: 142,
    pendingForms: 8,
    submittedClaims: 23,
    acceptedClaims: 19,
    rejectedClaims: 2
  };
  
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Welcome back, {user?.first_name}!
      </Typography>
      
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Patients"
            value={stats.totalPatients}
            icon={<PeopleIcon sx={{ color: 'white' }} />}
            color="#1976d2"
            action={() => navigate('/patients')}
            actionText="View Patients"
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Active Insurance"
            value={stats.activeInsurance}
            icon={<AssignmentIcon sx={{ color: 'white' }} />}
            color="#388e3c"
            action={() => navigate('/insurance')}
            actionText="Manage Insurance"
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Pending Forms"
            value={stats.pendingForms}
            icon={<DescriptionIcon sx={{ color: 'white' }} />}
            color="#f57c00"
            action={() => navigate('/forms')}
            actionText="Complete Forms"
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Submitted Claims"
            value={stats.submittedClaims}
            icon={<TrendingUpIcon sx={{ color: 'white' }} />}
            color="#7b1fa2"
            action={() => navigate('/claims')}
            actionText="View Claims"
          />
        </Grid>
      </Grid>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Recent Activity
            </Typography>
            
            <Box sx={{ mt: 2 }}>
              {/* Recent activity items */}
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <CheckCircleIcon sx={{ color: 'success.main', mr: 2 }} />
                <Box sx={{ flex: 1 }}>
                  <Typography variant="body1">
                    Claim #CLM-2024-001 approved
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    2 hours ago
                  </Typography>
                </Box>
              </Box>
              
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <WarningIcon sx={{ color: 'warning.main', mr: 2 }} />
                <Box sx={{ flex: 1 }}>
                  <Typography variant="body1">
                    Insurance verification required for John Doe
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    5 hours ago
                  </Typography>
                </Box>
              </Box>
              
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <PeopleIcon sx={{ color: 'primary.main', mr: 2 }} />
                <Box sx={{ flex: 1 }}>
                  <Typography variant="body1">
                    New patient registered: Jane Smith
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Yesterday
                  </Typography>
                </Box>
              </Box>
            </Box>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Claim Success Rate
            </Typography>
            
            <Box sx={{ mt: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2">Accepted</Typography>
                <Typography variant="body2">
                  {Math.round((stats.acceptedClaims / stats.submittedClaims) * 100)}%
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={(stats.acceptedClaims / stats.submittedClaims) * 100}
                sx={{ mb: 3, height: 8, borderRadius: 4 }}
              />
              
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Claims Summary
              </Typography>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
                <Typography variant="body2">Accepted:</Typography>
                <Typography variant="body2" color="success.main">
                  {stats.acceptedClaims}
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
                <Typography variant="body2">Rejected:</Typography>
                <Typography variant="body2" color="error.main">
                  {stats.rejectedClaims}
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
                <Typography variant="body2">Pending:</Typography>
                <Typography variant="body2" color="warning.main">
                  {stats.submittedClaims - stats.acceptedClaims - stats.rejectedClaims}
                </Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;