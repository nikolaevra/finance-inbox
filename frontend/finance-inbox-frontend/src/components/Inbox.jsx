import React, { useState, useEffect } from 'react'
import { Button } from './ui/button'
import { Card } from './ui/card'
import { RefreshCw, Settings, Search } from 'lucide-react'
import EmailList from './EmailList'
import EmailViewer from './EmailViewer'
import { useAuth } from '../contexts/AuthContext'
import axios from 'axios'
import { API_ENDPOINTS } from '../config/api'

const Inbox = () => {
  const [emails, setEmails] = useState([])
  const [selectedEmail, setSelectedEmail] = useState(null)
  const [loading, setLoading] = useState(false)
  const [syncing, setSyncing] = useState(false)
  
  const { getAuthHeaders } = useAuth()

  useEffect(() => {
    loadEmails()
  }, [])

  const loadEmails = async () => {
    setLoading(true)
    try {
      const response = await axios.get(`${API_ENDPOINTS.INBOX.LIST}?limit=50`, {
        headers: getAuthHeaders()
      })
      setEmails(response.data.inbox || [])
    } catch (error) {
      console.error('Error loading emails:', error)
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
      // Reload emails after sync
      await loadEmails()
    } catch (error) {
      console.error('Error syncing emails:', error)
      if (error.response?.status === 401) {
        console.error('Authentication failed - please login again')
      }
    } finally {
      setSyncing(false)
    }
  }

  const handleEmailSelect = (email) => {
    setSelectedEmail(email)
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
                onClick={loadEmails}
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
        {/* Email List - 1/3 width */}
        <div className="w-1/3 border-r">
          <Card className="h-full rounded-none border-0">
            <EmailList
              emails={emails}
              selectedEmail={selectedEmail}
              onEmailSelect={handleEmailSelect}
              loading={loading}
            />
          </Card>
        </div>

        {/* Email Viewer - 2/3 width */}
        <div className="flex-1">
          <EmailViewer
            email={selectedEmail}
            onEmailUpdate={() => loadEmails()}
          />
        </div>
      </div>

      {/* Status Bar */}
      <div className="border-t px-6 py-2 text-xs text-muted-foreground">
        <div className="flex items-center justify-between">
          <div>
            {emails.length > 0 ? (
              `${emails.length} emails loaded`
            ) : (
              'No emails'
            )}
          </div>
          <div className="flex items-center gap-4">
            {selectedEmail && (
              <span>Selected: {selectedEmail.subject || '(No Subject)'}</span>
            )}
            <span>Finance Inbox v1.0</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Inbox 