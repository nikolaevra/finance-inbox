import React, { useState, useEffect } from 'react'
import { Button } from './ui/button'
import { Card } from './ui/card'
import { RefreshCw, Settings, Search } from 'lucide-react'
import ThreadList from './ThreadList'
import ThreadViewer from './ThreadViewer'
import { useAuth } from '../contexts/AuthContext'
import axios from 'axios'
import { API_ENDPOINTS } from '../config/api'

const Inbox = () => {
  const [threads, setThreads] = useState([])
  const [selectedThread, setSelectedThread] = useState(null)
  const [loading, setLoading] = useState(false)
  const [syncing, setSyncing] = useState(false)
  
  const { getAuthHeaders } = useAuth()

  useEffect(() => {
    loadThreads()
  }, [])

  const loadThreads = async () => {
    setLoading(true)
    try {
      const response = await axios.get(`${API_ENDPOINTS.INBOX.LIST}?limit=50`, {
        headers: getAuthHeaders()
      })
      setThreads(response.data.threads || [])
    } catch (error) {
      console.error('Error loading threads:', error)
      if (error.response?.status === 401) {
        console.error('Authentication failed - please login again')
      }
    } finally {
      setLoading(false)
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

  const handleThreadSelect = (thread) => {
    setSelectedThread(thread)
  }

  return (
    <div className="h-full flex flex-col bg-background">
      {/* Header */}
      <div className="border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-2xl font-bold">Inbox</h1>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={loadThreads}
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
            {selectedThread && (
              <span>Selected: {selectedThread.subject || '(No Subject)'} ({selectedThread.email_count} emails)</span>
            )}
            <span>Finance Inbox v1.0</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Inbox 