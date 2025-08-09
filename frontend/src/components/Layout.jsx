import React, { useState, useEffect } from 'react'
import Sidebar from './Sidebar'
import Inbox from './Inbox'
import Settings from './Settings'
import { useAuth } from '../contexts/AuthContext'
import axios from 'axios'
import { API_ENDPOINTS } from '../config/api'

const Layout = () => {
  const [activeSection, setActiveSection] = useState('inbox')
  const [activeFilters, setActiveFilters] = useState([])
  const [threads, setThreads] = useState([])
  const { getAuthHeaders } = useAuth()

  // Load threads for sidebar category counts
  useEffect(() => {
    loadThreads()
  }, [])

  const loadThreads = async () => {
    try {
      const response = await axios.get(`${API_ENDPOINTS.INBOX.LIST}?limit=50`, {
        headers: getAuthHeaders()
      })
      setThreads(response.data.threads || [])
    } catch (error) {
      console.error('Error loading threads for sidebar:', error)
    }
  }

  const handleFilterChange = (newFilters) => {
    setActiveFilters(newFilters)
  }

  const renderContent = () => {
    switch (activeSection) {
      case 'inbox':
        return (
          <Inbox 
            activeFilters={activeFilters}
            onFilterChange={handleFilterChange}
          />
        )
      case 'settings':
        return <Settings />
      default:
        return (
          <Inbox 
            activeFilters={activeFilters}
            onFilterChange={handleFilterChange}
          />
        )
    }
  }

  return (
    <div className="h-screen flex bg-background">
      {/* Sidebar */}
      <Sidebar 
        activeSection={activeSection} 
        onSectionChange={setActiveSection}
        threads={threads}
        activeFilters={activeFilters}
        onFilterChange={handleFilterChange}
      />
      
      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        {renderContent()}
      </div>
    </div>
  )
}

export default Layout 