import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader } from './ui/card'
import { Badge } from './ui/badge'
import { Button } from './ui/button'
import { Paperclip, Star, AlertCircle, Reply, ReplyAll, Forward, Archive } from 'lucide-react'
import { cn } from '../lib/utils'
import axios from 'axios'
import { API_ENDPOINTS } from '../config/api'
import { useAuth } from '../contexts/AuthContext'

const EmailViewer = ({ email, onEmailUpdate }) => {
  const [fullEmail, setFullEmail] = useState(null)
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('text') // 'text' or 'html'
  
  const { getAuthHeaders } = useAuth()

  useEffect(() => {
    if (email && email.gmail_id) {
      fetchFullEmail(email.gmail_id)
    }
  }, [email])

  const fetchFullEmail = async (gmailId) => {
    setLoading(true)
    try {
      const response = await axios.get(API_ENDPOINTS.INBOX.EMAIL(gmailId), {
        headers: getAuthHeaders()
      })
      setFullEmail(response.data)
    } catch (error) {
      console.error('Error fetching full email:', error)
    } finally {
      setLoading(false)
    }
  }

  if (!email) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center text-muted-foreground">
          <div className="text-lg mb-2">Select an email</div>
          <div className="text-sm">Choose an email from the list to view its contents</div>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-muted-foreground">Loading email content...</div>
      </div>
    )
  }

  const emailToShow = fullEmail || email

  return (
    <div className="h-full flex flex-col">
      {/* Email Header */}
      <Card className="rounded-none border-x-0 border-t-0">
        <CardHeader className="pb-4">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <h1 className="text-xl font-semibold mb-2 break-words">
                {emailToShow.subject || '(No Subject)'}
              </h1>
              
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2">
                  <span className="text-muted-foreground">From:</span>
                  <span className="font-medium">{emailToShow.from_email || emailToShow.sender}</span>
                  <div className="flex items-center gap-1">
                    {email.is_important && (
                      <AlertCircle className="h-4 w-4 text-orange-500" />
                    )}
                    {email.is_starred && (
                      <Star className="h-4 w-4 text-yellow-500 fill-current" />
                    )}
                    {email.has_attachments && (
                      <Paperclip className="h-4 w-4 text-muted-foreground" />
                    )}
                  </div>
                </div>
                
                {emailToShow.to_email && (
                  <div className="flex items-center gap-2">
                    <span className="text-muted-foreground">To:</span>
                    <span>{emailToShow.to_email}</span>
                  </div>
                )}
                
                <div className="flex items-center gap-2">
                  <span className="text-muted-foreground">Date:</span>
                  <span>{email.date || emailToShow.date}</span>
                </div>
              </div>
              
              {email.labels && email.labels.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-3">
                  {email.labels.map((label) => (
                    <Badge
                      key={label}
                      variant={label === 'UNREAD' ? 'default' : 'secondary'}
                      className="text-xs"
                    >
                      {label}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
            
            {/* Action Buttons */}
            <div className="flex items-center gap-2 flex-shrink-0">
              <Button variant="ghost" size="icon">
                <Reply className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="icon">
                <ReplyAll className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="icon">
                <Forward className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="icon">
                <Archive className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Email Content */}
      <div className="flex-1 overflow-hidden">
        <Card className="h-full rounded-none border-x-0 border-b-0">
          <CardContent className="p-0 h-full">
            {fullEmail?.body && (fullEmail.body.text || fullEmail.body.html) ? (
              <div className="h-full flex flex-col">
                {/* Content Type Tabs */}
                {fullEmail.body.text && fullEmail.body.html && (
                  <div className="border-b px-6 py-2">
                    <div className="flex gap-2">
                      <Button
                        variant={activeTab === 'text' ? 'default' : 'ghost'}
                        size="sm"
                        onClick={() => setActiveTab('text')}
                      >
                        Plain Text
                      </Button>
                      <Button
                        variant={activeTab === 'html' ? 'default' : 'ghost'}
                        size="sm"
                        onClick={() => setActiveTab('html')}
                      >
                        HTML
                      </Button>
                    </div>
                  </div>
                )}
                
                {/* Email Body */}
                <div className="flex-1 overflow-y-auto p-6">
                  {activeTab === 'text' && fullEmail.body.text ? (
                    <div className="whitespace-pre-wrap font-mono text-sm leading-relaxed">
                      {fullEmail.body.text}
                    </div>
                  ) : activeTab === 'html' && fullEmail.body.html ? (
                    <div 
                      className="prose prose-sm max-w-none prose-headings:text-foreground prose-p:text-foreground prose-a:text-primary hover:prose-a:text-primary/80"
                      dangerouslySetInnerHTML={{ __html: fullEmail.body.html }}
                    />
                  ) : fullEmail.body.text ? (
                    <div className="whitespace-pre-wrap font-mono text-sm leading-relaxed">
                      {fullEmail.body.text}
                    </div>
                  ) : fullEmail.body.html ? (
                    <div 
                      className="prose prose-sm max-w-none prose-headings:text-foreground prose-p:text-foreground prose-a:text-primary hover:prose-a:text-primary/80"
                      dangerouslySetInnerHTML={{ __html: fullEmail.body.html }}
                    />
                  ) : (
                    <div className="text-muted-foreground text-center py-8">
                      <div className="text-lg mb-2">No Content Available</div>
                      <div className="text-sm">This email may not have readable content or it hasn't been fully synced yet.</div>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="h-full flex items-center justify-center">
                <div className="text-center text-muted-foreground">
                  <div className="text-lg mb-2">Email Preview</div>
                  <div className="text-sm max-w-md mx-auto leading-relaxed">
                    {email.snippet || 'No preview available for this email. Try syncing your emails to get the full content.'}
                  </div>
                  {!fullEmail && (
                    <div className="mt-4">
                      <div className="text-xs text-muted-foreground/60">
                        Loading full content...
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default EmailViewer 