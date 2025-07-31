import { useEffect, useCallback } from 'react';
import socketService from '../services/socket';
import { useAuth } from '../contexts/AuthContext';

interface UseSocketOptions {
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: any) => void;
}

export const useSocket = (options?: UseSocketOptions) => {
  const { isAuthenticated } = useAuth();
  
  useEffect(() => {
    if (isAuthenticated) {
      try {
        const socket = socketService.connect();
        
        if (options?.onConnect) {
          socket.on('connect', options.onConnect);
        }
        
        if (options?.onDisconnect) {
          socket.on('disconnect', options.onDisconnect);
        }
        
        if (options?.onError) {
          socket.on('error', options.onError);
        }
        
        return () => {
          if (options?.onConnect) {
            socket.off('connect', options.onConnect);
          }
          if (options?.onDisconnect) {
            socket.off('disconnect', options.onDisconnect);
          }
          if (options?.onError) {
            socket.off('error', options.onError);
          }
        };
      } catch (error) {
        console.error('Socket connection error:', error);
      }
    }
  }, [isAuthenticated, options]);
  
  const emit = useCallback((event: string, data: any, callback?: (response: any) => void) => {
    socketService.emit(event, data, callback);
  }, []);
  
  const on = useCallback((event: string, handler: (data: any) => void) => {
    socketService.on(event, handler);
    
    return () => {
      socketService.off(event, handler);
    };
  }, []);
  
  const off = useCallback((event: string, handler?: (data: any) => void) => {
    socketService.off(event, handler);
  }, []);
  
  return {
    emit,
    on,
    off,
    isConnected: socketService.isConnected()
  };
};