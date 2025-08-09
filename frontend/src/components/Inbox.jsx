import React, { useState, useEffect, useRef } from 'react'
import { Button } from './ui/button'
import { Card } from './ui/card'
import { RefreshCw, Settings, Search, Bell } from 'lucide-react'
import ThreadList from './ThreadList'
import ThreadViewer from './ThreadViewer'
import { useAuth } from '../contexts/AuthContext'
import axios from 'axios'
import { API_ENDPOINTS } from '../config/api'

const REFRESH_INTERVAL = 60000 // 1 minute

const Inbox = () => {
  const [threads, setThreads] = useState([])
  const [selectedThread, setSelectedThread] = useState(null)
  const [loading, setLoading] = useState(false)
  const [syncing, setSyncing] = useState(false)
  const [newEmailCount, setNewEmailCount] = useState(0)
  const [lastRefresh, setLastRefresh] = useState(Date.now())
  const refreshIntervalRef = useRef(null)
  
  const { getAuthHeaders } = useAuth()

  useEffect(() => {
    loadThreads()
    
    // Set up automatic refresh
    refreshIntervalRef.current = setInterval(() => {
      loadThreads(true) // Silent refresh
    }, REFRESH_INTERVAL)
    
    return () => {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current)
      }
    }
  }, [])

  const loadThreads = async (silent = false) => {
    if (!silent) setLoading(true)
    
    try {
      const response = await axios.get(`${API_ENDPOINTS.INBOX.LIST}?limit=50`, {
        headers: getAuthHeaders()
      })
      
      const newThreads = response.data.threads || []
      
      // Check for new emails
      if (threads.length > 0 && silent) {
        const currentUnreadCount = threads.reduce((sum, thread) => sum + (thread.unread_count || 0), 0)
        const newUnreadCount = newThreads.reduce((sum, thread) => sum + (thread.unread_count || 0), 0)
        
        if (newUnreadCount > currentUnreadCount) {
          setNewEmailCount(newUnreadCount - currentUnreadCount)
          // Auto-sync if there are new emails
          syncEmails()
        }
      }
      
      setThreads(newThreads)
      setLastRefresh(Date.now())
    } catch (error) {
      console.error('Error loading threads:', error)
      if (error.response?.status === 401) {
        console.error('Authentication failed - please login again')
      }
    } finally {
      if (!silent) setLoading(false)
    }
  }

  const syncEmails = async () => {
    setSyncing(true)
    try {
      await axios.post(`${API_ENDPOINTS.INBOX.SYNC}?max_results=20`, {}, {
        headers: getAuthHeaders()
      })
      // Reload threads after sync
      await loadThreads()
    } catch (error) {
      console.error('Error syncing emails:', error)
      if (error.response?.status === 401) {
        console.error('Authentication failed - please login again')
      }
    } finally {
      setSyncing(false)
    }
  }

  const handleThreadSelect = async (thread) => {
    setSelectedThread(thread)
    
    // Mark thread as read if it has unread emails
    if (thread.unread_count > 0) {
      try {
        await axios.put(API_ENDPOINTS.INBOX.MARK_THREAD_READ(thread.thread_id), {}, {
          headers: getAuthHeaders()
        })
        
        // Update the thread in the list to reflect read status
        setAllThreads(prevThreads => 
          prevThreads.map(t => 
            t.thread_id === thread.thread_id 
              ? { ...t, unread_count: 0, is_unread: false }
              : t
          )
        )
      } catch (error) {
        console.error('Error marking thread as read:', error)
      }
    }
  }

  return (
    <div className="h-full flex flex-col bg-background">
      {/* Header */}
      <div className="border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="fi-inbox-header-content flex items-center gap-4">
            <h1 className="fi-inbox-title text-2xl font-bold">Inbox</h1>
            
            {/* New email notification */}
            {newEmailCount > 0 && (
              <div className="fi-new-email-badge flex items-center gap-2 bg-blue-100 text-blue-800 px-3 py-1 rounded-full animate-pulse">
                <Bell className="fi-bell-icon h-4 w-4" />
                <span className="fi-badge-text text-sm font-medium">{newEmailCount} new</span>
              </div>
            )}
            
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setNewEmailCount(0)
                  loadThreads()
                }}
                disabled={loading}
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                onClick={syncEmails}
                disabled={syncing}
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${syncing ? 'animate-spin' : ''}`} />
                Sync Gmail
              </Button>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="icon">
              <Search className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Thread List - 1/3 width */}
        <div className="w-1/3 border-r">
          <Card className="h-full rounded-none border-0">
            <ThreadList
              threads={threads}
              selectedThread={selectedThread}
              onThreadSelect={handleThreadSelect}
              loading={loading}
            />
          </Card>
        </div>

        {/* Thread Viewer - 2/3 width */}
        <div className="flex-1">
          <ThreadViewer
            thread={selectedThread}
            onThreadUpdate={() => loadThreads()}
          />
        </div>
      </div>

      {/* Status Bar */}
      <div className="border-t px-6 py-2 text-xs text-muted-foreground">
        <div className="flex items-center justify-between">
          <div>
            {threads.length > 0 ? (
              `${threads.length} threads loaded (${threads.reduce((sum, thread) => sum + thread.email_count, 0)} total emails)`
            ) : (
              'No threads'
            )}
          </div>
          <div className="flex items-center gap-4">
            <span>Last refreshed: {new Date(lastRefresh).toLocaleTimeString()}</span>
            {selectedThread && (
              <span>Selected: {selectedThread.subject || '(No Subject)'} ({selectedThread.email_count} emails)</span>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default Inbox 