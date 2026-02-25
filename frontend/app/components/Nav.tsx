'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

const links = [
  { href: '/', label: 'My Cellar' },
  { href: '/add', label: 'Add a Bottle' },
  { href: '/ready', label: 'Ready to Drink' },
  { href: '/pairings', label: 'Food Pairings' },
  { href: '/recommendations', label: 'Recommendations' },
]

export default function Nav() {
  const pathname = usePathname()

  return (
    <aside className="w-56 min-h-screen bg-[#0a0907] border-r border-[#2e2a25] flex flex-col p-6">
      <h2 className="text-[#f0ead8] text-xl font-light mb-1" style={{ fontFamily: 'serif' }}>
        Wine Cellar
      </h2>
      <p className="text-[#f0ead8]/20 text-xs tracking-widest uppercase mb-8">Collection</p>

      <nav className="flex flex-col gap-1">
        {links.map(link => (
          <Link
            key={link.href}
            href={link.href}
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

      <div className="mt-auto">
        <p className="text-[#f0ead8]/20 text-xs tracking-wider">Powered by Claude</p>
      </div>
    </aside>
  )
}