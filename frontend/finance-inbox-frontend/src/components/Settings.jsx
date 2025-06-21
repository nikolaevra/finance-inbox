import React from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Badge } from './ui/badge'
import { Settings as SettingsIcon, Mail, CheckCircle, XCircle, MessageSquare, Users, Calendar, User, LogOut } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'

const Settings = () => {
  // For now, always show as connected - later this will be dynamic
  const isGmailConnected = true
  
  const { user, signOut } = useAuth()

  const handleConnectGmail = () => {
    // TODO: Implement Gmail connection logic
    console.log('Connecting to Gmail...')
  }

  const handleDisconnectGmail = () => {
    // TODO: Implement Gmail disconnection logic
    console.log('Disconnecting from Gmail...')
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
                        {isGmailConnected ? (
                          <Badge variant="default" className="bg-green-100 text-green-800 border-green-200">
                            <CheckCircle className="h-3 w-3 mr-1" />
                            Connected
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
                    {isGmailConnected ? (
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

              {/* Slack Integration Card */}
              <div className="border rounded-lg p-4 opacity-60">
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
                        <Badge variant="secondary" className="bg-orange-100 text-orange-800 border-orange-200">
                          Coming Soon
                        </Badge>
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button 
                      variant="outline" 
                      size="sm"
                      disabled
                    >
                      Connect
                    </Button>
                  </div>
                </div>
              </div>

              {/* Microsoft Teams Integration Card */}
              <div className="border rounded-lg p-4 opacity-60">
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
                        <Badge variant="secondary" className="bg-orange-100 text-orange-800 border-orange-200">
                          Coming Soon
                        </Badge>
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button 
                      variant="outline" 
                      size="sm"
                      disabled
                    >
                      Connect
                    </Button>
                  </div>
                </div>
              </div>

              {/* Outlook Integration Card */}
              <div className="border rounded-lg p-4 opacity-60">
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
                        <Badge variant="secondary" className="bg-orange-100 text-orange-800 border-orange-200">
                          Coming Soon
                        </Badge>
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button 
                      variant="outline" 
                      size="sm"
                      disabled
                    >
                      Connect
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