import React, { createContext, useContext, useEffect, useState } from 'react'
import { supabase } from '../lib/supabase'
import axios from 'axios'

const AuthContext = createContext({})

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [session, setSession] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
      setUser(session?.user ?? null)
      setLoading(false)
    })

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session)
      setUser(session?.user ?? null)
      setLoading(false)
    })

    return () => subscription.unsubscribe()
  }, [])

  // Set up axios interceptor to handle auth errors and token refresh
  useEffect(() => {
    const interceptor = axios.interceptors.response.use(
      (response) => response,
      async (error) => {
        // Check if the error is due to authentication failure
        if (error.response?.status === 401) {
          const authAction = error.response.headers['x-auth-action']
          
          if (authAction === 'refresh-required') {
            console.log('🔄 Token expired, refreshing session...')
            try {
              // Refresh the session using Supabase
              const { data, error: refreshError } = await supabase.auth.refreshSession()
              
              if (refreshError || !data.session) {
                console.log('❌ Session refresh failed, signing out user...')
                await signOut()
              } else {
                console.log('✅ Session refreshed successfully')
                // The auth state will update automatically via the listener
                // You might want to retry the original request here
              }
            } catch (refreshError) {
              console.error('❌ Error refreshing session:', refreshError)
              await signOut()
            }
          } else if (authAction === 'login-required') {
            console.log('🔐 Backend requires re-login, signing out user...')
            await signOut()
            // The auth state change will trigger a redirect to login
          }
        }
        
        return Promise.reject(error)
      }
    )

    return () => {
      axios.interceptors.response.eject(interceptor)
    }
  }, [])  // Empty dependency array since signOut is stable

  const signIn = async (email, password) => {
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      })
      
      if (error) {
        throw error
      }
      
      return { data, error: null }
    } catch (error) {
      return { data: null, error }
    }
  }

  const signUp = async (email, password) => {
    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
      })
      
      if (error) {
        throw error
      }
      
      return { data, error: null }
    } catch (error) {
      return { data: null, error }
    }
  }

  const signOut = async () => {
    try {
      const { error } = await supabase.auth.signOut()
      if (error) {
        throw error
      }
      return { error: null }
    } catch (error) {
      return { error }
    }
  }

  const getAccessToken = () => {
    return session?.access_token
  }

  const getAuthHeaders = () => {
    return session?.access_token 
      ? { Authorization: `Bearer ${session.access_token}` }
      : {}
  }

  const value = {
    user,
    session,
    loading,
    signIn,
    signUp,
    signOut,
    getAccessToken,
    getAuthHeaders,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
} 