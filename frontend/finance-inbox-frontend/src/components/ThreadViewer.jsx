import React, { useState, useEffect, useRef } from 'react'
import { Card, CardContent, CardHeader } from './ui/card'
import { Badge } from './ui/badge'
import { Button } from './ui/button'
import { Paperclip, Star, AlertCircle, Reply, ChevronUp, ChevronDown, Send, X, Plus, Minus, CheckCircle, AlertTriangle } from 'lucide-react'
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
  const [replySuccess, setReplySuccess] = useState(false)
  const [replyError, setReplyError] = useState('')
  const replyFormRef = useRef(null)
  
  const { getAuthHeaders } = useAuth()

  const extractEmailAddress = (email) => {
    // Extract just the email part from "Display Name <email@domain.com>" format
    const displayNameRegex = /^.+<([^\s@]+@[^\s@]+\.[^\s@]+)>$/
    const match = email.match(displayNameRegex)
    return match ? match[1] : email
  }

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

  // Auto-scroll to reply form when it becomes visible
  useEffect(() => {
    if (showReplyForm && replyFormRef.current) {
      // Use setTimeout to ensure the form is fully rendered before scrolling
      setTimeout(() => {
        replyFormRef.current.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'center' 
        })
      }, 100)
    }
  }, [showReplyForm])

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
    if (!email) {
      console.error('No email provided to handleReply')
      return
    }
    
    const currentThreadToShow = fullThread || thread
    const originalSubject = email.subject || currentThreadToShow?.subject || ''
    const replySubject = originalSubject.startsWith('Re:') ? originalSubject : `Re: ${originalSubject}`
    
    // Use the original email format for display, but it will be cleaned when sending
    const fromEmail = email.from_email || email.sender
    const newReplyData = {
      reply_body: '',
      reply_subject: replySubject,
      to: fromEmail ? [fromEmail] : [],
      cc: [],
      bcc: []
    }
    
    setReplyData(newReplyData)
    setShowReplyForm(true)
    setReplyError('')
    setReplySuccess(false)
  }

  const sendReply = async (emailId) => {
    setSendingReply(true)
    setReplyError('')
    setReplySuccess(false)
    
    try {
      // Extract clean email addresses for the backend
      const cleanReplyData = {
        ...replyData,
        to: replyData.to.map(email => extractEmailAddress(email)),
        cc: replyData.cc.map(email => extractEmailAddress(email)),
        bcc: replyData.bcc.map(email => extractEmailAddress(email))
      }
      

      
      const response = await axios.post(API_ENDPOINTS.INBOX.REPLY(emailId), cleanReplyData, {
        headers: getAuthHeaders()
      })
      
      // Show success feedback
      setReplySuccess(true)
      
      // Clear reply form and close it after a brief delay
      setTimeout(() => {
        setReplyData({
          reply_body: '',
          reply_subject: '',
          to: [],
          cc: [],
          bcc: []
        })
        setShowReplyForm(false)
        setReplySuccess(false)
      }, 1500)
      
      // Refresh the thread to show the new reply
      if (onThreadUpdate) {
        onThreadUpdate()
      }
      fetchFullThread(thread.thread_id)
      
    } catch (error) {
      console.error('Error sending reply:', error)
      setReplyError(error.response?.data?.detail || 'Failed to send reply. Please try again.')
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
                onClick={() => {
                  const lastEmail = emails[emails.length - 1]
                  if (lastEmail) {
                    handleReply(lastEmail)
                  } else {
                    console.error('No emails found to reply to')
                  }
                }}
                disabled={emails.length === 0}
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
            <div ref={replyFormRef}>
              <ReplyForm
                replyData={replyData}
                setReplyData={setReplyData}
                onSend={() => sendReply(emails[emails.length - 1]?.gmail_id)}
                onCancel={() => setShowReplyForm(false)}
                sending={sendingReply}
                success={replySuccess}
                error={replyError}
              />
            </div>
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

const ReplyForm = ({ replyData, setReplyData, onSend, onCancel, sending, success, error }) => {
  const [showCcBcc, setShowCcBcc] = useState(false)
  
  const isValidEmail = (email) => {
    // Handle both formats: "email@domain.com" and "Display Name <email@domain.com>"
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    const displayNameRegex = /^.+<([^\s@]+@[^\s@]+\.[^\s@]+)>$/
    
    if (emailRegex.test(email)) {
      return true
    }
    
    const match = email.match(displayNameRegex)
    if (match && match[1]) {
      return emailRegex.test(match[1])
    }
    
    return false
  }
  
  const hasValidRecipients = () => {
    return replyData.to.length > 0 && replyData.to.every(email => isValidEmail(email))
  }
  
  const canSend = () => {
    return replyData.reply_body.trim() && hasValidRecipients() && !sending
  }
  
  const handleKeyDown = (e) => {
    if (e.ctrlKey && e.key === 'Enter') {
      e.preventDefault()
      if (canSend()) {
        onSend()
      }
    }
  }

  return (
    <Card className="border-2 border-primary/20">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h3 className="font-medium">Reply</h3>
            {success && (
              <div className="flex items-center gap-1 text-green-600">
                <CheckCircle className="h-4 w-4" />
                <span className="text-sm">Sent successfully!</span>
              </div>
            )}
          </div>
          <Button variant="ghost" size="sm" onClick={onCancel} disabled={sending}>
            <X className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Error Message */}
        {error && (
          <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-md text-red-700">
            <AlertTriangle className="h-4 w-4 flex-shrink-0" />
            <span className="text-sm">{error}</span>
          </div>
        )}
        
        {/* To Field */}
        <div className="space-y-2">
          <label className="text-sm font-medium">To: <span className="text-red-500">*</span></label>
          <input
            type="text"
            value={replyData.to.join(', ')}
            onChange={(e) => setReplyData({
              ...replyData,
              to: e.target.value.split(',').map(email => email.trim()).filter(Boolean)
            })}
            className={cn(
              "w-full px-3 py-2 border rounded-md text-sm",
              !hasValidRecipients() && replyData.to.length > 0 ? "border-red-300" : "border-gray-300"
            )}
            placeholder="recipient@example.com, another@example.com"
            disabled={sending}
          />
          {!hasValidRecipients() && replyData.to.length > 0 && (
            <p className="text-xs text-red-600">Please enter valid email addresses</p>
          )}
        </div>
        
        {/* CC/BCC Toggle */}
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowCcBcc(!showCcBcc)}
            disabled={sending}
          >
            {showCcBcc ? (
              <>
                <Minus className="h-3 w-3 mr-1" />
                Hide CC/BCC
              </>
            ) : (
              <>
                <Plus className="h-3 w-3 mr-1" />
                Add CC/BCC
              </>
            )}
          </Button>
        </div>
        
        {/* CC Field */}
        {showCcBcc && (
          <div className="space-y-2">
            <label className="text-sm font-medium">CC:</label>
            <input
              type="text"
              value={replyData.cc.join(', ')}
              onChange={(e) => setReplyData({
                ...replyData,
                cc: e.target.value.split(',').map(email => email.trim()).filter(Boolean)
              })}
              className="w-full px-3 py-2 border rounded-md text-sm"
              placeholder="cc@example.com, another-cc@example.com"
              disabled={sending}
            />
          </div>
        )}
        
        {/* BCC Field */}
        {showCcBcc && (
          <div className="space-y-2">
            <label className="text-sm font-medium">BCC:</label>
            <input
              type="text"
              value={replyData.bcc.join(', ')}
              onChange={(e) => setReplyData({
                ...replyData,
                bcc: e.target.value.split(',').map(email => email.trim()).filter(Boolean)
              })}
              className="w-full px-3 py-2 border rounded-md text-sm"
              placeholder="bcc@example.com, another-bcc@example.com"
              disabled={sending}
            />
          </div>
        )}
        
        {/* Subject Field */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Subject:</label>
          <input
            type="text"
            value={replyData.reply_subject}
            onChange={(e) => setReplyData({...replyData, reply_subject: e.target.value})}
            className="w-full px-3 py-2 border rounded-md text-sm"
            disabled={sending}
          />
        </div>
        
        {/* Message Body */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Message: <span className="text-red-500">*</span></label>
          <textarea
            value={replyData.reply_body}
            onChange={(e) => setReplyData({...replyData, reply_body: e.target.value})}
            onKeyDown={handleKeyDown}
            className="w-full px-3 py-2 border rounded-md text-sm min-h-[120px] resize-y"
            placeholder="Type your reply... (Ctrl+Enter to send)"
            disabled={sending}
          />
          <div className="text-xs text-muted-foreground text-right">
            {replyData.reply_body.length} characters
          </div>
        </div>
        
        {/* Action Buttons */}
        <div className="flex justify-between items-center pt-2">
          <div className="text-xs text-muted-foreground">
            {showCcBcc && (replyData.cc.length > 0 || replyData.bcc.length > 0) && (
              <span>
                {replyData.cc.length > 0 && `CC: ${replyData.cc.length}`}
                {replyData.cc.length > 0 && replyData.bcc.length > 0 && ', '}
                {replyData.bcc.length > 0 && `BCC: ${replyData.bcc.length}`}
              </span>
            )}
          </div>
          
          <div className="flex gap-2">
            <Button variant="outline" onClick={onCancel} disabled={sending}>
              Cancel
            </Button>
            <Button 
              onClick={onSend} 
              disabled={!canSend()}
              className={cn(
                success && "bg-green-600 hover:bg-green-700"
              )}
              title="Send reply (Ctrl+Enter)"
            >
              {sending ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                  Sending...
                </>
              ) : success ? (
                <>
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Sent!
                </>
              ) : (
                <>
                  <Send className="h-4 w-4 mr-2" />
                  Send Reply
                </>
              )}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export default ThreadViewer 