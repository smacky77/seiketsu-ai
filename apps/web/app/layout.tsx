import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { ToolbarProvider } from '@/components/layout/ToolbarProvider'
import { ApiProvider } from '@/lib/providers/ApiProvider'
import { ReactQueryProvider } from '@/lib/providers/react-query-provider'
import { AuthProvider } from '@/lib/auth/auth-provider'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Seiketsu AI - Voice-First Real Estate Intelligence',
  description: 'Transform your real estate business with AI-powered voice agents that qualify leads, schedule appointments, and provide instant property insights.',
  keywords: 'real estate AI, voice agent, lead qualification, property search, real estate automation',
  authors: [{ name: 'Seiketsu AI' }],
  creator: 'Seiketsu AI',
  publisher: 'Seiketsu AI',
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://seiketsu.ai',
    title: 'Seiketsu AI - Voice-First Real Estate Intelligence',
    description: 'Transform your real estate business with AI-powered voice agents that qualify leads, schedule appointments, and provide instant property insights.',
    siteName: 'Seiketsu AI',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Seiketsu AI - Voice-First Real Estate Intelligence',
    description: 'Transform your real estate business with AI-powered voice agents that qualify leads, schedule appointments, and provide instant property insights.',
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="scroll-smooth" suppressHydrationWarning>
      <body className={inter.className}>
        <ReactQueryProvider>
          <AuthProvider>
            <ApiProvider>
              <ToolbarProvider />
              {children}
            </ApiProvider>
          </AuthProvider>
        </ReactQueryProvider>
      </body>
    </html>
  )
}