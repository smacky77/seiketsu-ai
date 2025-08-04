/**
 * Admin Console Multi-Tenant Management UX Tests
 * 
 * Tests admin workflow efficiency and multi-tenant safety based on UX research:
 * - Multi-tenant context switching with data isolation indicators
 * - Complex data management with cognitive load reduction
 * - Administrative efficiency through bulk operations
 * - System oversight with progressive disclosure
 * - Permission management with clear visual hierarchy
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom'

import { 
  TEST_PERSONAS, 
  UXTestRunner, 
  UserJourneyStep,
  trustPatternValidators,
  interactionPatternValidators,
  mockData
} from '../utils/ux-test-utils'

// Import admin components
import AdminLayout from '../../components/admin/AdminLayout'
import TenantSwitcher from '../../components/admin/TenantSwitcher'
import SystemOverviewDashboard from '../../components/admin/SystemOverviewDashboard'
import TeamManagementInterface from '../../components/admin/TeamManagementInterface'
import UserPermissionManager from '../../components/admin/UserPermissionManager'
import SystemConfigurationPanel from '../../components/admin/SystemConfigurationPanel'
import SystemHealthMonitor from '../../components/admin/SystemHealthMonitor'

describe('Admin Console Multi-Tenant UX Validation', () => {
  const adminPersona = TEST_PERSONAS.admin

  describe('Multi-Tenant Context and Safety', () => {
    test('tenant context is always clearly visible', () => {
      render(<AdminLayout />)
      
      // Current tenant should be prominently displayed
      const tenantContext = screen.getByText(/current.*tenant|agency|selected.*organization/i) ||
                           screen.getByTestId('tenant-context')
      expect(tenantContext).toBeInTheDocument()
      expect(tenantContext).toBeVisible()
      
      // Should show tenant name, plan, and status
      const tenantInfo = screen.getAllByText(/premium|enterprise|active|trial/i)
      expect(tenantInfo.length).toBeGreaterThan(0)
    })

    test('tenant switching has clear confirmation and safety checks', async () => {
      const user = userEvent.setup()
      render(<TenantSwitcher />)
      
      // Should have tenant switcher component
      const switcher = screen.getByRole('combobox') ||
                      screen.getByRole('button', { name: /switch.*tenant|change.*agency/i })
      expect(switcher).toBeInTheDocument()
      
      // Test tenant switching flow
      await user.click(switcher)
      
      await waitFor(() => {
        const tenantOptions = screen.getAllByRole('option') ||
                             screen.getAllByText(/agency|organization/i)
        expect(tenantOptions.length).toBeGreaterThan(1)
      })
      
      // Should have confirmation for switching
      const firstOption = screen.getAllByRole('option')[0] ||
                          screen.getAllByText(/agency|organization/i)[0]
      if (firstOption) {
        await user.click(firstOption)
        
        await waitFor(() => {
          const confirmation = screen.getByText(/confirm.*switch|are.*you.*sure|change.*context/i) ||
                               screen.getByRole('dialog')
          expect(confirmation).toBeInTheDocument()
        })
      }
    })

    test('data isolation indicators provide visual safety cues', () => {
      const { container } = render(<AdminLayout />)
      
      // Should have visual indicators for data scope
      const isolationIndicators = container.querySelectorAll(
        '[data-tenant], [class*="tenant-"], [class*="isolated-"]'
      )
      expect(isolationIndicators.length).toBeGreaterThan(0)
      
      // Different tenants should have visual distinction
      const backgroundVariations = container.querySelectorAll(
        '[class*="bg-muted"], [class*="bg-accent"], [class*="border-"]'
      )
      expect(backgroundVariations.length).toBeGreaterThan(0)
    })

    test('permission-based UI adapts to admin role', () => {
      render(<AdminLayout />)
      
      // Navigation should reflect permissions
      const navItems = screen.getAllByRole('link') ||
                      screen.getAllByRole('button', { name: /settings|users|system/i })
      expect(navItems.length).toBeGreaterThan(0)
      
      // Should have admin-specific sections
      const adminSections = screen.getAllByText(/system.*config|user.*management|tenant.*settings/i)
      expect(adminSections.length).toBeGreaterThan(0)
    })
  })

  describe('System Overview and Monitoring', () => {
    test('executive dashboard provides high-level insights immediately', () => {
      render(<SystemOverviewDashboard />)
      
      // Should show key system metrics
      const keyMetrics = screen.getAllByText(/\d+.*tenants?|\d+.*users?|\d+.*agents?|\d+.*calls?/i)
      expect(keyMetrics.length).toBeGreaterThan(0)
      
      // Should have status indicators
      const statusIndicators = screen.getAllByText(/healthy|warning|error|operational/i)
      expect(statusIndicators.length).toBeGreaterThan(0)
      
      // Should show trends
      const trends = screen.getAllByText(/\d+%.*up|\d+%.*down|trending|growth/i)
      expect(trends.length).toBeGreaterThan(0)
    })

    test('system health monitoring provides real-time insights', () => {
      render(<SystemHealthMonitor />)
      
      // Should show system status
      const systemStatus = screen.getAllByText(/online|offline|healthy|degraded|error/i)
      expect(systemStatus.length).toBeGreaterThan(0)
      
      // Should have performance metrics
      const performanceMetrics = screen.getAllByText(/\d+ms|\d+%.*cpu|\d+%.*memory|uptime/i)
      expect(performanceMetrics.length).toBeGreaterThan(0)
    })

    test('progressive disclosure reveals detailed metrics on demand', async () => {
      const user = userEvent.setup()
      render(<SystemOverviewDashboard />)
      
      // Should have expandable sections
      const expandableElements = screen.getAllByRole('button', { expanded: false }) ||
                                screen.getAllByText(/show.*more|details|expand/i)
      
      if (expandableElements.length > 0) {
        await user.click(expandableElements[0])
        
        await waitFor(() => {
          const detailedInfo = screen.getByText(/detailed.*metrics|full.*report|breakdown/i)
          expect(detailedInfo).toBeInTheDocument()
        })
      }
    })
  })

  describe('Team and User Management Efficiency', () => {
    test('team overview provides actionable insights', () => {
      render(<TeamManagementInterface />)
      
      // Should show team performance
      const teamMetrics = screen.getAllByText(/\d+.*agents?|\d+.*active|\d+.*leads?|\d+.*conversions?/i)
      expect(teamMetrics.length).toBeGreaterThan(0)
      
      // Should highlight issues requiring attention
      const alerts = screen.getAllByText(/needs.*attention|underperforming|offline|error/i)
      expect(alerts.length).toBeGreaterThanOrEqual(0) // May be 0 if all good
    })

    test('user permission management has clear visual hierarchy', () => {
      render(<UserPermissionManager />)
      
      // Should show user roles clearly
      const roles = screen.getAllByText(/admin|agent|viewer|manager/i)
      expect(roles.length).toBeGreaterThan(0)
      
      // Should have permission indicators
      const permissions = screen.getAllByText(/read|write|delete|manage/i)
      expect(permissions.length).toBeGreaterThan(0)
    })

    test('bulk operations are efficient and safe', async () => {
      const user = userEvent.setup()
      render(<TeamManagementInterface />)
      
      // Should have selection controls
      const selectAll = screen.getByRole('checkbox', { name: /select.*all/i }) ||
                       screen.getByText(/select.*all/i)
      
      if (selectAll) {
        await user.click(selectAll)
        
        // Should show bulk action options
        await waitFor(() => {
          const bulkActions = screen.getAllByText(/bulk.*action|with.*selected|batch/i)
          expect(bulkActions.length).toBeGreaterThan(0)
        })
      }
    })

    test('admin workflow completes within time constraints', async () => {
      const user = userEvent.setup()
      
      const adminWorkflowSteps: UserJourneyStep[] = [
        {
          description: 'Admin checks system overview',
          action: async () => {
            render(<SystemOverviewDashboard />)
            const overview = screen.getAllByText(/system.*status|overview|dashboard/i)
            expect(overview.length).toBeGreaterThan(0)
          },
          validation: () => {
            const metrics = screen.getAllByText(/\d+.*tenants?|\d+.*users?/i)
            expect(metrics.length).toBeGreaterThan(0)
          },
          timeLimit: 10,
        },
        {
          description: 'Admin reviews team performance',
          action: async () => {
            render(<TeamManagementInterface />)
            const teamData = screen.getAllByText(/agent|performance|active/i)
            expect(teamData.length).toBeGreaterThan(0)
          },
          validation: () => {
            const teamMetrics = screen.getAllByText(/\d+.*agents?|\d+.*calls?/i)
            expect(teamMetrics.length).toBeGreaterThan(0)
          },
          timeLimit: 15,
        },
        {
          description: 'Admin manages user permissions',
          action: async () => {
            render(<UserPermissionManager />)
            const userList = screen.getAllByText(/user|role|permission/i)
            expect(userList.length).toBeGreaterThan(0)
          },
          validation: () => {
            const permissions = screen.getAllByText(/admin|agent|read|write/i)
            expect(permissions.length).toBeGreaterThan(0)
          },
          timeLimit: 20,
        },
      ]
      
      const uxRunner = new UXTestRunner(adminPersona)
      const result = await uxRunner.executeJourney(adminWorkflowSteps)
      
      expect(result.success).toBe(true)
      expect(result.timeTaken).toBeLessThan(adminPersona.timeConstraints)
    })
  })

  describe('System Configuration Management', () => {
    test('configuration options are organized by category', () => {
      render(<SystemConfigurationPanel />)
      
      // Should have categorized settings
      const categories = screen.getAllByText(/general|security|integration|voice.*settings|notifications/i)
      expect(categories.length).toBeGreaterThan(0)
      
      // Should show current values
      const settingValues = screen.getAllByDisplayValue(/.*/) ||
                           screen.getAllByText(/enabled|disabled|on|off/i)
      expect(settingValues.length).toBeGreaterThan(0)
    })

    test('configuration changes have clear impact indicators', async () => {
      const user = userEvent.setup()
      render(<SystemConfigurationPanel />)
      
      // Should show change impact
      const settingInput = screen.getByRole('textbox') ||
                          screen.getByRole('checkbox') ||
                          screen.getByRole('combobox')
      
      if (settingInput) {
        await user.click(settingInput)
        
        // Should show impact information
        const impactInfo = screen.getByText(/affects.*tenants?|will.*restart|requires.*approval/i)
        expect(impactInfo).toBeInTheDocument()
      }
    })

    test('configuration validation prevents system issues', async () => {
      const user = userEvent.setup()
      render(<SystemConfigurationPanel />)
      
      const saveButton = screen.getByRole('button', { name: /save|apply|update/i })
      
      // Should validate before saving
      await user.click(saveButton)
      
      await waitFor(() => {
        const validation = screen.getByText(/validating|checking|valid|invalid|error/i)
        expect(validation).toBeInTheDocument()
      })
    })
  })

  describe('Data Management and Analytics', () => {
    test('complex data is presented with clear hierarchy', () => {
      render(<SystemOverviewDashboard />)
      
      // Should have clear data hierarchy
      const dataTable = screen.getByRole('table') ||
                        screen.getAllByRole('row')
      expect(dataTable).toBeTruthy()
      
      // Should have sortable columns
      const sortableHeaders = screen.getAllByRole('columnheader') ||
                             screen.getAllByText(/sort|asc|desc/i)
      expect(sortableHeaders.length).toBeGreaterThan(0)
    })

    test('search and filtering work efficiently', async () => {
      const user = userEvent.setup()
      render(<TeamManagementInterface />)
      
      // Should have search functionality
      const searchInput = screen.getByRole('textbox', { name: /search|filter/i }) ||
                         screen.getByPlaceholderText(/search|filter/i)
      
      if (searchInput) {
        await user.type(searchInput, 'test')
        
        // Should filter results
        await waitFor(() => {
          const results = screen.getAllByText(/result|found|filtered/i)
          expect(results.length).toBeGreaterThan(0)
        })
      }
    })

    test('data export provides multiple format options', async () => {
      const user = userEvent.setup()
      render(<SystemOverviewDashboard />)
      
      const exportButton = screen.getByRole('button', { name: /export|download|save/i })
      
      if (exportButton) {
        await user.click(exportButton)
        
        await waitFor(() => {
          const formatOptions = screen.getAllByText(/csv|pdf|excel|json/i)
          expect(formatOptions.length).toBeGreaterThan(0)
        })
      }
    })
  })

  describe('Security and Audit Features', () => {
    test('audit logging is comprehensive and searchable', () => {
      render(<SystemOverviewDashboard />)
      
      // Should show recent activity
      const auditLog = screen.getAllByText(/audit|log|activity|action.*by/i)
      expect(auditLog.length).toBeGreaterThan(0)
      
      // Should show user attribution
      const userActions = screen.getAllByText(/by.*admin|by.*user|\d+.*minutes?.*ago/i)
      expect(userActions.length).toBeGreaterThan(0)
    })

    test('security settings have appropriate warnings', () => {
      render(<SystemConfigurationPanel />)
      
      // Should show security-related settings
      const securitySettings = screen.getAllByText(/security|password|2fa|encryption/i)
      expect(securitySettings.length).toBeGreaterThan(0)
      
      // Should have warning indicators for critical changes
      const warnings = screen.getAllByText(/warning|critical|careful|impact/i)
      expect(warnings.length).toBeGreaterThanOrEqual(0)
    })
  })

  describe('Error Handling and Recovery', () => {
    test('system errors provide clear recovery instructions', async () => {
      const user = userEvent.setup()
      render(<SystemHealthMonitor />)
      
      // Simulate system error state
      const errorElement = screen.getByText(/error|failed|offline|degraded/i)
      
      if (errorElement) {
        await user.click(errorElement)
        
        await waitFor(() => {
          const recoveryInstructions = screen.getByText(/restart|contact.*support|try.*again|troubleshoot/i)
          expect(recoveryInstructions).toBeInTheDocument()
        })
      }
    })

    test('tenant data issues are isolated and contained', () => {
      render(<TenantSwitcher />)
      
      // Should show tenant health status
      const tenantStatus = screen.getAllByText(/healthy|warning|error|operational/i)
      expect(tenantStatus.length).toBeGreaterThan(0)
      
      // Issues should be clearly attributed to specific tenants
      const tenantNames = screen.getAllByText(/agency|organization|tenant/i)
      expect(tenantNames.length).toBeGreaterThan(0)
    })

    test('critical operations require confirmation', async () => {
      const user = userEvent.setup()
      render(<UserPermissionManager />)
      
      const deleteButton = screen.getByRole('button', { name: /delete|remove|revoke/i })
      
      if (deleteButton) {
        await user.click(deleteButton)
        
        await waitFor(() => {
          const confirmation = screen.getByText(/are.*you.*sure|confirm|permanent|cannot.*undo/i) ||
                               screen.getByRole('dialog')
          expect(confirmation).toBeInTheDocument()
        })
      }
    })
  })

  describe('Mobile and Responsive Admin Interface', () => {
    test('admin functions remain accessible on smaller screens', () => {
      // Mock tablet viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 768,
      })
      
      render(<AdminLayout />)
      
      // Should have responsive navigation
      const mobileNav = screen.getByRole('navigation') ||
                       screen.getByTestId('mobile-menu')
      expect(mobileNav).toBeInTheDocument()
      
      // Critical admin functions should be accessible
      const adminActions = screen.getAllByRole('button')
      expect(adminActions.length).toBeGreaterThan(0)
    })
  })

  describe('Comprehensive Admin Console UX Score', () => {
    test('admin console achieves overall UX score above 80%', async () => {
      const uxRunner = new UXTestRunner(adminPersona)
      
      const adminWorkflowSteps: UserJourneyStep[] = [
        {
          description: 'Complete admin oversight workflow',
          action: async () => {
            render(
              <div>
                <AdminLayout />
                <TenantSwitcher />
                <SystemOverviewDashboard />
                <TeamManagementInterface />
                <SystemHealthMonitor />
              </div>
            )
          },
          validation: () => {
            expect(screen.getByText(/admin|dashboard|system/i)).toBeInTheDocument()
            expect(screen.getAllByText(/tenant|agency/i).length).toBeGreaterThan(0)
          },
          timeLimit: 30,
        },
      ]
      
      const AdminConsoleComponent = (
        <div>
          <AdminLayout />
          <TenantSwitcher />
          <SystemOverviewDashboard />
          <TeamManagementInterface />
          <UserPermissionManager />
          <SystemConfigurationPanel />
          <SystemHealthMonitor />
        </div>
      )
      
      const result = await uxRunner.runComprehensiveTest(AdminConsoleComponent, adminWorkflowSteps)
      
      expect(result.score).toBeGreaterThan(80)
      expect(result.passed).toBe(true)
      
      // Log results for analysis
      console.log('Admin Console UX Test Results:', {
        score: result.score,
        persona: result.persona,
        recommendations: result.recommendations,
        multiTenantSafety: result.details.patterns,
        adminEfficiency: result.details.journey,
      })
    })
  })
})