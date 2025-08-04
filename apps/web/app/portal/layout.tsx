import { Inter } from 'next/font/google'
import ClientNavigation from '@/components/portal/ClientNavigation'
import ClientHeader from '@/components/portal/ClientHeader'

const inter = Inter({ subsets: ['latin'] })

export default function ClientPortalLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className={`min-h-screen bg-background ${inter.className}`}>
      {/* Trust-building header with agent info and status */}
      <ClientHeader />
      
      <div className="flex">
        {/* Simplified navigation based on client IA */}
        <ClientNavigation />
        
        {/* Main content area with generous white space */}
        <main className="flex-1 p-6 lg:p-8">
          <div className="max-w-6xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}