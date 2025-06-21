import React, { useState } from 'react'
import Sidebar from './Sidebar'
import Inbox from './Inbox'
import Settings from './Settings'

const Layout = () => {
  const [activeSection, setActiveSection] = useState('inbox')

  const renderContent = () => {
    switch (activeSection) {
      case 'inbox':
        return <Inbox />
      case 'settings':
        return <Settings />
      default:
        return <Inbox />
    }
  }

  return (
    <div className="h-screen flex bg-background">
      {/* Sidebar */}
      <Sidebar 
        activeSection={activeSection} 
        onSectionChange={setActiveSection}
      />
      
      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        {renderContent()}
      </div>
    </div>
  )
}

export default Layout 