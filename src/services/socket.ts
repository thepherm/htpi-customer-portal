import { io, Socket } from 'socket.io-client';
import { getToken } from '../utils/auth';

class SocketService {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  
  connect(): Socket {
    if (this.socket?.connected) {
      return this.socket;
    }
    
    const token = getToken();
    if (!token) {
      throw new Error('No authentication token found');
    }
    
    this.socket = io(process.env.REACT_APP_GATEWAY_URL || 'http://localhost:8000', {
      auth: {
        token
      },
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: this.maxReconnectAttempts
    });
    
    this.setupEventHandlers();
    
    return this.socket;
  }
  
  private setupEventHandlers() {
    if (!this.socket) return;
    
    this.socket.on('connect', () => {
      console.log('Connected to gateway');
      this.reconnectAttempts = 0;
    });
    
    this.socket.on('disconnect', (reason) => {
      console.log('Disconnected from gateway:', reason);
    });
    
    this.socket.on('connect_error', (error) => {
      console.error('Connection error:', error.message);
      this.reconnectAttempts++;
      
      if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        console.error('Max reconnection attempts reached');
        this.disconnect();
      }
    });
    
    this.socket.on('error', (error) => {
      console.error('Socket error:', error);
    });
  }
  
  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }
  
  emit(event: string, data: any, callback?: (response: any) => void) {
    if (!this.socket?.connected) {
      console.error('Socket not connected');
      return;
    }
    
    if (callback) {
      this.socket.emit(event, data, callback);
    } else {
      this.socket.emit(event, data);
    }
  }
  
  on(event: string, handler: (data: any) => void) {
    if (!this.socket) {
      console.error('Socket not initialized');
      return;
    }
    
    this.socket.on(event, handler);
  }
  
  off(event: string, handler?: (data: any) => void) {
    if (!this.socket) return;
    
    if (handler) {
      this.socket.off(event, handler);
    } else {
      this.socket.off(event);
    }
  }
  
  isConnected(): boolean {
    return this.socket?.connected || false;
  }
}

export default new SocketService();