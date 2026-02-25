'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState } from 'react'
import Nav from './components/Nav'
import './globals.css'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const [queryClient] = useState(() => new QueryClient())

  return (
    <html lang="en">
      <body className="bg-[#0f0d0b]">
        <QueryClientProvider client={queryClient}>
          <div className="flex min-h-screen">
            <Nav />
            <main className="flex-1 p-8">
              {children}
            </main>
          </div>
        </QueryClientProvider>
      </body>
    </html>
  )
}