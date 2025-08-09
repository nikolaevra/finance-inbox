import React from 'react'
import { Badge } from './ui/badge'

const EmailCategoryBadge = ({ category, confidence, className = "" }) => {
  if (!category) return null

  // Category color mapping for financial professionals
  const categoryColors = {
    'CLIENT_COMMUNICATION': 'bg-blue-100 text-blue-800 border-blue-200',
    'MARKET_RESEARCH': 'bg-green-100 text-green-800 border-green-200',
    'REGULATORY_COMPLIANCE': 'bg-red-100 text-red-800 border-red-200',
    'FINANCIAL_REPORTING': 'bg-purple-100 text-purple-800 border-purple-200',
    'TRANSACTION_ALERTS': 'bg-yellow-100 text-yellow-800 border-yellow-200',
    'INTERNAL_OPERATIONS': 'bg-gray-100 text-gray-800 border-gray-200',
    'VENDOR_SERVICES': 'bg-indigo-100 text-indigo-800 border-indigo-200',
    'MARKETING_SALES': 'bg-orange-100 text-orange-800 border-orange-200',
    'EDUCATIONAL_CONTENT': 'bg-teal-100 text-teal-800 border-teal-200',
    'OTHER': 'bg-slate-100 text-slate-800 border-slate-200'
  }

  // Category display names (user-friendly)
  const categoryNames = {
    'CLIENT_COMMUNICATION': 'Client',
    'MARKET_RESEARCH': 'Research',
    'REGULATORY_COMPLIANCE': 'Compliance',
    'FINANCIAL_REPORTING': 'Reporting',
    'TRANSACTION_ALERTS': 'Transaction',
    'INTERNAL_OPERATIONS': 'Internal',
    'VENDOR_SERVICES': 'Vendor',
    'MARKETING_SALES': 'Marketing',
    'EDUCATIONAL_CONTENT': 'Education',
    'OTHER': 'Other'
  }

  // Confidence indicators
  const getConfidenceIcon = (confidence) => {
    if (!confidence) return null
    if (confidence >= 0.8) return '●' // High confidence
    if (confidence >= 0.5) return '◐' // Medium confidence
    return '○' // Low confidence
  }

  const colorClass = categoryColors[category] || categoryColors['OTHER']
  const displayName = categoryNames[category] || category

  return (
    <Badge 
      variant="secondary" 
      className={`${colorClass} ${className} text-xs font-medium flex items-center gap-1`}
      title={`Category: ${category}${confidence ? ` (${Math.round(confidence * 100)}% confidence)` : ''}`}
    >
      {confidence && (
        <span className="opacity-60" title={`${Math.round(confidence * 100)}% confidence`}>
          {getConfidenceIcon(confidence)}
        </span>
      )}
      {displayName}
    </Badge>
  )
}

export default EmailCategoryBadge 