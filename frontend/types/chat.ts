export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
}

export interface ContextDocument {
  id: string;
  text: string;
  source: string;
  type: string;
  server?: string;
  score: number;
}

export interface ChatSession {
  id: string;
  title: string;
  messages: Message[];
  createdAt: Date;
  updatedAt: Date;
}

export interface ChatRequest {
  messages: Pick<Message, 'role' | 'content'>[];
  server?: string;
  temperature?: number;
}

export interface ChatResponse {
  id: string;
  response: string;
  context_documents: ContextDocument[];
  timestamp: string;
}
