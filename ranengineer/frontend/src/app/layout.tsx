import type { Metadata } from 'next'
import './globals.css'
import Navbar from '../components/Navbar'

export const metadata: Metadata = {
  title: 'AI Telecom Copilot | RAN Engineer',
  description: 'AI-powered RAN Engineering Assistant for 4G/5G/O-RAN KPI analysis, anomaly detection, and RCA.',
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans antialiased">
        <Navbar />
        <div className="flex-1">{children}</div>
      </body>
    </html>
  )
}
