'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

const NAV_LINKS = [
  { href: '/', label: 'Dashboard' },
  { href: '/datasets', label: 'Datasets' },
  { href: '/cells', label: 'Cells' },
  { href: '/anomalies', label: 'Anomalies' },
  { href: '/alarms', label: 'Alarms' },
  { href: '/incidents', label: 'Incidents' },
  { href: '/knowledge', label: 'Knowledge (RAG)' },
  { href: '/oran', label: 'O-RAN Studio' },
  { href: '/digital-twin', label: 'Digital Twin (6G)' },
  { href: '/chat', label: 'Copilot Chat' },
  { href: '/settings', label: 'Settings' },
]

export default function Navbar() {
  const pathname = usePathname() || ''

  return (
    <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur-md sticky top-0 z-50">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-3.5 sm:px-8">
        <div className="flex items-center gap-8">
          <Link href="/" className="flex items-center gap-2.5">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-teal-400 font-mono text-sm font-bold text-slate-950 shadow-md shadow-teal-500/20">
              RAN
            </span>
            <div>
              <p className="font-semibold tracking-tight text-slate-100 text-sm">AI Telecom Copilot</p>
              <p className="font-mono text-[10px] tracking-widest uppercase text-teal-400">RAN Engineer</p>
            </div>
          </Link>

          <nav className="hidden md:flex items-center gap-1">
            {NAV_LINKS.map((link) => {
              const isActive = pathname === link.href || (link.href !== '/' && pathname.startsWith(link.href))
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`rounded-md px-3 py-1.5 text-xs font-medium transition ${
                    isActive
                      ? 'bg-slate-800 text-teal-300 font-semibold'
                      : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200'
                  }`}
                >
                  {link.label}
                </Link>
              )
            })}
          </nav>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-1.5 rounded-md border border-cyan-500/30 bg-cyan-950/40 px-2.5 py-1 text-[11px] font-mono text-cyan-300">
            <span className="h-1.5 w-1.5 rounded-full bg-cyan-400"></span>
            <span>ROLE: RAN_ENGINEER</span>
          </div>
          <div className="hidden sm:flex items-center gap-2 rounded-full border border-slate-800 bg-slate-900 px-3 py-1 text-[11px] text-slate-400 font-mono">
            <span className="h-2 w-2 rounded-full bg-teal-400 animate-pulse"></span>
            <span>Online</span>
          </div>
        </div>
      </div>

      {/* Mobile nav */}
      <div className="flex md:hidden overflow-x-auto border-t border-slate-800/60 px-4 py-2 gap-2 text-xs">
        {NAV_LINKS.map((link) => {
          const isActive = pathname === link.href || (link.href !== '/' && pathname.startsWith(link.href))
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`whitespace-nowrap px-2.5 py-1 rounded ${
                isActive ? 'bg-slate-800 text-teal-300' : 'text-slate-400'
              }`}
            >
              {link.label}
            </Link>
          )
        })}
      </div>
    </header>
  )
}

