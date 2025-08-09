'use client'

import React, { useState, useEffect } from 'react'
import { Button } from '../ui/button'
import { Card } from '../ui/card'
import { Input } from '../ui/input'
import { gdprService } from '../../lib/compliance/gdpr.service'
import type { DataSubjectRequest } from '../../types/epic4'

interface DataSubjectRightsProps {
  userId: string
  onRequestSubmitted?: (request: DataSubjectRequest) => void
}

type RequestType = 'access' | 'rectification' | 'erasure' | 'portability' | 'restriction' | 'objection'

const REQUEST_TYPES: Array<{
  type: RequestType
  title: string
  description: string
  icon: string
  processingTime: string
}> = [
  {
    type: 'access',
    title: 'Right to Access',
    description: 'Request a copy of all personal data we hold about you',
    icon: '📋',
    processingTime: '30 days'
  },
  {
    type: 'rectification',
    title: 'Right to Rectification',
    description: 'Request correction of inaccurate or incomplete personal data',
    icon: '✏️',
    processingTime: '30 days'
  },
  {
    type: 'erasure',
    title: 'Right to Erasure',
    description: 'Request deletion of your personal data ("right to be forgotten")',
    icon: '🗑️',
    processingTime: '30 days'
  },
  {
    type: 'portability',
    title: 'Right to Data Portability',
    description: 'Request your data in a machine-readable format',
    icon: '📤',
    processingTime: '30 days'
  },
  {
    type: 'restriction',
    title: 'Right to Restriction',
    description: 'Request limitation of processing of your personal data',
    icon: '⏸️',
    processingTime: '30 days'
  },
  {
    type: 'objection',
    title: 'Right to Object',
    description: 'Object to processing based on legitimate interests or direct marketing',
    icon: '🚫',
    processingTime: '30 days'
  }
]

export function DataSubjectRights({ userId, onRequestSubmitted }: DataSubjectRightsProps) {
  const [selectedType, setSelectedType] = useState<RequestType | null>(null)
  const [requestDetails, setRequestDetails] = useState('')
  const [userRequests, setUserRequests] = useState<DataSubjectRequest[]>([])
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [showForm, setShowForm] = useState(false)

  useEffect(() => {
    loadUserRequests()
  }, [userId])

  const loadUserRequests = async () => {
    setLoading(true)
    try {
      const requests = await gdprService.getUserDataSubjectRequests(userId)
      setUserRequests(requests)
    } catch (error) {
      console.error('Failed to load user requests:', error)
    }
    setLoading(false)
  }

  const handleSubmitRequest = async () => {
    if (!selectedType || !requestDetails.trim()) return

    setSubmitting(true)
    try {
      const request = await gdprService.submitDataSubjectRequest({
        userId,
        requestType: selectedType,
        requestDetails: requestDetails.trim()
      })

      await gdprService.logGDPREvent({
        userId,
        action: 'data_subject_request_submitted',
        resource: 'data_subject_rights',
        resourceId: request.id,
        ipAddress: 'unknown',
        userAgent: navigator.userAgent,
        outcome: 'success',
        riskLevel: selectedType === 'erasure' ? 'high' : 'medium',
        details: { 
          requestType: selectedType,
          requestId: request.id
        }
      })

      setUserRequests(prev => [request, ...prev])
      setShowForm(false)
      setSelectedType(null)
      setRequestDetails('')
      onRequestSubmitted?.(request)
      
      // Show success message
      alert(`Your ${selectedType} request has been submitted successfully. You will receive updates via email.`)
    } catch (error) {
      console.error('Failed to submit request:', error)
      alert('Failed to submit request. Please try again.')
    }
    setSubmitting(false)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 bg-green-100'
      case 'in_progress':
        return 'text-blue-600 bg-blue-100'
      case 'rejected':
        return 'text-red-600 bg-red-100'
      default:
        return 'text-yellow-600 bg-yellow-100'
    }
  }

  const formatDate = (date: Date | string) => {
    return new Date(date).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const handleQuickAction = async (type: RequestType) => {
    if (type === 'access') {
      // Quick data access request
      setSubmitting(true)
      try {
        const request = await gdprService.submitDataSubjectRequest({
          userId,
          requestType: 'access',
          requestDetails: 'Request for complete data export including all personal information, conversation logs, and processing activities.'
        })
        
        setUserRequests(prev => [request, ...prev])
        onRequestSubmitted?.(request)
        alert('Your data access request has been submitted. You will receive a download link via email within 30 days.')
      } catch (error) {
        console.error('Failed to submit access request:', error)
        alert('Failed to submit access request. Please try again.')
      }
      setSubmitting(false)
    } else {
      setSelectedType(type)
      setShowForm(true)
    }
  }

  const RequestForm = () => (
    <Card className="p-6 mt-4">
      <h3 className="text-lg font-semibold mb-4">
        {REQUEST_TYPES.find(r => r.type === selectedType)?.icon}{' '}
        {REQUEST_TYPES.find(r => r.type === selectedType)?.title}
      </h3>
      
      <p className="text-gray-600 mb-4">
        {REQUEST_TYPES.find(r => r.type === selectedType)?.description}
      </p>

      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Request Details
        </label>
        <textarea
          value={requestDetails}
          onChange={(e) => setRequestDetails(e.target.value)}
          placeholder="Please provide specific details about your request..."
          rows={4}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          required
        />
      </div>

      <div className="bg-blue-50 p-3 rounded-md mb-4">
        <p className="text-sm text-blue-800">
          <strong>Processing Time:</strong> {REQUEST_TYPES.find(r => r.type === selectedType)?.processingTime}
        </p>
        <p className="text-sm text-blue-800 mt-1">
          You will receive email updates on the status of your request.
        </p>
      </div>

      <div className="flex gap-3">
        <Button
          variant="outline"
          onClick={() => {
            setShowForm(false)
            setSelectedType(null)
            setRequestDetails('')
          }}
          disabled={submitting}
        >
          Cancel
        </Button>
        <Button
          onClick={handleSubmitRequest}
          disabled={submitting || !requestDetails.trim()}
        >
          {submitting ? 'Submitting...' : 'Submit Request'}
        </Button>
      </div>
    </Card>
  )

  return (
    <div className="space-y-6">
      {/* Request Types Grid */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Your Data Protection Rights</h2>
        <p className="text-gray-600 mb-6">
          Under GDPR, you have several rights regarding your personal data. Click on any right below to learn more or submit a request.
        </p>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {REQUEST_TYPES.map(requestType => (
            <div
              key={requestType.type}
              className="border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => handleQuickAction(requestType.type)}
            >
              <div className="text-2xl mb-2">{requestType.icon}</div>
              <h3 className="font-medium mb-2">{requestType.title}</h3>
              <p className="text-sm text-gray-600 mb-3">{requestType.description}</p>
              <div className="text-xs text-gray-500">
                Processing time: {requestType.processingTime}
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Request Form */}
      {showForm && <RequestForm />}

      {/* Previous Requests */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Your Previous Requests</h3>
        
        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="text-gray-600 mt-2">Loading requests...</p>
          </div>
        ) : userRequests.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <div className="text-4xl mb-2">📝</div>
            <p>No previous requests found.</p>
            <p className="text-sm">Your submitted requests will appear here.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {userRequests.map(request => (
              <div
                key={request.id}
                className="border rounded-lg p-4 hover:shadow-sm transition-shadow"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">
                      {REQUEST_TYPES.find(r => r.type === request.requestType)?.icon}
                    </span>
                    <h4 className="font-medium">
                      {REQUEST_TYPES.find(r => r.type === request.requestType)?.title}
                    </h4>
                  </div>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(request.status)}`}>
                    {request.status.replace('_', ' ').toUpperCase()}
                  </span>
                </div>
                
                <p className="text-gray-600 text-sm mb-3">{request.requestDetails}</p>
                
                <div className="flex items-center justify-between text-xs text-gray-500">
                  <span>Submitted: {formatDate(request.requestedAt)}</span>
                  {request.completedAt && (
                    <span>Completed: {formatDate(request.completedAt)}</span>
                  )}
                </div>
                
                {request.processingNotes && (
                  <div className="mt-3 p-3 bg-gray-50 rounded-md">
                    <p className="text-sm text-gray-700">
                      <strong>Processing Notes:</strong> {request.processingNotes}
                    </p>
                  </div>
                )}
                
                {request.responseData && (
                  <div className="mt-3">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        // Handle download or view response data
                        const blob = new Blob([JSON.stringify(request.responseData, null, 2)], {
                          type: 'application/json'
                        })
                        const url = URL.createObjectURL(blob)
                        const a = document.createElement('a')
                        a.href = url
                        a.download = `data-request-${request.id}.json`
                        document.body.appendChild(a)
                        a.click()
                        document.body.removeChild(a)
                        URL.revokeObjectURL(url)
                      }}
                    >
                      Download Response
                    </Button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Help Section */}
      <Card className="p-6 bg-blue-50">
        <h3 className="text-lg font-semibold text-blue-900 mb-2">Need Help?</h3>
        <p className="text-blue-800 text-sm mb-4">
          If you have questions about your data protection rights or need assistance with a request, 
          please contact our Data Protection Officer.
        </p>
        <div className="text-sm text-blue-700">
          <p><strong>Email:</strong> privacy@seiketsu.ai</p>
          <p><strong>Response Time:</strong> Within 72 hours</p>
          <p><strong>Phone:</strong> +1 (555) 123-4567</p>
        </div>
      </Card>
    </div>
  )
}

export default DataSubjectRights