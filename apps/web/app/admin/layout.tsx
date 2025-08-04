import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Admin Console - Seiketsu AI',
  description: 'Multi-tenant management console for Seiketsu AI Voice Agent Platform',
  robots: {
    index: false,
    follow: false,
  },
}

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return children
}