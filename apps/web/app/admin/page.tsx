import { SystemOverviewDashboard } from '@/components/admin/SystemOverviewDashboard'
import { AdminLayout } from '@/components/admin/AdminLayout'

export default function AdminPage() {
  return (
    <AdminLayout>
      <SystemOverviewDashboard />
    </AdminLayout>
  )
}