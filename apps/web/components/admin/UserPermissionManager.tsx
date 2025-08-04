'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Shield, 
  Users, 
  Settings, 
  Eye, 
  Edit, 
  Trash2,
  Plus,
  Check,
  X,
  Lock,
  Unlock,
  AlertTriangle,
  Info
} from 'lucide-react'

interface Permission {
  id: string
  name: string
  description: string
  category: 'leads' | 'agents' | 'reports' | 'system' | 'voice'
  level: 'read' | 'write' | 'admin'
  critical: boolean
}

interface Role {
  id: string
  name: string
  description: string
  permissions: string[]
  userCount: number
  isCustom: boolean
}

const mockPermissions: Permission[] = [
  // Leads permissions
  { id: 'view_own_leads', name: 'View Own Leads', description: 'Can view leads assigned to them', category: 'leads', level: 'read', critical: false },
  { id: 'view_all_leads', name: 'View All Leads', description: 'Can view all leads in the system', category: 'leads', level: 'read', critical: false },
  { id: 'edit_leads', name: 'Edit Leads', description: 'Can modify lead information', category: 'leads', level: 'write', critical: false },
  { id: 'delete_leads', name: 'Delete Leads', description: 'Can delete leads from the system', category: 'leads', level: 'admin', critical: true },
  { id: 'assign_leads', name: 'Assign Leads', description: 'Can assign leads to other agents', category: 'leads', level: 'write', critical: false },
  
  // Agents permissions
  { id: 'view_team', name: 'View Team', description: 'Can view team member information', category: 'agents', level: 'read', critical: false },
  { id: 'manage_team', name: 'Manage Team', description: 'Can add, edit, and remove team members', category: 'agents', level: 'admin', critical: true },
  { id: 'view_performance', name: 'View Performance', description: 'Can view team performance metrics', category: 'agents', level: 'read', critical: false },
  
  // Reports permissions
  { id: 'access_basic_reports', name: 'Basic Reports', description: 'Can access standard performance reports', category: 'reports', level: 'read', critical: false },
  { id: 'access_advanced_reports', name: 'Advanced Reports', description: 'Can access detailed analytics and reports', category: 'reports', level: 'read', critical: false },
  { id: 'export_reports', name: 'Export Reports', description: 'Can export report data', category: 'reports', level: 'write', critical: false },
  
  // Voice permissions
  { id: 'voice_config', name: 'Voice Configuration', description: 'Can configure voice agent settings', category: 'voice', level: 'write', critical: false },
  { id: 'voice_admin', name: 'Voice Administration', description: 'Can manage voice system settings', category: 'voice', level: 'admin', critical: true },
  { id: 'monitor_conversations', name: 'Monitor Conversations', description: 'Can listen to live conversations', category: 'voice', level: 'read', critical: false },
  
  // System permissions
  { id: 'system_settings', name: 'System Settings', description: 'Can modify system configuration', category: 'system', level: 'admin', critical: true },
  { id: 'user_management', name: 'User Management', description: 'Can manage user accounts and permissions', category: 'system', level: 'admin', critical: true },
  { id: 'billing_access', name: 'Billing Access', description: 'Can view and manage billing information', category: 'system', level: 'admin', critical: true }
]

const mockRoles: Role[] = [
  {
    id: 'agent',
    name: 'Agent',
    description: 'Basic agent with access to own leads and voice configuration',
    permissions: ['view_own_leads', 'voice_config', 'access_basic_reports'],
    userCount: 12,
    isCustom: false
  },
  {
    id: 'senior_agent',
    name: 'Senior Agent',
    description: 'Experienced agent with additional reporting capabilities',
    permissions: ['view_own_leads', 'edit_leads', 'voice_config', 'access_basic_reports', 'access_advanced_reports', 'monitor_conversations'],
    userCount: 5,
    isCustom: false
  },
  {
    id: 'team_lead',
    name: 'Team Lead',
    description: 'Team leader with team management and lead assignment capabilities',
    permissions: ['view_all_leads', 'edit_leads', 'assign_leads', 'view_team', 'view_performance', 'voice_config', 'access_advanced_reports', 'export_reports', 'monitor_conversations'],
    userCount: 3,
    isCustom: false
  },
  {
    id: 'manager',
    name: 'Manager',
    description: 'Full management access with system administration capabilities',
    permissions: ['view_all_leads', 'edit_leads', 'delete_leads', 'assign_leads', 'manage_team', 'view_performance', 'voice_admin', 'access_advanced_reports', 'export_reports', 'monitor_conversations', 'user_management', 'billing_access'],
    userCount: 1,
    isCustom: false
  }
]

interface UserPermissionManagerProps {
  onClose: () => void
}

const getCategoryColor = (category: string) => {
  switch (category) {
    case 'leads':
      return 'bg-blue-100 text-blue-800 border-blue-200'
    case 'agents':
      return 'bg-green-100 text-green-800 border-green-200'
    case 'reports':
      return 'bg-purple-100 text-purple-800 border-purple-200'
    case 'voice':
      return 'bg-orange-100 text-orange-800 border-orange-200'
    case 'system':
      return 'bg-red-100 text-red-800 border-red-200'
    default:
      return 'bg-gray-100 text-gray-800 border-gray-200'
  }
}

const getLevelIcon = (level: string) => {
  switch (level) {
    case 'read':
      return <Eye className="w-3 h-3" />
    case 'write':
      return <Edit className="w-3 h-3" />
    case 'admin':
      return <Shield className="w-3 h-3" />
    default:
      return <Eye className="w-3 h-3" />
  }
}

export function UserPermissionManager({ onClose }: UserPermissionManagerProps) {
  const [activeTab, setActiveTab] = useState<'roles' | 'permissions'>('roles')
  const [selectedRole, setSelectedRole] = useState<Role | null>(null)
  const [editingRole, setEditingRole] = useState<Role | null>(null)

  const groupedPermissions = mockPermissions.reduce((acc, permission) => {
    if (!acc[permission.category]) {
      acc[permission.category] = []
    }
    acc[permission.category].push(permission)
    return acc
  }, {} as Record<string, Permission[]>)

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-card rounded-lg shadow-lg max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col"
      >
        {/* Header */}
        <div className="p-6 border-b border-border">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Shield className="w-6 h-6 text-blue-500" />
              <div>
                <h2 className="text-lg font-semibold">Permission Management</h2>
                <p className="text-sm text-muted-foreground">Manage roles and permissions for your team</p>
              </div>
            </div>
            <button 
              onClick={onClose}
              className="p-2 text-muted-foreground hover:text-foreground rounded-lg"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="border-b border-border">
          <div className="flex">
            <button
              onClick={() => setActiveTab('roles')}
              className={`px-6 py-3 font-medium text-sm border-b-2 transition-colors ${
                activeTab === 'roles' 
                  ? 'border-foreground text-foreground' 
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              Roles ({mockRoles.length})
            </button>
            <button
              onClick={() => setActiveTab('permissions')}
              className={`px-6 py-3 font-medium text-sm border-b-2 transition-colors ${
                activeTab === 'permissions' 
                  ? 'border-foreground text-foreground' 
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              Permissions ({mockPermissions.length})
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto">
          {activeTab === 'roles' && (
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="font-semibold">User Roles</h3>
                  <p className="text-sm text-muted-foreground">Predefined permission sets for different user types</p>
                </div>
                <button className="btn btn-primary">
                  <Plus className="w-4 h-4 mr-2" />
                  Create Role
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {mockRoles.map((role) => (
                  <motion.div
                    key={role.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-muted rounded-lg p-4 hover:bg-accent transition-colors cursor-pointer"
                    onClick={() => setSelectedRole(role)}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h4 className="font-medium">{role.name}</h4>
                        <p className="text-sm text-muted-foreground">{role.description}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        {role.isCustom && (
                          <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                            Custom
                          </span>
                        )}
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            setEditingRole(role)
                          }}
                          className="p-1 text-muted-foreground hover:text-foreground"
                        >
                          <Edit className="w-4 h-4" />
                        </button>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Users</span>
                        <span className="font-medium">{role.userCount}</span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Permissions</span>
                        <span className="font-medium">{role.permissions.length}</span>
                      </div>
                    </div>

                    {/* Permission preview */}
                    <div className="mt-3 pt-3 border-t border-border">
                      <div className="flex flex-wrap gap-1">
                        {role.permissions.slice(0, 3).map((permissionId) => {
                          const permission = mockPermissions.find(p => p.id === permissionId)
                          return permission ? (
                            <span
                              key={permissionId}
                              className={`inline-flex items-center px-2 py-1 rounded text-xs border ${getCategoryColor(permission.category)}`}
                            >
                              {getLevelIcon(permission.level)}
                              <span className="ml-1">{permission.name}</span>
                            </span>
                          ) : null
                        })}
                        {role.permissions.length > 3 && (
                          <span className="text-xs text-muted-foreground">
                            +{role.permissions.length - 3} more
                          </span>
                        )}
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'permissions' && (
            <div className="p-6">
              <div className="mb-6">
                <h3 className="font-semibold">System Permissions</h3>
                <p className="text-sm text-muted-foreground">Individual permissions that can be assigned to roles</p>
              </div>

              <div className="space-y-6">
                {Object.entries(groupedPermissions).map(([category, permissions]) => (
                  <div key={category} className="space-y-3">
                    <h4 className="font-medium capitalize flex items-center gap-2">
                      <span className={`inline-flex items-center px-2 py-1 rounded text-xs border ${getCategoryColor(category)}`}>
                        {category}
                      </span>
                      <span className="text-muted-foreground">({permissions.length})</span>
                    </h4>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {permissions.map((permission) => (
                        <div
                          key={permission.id}
                          className="bg-muted rounded-lg p-4 flex items-start gap-3"
                        >
                          <div className="flex-shrink-0 mt-1">
                            {getLevelIcon(permission.level)}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <h5 className="font-medium">{permission.name}</h5>
                              {permission.critical && (
                                <AlertTriangle className="w-4 h-4 text-red-500" />
                              )}
                            </div>
                            <p className="text-sm text-muted-foreground">{permission.description}</p>
                            <div className="flex items-center gap-2 mt-2">
                              <span className={`inline-flex items-center px-2 py-1 rounded text-xs border ${getCategoryColor(permission.category)}`}>
                                {permission.level}
                              </span>
                              {permission.critical && (
                                <span className="text-xs text-red-600 bg-red-50 px-2 py-1 rounded border border-red-200">
                                  Critical
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-border bg-muted/50">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Info className="w-4 h-4" />
              <span>Changes to permissions require administrator approval</span>
            </div>
            <div className="flex items-center gap-3">
              <button onClick={onClose} className="btn btn-secondary">
                Close
              </button>
              <button className="btn btn-primary">
                Save Changes
              </button>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Role Detail Modal */}
      <AnimatePresence>
        {selectedRole && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-60 p-4"
            onClick={() => setSelectedRole(null)}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-card rounded-lg shadow-lg max-w-2xl w-full max-h-[80vh] overflow-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="p-6 border-b border-border">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold">{selectedRole.name} Role</h3>
                  <button 
                    onClick={() => setSelectedRole(null)}
                    className="p-2 text-muted-foreground hover:text-foreground rounded-lg"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>
              
              <div className="p-6 space-y-6">
                <div>
                  <p className="text-muted-foreground">{selectedRole.description}</p>
                  <div className="flex items-center gap-4 mt-2 text-sm">
                    <span><strong>{selectedRole.userCount}</strong> users assigned</span>
                    <span><strong>{selectedRole.permissions.length}</strong> permissions</span>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium mb-3">Assigned Permissions</h4>
                  <div className="space-y-2">
                    {selectedRole.permissions.map((permissionId) => {
                      const permission = mockPermissions.find(p => p.id === permissionId)
                      return permission ? (
                        <div key={permissionId} className="flex items-center gap-3 p-3 bg-muted rounded-lg">
                          {getLevelIcon(permission.level)}
                          <div className="flex-1">
                            <div className="font-medium">{permission.name}</div>
                            <div className="text-sm text-muted-foreground">{permission.description}</div>
                          </div>
                          <span className={`inline-flex items-center px-2 py-1 rounded text-xs border ${getCategoryColor(permission.category)}`}>
                            {permission.category}
                          </span>
                        </div>
                      ) : null
                    })}
                  </div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}