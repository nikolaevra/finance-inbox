import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Badge } from './ui/badge'
import { Settings as SettingsIcon, Mail, CheckCircle, XCircle, MessageSquare, Users, Calendar, User, LogOut, Loader2, Brain, Save, RefreshCw, CheckCircle2, AlertCircle, Eye } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import axios from 'axios'
import { API_ENDPOINTS } from '../config/api'

const Settings = () => {
  const [connections, setConnections] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  
  // Prompt settings state
  const [promptConfig, setPromptConfig] = useState(null)
  const [promptLoading, setPromptLoading] = useState(false)
  const [promptError, setPromptError] = useState(null)
  const [promptSuccess, setPromptSuccess] = useState(null)
  const [promptTemplate, setPromptTemplate] = useState('')
  const [promptModel, setPromptModel] = useState('gpt-3.5-turbo')
  const [promptTemperature, setPromptTemperature] = useState(0.1)
  const [promptMaxTokens, setPromptMaxTokens] = useState(200)
  const [promptTimeout, setPromptTimeout] = useState(10)
  const [showPreview, setShowPreview] = useState(false)
  const [previewText, setPreviewText] = useState('')
  const [isEditing, setIsEditing] = useState(false)
  
  const { user, signOut, getAuthHeaders } = useAuth()

  // Fetch connections from API
  const fetchConnections = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await axios.get(API_ENDPOINTS.SETTINGS.CONNECTIONS, {
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
    fetchPromptConfig()
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
    } else if (success === 'slack_connected') {
      console.log('Slack connected successfully!')
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
        API_ENDPOINTS.SETTINGS.DISCONNECT('gmail'),
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

  const handleConnectSlack = async () => {
    try {
      const response = await axios.get(API_ENDPOINTS.SLACK_AUTH.AUTHORIZE, {
        headers: getAuthHeaders()
      })
      
      if (response.data.authorization_url) {
        // Redirect to Slack OAuth
        window.location.href = response.data.authorization_url
      } else {
        console.error('No authorization URL received')
      }
    } catch (error) {
      console.error('Error getting Slack authorization URL:', error)
      // Handle error - maybe show a toast notification
    }
  }

  const handleDisconnectSlack = async () => {
    try {
      const response = await axios.post(
        API_ENDPOINTS.SETTINGS.DISCONNECT('slack'),
        {},
        { headers: getAuthHeaders() }
      )
      
      console.log('Slack disconnected:', response.data)
      
      // Refresh connections after disconnect
      await fetchConnections()
    } catch (error) {
      console.error('Error disconnecting Slack:', error)
    }
  }

  const handleSignOut = async () => {
    try {
      await signOut()
    } catch (error) {
      console.error('Error signing out:', error)
    }
  }

  // Prompt settings functions
  const fetchPromptConfig = async () => {
    try {
      setPromptLoading(true)
      setPromptError(null)
      
      const response = await axios.get(API_ENDPOINTS.SETTINGS.PROMPT, {
        headers: getAuthHeaders()
      })
      
      const config = response.data.prompt
      setPromptConfig(config)
      setPromptTemplate(config.template || '')
      setPromptModel(config.model || 'gpt-3.5-turbo')
      setPromptTemperature(config.temperature || 0.1)
      setPromptMaxTokens(config.max_tokens || 200)
      setPromptTimeout(config.timeout || 10)
      
    } catch (error) {
      console.error('Error fetching prompt config:', error)
      setPromptError('Failed to load prompt configuration')
    } finally {
      setPromptLoading(false)
    }
  }

  const handleUpdatePrompt = async () => {
    try {
      setPromptLoading(true)
      setPromptError(null)
      setPromptSuccess(null)
      
      const response = await axios.put(API_ENDPOINTS.SETTINGS.PROMPT, {
        template: promptTemplate,
        model: promptModel,
        temperature: promptTemperature,
        max_tokens: promptMaxTokens,
        timeout: promptTimeout
      }, {
        headers: getAuthHeaders()
      })
      
      if (response.data.success) {
        setPromptSuccess('Prompt updated successfully!')
        setIsEditing(false)
        await fetchPromptConfig() // Refresh config
        
        // Clear success message after 3 seconds
        setTimeout(() => setPromptSuccess(null), 3000)
      }
      
    } catch (error) {
      console.error('Error updating prompt:', error)
      setPromptError(error.response?.data?.detail || 'Failed to update prompt')
    } finally {
      setPromptLoading(false)
    }
  }

  const handleResetPrompt = async () => {
    try {
      setPromptLoading(true)
      setPromptError(null)
      setPromptSuccess(null)
      
      const response = await axios.post(API_ENDPOINTS.SETTINGS.PROMPT_RESET, {}, {
        headers: getAuthHeaders()
      })
      
      if (response.data.success) {
        setPromptSuccess('Prompt reset to default successfully!')
        setIsEditing(false)
        await fetchPromptConfig() // Refresh config
        
        // Clear success message after 3 seconds
        setTimeout(() => setPromptSuccess(null), 3000)
      }
      
    } catch (error) {
      console.error('Error resetting prompt:', error)
      setPromptError(error.response?.data?.detail || 'Failed to reset prompt')
    } finally {
      setPromptLoading(false)
    }
  }

  const handlePreviewPrompt = async () => {
    try {
      setPromptError(null)
      
      const response = await axios.post(API_ENDPOINTS.SETTINGS.PROMPT_VALIDATE, {
        template: promptTemplate
      }, {
        headers: getAuthHeaders()
      })
      
      if (response.data.success) {
        setPreviewText(response.data.preview)
        setShowPreview(true)
      }
      
    } catch (error) {
      console.error('Error previewing prompt:', error)
      setPromptError(error.response?.data?.detail || 'Failed to preview prompt')
    }
  }

  const handleCancelEdit = () => {
    // Reset to original values
    if (promptConfig) {
      setPromptTemplate(promptConfig.template || '')
      setPromptModel(promptConfig.model || 'gpt-3.5-turbo')
      setPromptTemperature(promptConfig.temperature || 0.1)
      setPromptMaxTokens(promptConfig.max_tokens || 200)
      setPromptTimeout(promptConfig.timeout || 10)
    }
    setIsEditing(false)
    setPromptError(null)
    setPromptSuccess(null)
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
      <div className="flex-1 p-6 overflow-y-auto">
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
                  <div className="border rounded-lg p-4">
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
                              <Badge variant="secondary" className="bg-gray-100 text-gray-800 border-gray-200">
                                <XCircle className="h-3 w-3 mr-1" />
                                Disconnected
                              </Badge>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        {isProviderConnected('slack') ? (
                          <Button 
                            variant="destructive" 
                            size="sm"
                            onClick={handleDisconnectSlack}
                          >
                            Disconnect
                          </Button>
                        ) : (
                          <Button 
                            variant="default" 
                            size="sm"
                            onClick={handleConnectSlack}
                          >
                            Connect
                          </Button>
                        )}
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

          {/* AI Prompt Settings Section */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Brain className="h-5 w-5" />
                AI Email Categorization
              </CardTitle>
              <CardDescription>
                Customize the AI prompt used to categorize your emails
              </CardDescription>
            </CardHeader>
            <CardContent>
              {promptLoading ? (
                <div className="flex items-center justify-center p-8">
                  <Loader2 className="h-6 w-6 animate-spin mr-2" />
                  <span>Loading prompt configuration...</span>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Status Messages */}
                  {promptError && (
                    <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700">
                      <AlertCircle className="h-4 w-4" />
                      <span className="text-sm">{promptError}</span>
                    </div>
                  )}
                  
                  {promptSuccess && (
                    <div className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700">
                      <CheckCircle2 className="h-4 w-4" />
                      <span className="text-sm">{promptSuccess}</span>
                    </div>
                  )}

                  {/* Prompt Template Section */}
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="text-lg font-semibold">Email Categorization Prompt</h3>
                      <div className="flex gap-2">
                        {!isEditing ? (
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={() => setIsEditing(true)}
                          >
                            Edit Prompt
                          </Button>
                        ) : (
                          <>
                            <Button 
                              variant="outline" 
                              size="sm"
                              onClick={handleCancelEdit}
                            >
                              Cancel
                            </Button>
                            <Button 
                              variant="outline" 
                              size="sm"
                              onClick={handlePreviewPrompt}
                            >
                              <Eye className="h-4 w-4 mr-1" />
                              Preview
                            </Button>
                            <Button 
                              variant="outline" 
                              size="sm"
                              onClick={handleResetPrompt}
                              disabled={promptLoading}
                            >
                              <RefreshCw className="h-4 w-4 mr-1" />
                              Reset
                            </Button>
                            <Button 
                              variant="default" 
                              size="sm"
                              onClick={handleUpdatePrompt}
                              disabled={promptLoading}
                            >
                              <Save className="h-4 w-4 mr-1" />
                              Save
                            </Button>
                          </>
                        )}
                      </div>
                    </div>

                    {/* Prompt Template Textarea */}
                    <div className="space-y-2">
                      <label className="text-sm font-medium">
                        Prompt Template
                      </label>
                      <textarea
                        value={promptTemplate}
                        onChange={(e) => setPromptTemplate(e.target.value)}
                        disabled={!isEditing}
                        rows={10}
                        className={`w-full p-3 border rounded-lg font-mono text-sm resize-none ${
                          isEditing 
                            ? 'border-gray-300 bg-white' 
                            : 'border-gray-200 bg-gray-50 text-gray-600'
                        }`}
                        placeholder="Enter your custom prompt template here..."
                      />
                      <div className="text-xs text-gray-500">
                        Template must include these variables: {'{subject}'}, {'{sender}'}, {'{content}'}
                      </div>
                    </div>

                    {/* Advanced Settings */}
                    {isEditing && (
                      <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
                        <div className="space-y-2">
                          <label className="text-sm font-medium">Model</label>
                          <select 
                            value={promptModel}
                            onChange={(e) => setPromptModel(e.target.value)}
                            className="w-full p-2 border rounded text-sm"
                          >
                            <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                            <option value="gpt-4">GPT-4</option>
                            <option value="gpt-4-turbo">GPT-4 Turbo</option>
                          </select>
                        </div>
                        
                        <div className="space-y-2">
                          <label className="text-sm font-medium">Temperature</label>
                          <input
                            type="number"
                            value={promptTemperature}
                            onChange={(e) => setPromptTemperature(parseFloat(e.target.value))}
                            min="0"
                            max="1"
                            step="0.1"
                            className="w-full p-2 border rounded text-sm"
                          />
                        </div>
                        
                        <div className="space-y-2">
                          <label className="text-sm font-medium">Max Tokens</label>
                          <input
                            type="number"
                            value={promptMaxTokens}
                            onChange={(e) => setPromptMaxTokens(parseInt(e.target.value))}
                            min="50"
                            max="1000"
                            className="w-full p-2 border rounded text-sm"
                          />
                        </div>
                        
                        <div className="space-y-2">
                          <label className="text-sm font-medium">Timeout (seconds)</label>
                          <input
                            type="number"
                            value={promptTimeout}
                            onChange={(e) => setPromptTimeout(parseInt(e.target.value))}
                            min="5"
                            max="60"
                            className="w-full p-2 border rounded text-sm"
                          />
                        </div>
                      </div>
                    )}

                    {/* Prompt Preview Modal */}
                    {showPreview && (
                      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                        <div className="bg-white rounded-lg p-6 max-w-2xl max-h-[80vh] overflow-y-auto">
                          <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-semibold">Prompt Preview</h3>
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => setShowPreview(false)}
                            >
                              ×
                            </Button>
                          </div>
                          <div className="space-y-4">
                            <div className="text-sm text-gray-600">
                              This is how your prompt will look when sent to the AI:
                            </div>
                            <div className="bg-gray-50 p-4 rounded-lg border">
                              <pre className="text-sm whitespace-pre-wrap font-mono">
                                {previewText}
                              </pre>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Prompt Info */}
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <h4 className="font-medium text-blue-900 mb-2">About Email Categorization</h4>
                      <p className="text-sm text-blue-800">
                        This prompt is used by AI to automatically categorize your emails into 10 financial professional categories:
                        Client Communication, Market Research, Regulatory Compliance, Financial Reporting, Transaction Alerts, 
                        Internal Operations, Vendor Services, Marketing/Sales, Educational Content, and Other.
                      </p>
                      {promptConfig && (
                        <div className="mt-3 text-xs text-blue-700">
                          <div>Current version: {promptConfig.prompt_version}</div>
                          <div>Last updated: {promptConfig.updated_at ? new Date(promptConfig.updated_at).toLocaleDateString() : 'Never'}</div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
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