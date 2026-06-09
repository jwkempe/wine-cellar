'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useState } from 'react'
import { UserButton } from '@clerk/nextjs'

const links = [
  { href: '/', label: 'My Cellar' },
  { href: '/add', label: 'Add a Bottle' },
  { href: '/ready', label: 'Ready to Drink' },
  { href: '/log', label: 'Drink Log' },
  { href: '/pairings', label: 'Food Pairings' },
  { href: '/meal', label: "What's for Dinner?" },
  { href: '/recommendations', label: 'Recommendations' },
]

function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname()
  return (
    <nav className="flex flex-col gap-1">
      {links.map(link => (
        <Link
          key={link.href}
          href={link.href}
          onClick={onNavigate}
          className={`text-sm px-3 py-2 rounded transition-colors ${
            pathname === link.href
              ? 'text-[#c9a84c] bg-[#c9a84c]/10'
              : 'text-[#f0ead8]/50 hover:text-[#f0ead8] hover:bg-[#f0ead8]/5'
          }`}
        >
          {link.label}
        </Link>
      ))}
    </nav>
  )
}

export default function Nav() {
  const [open, setOpen] = useState(false)

  return (
    <>
      {/* Mobile top bar */}
      <div className="lg:hidden fixed top-0 left-0 right-0 z-40 h-14 bg-[#0a0907] border-b border-[#2e2a25] flex items-center justify-between px-4">
        <span className="text-[#f0ead8] text-lg font-light">Wine Cellar</span>
        <div className="flex items-center gap-3">
          <UserButton />
          <button
            onClick={() => setOpen(o => !o)}
            aria-label="Toggle menu"
            className="text-[#f0ead8]/50 hover:text-[#f0ead8] p-2 text-lg leading-none"
          >
            {open ? '✕' : '☰'}
          </button>
        </div>
      </div>

      {/* Mobile backdrop */}
      {open && (
        <div
          className="lg:hidden fixed inset-0 z-30 bg-black/60"
          onClick={() => setOpen(false)}
        />
      )}

      {/* Mobile slide-in sidebar */}
      <aside
        className={`lg:hidden fixed top-14 left-0 bottom-0 z-40 w-56 bg-[#0a0907] border-r border-[#2e2a25] flex flex-col p-6 transition-transform duration-200 ${
          open ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <NavLinks onNavigate={() => setOpen(false)} />
        <div className="mt-auto">
          <p className="text-[#f0ead8]/20 text-xs tracking-wider">Powered by Claude</p>
        </div>
      </aside>

      {/* Desktop sidebar */}
      <aside className="hidden lg:flex w-56 shrink-0 min-h-screen bg-[#0a0907] border-r border-[#2e2a25] flex-col p-6">
        <div className="flex items-center gap-3 mb-1">
          <UserButton />
          <h2 className="text-[#f0ead8] text-xl font-light">
            Wine Cellar
          </h2>
        </div>
        <p className="text-[#f0ead8]/20 text-xs tracking-widest uppercase mb-8">Collection</p>
        <NavLinks />
        <div className="mt-auto">
          <p className="text-[#f0ead8]/20 text-xs tracking-wider">Powered by Claude</p>
        </div>
      </aside>
    </>
  )
}
