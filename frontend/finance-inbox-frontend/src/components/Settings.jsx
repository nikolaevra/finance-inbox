import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Badge } from './ui/badge'
import { Settings as SettingsIcon, Mail, CheckCircle, XCircle, MessageSquare, Users, Calendar, User, LogOut, Loader2 } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import axios from 'axios'
import { API_ENDPOINTS } from '../config/api'

const Settings = () => {
  const [connections, setConnections] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  
  const { user, signOut, getAuthHeaders } = useAuth()

  // Fetch connections from API
  const fetchConnections = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await axios.get(API_ENDPOINTS.INBOX.CONNECTIONS, {
        headers: getAuthHeaders()
      })
      
      setConnections(response.data.connections || [])
    } catch (error) {
      console.error('Error fetching connections:', error)
      setError('Failed to load connections')
      setConnections([])
    } finally {
      setLoading(false)
    }
  }

  // Load connections on component mount
  useEffect(() => {
    fetchConnections()
  }, [])

  // Handle OAuth callback parameters
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search)
    const success = urlParams.get('success')
    const error = urlParams.get('error')
    
    if (success === 'gmail_connected') {
      console.log('Gmail connected successfully!')
      // Refresh connections to show updated status
      fetchConnections()
      // Clear URL parameters
      window.history.replaceState({}, document.title, window.location.pathname)
    } else if (error) {
      console.error('OAuth error:', error)
      setError(`Connection failed: ${error}`)
      // Clear URL parameters
      window.history.replaceState({}, document.title, window.location.pathname)
    }
  }, [])

  // Helper function to get connection status for a provider
  const getConnectionStatus = (provider) => {
    const connection = connections.find(conn => 
      conn.connection_provider === provider.toLowerCase()
    )
    return connection ? connection.status : 'disconnected'
  }

  // Helper function to check if provider is connected
  const isProviderConnected = (provider) => {
    return getConnectionStatus(provider) === 'connected'
  }

  const handleConnectGmail = async () => {
    try {
      const response = await axios.get(API_ENDPOINTS.GOOGLE_AUTH.AUTHORIZE, {
        headers: getAuthHeaders()
      })
      
      if (response.data.authorization_url) {
        // Redirect to Google OAuth
        window.location.href = response.data.authorization_url
      } else {
        console.error('No authorization URL received')
      }
    } catch (error) {
      console.error('Error getting Gmail authorization URL:', error)
      // Handle error - maybe show a toast notification
    }
  }

  const handleDisconnectGmail = async () => {
    try {
      const response = await axios.post(
        API_ENDPOINTS.INBOX.DISCONNECT('gmail'),
        {},
        { headers: getAuthHeaders() }
      )
      
      console.log('Gmail disconnected:', response.data)
      
      // Refresh connections after disconnect
      await fetchConnections()
    } catch (error) {
      console.error('Error disconnecting Gmail:', error)
    }
  }

  const handleSignOut = async () => {
    try {
      await signOut()
    } catch (error) {
      console.error('Error signing out:', error)
    }
  }

  return (
    <div className="h-full flex flex-col bg-background">
      {/* Header */}
      <div className="border-b px-6 py-4">
        <div className="flex items-center gap-3">
          <SettingsIcon className="h-6 w-6" />
          <h1 className="text-2xl font-bold">Settings</h1>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 p-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Account Section */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5" />
                Account
              </CardTitle>
              <CardDescription>
                Your account information and authentication settings
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 border rounded-lg">
                  <div>
                    <h3 className="font-semibold">Email</h3>
                    <p className="text-sm text-muted-foreground">{user?.email}</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      User ID: {user?.id}
                    </p>
                  </div>
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={handleSignOut}
                  >
                    <LogOut className="h-4 w-4 mr-2" />
                    Sign Out
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Inbox Connections Section */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Mail className="h-5 w-5" />
                Inbox Connections
              </CardTitle>
              <CardDescription>
                Manage your email account connections and sync settings
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {loading ? (
                <div className="flex items-center justify-center p-8">
                  <Loader2 className="h-6 w-6 animate-spin mr-2" />
                  <span>Loading connections...</span>
                </div>
              ) : error ? (
                <div className="text-center p-8 text-red-600">
                  <XCircle className="h-8 w-8 mx-auto mb-2" />
                  <p>{error}</p>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={fetchConnections}
                    className="mt-2"
                  >
                    Retry
                  </Button>
                </div>
              ) : (
                <>
                  {/* Gmail Integration Card */}
                  <div className="border rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className="flex items-center justify-center w-12 h-12 bg-red-50 rounded-lg">
                          <Mail className="h-6 w-6 text-red-600" />
                        </div>
                        <div>
                          <h3 className="font-semibold text-lg">Gmail</h3>
                          <p className="text-sm text-muted-foreground">
                            Connect your Gmail account to sync emails
                          </p>
                          <div className="flex items-center gap-2 mt-2">
                            <span className="text-sm font-medium">Status:</span>
                            {isProviderConnected('gmail') ? (
                              <Badge variant="default" className="bg-green-100 text-green-800 border-green-200">
                                <CheckCircle className="h-3 w-3 mr-1" />
                                Connected
                              </Badge>
                            ) : getConnectionStatus('gmail') === 'refresh_required' ? (
                              <Badge variant="destructive" className="bg-yellow-100 text-yellow-800 border-yellow-200">
                                <XCircle className="h-3 w-3 mr-1" />
                                Refresh Required
                              </Badge>
                            ) : (
                              <Badge variant="secondary" className="bg-gray-100 text-gray-800 border-gray-200">
                                <XCircle className="h-3 w-3 mr-1" />
                                Disconnected
                              </Badge>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        {isProviderConnected('gmail') ? (
                          <Button 
                            variant="destructive" 
                            size="sm"
                            onClick={handleDisconnectGmail}
                          >
                            Disconnect
                          </Button>
                        ) : (
                          <Button 
                            variant="default" 
                            size="sm"
                            onClick={handleConnectGmail}
                          >
                            Connect
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                </>
              )}

                  {/* Slack Integration Card */}
                  <div className={`border rounded-lg p-4 ${!isProviderConnected('slack') ? 'opacity-60' : ''}`}>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className="flex items-center justify-center w-12 h-12 bg-purple-50 rounded-lg">
                          <MessageSquare className="h-6 w-6 text-purple-600" />
                        </div>
                        <div>
                          <h3 className="font-semibold text-lg">Slack</h3>
                          <p className="text-sm text-muted-foreground">
                            Connect your Slack workspace to sync messages
                          </p>
                          <div className="flex items-center gap-2 mt-2">
                            <span className="text-sm font-medium">Status:</span>
                            {isProviderConnected('slack') ? (
                              <Badge variant="default" className="bg-green-100 text-green-800 border-green-200">
                                <CheckCircle className="h-3 w-3 mr-1" />
                                Connected
                              </Badge>
                            ) : getConnectionStatus('slack') === 'refresh_required' ? (
                              <Badge variant="destructive" className="bg-yellow-100 text-yellow-800 border-yellow-200">
                                <XCircle className="h-3 w-3 mr-1" />
                                Refresh Required
                              </Badge>
                            ) : (
                              <Badge variant="secondary" className="bg-orange-100 text-orange-800 border-orange-200">
                                Coming Soon
                              </Badge>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Button 
                          variant="outline" 
                          size="sm"
                          disabled={!isProviderConnected('slack')}
                        >
                          {isProviderConnected('slack') ? 'Disconnect' : 'Connect'}
                        </Button>
                      </div>
                    </div>
                  </div>

                  {/* Microsoft Teams Integration Card */}
                  <div className={`border rounded-lg p-4 ${!isProviderConnected('teams') ? 'opacity-60' : ''}`}>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className="flex items-center justify-center w-12 h-12 bg-blue-50 rounded-lg">
                          <Users className="h-6 w-6 text-blue-600" />
                        </div>
                        <div>
                          <h3 className="font-semibold text-lg">Microsoft Teams</h3>
                          <p className="text-sm text-muted-foreground">
                            Connect your Teams account to sync messages and files
                          </p>
                          <div className="flex items-center gap-2 mt-2">
                            <span className="text-sm font-medium">Status:</span>
                            {isProviderConnected('teams') ? (
                              <Badge variant="default" className="bg-green-100 text-green-800 border-green-200">
                                <CheckCircle className="h-3 w-3 mr-1" />
                                Connected
                              </Badge>
                            ) : getConnectionStatus('teams') === 'refresh_required' ? (
                              <Badge variant="destructive" className="bg-yellow-100 text-yellow-800 border-yellow-200">
                                <XCircle className="h-3 w-3 mr-1" />
                                Refresh Required
                              </Badge>
                            ) : (
                              <Badge variant="secondary" className="bg-orange-100 text-orange-800 border-orange-200">
                                Coming Soon
                              </Badge>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Button 
                          variant="outline" 
                          size="sm"
                          disabled={!isProviderConnected('teams')}
                        >
                          {isProviderConnected('teams') ? 'Disconnect' : 'Connect'}
                        </Button>
                      </div>
                    </div>
                  </div>

                  {/* Outlook Integration Card */}
                  <div className={`border rounded-lg p-4 ${!isProviderConnected('outlook') ? 'opacity-60' : ''}`}>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className="flex items-center justify-center w-12 h-12 bg-blue-50 rounded-lg">
                          <Calendar className="h-6 w-6 text-blue-600" />
                        </div>
                        <div>
                          <h3 className="font-semibold text-lg">Outlook</h3>
                          <p className="text-sm text-muted-foreground">
                            Connect your Outlook account to sync emails and calendar
                          </p>
                          <div className="flex items-center gap-2 mt-2">
                            <span className="text-sm font-medium">Status:</span>
                            {isProviderConnected('outlook') ? (
                              <Badge variant="default" className="bg-green-100 text-green-800 border-green-200">
                                <CheckCircle className="h-3 w-3 mr-1" />
                                Connected
                              </Badge>
                            ) : getConnectionStatus('outlook') === 'refresh_required' ? (
                              <Badge variant="destructive" className="bg-yellow-100 text-yellow-800 border-yellow-200">
                                <XCircle className="h-3 w-3 mr-1" />
                                Refresh Required
                              </Badge>
                            ) : (
                              <Badge variant="secondary" className="bg-orange-100 text-orange-800 border-orange-200">
                                Coming Soon
                              </Badge>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Button 
                          variant="outline" 
                          size="sm"
                          disabled={!isProviderConnected('outlook')}
                        >
                          {isProviderConnected('outlook') ? 'Disconnect' : 'Connect'}
                        </Button>
                      </div>
                    </div>
                  </div>
            </CardContent>
          </Card>

          {/* Future Settings Sections */}
          <Card>
            <CardHeader>
              <CardTitle>Application Settings</CardTitle>
              <CardDescription>
                General application preferences and configuration
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center text-muted-foreground py-8">
                <SettingsIcon className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <h3 className="text-lg font-medium mb-2">More Settings Coming Soon</h3>
                <p className="text-sm">
                  Additional configuration options will be available here.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

export default Settings 