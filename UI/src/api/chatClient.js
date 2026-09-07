// Talks to whatever HTTP endpoint fronts your MCP-backed chatbot.
// Point it at a real backend by setting VITE_CHAT_API_URL (e.g. in a .env file):
//   VITE_CHAT_API_URL=http://localhost:8000/chat
//
// Expected contract:
//   POST { message: string, history: [{ role: 'user'|'assistant', text: string }] }
//   ->   { reply: string }
// Adjust this file if your backend's shape differs.

const CHAT_API_URL = import.meta.env.VITE_CHAT_API_URL || '/api/chat';

// Session id per browser tab; the backend owns the conversation history.
const SESSION_ID = crypto.randomUUID();

export async function sendChatMessage(message) {
  const res = await fetch(CHAT_API_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: SESSION_ID, mensaje: message }),
  });

  if (!res.ok) {
    throw new Error(`Chat request failed with status ${res.status}`);
  }

  const data = await res.json();
  if (typeof data.respuesta !== 'string') {
    throw new Error('Unexpected chat response shape.');
  }
  return { reply: data.respuesta, tools: data.tools_usadas ?? [] };
}