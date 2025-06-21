import React from 'react'
import { Card } from './ui/card'
import { Badge } from './ui/badge'
import { Paperclip, Star, AlertCircle } from 'lucide-react'
import { cn } from '../lib/utils'

const EmailList = ({ emails, selectedEmail, onEmailSelect, loading }) => {
  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-muted-foreground">Loading emails...</div>
      </div>
    )
  }

  if (!emails || emails.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center text-muted-foreground">
          <div className="text-lg mb-2">No emails found</div>
          <div className="text-sm">Try syncing your emails first</div>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-4 border-b">
        <h2 className="text-lg font-semibold">Inbox</h2>
        <p className="text-sm text-muted-foreground">{emails.length} emails</p>
      </div>
      
      <div className="divide-y">
        {emails.map((email) => (
          <EmailListItem
            key={email.gmail_id}
            email={email}
            isSelected={selectedEmail?.gmail_id === email.gmail_id}
            onClick={() => onEmailSelect(email)}
          />
        ))}
      </div>
    </div>
  )
}

const EmailListItem = ({ email, isSelected, onClick }) => {
  return (
    <div
      className={cn(
        "p-4 cursor-pointer hover:bg-accent transition-colors",
        isSelected && "bg-accent",
        email.is_unread && "border-l-2 border-l-blue-500"
      )}
      onClick={onClick}
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <div className={cn(
              "font-medium text-sm truncate",
              email.is_unread && "font-semibold"
            )}>
              {email.sender || email.from_email}
            </div>
            <div className="flex items-center gap-1 flex-shrink-0">
              {email.is_important && (
                <AlertCircle className="h-3 w-3 text-orange-500" />
              )}
              {email.is_starred && (
                <Star className="h-3 w-3 text-yellow-500 fill-current" />
              )}
              {email.has_attachments && (
                <Paperclip className="h-3 w-3 text-muted-foreground" />
              )}
            </div>
          </div>
          
          <div className={cn(
            "text-sm mb-1 truncate",
            email.is_unread ? "font-medium" : "text-muted-foreground"
          )}>
            {email.subject}
          </div>
          
          <div className="text-xs text-muted-foreground truncate mb-2">
            {email.snippet}
          </div>
        </div>
        
        <div className="text-xs text-muted-foreground flex-shrink-0">
          {email.date}
        </div>
      </div>
      
      {email.labels && email.labels.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {email.labels.slice(0, 3).map((label) => (
            <Badge
              key={label}
              variant="secondary"
              className="text-xs px-1.5 py-0.5"
            >
              {label}
            </Badge>
          ))}
          {email.labels.length > 3 && (
            <Badge variant="outline" className="text-xs px-1.5 py-0.5">
              +{email.labels.length - 3}
            </Badge>
          )}
        </div>
      )}
    </div>
  )
}

export default EmailList 