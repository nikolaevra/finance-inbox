import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader } from './ui/card'
import { Badge } from './ui/badge'
import { Button } from './ui/button'
import { Paperclip, Star, AlertCircle, Reply, ChevronUp, ChevronDown, Send, X } from 'lucide-react'
import { cn } from '../lib/utils'
import axios from 'axios'
import { API_ENDPOINTS } from '../config/api'
import { useAuth } from '../contexts/AuthContext'

const ThreadViewer = ({ thread, onThreadUpdate }) => {
  const [fullThread, setFullThread] = useState(null)
  const [loading, setLoading] = useState(false)
  const [expandedEmails, setExpandedEmails] = useState(new Set())
  const [showReplyForm, setShowReplyForm] = useState(false)
  const [replyData, setReplyData] = useState({
    reply_body: '',
    reply_subject: '',
    to: [],
    cc: [],
    bcc: []
  })
  const [sendingReply, setSendingReply] = useState(false)
  
  const { getAuthHeaders } = useAuth()

  useEffect(() => {
    if (thread && thread.thread_id) {
      fetchFullThread(thread.thread_id)
      // Auto-expand the latest email
      if (thread.emails && thread.emails.length > 0) {
        const latestEmailId = thread.emails[thread.emails.length - 1]?.gmail_id
        if (latestEmailId) {
          setExpandedEmails(new Set([latestEmailId]))
        }
      }
    }
  }, [thread])

  const fetchFullThread = async (threadId) => {
    setLoading(true)
    try {
      const response = await axios.get(API_ENDPOINTS.INBOX.THREAD(threadId), {
        headers: getAuthHeaders()
      })
      setFullThread(response.data)
      
      // Auto-expand the latest email in the full thread
      if (response.data.emails && response.data.emails.length > 0) {
        const latestEmailId = response.data.emails[response.data.emails.length - 1]?.gmail_id
        if (latestEmailId) {
          setExpandedEmails(new Set([latestEmailId]))
        }
      }
    } catch (error) {
      console.error('Error fetching full thread:', error)
    } finally {
      setLoading(false)
    }
  }

  const toggleEmailExpansion = (emailId) => {
    const newExpanded = new Set(expandedEmails)
    if (newExpanded.has(emailId)) {
      newExpanded.delete(emailId)
    } else {
      newExpanded.add(emailId)
    }
    setExpandedEmails(newExpanded)
  }

  const handleReply = (email) => {
    const originalSubject = email.subject || ''
    const replySubject = originalSubject.startsWith('Re:') ? originalSubject : `Re: ${originalSubject}`
    
    setReplyData({
      reply_body: '',
      reply_subject: replySubject,
      to: [email.from_email],
      cc: [],
      bcc: []
    })
    setShowReplyForm(true)
  }

  const sendReply = async (emailId) => {
    setSendingReply(true)
    try {
      await axios.post(API_ENDPOINTS.INBOX.REPLY(emailId), replyData, {
        headers: getAuthHeaders()
      })
      
      // Clear reply form and close it
      setReplyData({
        reply_body: '',
        reply_subject: '',
        to: [],
        cc: [],
        bcc: []
      })
      setShowReplyForm(false)
      
      // Refresh the thread
      if (onThreadUpdate) {
        onThreadUpdate()
      }
      fetchFullThread(thread.thread_id)
    } catch (error) {
      console.error('Error sending reply:', error)
    } finally {
      setSendingReply(false)
    }
  }

  if (!thread) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center text-muted-foreground">
          <div className="text-lg mb-2">Select a thread</div>
          <div className="text-sm">Choose a thread from the list to view the conversation</div>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-muted-foreground">Loading thread conversation...</div>
      </div>
    )
  }

  const threadToShow = fullThread || thread
  const emails = threadToShow.emails || []

  return (
    <div className="h-full flex flex-col">
      {/* Thread Header */}
      <Card className="rounded-none border-x-0 border-t-0">
        <CardHeader className="pb-4">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <h1 className="text-xl font-semibold mb-2 break-words">
                {threadToShow.subject || '(No Subject)'}
              </h1>
              
              <div className="flex items-center gap-4 text-sm text-muted-foreground">
                <span>{threadToShow.email_count} messages</span>
                {threadToShow.unread_count > 0 && (
                  <span className="text-blue-600 font-medium">
                    {threadToShow.unread_count} unread
                  </span>
                )}
                {threadToShow.has_attachments && (
                  <span className="flex items-center gap-1">
                    <Paperclip className="h-3 w-3" />
                    Attachments
                  </span>
                )}
              </div>
              
              {threadToShow.labels && threadToShow.labels.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-3">
                  {threadToShow.labels.map((label) => (
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
            
            {/* Thread Action Buttons */}
            <div className="flex items-center gap-2 flex-shrink-0">
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => handleReply(emails[emails.length - 1])}
              >
                <Reply className="h-4 w-4 mr-2" />
                Reply
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Email Thread */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-4 space-y-4">
          {emails.map((email, index) => (
            <EmailCard
              key={email.gmail_id}
              email={email}
              isLatest={index === emails.length - 1}
              isExpanded={expandedEmails.has(email.gmail_id)}
              onToggleExpand={() => toggleEmailExpansion(email.gmail_id)}
              onReply={() => handleReply(email)}
            />
          ))}
          
          {/* Reply Form */}
          {showReplyForm && (
            <ReplyForm
              replyData={replyData}
              setReplyData={setReplyData}
              onSend={() => sendReply(emails[emails.length - 1]?.gmail_id)}
              onCancel={() => setShowReplyForm(false)}
              sending={sendingReply}
            />
          )}
        </div>
      </div>
    </div>
  )
}

const EmailCard = ({ email, isLatest, isExpanded, onToggleExpand, onReply }) => {
  return (
    <Card className={cn(
      "transition-all duration-200",
      email.is_unread && "border-l-4 border-l-blue-500",
      isLatest && "ring-1 ring-primary/20"
    )}>
      <CardHeader 
        className="pb-2 cursor-pointer hover:bg-accent/50 transition-colors"
        onClick={onToggleExpand}
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <div className={cn(
                "font-medium text-sm",
                email.is_unread && "font-semibold"
              )}>
                {email.sender || email.from_email}
              </div>
              
              <div className="flex items-center gap-1">
                {email.is_unread && (
                  <Badge variant="default" className="text-xs">
                    Unread
                  </Badge>
                )}
                {email.has_attachments && (
                  <Paperclip className="h-3 w-3 text-muted-foreground" />
                )}
              </div>
            </div>
            
            <div className="text-xs text-muted-foreground">
              {email.date}
            </div>
            
            {!isExpanded && (
              <div className="text-sm text-muted-foreground mt-1 truncate">
                {email.snippet}
              </div>
            )}
          </div>
          
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation()
                onReply()
              }}
            >
              <Reply className="h-3 w-3" />
            </Button>
            {isExpanded ? (
              <ChevronUp className="h-4 w-4 text-muted-foreground" />
            ) : (
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            )}
          </div>
        </div>
      </CardHeader>
      
      {isExpanded && (
        <CardContent className="pt-2">
          <div className="border-t pt-4">
            <div className="space-y-2 text-sm mb-4">
              <div><span className="text-muted-foreground">From:</span> {email.from_email}</div>
              {email.to_email && (
                <div><span className="text-muted-foreground">To:</span> {email.to_email}</div>
              )}
              {email.cc_email && (
                <div><span className="text-muted-foreground">CC:</span> {email.cc_email}</div>
              )}
            </div>
            
            {email.body ? (
              <div className="prose prose-sm max-w-none">
                {email.body.html ? (
                  <div dangerouslySetInnerHTML={{ __html: email.body.html }} />
                ) : (
                  <div className="whitespace-pre-wrap">{email.body.text}</div>
                )}
              </div>
            ) : (
              <div className="text-muted-foreground italic">
                {email.snippet || 'No content available'}
              </div>
            )}
          </div>
        </CardContent>
      )}
    </Card>
  )
}

const ReplyForm = ({ replyData, setReplyData, onSend, onCancel, sending }) => {
  return (
    <Card className="border-2 border-primary/20">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <h3 className="font-medium">Reply</h3>
          <Button variant="ghost" size="sm" onClick={onCancel}>
            <X className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">To:</label>
          <input
            type="text"
            value={replyData.to.join(', ')}
            onChange={(e) => setReplyData({
              ...replyData,
              to: e.target.value.split(',').map(email => email.trim()).filter(Boolean)
            })}
            className="w-full px-3 py-2 border rounded-md text-sm"
            placeholder="recipient@example.com"
          />
        </div>
        
        <div className="space-y-2">
          <label className="text-sm font-medium">Subject:</label>
          <input
            type="text"
            value={replyData.reply_subject}
            onChange={(e) => setReplyData({...replyData, reply_subject: e.target.value})}
            className="w-full px-3 py-2 border rounded-md text-sm"
          />
        </div>
        
        <div className="space-y-2">
          <label className="text-sm font-medium">Message:</label>
          <textarea
            value={replyData.reply_body}
            onChange={(e) => setReplyData({...replyData, reply_body: e.target.value})}
            className="w-full px-3 py-2 border rounded-md text-sm min-h-[120px]"
            placeholder="Type your reply..."
          />
        </div>
        
        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={onCancel} disabled={sending}>
            Cancel
          </Button>
          <Button onClick={onSend} disabled={sending || !replyData.reply_body.trim()}>
            {sending ? (
              <>Sending...</>
            ) : (
              <>
                <Send className="h-4 w-4 mr-2" />
                Send Reply
              </>
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

export default ThreadViewer 