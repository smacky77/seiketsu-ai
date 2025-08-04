import { SystemConfigurationPanel } from '@/components/admin/SystemConfigurationPanel'
import { AdminLayout } from '@/components/admin/AdminLayout'

export default function AdminSettingsPage() {
  return (
    <AdminLayout>
      <SystemConfigurationPanel />
    </AdminLayout>
  )
}