'use client'

import React, { useState, useEffect } from 'react'
import { Card } from '../ui/card'
import { Button } from '../ui/button'
import { Input } from '../ui/input'
import { rbacService } from '../../lib/rbac/rbac.service'
import type { Role, Permission, UserRole } from '../../types/epic4'

interface RoleManagementProps {
  tenantId?: string
  onRoleChange?: (roles: Role[]) => void
}

interface RoleFormData {
  name: string
  description: string
  permissions: string[]
  inheritedRoles: string[]
}

export function RoleManagement({ tenantId, onRoleChange }: RoleManagementProps) {
  const [activeTab, setActiveTab] = useState<'roles' | 'permissions' | 'users' | 'analytics'>('roles')
  const [roles, setRoles] = useState<Role[]>([])
  const [permissions, setPermissions] = useState<Permission[]>([])
  const [selectedRole, setSelectedRole] = useState<Role | null>(null)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [showPermissionForm, setShowPermissionForm] = useState(false)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [formData, setFormData] = useState<RoleFormData>({
    name: '',
    description: '',
    permissions: [],
    inheritedRoles: []
  })

  useEffect(() => {
    loadRBACData()
  }, [tenantId])

  const loadRBACData = async () => {
    setLoading(true)
    try {
      const [rolesData, permissionsData] = await Promise.all([
        rbacService.getRoles(tenantId),
        rbacService.getPermissions()
      ])

      setRoles(rolesData)
      setPermissions(permissionsData)
      onRoleChange?.(rolesData)
    } catch (error) {
      console.error('Failed to load RBAC data:', error)
    }
    setLoading(false)
  }

  const handleCreateRole = async () => {
    if (!formData.name.trim()) return

    setSaving(true)
    try {
      const selectedPermissions = permissions.filter(p => formData.permissions.includes(p.id))
      
      const newRole = await rbacService.createRole({
        name: formData.name.trim(),
        description: formData.description.trim(),
        permissions: selectedPermissions,
        isSystem: false,
        tenantId,
        inheritedRoles: formData.inheritedRoles
      })

      setRoles(prev => [...prev, newRole])
      setShowCreateForm(false)
      setFormData({ name: '', description: '', permissions: [], inheritedRoles: [] })
      onRoleChange?.([...roles, newRole])
    } catch (error) {
      console.error('Failed to create role:', error)
      alert('Failed to create role. Please try again.')
    }
    setSaving(false)
  }

  const handleUpdateRole = async (roleId: string, updates: Partial<Role>) => {
    setSaving(true)
    try {
      const updatedRole = await rbacService.updateRole(roleId, updates)
      setRoles(prev => prev.map(role => role.id === roleId ? updatedRole : role))
      onRoleChange?.(roles.map(role => role.id === roleId ? updatedRole : role))
    } catch (error) {
      console.error('Failed to update role:', error)
      alert('Failed to update role. Please try again.')
    }
    setSaving(false)
  }

  const handleDeleteRole = async (roleId: string) => {
    if (!confirm('Are you sure you want to delete this role? This action cannot be undone.')) return

    setSaving(true)
    try {
      await rbacService.deleteRole(roleId)
      const updatedRoles = roles.filter(role => role.id !== roleId)
      setRoles(updatedRoles)
      setSelectedRole(null)
      onRoleChange?.(updatedRoles)
    } catch (error) {
      console.error('Failed to delete role:', error)
      alert('Failed to delete role. Please try again.')
    }
    setSaving(false)
  }

  const handlePermissionToggle = (roleId: string, permissionId: string, granted: boolean) => {
    const role = roles.find(r => r.id === roleId)
    if (!role) return

    let updatedPermissions = [...role.permissions]
    
    if (granted) {
      const permission = permissions.find(p => p.id === permissionId)
      if (permission && !updatedPermissions.some(p => p.id === permissionId)) {
        updatedPermissions.push(permission)
      }
    } else {
      updatedPermissions = updatedPermissions.filter(p => p.id !== permissionId)
    }

    handleUpdateRole(roleId, { permissions: updatedPermissions })
  }

  const getPermissionsByResource = () => {
    const grouped: Record<string, Permission[]> = {}
    permissions.forEach(permission => {
      if (!grouped[permission.resource]) {
        grouped[permission.resource] = []
      }
      grouped[permission.resource].push(permission)
    })
    return grouped
  }

  const RoleCard = ({ role }: { role: Role }) => (
    <Card className="p-4 hover:shadow-md transition-shadow cursor-pointer"
          onClick={() => setSelectedRole(role)}>
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-medium text-gray-900">{role.name}</h3>
        <div className="flex items-center gap-2">
          {role.isSystem && (
            <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
              System
            </span>
          )}
          <span className="text-sm text-gray-500">
            {role.permissions.length} permissions
          </span>
        </div>
      </div>
      <p className="text-sm text-gray-600 mb-3">{role.description}</p>
      <div className="flex flex-wrap gap-1">
        {role.permissions.slice(0, 3).map(permission => (
          <span key={permission.id} className="px-2 py-1 bg-gray-100 text-xs rounded">
            {permission.resource}:{permission.action}
          </span>
        ))}
        {role.permissions.length > 3 && (
          <span className="px-2 py-1 bg-gray-100 text-xs rounded">
            +{role.permissions.length - 3} more
          </span>
        )}
      </div>
    </Card>
  )

  const PermissionMatrix = ({ role }: { role: Role }) => {
    const groupedPermissions = getPermissionsByResource()
    
    return (
      <div className="space-y-6">
        {Object.entries(groupedPermissions).map(([resource, resourcePermissions]) => (
          <div key={resource} className="border rounded-lg p-4">
            <h4 className="font-medium text-gray-900 mb-3 capitalize">
              {resource.replace(/_/g, ' ')}
            </h4>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
              {resourcePermissions.map(permission => {
                const hasPermission = role.permissions.some(p => p.id === permission.id)
                return (
                  <label key={permission.id} className="flex items-center gap-2 p-2 rounded hover:bg-gray-50">
                    <input
                      type="checkbox"
                      checked={hasPermission}
                      onChange={(e) => handlePermissionToggle(role.id, permission.id, e.target.checked)}
                      disabled={role.isSystem}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm">
                      {permission.action}
                      {permission.scope && permission.scope !== 'global' && (
                        <span className="text-xs text-gray-500 ml-1">({permission.scope})</span>
                      )}
                    </span>
                  </label>
                )
              })}
            </div>
          </div>
        ))}
      </div>
    )
  }

  const CreateRoleForm = () => (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4">Create New Role</h3>
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Role Name
          </label>
          <Input
            value={formData.name}
            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
            placeholder="Enter role name"
            required
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Description
          </label>
          <textarea
            value={formData.description}
            onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
            placeholder="Describe what this role can do"
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Base Permissions
          </label>
          <div className="max-h-60 overflow-y-auto border border-gray-300 rounded-md p-3">
            {Object.entries(getPermissionsByResource()).map(([resource, resourcePermissions]) => (
              <div key={resource} className="mb-4 last:mb-0">
                <h5 className="font-medium text-gray-900 mb-2 capitalize">
                  {resource.replace(/_/g, ' ')}
                </h5>
                <div className="space-y-1">
                  {resourcePermissions.map(permission => (
                    <label key={permission.id} className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={formData.permissions.includes(permission.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setFormData(prev => ({ 
                              ...prev, 
                              permissions: [...prev.permissions, permission.id] 
                            }))
                          } else {
                            setFormData(prev => ({ 
                              ...prev, 
                              permissions: prev.permissions.filter(id => id !== permission.id) 
                            }))
                          }
                        }}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="text-sm">
                        {permission.action}
                        {permission.scope && permission.scope !== 'global' && (
                          <span className="text-xs text-gray-500 ml-1">({permission.scope})</span>
                        )}
                      </span>
                    </label>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
        
        <div className="flex gap-3">
          <Button
            onClick={() => {
              setShowCreateForm(false)
              setFormData({ name: '', description: '', permissions: [], inheritedRoles: [] })
            }}
            variant="outline"
            disabled={saving}
          >
            Cancel
          </Button>
          <Button
            onClick={handleCreateRole}
            disabled={saving || !formData.name.trim()}
          >
            {saving ? 'Creating...' : 'Create Role'}
          </Button>
        </div>
      </div>
    </Card>
  )

  const tabs = [
    { id: 'roles' as const, label: 'Roles', icon: '👥' },
    { id: 'permissions' as const, label: 'Permissions', icon: '🔐' },
    { id: 'users' as const, label: 'User Assignments', icon: '👤' },
    { id: 'analytics' as const, label: 'Analytics', icon: '📊' }
  ]

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading role management...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Role-Based Access Control</h1>
            <p className="text-gray-600">Manage roles, permissions, and user access</p>
          </div>
          <div className="flex items-center gap-4">
            <Button
              onClick={() => setShowCreateForm(true)}
              className="bg-blue-600 text-white hover:bg-blue-700"
            >
              Create Role
            </Button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Roles</p>
                <p className="text-2xl font-bold text-gray-900">{roles.length}</p>
              </div>
              <div className="text-blue-500">👥</div>
            </div>
          </Card>
          
          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">System Roles</p>
                <p className="text-2xl font-bold text-gray-900">
                  {roles.filter(r => r.isSystem).length}
                </p>
              </div>
              <div className="text-purple-500">⚙️</div>
            </div>
          </Card>
          
          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Custom Roles</p>
                <p className="text-2xl font-bold text-gray-900">
                  {roles.filter(r => !r.isSystem).length}
                </p>
              </div>
              <div className="text-green-500">🎨</div>
            </div>
          </Card>
          
          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Permissions</p>
                <p className="text-2xl font-bold text-gray-900">{permissions.length}</p>
              </div>
              <div className="text-orange-500">🔐</div>
            </div>
          </Card>
        </div>

        {/* Tab Navigation */}
        <div className="mb-8">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              {tabs.map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-2 px-1 border-b-2 font-medium text-sm whitespace-nowrap ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <span className="mr-2">{tab.icon}</span>
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        <div className="space-y-6">
          {activeTab === 'roles' && (
            <div>
              {showCreateForm && <CreateRoleForm />}
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-6">
                {roles.map(role => (
                  <RoleCard key={role.id} role={role} />
                ))}
              </div>

              {/* Role Detail Modal/Panel */}
              {selectedRole && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
                  <Card className="w-full max-w-4xl max-h-[90vh] m-4 overflow-hidden">
                    <div className="p-6 border-b flex items-center justify-between">
                      <div>
                        <h2 className="text-xl font-semibold">{selectedRole.name}</h2>
                        <p className="text-gray-600">{selectedRole.description}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        {!selectedRole.isSystem && (
                          <Button
                            onClick={() => handleDeleteRole(selectedRole.id)}
                            variant="outline"
                            className="text-red-600 hover:text-red-700"
                            disabled={saving}
                          >
                            Delete
                          </Button>
                        )}
                        <Button
                          onClick={() => setSelectedRole(null)}
                          variant="outline"
                        >
                          Close
                        </Button>
                      </div>
                    </div>
                    
                    <div className="overflow-y-auto max-h-[70vh] p-6">
                      <h3 className="text-lg font-medium mb-4">Permissions</h3>
                      <PermissionMatrix role={selectedRole} />
                    </div>
                  </Card>
                </div>
              )}
            </div>
          )}

          {activeTab === 'permissions' && (
            <Card className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold">All Permissions</h3>
                <Button
                  onClick={() => setShowPermissionForm(true)}
                  variant="outline"
                >
                  Create Permission
                </Button>
              </div>
              
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Resource
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Action
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Scope
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Description
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Used in Roles
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {permissions.map(permission => (
                      <tr key={permission.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 text-sm font-medium text-gray-900">
                          {permission.resource}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-900">
                          <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs">
                            {permission.action}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-500">
                          {permission.scope || 'global'}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-500">
                          {permission.description}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-500">
                          {roles.filter(role => role.permissions.some(p => p.id === permission.id)).length} roles
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}

          {activeTab === 'users' && (
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">User Role Assignments</h3>
              <div className="text-center py-12 text-gray-500">
                <div className="text-4xl mb-4">👤</div>
                <p>User role assignments will be displayed here.</p>
                <p className="text-sm mt-2">This feature requires integration with your user management system.</p>
              </div>
            </Card>
          )}

          {activeTab === 'analytics' && (
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Role Analytics</h3>
              <div className="text-center py-12 text-gray-500">
                <div className="text-4xl mb-4">📊</div>
                <p>Role usage analytics and insights will be displayed here.</p>
                <p className="text-sm mt-2">This includes permission usage patterns, access logs, and security metrics.</p>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}

export default RoleManagement