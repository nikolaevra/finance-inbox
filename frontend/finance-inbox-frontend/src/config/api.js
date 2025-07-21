// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const FRONTEND_URL = import.meta.env.VITE_FRONTEND_URL || 'http://localhost:5173'

export const API_ENDPOINTS = {
  // Auth endpoints
  AUTH: {
    LOGIN: `${API_BASE_URL}/auth/login`,
    REFRESH: `${API_BASE_URL}/auth/refresh`,
    LOGOUT: `${API_BASE_URL}/auth/logout`,
    ME: `${API_BASE_URL}/auth/me`,
    PROFILE: `${API_BASE_URL}/auth/profile`,
  },
  
  // Inbox endpoints
  INBOX: {
    LIST: `${API_BASE_URL}/inbox/`,           // Get threads (new)
    EMAILS: `${API_BASE_URL}/inbox/emails`,   // Get individual emails (legacy)
    SYNC: `${API_BASE_URL}/inbox/emails/sync`,
    EMAIL: (emailId) => `${API_BASE_URL}/inbox/email/${emailId}`,
    THREAD: (threadId) => `${API_BASE_URL}/inbox/thread/${threadId}`,
    REPLY: (emailId) => `${API_BASE_URL}/inbox/email/${emailId}/reply`,
  },
  
  // Settings endpoints
  SETTINGS: {
    CONNECTIONS: `${API_BASE_URL}/settings/connections`,
    DISCONNECT: (provider) => `${API_BASE_URL}/settings/connections/${provider}/disconnect`,
    PROMPT: `${API_BASE_URL}/settings/prompt`,
    PROMPT_RESET: `${API_BASE_URL}/settings/prompt/reset`,
    PROMPT_VALIDATE: `${API_BASE_URL}/settings/prompt/validate`,
  },
  
  // Google OAuth endpoints
  GOOGLE_AUTH: {
    AUTHORIZE: `${API_BASE_URL}/google-auth/`,
    CALLBACK: `${API_BASE_URL}/google-auth/callback`,
    STATUS: `${API_BASE_URL}/google-auth/status`,
    CLEAR: `${API_BASE_URL}/google-auth/clear`,
  }
}

export const CONFIG = {
  API_BASE_URL,
  FRONTEND_URL
}

export default API_ENDPOINTS 