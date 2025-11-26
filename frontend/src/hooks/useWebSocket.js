import { useEffect, useRef, useState } from 'react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
const WS_URL = BACKEND_URL.replace('http://', 'ws://').replace('https://', 'wss://');

export const useWebSocket = (onMessage) => {
  const ws = useRef(null);
  const [isConnected, setIsConnected] = useState(false);
  const reconnectTimeout = useRef(null);
  const reconnectAttempts = useRef(0);

  const connect = () => {
    try {
      ws.current = new WebSocket(`${WS_URL}/ws`);

      ws.current.onopen = () => {
        console.log('✅ WebSocket conectado');
        setIsConnected(true);
        reconnectAttempts.current = 0;
      };

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('📨 Mensagem WebSocket recebida:', data);
          if (onMessage) {
            onMessage(data);
          }
        } catch (error) {
          console.error('Erro ao processar mensagem WebSocket:', error);
        }
      };

      ws.current.onerror = (error) => {
        console.error('❌ Erro no WebSocket:', error);
      };

      ws.current.onclose = () => {
        console.log('🔌 WebSocket desconectado');
        setIsConnected(false);

        // Tentar reconectar com backoff exponencial
        if (reconnectAttempts.current < 10) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
          console.log(`🔄 Tentando reconectar em ${delay / 1000}s...`);
          
          reconnectTimeout.current = setTimeout(() => {
            reconnectAttempts.current++;
            connect();
          }, delay);
        }
      };
    } catch (error) {
      console.error('Erro ao conectar WebSocket:', error);
    }
  };

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
      if (ws.current) {
        ws.current.close();
      }
    };
  }, []);

  const sendMessage = (message) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket não está conectado');
    }
  };

  return { isConnected, sendMessage };
};
