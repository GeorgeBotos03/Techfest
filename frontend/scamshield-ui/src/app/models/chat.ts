export type ChatRole = 'user' | 'assistant' | 'system';

export interface ChatMessage {
  id: string;
  role: ChatRole;
  text: string;
  ts: number;        // epoch ms
  pending?: boolean; // pt. “typing”
  error?: boolean;
}
