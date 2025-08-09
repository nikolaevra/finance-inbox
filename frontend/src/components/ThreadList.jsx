import React from 'react'
import { Card } from './ui/card'
import { Badge } from './ui/badge'
import { Paperclip, Star, AlertCircle, Users, Filter } from 'lucide-react'
import { clsx } from 'clsx'
import EmailCategoryBadge from './EmailCategoryBadge'

const ThreadList = ({ threads, selectedThread, onThreadSelect, loading, activeFilters = [] }) => {
  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-muted-foreground">Loading email threads...</div>
      </div>
    )
  }

  if (!threads || threads.length === 0) {
    const isFiltered = activeFilters.length > 0
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center text-muted-foreground">
          <div className="text-lg mb-2">
            {isFiltered ? 'No emails match the selected filters' : 'No email threads found'}
          </div>
          <div className="text-sm">
            {isFiltered ? 'Try selecting different categories or clearing filters' : 'Try syncing your emails first'}
          </div>
          {isFiltered && (
            <div className="mt-4 flex items-center justify-center gap-2">
              <Filter className="h-4 w-4" />
              <span className="text-xs">
                {activeFilters.length} filter{activeFilters.length > 1 ? 's' : ''} active
              </span>
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-4 border-b">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Inbox</h2>
          {activeFilters.length > 0 && (
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Filter className="h-3 w-3" />
              <span>Filtered</span>
            </div>
          )}
        </div>
        <p className="text-sm text-muted-foreground">
          {activeFilters.length > 0 
            ? `${threads.length} threads match filters (${threads.reduce((sum, thread) => sum + thread.email_count, 0)} emails)`
            : `${threads.length} threads, ${threads.reduce((sum, thread) => sum + thread.email_count, 0)} total emails`
          }
        </p>
      </div>
      
      <div className="divide-y">
        {threads.map((thread) => (
          <ThreadListItem
            key={thread.thread_id}
            thread={thread}
            isSelected={selectedThread?.thread_id === thread.thread_id}
            onClick={() => onThreadSelect(thread)}
            activeFilters={activeFilters}
          />
        ))}
      </div>
    </div>
  )
}

const ThreadListItem = ({ thread, isSelected, onClick, activeFilters = [] }) => {
  // Check if this thread has categories that match active filters
  const hasMatchingCategory = activeFilters.length > 0 && thread.emails && thread.emails.some(email => 
    email.category && activeFilters.includes(email.category)
  )

  return (
    <div
      className={clsx(
        "p-4 cursor-pointer hover:bg-accent transition-colors",
        isSelected && "bg-accent",
        thread.is_unread && "border-l-2 border-l-blue-500",
        hasMatchingCategory && "ring-1 ring-blue-200 bg-blue-50/30"
      )}
      onClick={onClick}
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <div className={clsx(
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

              {hasMatchingCategory && (
                <div className="bg-blue-100 text-blue-600 px-1.5 py-0.5 rounded text-xs font-medium">
                  ✓
                </div>
              )}
            </div>
          </div>
          
          <div className={clsx(
            "text-sm mb-1 truncate",
            thread.is_unread ? "font-medium" : "text-muted-foreground"
          )}>
            {thread.subject}
          </div>
          
          <div className="text-xs text-muted-foreground truncate mb-2">
            {thread.latest_snippet}
          </div>
          
          {/* Show category badges - highlight active ones */}
          {thread.emails && thread.emails.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {thread.emails
                .filter(email => email.category)
                .slice(0, 3) // Limit to 3 categories to avoid clutter
                .map((email, index) => (
                  <EmailCategoryBadge 
                    key={`${email.category}-${index}`}
                    category={email.category}
                    confidence={email.category_confidence}
                    className={clsx(
                      "text-xs",
                      activeFilters.includes(email.category) && "ring-1 ring-current"
                    )}
                  />
                ))
              }
              {thread.emails.filter(email => email.category).length > 3 && (
                <Badge variant="outline" className="text-xs px-1.5 py-0.5">
                  +{thread.emails.filter(email => email.category).length - 3}
                </Badge>
              )}
            </div>
          )}
        </div>
        
        <div className="text-xs text-muted-foreground flex-shrink-0">
          {thread.latest_date}
        </div>
      </div>
      
      {thread.labels && thread.labels.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-2">
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