'use client'

import { ClerkProvider, useAuth } from '@clerk/nextjs'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState, useEffect } from 'react'
import { usePathname } from 'next/navigation'
import { GeistSans } from 'geist/font/sans'
import { Analytics } from '@vercel/analytics/next'
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
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        // Keep data fresh in cache so navigating between pages is instant
        // instead of refetching the cellar on every visit. Mutations call
        // invalidateQueries, so edits still show up immediately.
        staleTime: 60_000,
        gcTime: 5 * 60_000,
        refetchOnWindowFocus: false,
        retry: 1,
      },
    },
  }))

  return (
    <ClerkProvider>
      <html lang="en" className={GeistSans.variable}>
        <body className="bg-[#0f0d0b] font-sans">
          <QueryClientProvider client={queryClient}>
            <AppShell>{children}</AppShell>
          </QueryClientProvider>
          <Analytics />
        </body>
      </html>
    </ClerkProvider>
  )
}
