import React, { useState } from 'react'
import { clsx } from 'clsx'
import { Inbox, Settings, Mail, ChevronLeft, ChevronRight } from 'lucide-react'
import { Button } from './ui/button'

const Sidebar = ({ activeSection, onSectionChange }) => {
  const [isCollapsed, setIsCollapsed] = useState(false)

  const navigationItems = [
    {
      id: 'inbox',
      label: 'Inbox',
      icon: Inbox,
      position: 'top'
    }
  ]

  const settingsItems = [
    {
      id: 'settings',
      label: 'Settings',
      icon: Settings,
      position: 'bottom'
    }
  ]

  const SidebarItem = ({ item, isActive, onClick }) => {
    const Icon = item.icon
    
    return (
      <button
        onClick={() => onClick(item.id)}
        className={clsx(
          "w-full flex items-center gap-3 px-4 py-3 text-left rounded-lg transition-colors",
          "hover:bg-accent hover:text-accent-foreground",
          isActive && "bg-accent text-accent-foreground font-medium",
          isCollapsed && "justify-center px-2"
        )}
        title={isCollapsed ? item.label : undefined}
      >
        <Icon className="h-5 w-5 flex-shrink-0" />
        {!isCollapsed && <span className="truncate">{item.label}</span>}
      </button>
    )
  }

  return (
    <div className={clsx(
      "bg-background border-r flex flex-col h-full transition-all duration-300",
      isCollapsed ? "w-16" : "w-64"
    )}>
      {/* Header */}
      <div className={clsx(
        "border-b flex items-center justify-between",
        isCollapsed ? "p-3" : "p-6"
      )}>
        <div className="fi-sidebar-header-content flex items-center gap-2">
          <Mail className="fi-sidebar-logo h-6 w-6 text-primary flex-shrink-0" />
          {!isCollapsed && <h1 className="fi-app-title text-xl font-bold">Finance Inbox</h1>}
        </div>
        
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setIsCollapsed(!isCollapsed)}
          className={clsx(
            "h-8 w-8 flex-shrink-0",
            isCollapsed && "ml-0"
          )}
        >
          {isCollapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </Button>
      </div>

      {/* Navigation Items */}
      <div className={clsx(
        "flex-1",
        isCollapsed ? "p-2" : "p-4"
      )}>
        <nav className="space-y-1">
          {navigationItems.map((item) => (
            <SidebarItem
              key={item.id}
              item={item}
              isActive={activeSection === item.id}
              onClick={onSectionChange}
            />
          ))}
        </nav>
      </div>

      {/* Settings at Bottom */}
      <div className={clsx(
        "border-t",
        isCollapsed ? "p-2" : "p-4"
      )}>
        <nav className="space-y-1">
          {settingsItems.map((item) => (
            <SidebarItem
              key={item.id}
              item={item}
              isActive={activeSection === item.id}
              onClick={onSectionChange}
            />
          ))}
        </nav>
      </div>
    </div>
  )
}

export default Sidebar 