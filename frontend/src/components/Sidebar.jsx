import React, { useState } from 'react'
import { clsx } from 'clsx'
import { 
  Inbox, Settings, Mail, ChevronLeft, ChevronRight, 
  Users, TrendingUp, Shield, BarChart3, CreditCard, 
  Building2, Package, Megaphone, GraduationCap, HelpCircle,
  X, Filter
} from 'lucide-react'
import { Button } from './ui/button'
import { Badge } from './ui/badge'

const Sidebar = ({ activeSection, onSectionChange, threads = [], activeFilters = [], onFilterChange }) => {
  const [isCollapsed, setIsCollapsed] = useState(false)

  // Calculate category counts from threads
  const getCategoryCounts = () => {
    const counts = {}
    
    threads.forEach(thread => {
      if (thread.emails && thread.emails.length > 0) {
        // Only count unread emails (is_read is false or not set)
        const unreadEmailsWithCategories = thread.emails.filter(email => 
          email.category && !email.is_read
        )
        
        unreadEmailsWithCategories.forEach(email => {
          counts[email.category] = (counts[email.category] || 0) + 1
        })
      }
    })
    
    return counts
  }

  const categoryCounts = getCategoryCounts()

  // Category configuration with beautiful icons and colors
  const categoryConfig = {
    'CLIENT_COMMUNICATION': {
      name: 'Client Comm',
      icon: Users,
      gradient: 'from-blue-500 to-blue-600',
      bgGradient: 'from-blue-50 to-blue-100',
      textColor: 'text-blue-700',
      borderColor: 'border-blue-500',
      badgeColor: 'bg-blue-100 text-blue-700 border-blue-200',
      activeBg: 'bg-gradient-to-r from-blue-500 to-blue-600',
      hoverBg: 'hover:from-blue-100 hover:to-blue-200'
    },
    'MARKET_RESEARCH': {
      name: 'Research',
      icon: TrendingUp,
      gradient: 'from-emerald-500 to-emerald-600',
      bgGradient: 'from-emerald-50 to-emerald-100',
      textColor: 'text-emerald-700',
      borderColor: 'border-emerald-500',
      badgeColor: 'bg-emerald-100 text-emerald-700 border-emerald-200',
      activeBg: 'bg-gradient-to-r from-emerald-500 to-emerald-600',
      hoverBg: 'hover:from-emerald-100 hover:to-emerald-200'
    },
    'REGULATORY_COMPLIANCE': {
      name: 'Compliance',
      icon: Shield,
      gradient: 'from-red-500 to-red-600',
      bgGradient: 'from-red-50 to-red-100',
      textColor: 'text-red-700',
      borderColor: 'border-red-500',
      badgeColor: 'bg-red-100 text-red-700 border-red-200',
      activeBg: 'bg-gradient-to-r from-red-500 to-red-600',
      hoverBg: 'hover:from-red-100 hover:to-red-200'
    },
    'FINANCIAL_REPORTING': {
      name: 'Reporting',
      icon: BarChart3,
      gradient: 'from-purple-500 to-purple-600',
      bgGradient: 'from-purple-50 to-purple-100',
      textColor: 'text-purple-700',
      borderColor: 'border-purple-500',
      badgeColor: 'bg-purple-100 text-purple-700 border-purple-200',
      activeBg: 'bg-gradient-to-r from-purple-500 to-purple-600',
      hoverBg: 'hover:from-purple-100 hover:to-purple-200'
    },
    'TRANSACTION_ALERTS': {
      name: 'Transactions',
      icon: CreditCard,
      gradient: 'from-amber-500 to-amber-600',
      bgGradient: 'from-amber-50 to-amber-100',
      textColor: 'text-amber-700',
      borderColor: 'border-amber-500',
      badgeColor: 'bg-amber-100 text-amber-700 border-amber-200',
      activeBg: 'bg-gradient-to-r from-amber-500 to-amber-600',
      hoverBg: 'hover:from-amber-100 hover:to-amber-200'
    },
    'INTERNAL_OPERATIONS': {
      name: 'Internal',
      icon: Building2,
      gradient: 'from-slate-500 to-slate-600',
      bgGradient: 'from-slate-50 to-slate-100',
      textColor: 'text-slate-700',
      borderColor: 'border-slate-500',
      badgeColor: 'bg-slate-100 text-slate-700 border-slate-200',
      activeBg: 'bg-gradient-to-r from-slate-500 to-slate-600',
      hoverBg: 'hover:from-slate-100 hover:to-slate-200'
    },
    'VENDOR_SERVICES': {
      name: 'Vendors',
      icon: Package,
      gradient: 'from-indigo-500 to-indigo-600',
      bgGradient: 'from-indigo-50 to-indigo-100',
      textColor: 'text-indigo-700',
      borderColor: 'border-indigo-500',
      badgeColor: 'bg-indigo-100 text-indigo-700 border-indigo-200',
      activeBg: 'bg-gradient-to-r from-indigo-500 to-indigo-600',
      hoverBg: 'hover:from-indigo-100 hover:to-indigo-200'
    },
    'MARKETING_SALES': {
      name: 'Marketing',
      icon: Megaphone,
      gradient: 'from-orange-500 to-orange-600',
      bgGradient: 'from-orange-50 to-orange-100',
      textColor: 'text-orange-700',
      borderColor: 'border-orange-500',
      badgeColor: 'bg-orange-100 text-orange-700 border-orange-200',
      activeBg: 'bg-gradient-to-r from-orange-500 to-orange-600',
      hoverBg: 'hover:from-orange-100 hover:to-orange-200'
    },
    'EDUCATIONAL_CONTENT': {
      name: 'Education',
      icon: GraduationCap,
      gradient: 'from-teal-500 to-teal-600',
      bgGradient: 'from-teal-50 to-teal-100',
      textColor: 'text-teal-700',
      borderColor: 'border-teal-500',
      badgeColor: 'bg-teal-100 text-teal-700 border-teal-200',
      activeBg: 'bg-gradient-to-r from-teal-500 to-teal-600',
      hoverBg: 'hover:from-teal-100 hover:to-teal-200'
    },
    'OTHER': {
      name: 'Other',
      icon: HelpCircle,
      gradient: 'from-gray-500 to-gray-600',
      bgGradient: 'from-gray-50 to-gray-100',
      textColor: 'text-gray-700',
      borderColor: 'border-gray-500',
      badgeColor: 'bg-gray-100 text-gray-700 border-gray-200',
      activeBg: 'bg-gradient-to-r from-gray-500 to-gray-600',
      hoverBg: 'hover:from-gray-100 hover:to-gray-200'
    }
  }

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

  const handleCategoryFilter = (category) => {
    // Single-select mode: if the same category is clicked, clear it; otherwise set new category
    const newFilters = activeFilters.includes(category) ? [] : [category]
    onFilterChange(newFilters)
  }

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

  const CategoryFilterItem = ({ category, config, count, isActive, hasUnread }) => {
    const Icon = config.icon
    
    return (
      <button
        onClick={() => handleCategoryFilter(category)}
        className={clsx(
          "group relative w-full flex items-center gap-3 px-4 py-3.5 text-left rounded-xl transition-all duration-300 transform",
          "shadow-sm backdrop-blur-sm",
          isActive 
            ? `bg-gradient-to-r ${config.bgGradient} ${config.textColor} shadow-md scale-[1.02] border-2 ${config.borderColor}` 
            : hasUnread
              ? `bg-gradient-to-r ${config.bgGradient} ${config.textColor} hover:shadow-md hover:scale-[1.01] border border-transparent ${config.hoverBg}`
              : "bg-gray-50 text-gray-400 hover:bg-gray-100 border border-transparent",
          isCollapsed && "justify-center px-3",
          "hover:translate-y-[-1px]",
          !hasUnread && !isActive && "opacity-60"
        )}
        title={isCollapsed ? `${config.name} (${count} unread)` : undefined}
      >
        {/* Icon with gradient background */}
        <div className={clsx(
          "flex items-center justify-center w-8 h-8 rounded-lg transition-all duration-300",
          isActive 
            ? `bg-gradient-to-br ${config.gradient} shadow-sm` 
            : hasUnread
              ? `bg-gradient-to-br ${config.gradient} shadow-sm`
              : "bg-gray-300"
        )}>
          <Icon className={clsx(
            "h-4 w-4 transition-all duration-300",
            isActive ? "text-white" : hasUnread ? "text-white" : "text-gray-500"
          )} />
        </div>
        
        {!isCollapsed && (
          <>
            <div className="flex-1 min-w-0">
              <span className={clsx(
                "font-semibold text-sm transition-all duration-300",
                isActive 
                  ? config.textColor 
                  : hasUnread 
                    ? config.textColor 
                    : "text-gray-400"
              )}>
                {config.name}
              </span>
              <div className={clsx(
                "text-xs mt-0.5 transition-all duration-300",
                isActive 
                  ? "text-gray-600" 
                  : hasUnread 
                    ? "text-gray-500" 
                    : "text-gray-400"
              )}>
                {count} unread
              </div>
            </div>
            
            {/* Count badge */}
            <div className={clsx(
              "flex items-center justify-center min-w-[24px] h-6 px-2 rounded-full text-xs font-bold transition-all duration-300",
              isActive 
                ? "bg-white shadow-sm " + config.textColor
                : hasUnread
                  ? "bg-white shadow-sm " + config.textColor
                  : "bg-gray-200 text-gray-400"
            )}>
              {count}
            </div>
          </>
        )}
        
        {/* Remove the ring effect since we're using border now */}
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

      {/* AI Categories Section */}
      <div className={clsx(
        "flex-1 border-t border-gray-200/50",
        isCollapsed ? "p-2" : "p-4"
      )}>
        {!isCollapsed && (
          <div className="flex items-center mb-4">
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 shadow-sm">
                <Filter className="h-4 w-4 text-white" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-gray-900">Smart Filters</h3>
                <p className="text-xs text-gray-500">AI-powered categories</p>
              </div>
            </div>
          </div>
        )}
        
        <nav className="space-y-2.5 max-h-96 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-transparent">
          {Object.entries(categoryConfig).map(([category, config]) => {
            const count = categoryCounts[category] || 0
            const isActive = activeFilters.includes(category)
            
            // Show all categories, but style them differently based on count and active state
            return (
              <CategoryFilterItem
                key={category}
                category={category}
                config={config}
                count={count}
                isActive={isActive}
                hasUnread={count > 0}
              />
            )
          })}
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