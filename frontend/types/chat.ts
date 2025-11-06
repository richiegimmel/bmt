export interface ChatSession {
  id: number;
  user_id: number;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ChatSessionListResponse {
  sessions: ChatSession[];
  total: number;
  page: number;
  page_size: number;
}

export interface Citation {
  document_id: number;
  document_title: string;
  chunk_index: number;
  page_number?: number;
  relevance_score: number;
}

export interface ChatMessage {
  id: number;
  session_id: number;
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  created_at: string;
}

export interface ChatMessageListResponse {
  messages: ChatMessage[];
  total: number;
}

export interface StreamChunk {
  type: 'content' | 'citation' | 'done' | 'error';
  content?: string;
  citation?: Citation;
  error?: string;
}

export interface ChatResponse {
  message: string;
  citations: Citation[];
}
