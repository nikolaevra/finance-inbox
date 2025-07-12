import React from 'react'
import { Card } from './ui/card'
import { Badge } from './ui/badge'
import { Paperclip, Star, AlertCircle, Users } from 'lucide-react'
import { cn } from '../lib/utils'
import EmailCategoryBadge from './EmailCategoryBadge'

const ThreadList = ({ threads, selectedThread, onThreadSelect, loading }) => {
  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-muted-foreground">Loading email threads...</div>
      </div>
    )
  }

  if (!threads || threads.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center text-muted-foreground">
          <div className="text-lg mb-2">No email threads found</div>
          <div className="text-sm">Try syncing your emails first</div>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-4 border-b">
        <h2 className="text-lg font-semibold">Inbox</h2>
        <p className="text-sm text-muted-foreground">
          {threads.length} threads, {threads.reduce((sum, thread) => sum + thread.email_count, 0)} total emails
        </p>
      </div>
      
      <div className="divide-y">
        {threads.map((thread) => (
          <ThreadListItem
            key={thread.thread_id}
            thread={thread}
            isSelected={selectedThread?.thread_id === thread.thread_id}
            onClick={() => onThreadSelect(thread)}
          />
        ))}
      </div>
    </div>
  )
}

const ThreadListItem = ({ thread, isSelected, onClick }) => {
  return (
    <div
      className={cn(
        "p-4 cursor-pointer hover:bg-accent transition-colors",
        isSelected && "bg-accent",
        thread.is_unread && "border-l-2 border-l-blue-500"
      )}
      onClick={onClick}
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <div className={cn(
              "font-medium text-sm truncate",
              thread.is_unread && "font-semibold"
            )}>
              {thread.latest_sender}
            </div>
            
            {/* Thread indicators */}
            <div className="flex items-center gap-1 flex-shrink-0">
              {thread.email_count > 1 && (
                <div className="flex items-center gap-1 bg-muted px-1.5 py-0.5 rounded text-xs">
                  <Users className="h-3 w-3" />
                  <span>{thread.email_count}</span>
                </div>
              )}
              
              {thread.unread_count > 0 && (
                <div className="bg-blue-500 text-white px-1.5 py-0.5 rounded text-xs font-medium">
                  {thread.unread_count}
                </div>
              )}
              
              {thread.has_attachments && (
                <Paperclip className="h-3 w-3 text-muted-foreground" />
              )}
            </div>
          </div>
          
          <div className={cn(
            "text-sm mb-1 truncate",
            thread.is_unread ? "font-medium" : "text-muted-foreground"
          )}>
            {thread.subject}
          </div>
          
          <div className="text-xs text-muted-foreground truncate mb-2">
            {thread.latest_snippet}
          </div>
          
          {/* Show category badge if available */}
          {thread.emails && thread.emails.length > 0 && thread.emails[0].category && (
            <div className="mt-2">
              <EmailCategoryBadge 
                category={thread.emails[0].category}
                confidence={thread.emails[0].category_confidence}
                className="text-xs"
              />
            </div>
          )}
        </div>
        
        <div className="text-xs text-muted-foreground flex-shrink-0">
          {thread.latest_date}
        </div>
      </div>
      
      {thread.labels && thread.labels.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {thread.labels.slice(0, 3).map((label) => (
            <Badge
              key={label}
              variant="secondary"
              className="text-xs px-1.5 py-0.5"
            >
              {label}
            </Badge>
          ))}
          {thread.labels.length > 3 && (
            <Badge variant="outline" className="text-xs px-1.5 py-0.5">
              +{thread.labels.length - 3}
            </Badge>
          )}
        </div>
      )}
    </div>
  )
}

export default ThreadList 