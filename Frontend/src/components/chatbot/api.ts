import { apiClient } from '@/infrastructure/api/client';
import { ChatRequest, ChatResponse } from './types';

export const chatbotApi = {
  /**
   * Send a message to the chatbot
   */
  chat: async (request: ChatRequest): Promise<ChatResponse> => {
    const response = await apiClient.post<ChatResponse>('/chat', request);
    return response.data;
  },

  /**
   * Clear a chat session
   */
  clearSession: async (sessionId: string): Promise<void> => {
    await apiClient.delete(`/chat/session/${sessionId}`);
  },

  /**
   * Get document count in knowledge base
   */
  getDocumentCount: async (): Promise<{ chunk_count: number }> => {
    const response = await apiClient.get<{ chunk_count: number }>('/chat/documents/count');
    return response.data;
  },
};

