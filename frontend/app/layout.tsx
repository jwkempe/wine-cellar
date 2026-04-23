'use client'

import { ClerkProvider, useAuth } from '@clerk/nextjs'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState, useEffect } from 'react'
import { usePathname } from 'next/navigation'
import { GeistSans } from 'geist/font/sans'
import Nav from './components/Nav'
import './globals.css'
import { api } from '@/lib/api'

function AuthInterceptor() {
  const { getToken } = useAuth()
  useEffect(() => {
    const id = api.interceptors.request.use(async config => {
      const token = await getToken()
      if (token) config.headers.Authorization = `Bearer ${token}`
      return config
    })
    return () => api.interceptors.request.eject(id)
  }, [getToken])
  return null
}

function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const isAuthPage = pathname.startsWith('/sign-in') || pathname.startsWith('/sign-up')

  if (isAuthPage) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        {children}
      </main>
    )
  }

  return (
    <>
      <AuthInterceptor />
      <div className="flex min-h-screen">
        <Nav />
        <main className="flex-1 p-4 pt-20 lg:p-8 lg:pt-8 min-w-0">
          {children}
        </main>
      </div>
    </>
  )
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const [queryClient] = useState(() => new QueryClient())

  return (
    <ClerkProvider>
      <html lang="en" className={GeistSans.variable}>
        <body className="bg-[#0f0d0b] font-sans">
          <QueryClientProvider client={queryClient}>
            <AppShell>{children}</AppShell>
          </QueryClientProvider>
        </body>
      </html>
    </ClerkProvider>
  )
}
