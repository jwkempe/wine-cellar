import type { Metadata, Viewport } from 'next'
import { GeistSans } from 'geist/font/sans'
import { Analytics } from '@vercel/analytics/next'
import Providers from './providers'
import './globals.css'

export const metadata: Metadata = {
  title: {
    default: 'Wine Cellar',
    template: '%s · Wine Cellar',
  },
  description: 'Track your wine collection, drinking windows, and AI sommelier pairings.',
}

export const viewport: Viewport = {
  themeColor: '#0f0d0b',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={GeistSans.variable}>
      <body className="bg-[#0f0d0b] font-sans">
        <Providers>{children}</Providers>
        <Analytics />
      </body>
    </html>
  )
}
