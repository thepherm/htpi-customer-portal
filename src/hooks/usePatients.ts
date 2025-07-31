import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useSocket } from './useSocket';
import { Patient, ApiResponse, PaginationParams, PaginatedResponse } from '../types';
import { useEffect } from 'react';

export const usePatients = (params?: PaginationParams) => {
  const { emit } = useSocket();
  const queryClient = useQueryClient();
  
  const query = useQuery({
    queryKey: ['patients', params],
    queryFn: async () => {
      return new Promise<PaginatedResponse<Patient>>((resolve, reject) => {
        emit('patient:list', params || {}, (response: ApiResponse<PaginatedResponse<Patient>>) => {
          if (response.success && response.data) {
            resolve(response.data);
          } else {
            reject(new Error(response.error?.message || 'Failed to fetch patients'));
          }
        });
      });
    }
  });
  
  // Subscribe to real-time updates
  useEffect(() => {
    const unsubscribe = emit('patient:subscribe', {}, (response: ApiResponse<any>) => {
      console.log('Subscribed to patient updates:', response);
    });
    
    const handlers = {
      patient_created: (patient: Patient) => {
        queryClient.invalidateQueries({ queryKey: ['patients'] });
      },
      patient_updated: (patient: Patient) => {
        queryClient.setQueryData(['patient', patient.id], patient);
        queryClient.invalidateQueries({ queryKey: ['patients'] });
      },
      patient_deleted: (data: { patient_id: string }) => {
        queryClient.removeQueries({ queryKey: ['patient', data.patient_id] });
        queryClient.invalidateQueries({ queryKey: ['patients'] });
      }
    };
    
    // Set up event handlers
    const cleanups = Object.entries(handlers).map(([event, handler]) => {
      const { on } = useSocket();
      return on(event, handler);
    });
    
    return () => {
      cleanups.forEach(cleanup => cleanup());
    };
  }, [emit, queryClient]);
  
  return query;
};

export const usePatient = (patientId: string) => {
  const { emit } = useSocket();
  
  return useQuery({
    queryKey: ['patient', patientId],
    queryFn: async () => {
      return new Promise<Patient>((resolve, reject) => {
        emit('patient:get', { patient_id: patientId }, (response: ApiResponse<Patient>) => {
          if (response.success && response.data) {
            resolve(response.data);
          } else {
            reject(new Error(response.error?.message || 'Failed to fetch patient'));
          }
        });
      });
    },
    enabled: !!patientId
  });
};

export const useCreatePatient = () => {
  const { emit } = useSocket();
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (patient: Omit<Patient, 'id'>) => {
      return new Promise<Patient>((resolve, reject) => {
        emit('patient:create', patient, (response: ApiResponse<Patient>) => {
          if (response.success && response.data) {
            resolve(response.data);
          } else {
            reject(new Error(response.error?.message || 'Failed to create patient'));
          }
        });
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patients'] });
    }
  });
};

export const useUpdatePatient = () => {
  const { emit } = useSocket();
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ id, ...updates }: Partial<Patient> & { id: string }) => {
      return new Promise<Patient>((resolve, reject) => {
        emit('patient:update', { patient_id: id, updates }, (response: ApiResponse<Patient>) => {
          if (response.success && response.data) {
            resolve(response.data);
          } else {
            reject(new Error(response.error?.message || 'Failed to update patient'));
          }
        });
      });
    },
    onSuccess: (patient) => {
      queryClient.setQueryData(['patient', patient.id], patient);
      queryClient.invalidateQueries({ queryKey: ['patients'] });
    }
  });
};

export const useDeletePatient = () => {
  const { emit } = useSocket();
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (patientId: string) => {
      return new Promise<void>((resolve, reject) => {
        emit('patient:delete', { patient_id: patientId }, (response: ApiResponse<any>) => {
          if (response.success) {
            resolve();
          } else {
            reject(new Error(response.error?.message || 'Failed to delete patient'));
          }
        });
      });
    },
    onSuccess: (_, patientId) => {
      queryClient.removeQueries({ queryKey: ['patient', patientId] });
      queryClient.invalidateQueries({ queryKey: ['patients'] });
    }
  });
};

export const useSearchPatients = () => {
  const { emit } = useSocket();
  
  return useMutation({
    mutationFn: async (query: string) => {
      return new Promise<Patient[]>((resolve, reject) => {
        emit('patient:search', { query }, (response: ApiResponse<Patient[]>) => {
          if (response.success && response.data) {
            resolve(response.data);
          } else {
            reject(new Error(response.error?.message || 'Failed to search patients'));
          }
        });
      });
    }
  });
};