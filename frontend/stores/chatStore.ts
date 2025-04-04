'use client'

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { Message } from '@/types/chat'

interface ChatState {
  messages: Message[];
  isLoading: boolean;
  addMessage: (message: Message) => void;
  setMessages: (messages: Message[]) => void;
  setIsLoading: (isLoading: boolean) => void;
}

export const useChatStore = create<ChatState>()(
  persist(
    (set) => ({
      messages: [],
      isLoading: false,
      addMessage: (message) => set((state) => ({ 
        messages: [...state.messages, message] 
      })),
      setMessages: (messages) => set({ messages }),
      setIsLoading: (isLoading) => set({ isLoading }),
    }),
    {
      name: 'ashes-chat-storage',
    }
  )
)
