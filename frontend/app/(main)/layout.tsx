'use client'
import { useEffect, useState, useRef } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import Link from 'next/link'
import {
  TrendingUp, Search, Bell, Settings, LogOut,
  LayoutDashboard, ArrowLeftRight, Users, ChevronDown,
  CheckCircle2
} from 'lucide-react'
import { getUser, logout, isAuthenticated, AuthUser } from '@/lib/auth'
import { getMe, getNotifications, markAllRead } from '@/lib/api'

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()
  const [user, setUser] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState(true)
  const [notifications, setNotifications] = useState<any[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [showNotifs, setShowNotifs] = useState(false)
  const [showUserMenu, setShowUserMenu] = useState(false)
  const notifRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!isAuthenticated()) { router.replace('/login'); return }
    // Use cached user instantly to remove the loading spinner immediately.
    // Then verify/refresh in the background — no blocking wait.
    const cached = getUser()
    if (cached) {
      setUser(cached)
      setLoading(false)
      getMe().then((res) => setUser(res.data)).catch(() => logout())
    } else {
      getMe().then((res) => { setUser(res.data); setLoading(false) }).catch(() => logout())
    }
  }, [router])

  useEffect(() => {
    if (!user) return
    getNotifications().then((res) => {
      setNotifications(res.data.notifications || [])
      setUnreadCount(res.data.unread_count || 0)
    }).catch(() => {})
  }, [user])

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) {
        setShowNotifs(false); setShowUserMenu(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center"
        style={{ background: 'linear-gradient(135deg, #c8d8eb 0%, #dce8f5 100%)' }}>
        <div className="text-center">
          <div className="w-10 h-10 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-slate-600 text-sm">Loading your dashboard...</p>
        </div>
      </div>
    )
  }

  const NAV_LINKS = [
    { href: '/dashboard', label: 'Overview' },
    { href: '/transactions', label: 'Transactions' },
    ...(user?.role === 'admin' ? [
      { href: '/users', label: 'Users' },
      { href: '/approvals', label: 'Approvals' },
    ] : []),
  ]

  const initials = user?.full_name?.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase() || 'U'
  const ROLE_COLORS: Record<string, string> = {
    admin: 'bg-red-100 text-red-600',
    analyst: 'bg-purple-100 text-purple-600',
    viewer: 'bg-slate-100 text-slate-600',
  }

  return (
    <div className="min-h-screen" style={{ background: 'linear-gradient(135deg, #c8d8eb 0%, #dce8f5 50%, #e8f0f8 100%)' }}>
      <div className="max-w-[1400px] mx-auto p-4 md:p-6">
        <div className="bg-white rounded-3xl shadow-lg overflow-hidden" style={{ minHeight: 'calc(100vh - 48px)' }}>

          {/* Top navbar */}
          <nav className="flex items-center gap-6 px-7 py-4 border-b border-slate-100">
            <Link href="/dashboard" className="flex items-center gap-2.5 shrink-0">
              <div className="w-8 h-8 bg-emerald-500 rounded-xl flex items-center justify-center">
                <TrendingUp className="w-4 h-4 text-white" />
              </div>
              <span className="text-slate-900 font-bold text-base tracking-tight">FinanceDesk</span>
            </Link>

            <div className="flex items-center gap-1 flex-1">
              {NAV_LINKS.map(({ href, label }) => {
                const active = pathname === href
                return (
                  <Link key={href} href={href}
                    className={`px-4 py-2 rounded-xl text-sm font-medium transition-colors ${
                      active ? 'bg-slate-100 text-slate-900' : 'text-slate-500 hover:text-slate-800 hover:bg-slate-50'
                    }`}>
                    {label}
                  </Link>
                )
              })}
            </div>

            <div className="relative hidden md:flex items-center">
              <Search className="absolute left-3.5 w-4 h-4 text-slate-400" />
              <input placeholder="Search transactions..."
                className="pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-700 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-400 w-52" />
            </div>

            <div className="flex items-center gap-2" ref={notifRef}>
              {/* Notifications */}
              <div className="relative">
                <button onClick={() => { setShowNotifs(!showNotifs); setShowUserMenu(false) }}
                  className="relative p-2.5 rounded-xl hover:bg-slate-100 transition-colors text-slate-500 hover:text-slate-800">
                  <Bell className="w-5 h-5" />
                  {unreadCount > 0 && (
                    <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full" />
                  )}
                </button>
                {showNotifs && (
                  <div className="absolute right-0 top-12 w-80 bg-white rounded-2xl shadow-xl border border-slate-100 z-50 overflow-hidden">
                    <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
                      <p className="font-semibold text-slate-900 text-sm">Notifications</p>
                      {unreadCount > 0 && (
                        <button onClick={() => { markAllRead(); setUnreadCount(0) }}
                          className="text-xs text-emerald-600 hover:underline">Mark all read</button>
                      )}
                    </div>
                    <div className="max-h-72 overflow-y-auto divide-y divide-slate-50">
                      {notifications.length === 0 ? (
                        <p className="text-sm text-slate-400 text-center py-8">No notifications</p>
                      ) : notifications.map((n) => (
                        <div key={n.id} className={`px-4 py-3 hover:bg-slate-50 ${!n.is_read ? 'bg-emerald-50/50' : ''}`}>
                          <div className="flex items-start gap-2">
                            {!n.is_read && <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full mt-1.5 shrink-0" />}
                            <div>
                              <p className="text-sm font-medium text-slate-800">{n.title}</p>
                              <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">{n.message}</p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <button className="p-2.5 rounded-xl hover:bg-slate-100 transition-colors text-slate-500 hover:text-slate-800">
                <Settings className="w-5 h-5" />
              </button>

              {/* User avatar + dropdown */}
              <div className="relative">
                <button onClick={() => { setShowUserMenu(!showUserMenu); setShowNotifs(false) }}
                  className="flex items-center gap-2.5 pl-1 pr-2 py-1 rounded-xl hover:bg-slate-100 transition-colors">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center text-white text-xs font-bold">
                    {initials}
                  </div>
                  <div className="hidden md:block text-left">
                    <p className="text-sm font-medium text-slate-800 leading-none">{user?.full_name}</p>
                    <p className="text-xs text-slate-500 mt-0.5">{user?.role}</p>
                  </div>
                  <ChevronDown className="w-3.5 h-3.5 text-slate-400 hidden md:block" />
                </button>
                {showUserMenu && (
                  <div className="absolute right-0 top-12 w-48 bg-white rounded-2xl shadow-xl border border-slate-100 z-50 overflow-hidden">
                    <div className="px-4 py-3 border-b border-slate-100">
                      <p className="text-sm font-semibold text-slate-900">{user?.full_name}</p>
                      <p className="text-xs text-slate-500">{user?.email}</p>
                      <span className={`text-xs font-medium px-2 py-0.5 rounded-full mt-1 inline-block ${ROLE_COLORS[user?.role || 'viewer']}`}>
                        {user?.role}
                      </span>
                    </div>
                    <button onClick={logout}
                      className="flex items-center gap-2 w-full px-4 py-3 text-sm text-red-600 hover:bg-red-50 transition-colors">
                      <LogOut className="w-4 h-4" /> Sign out
                    </button>
                  </div>
                )}
              </div>
            </div>
          </nav>

          <div className="p-6 md:p-8">
            {children}
          </div>
        </div>
      </div>
    </div>
  )
}
