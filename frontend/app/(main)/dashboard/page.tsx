'use client'
import { useEffect, useState } from 'react'
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis,
  Tooltip, ResponsiveContainer, CartesianGrid
} from 'recharts'
import {
  ArrowUpRight, ArrowDownRight, TrendingUp, RefreshCw,
  ArrowRight, Wallet, CreditCard
} from 'lucide-react'
import { getDashboardSummary, getMonthlyTrends, getRecentActivity, getHealthScore } from '@/lib/api'
import { getUser, formatINR, AuthUser } from '@/lib/auth'

function Skeleton({ className = '' }: { className?: string }) {
  return <div className={`animate-pulse bg-slate-100 rounded-xl ${className}`} />
}

export default function DashboardPage() {
  const user = getUser() as AuthUser
  const [summary, setSummary] = useState<any>(null)
  const [monthly, setMonthly] = useState<any[]>([])
  const [activity, setActivity] = useState<any[]>([])
  const [health, setHealth] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const year = new Date().getFullYear()

  const fetchAll = async () => {
    setLoading(true)
    try {
      const results = await Promise.allSettled([
        getDashboardSummary(),
        getMonthlyTrends(year),
        getRecentActivity(5),
        ...(user?.role !== 'viewer' ? [getHealthScore()] : []),
      ])
      if (results[0].status === 'fulfilled') setSummary(results[0].value.data)
      if (results[1].status === 'fulfilled') setMonthly(results[1].value.data)
      if (results[2].status === 'fulfilled') setActivity(results[2].value.data)
      if (results[3]?.status === 'fulfilled') setHealth((results[3] as any).value.data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchAll() }, [])

  const spendingData = monthly.map((m) => ({
    name: m.month_name.slice(0, 3),
    expenses: m.expenses,
    income: m.income,
  }))

  const areaData = monthly.filter((m) => m.income > 0 || m.expenses > 0).map((m) => ({
    name: m.month_name.slice(0, 3),
    value: m.expenses,
  }))

  const netBalance = summary?.net_balance || 0
  const isPositive = netBalance >= 0
  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'morning' : hour < 18 ? 'afternoon' : 'evening'

  const txColors = ['#e0f2fe', '#fef3c7', '#fce7f3', '#ede9fe', '#d1fae5', '#fee2e2']
  const txIconColors = ['#0284c7', '#d97706', '#db2777', '#7c3aed', '#059669', '#dc2626']

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900">
            Good {greeting}, {user?.full_name?.split(' ')[0]} 👋
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            {"Here's what's happening with your finances today."}
          </p>
        </div>
        <button onClick={fetchAll}
          className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-800 bg-slate-100 hover:bg-slate-200 px-3 py-1.5 rounded-xl transition-colors">
          <RefreshCw className="w-3.5 h-3.5" /> Refresh
        </button>
      </div>

      {/* 3-col grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">

        {/* Col 1: Balance card + Quick Actions */}
        <div className="space-y-5">
          <div className="rounded-2xl p-5" style={{ background: 'linear-gradient(135deg, #e8f4fd 0%, #f0f9f5 100%)', border: '1px solid #e0eefc' }}>
            {loading ? <Skeleton className="h-44" /> : (
              <>
                <p className="text-sm text-slate-500 font-medium mb-1">Net Balance</p>
                <div className="flex items-baseline gap-1 mb-4">
                  <span className="text-4xl font-bold text-slate-900">
                    {isPositive ? '+' : '-'}₹{Math.floor(Math.abs(netBalance)).toLocaleString('en-IN')}
                  </span>
                </div>
                <div className="flex gap-2 mb-5">
                  <div className="flex items-center gap-1.5 bg-emerald-100 px-3 py-1.5 rounded-full">
                    <ArrowUpRight className="w-3.5 h-3.5 text-emerald-600" />
                    <span className="text-xs font-semibold text-emerald-700">{formatINR(summary?.total_income || 0)}</span>
                  </div>
                  <div className="flex items-center gap-1.5 bg-red-100 px-3 py-1.5 rounded-full">
                    <ArrowDownRight className="w-3.5 h-3.5 text-red-600" />
                    <span className="text-xs font-semibold text-red-700">{formatINR(summary?.total_expenses || 0)}</span>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-white rounded-xl px-3 py-2.5">
                    <p className="text-xs text-slate-400">Transactions</p>
                    <p className="text-lg font-bold text-slate-900 mt-0.5">{summary?.transaction_count || 0}</p>
                  </div>
                  <div className="bg-white rounded-xl px-3 py-2.5">
                    <p className="text-xs text-slate-400">This Month</p>
                    <p className="text-lg font-bold text-slate-900 mt-0.5">
                      {(() => {
                        const cur = monthly.find((m) => m.month === new Date().getMonth() + 1)
                        return cur?.expenses ? `₹${(cur.expenses / 1000).toFixed(0)}k` : '₹0'
                      })()}
                    </p>
                  </div>
                </div>
              </>
            )}
          </div>

          <div className="bg-slate-50 rounded-2xl p-4 border border-slate-100">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">Quick Actions</p>
            <div className="grid grid-cols-2 gap-2">
              {[
                { label: 'All Transactions', href: '/transactions', Icon: ArrowRight, color: 'bg-white text-slate-700' },
                { label: 'Add Transaction', href: '/transactions?action=new', Icon: TrendingUp, color: 'bg-emerald-500 text-white' },
                ...(user?.role === 'admin' ? [
                  { label: 'Manage Users', href: '/users', Icon: Wallet, color: 'bg-white text-slate-700' },
                  { label: 'Approvals', href: '/approvals', Icon: CreditCard, color: 'bg-amber-400 text-white' },
                ] : []),
              ].slice(0, 4).map(({ label, href, Icon, color }) => (
                <a key={label} href={href}
                  className={`flex flex-col items-center justify-center gap-1.5 p-3 rounded-xl text-center text-xs font-medium transition-all hover:scale-105 border border-slate-200 ${color}`}>
                  <Icon className="w-4 h-4" />
                  {label}
                </a>
              ))}
            </div>
          </div>
        </div>

        {/* Col 2: Spending bar chart + Health score */}
        <div className="space-y-5">
          <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-semibold text-slate-900">Spending</h2>
              <span className="text-xs text-slate-500 bg-slate-100 px-3 py-1 rounded-full">{year}</span>
            </div>
            {loading ? <Skeleton className="h-48" /> : (
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={spendingData} barGap={2}>
                  <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                  <YAxis hide />
                  <Tooltip
                    contentStyle={{ fontSize: 12, borderRadius: 12, border: 'none', boxShadow: '0 4px 20px rgba(0,0,0,0.1)' }}
                    formatter={(v) => formatINR(Number(v))}
                  />
                  <Bar dataKey="expenses" name="Expenses" fill="#93c5fd" radius={[6, 6, 0, 0]} />
                  <Bar dataKey="income" name="Income" fill="#6ee7b7" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>

          {health ? (
            <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-base font-semibold text-slate-900">Financial Health</h2>
                <span className="text-lg font-bold text-emerald-600">{health.grade}</span>
              </div>
              <div className="flex items-center gap-4 mb-3">
                <div className="w-16 h-16 rounded-full bg-emerald-100 flex items-center justify-center shrink-0">
                  <p className="text-xl font-bold text-emerald-700">{health.score}</p>
                </div>
                <div className="flex-1 space-y-2">
                  {[
                    { label: 'Savings', pts: health.breakdown?.savings_rate_pts ?? 0, max: 40 },
                    { label: 'Diversity', pts: health.breakdown?.diversity_pts ?? 0, max: 20 },
                    { label: 'Consistency', pts: health.breakdown?.consistency_pts ?? 0, max: 20 },
                    { label: 'Balance', pts: health.breakdown?.balance_pts ?? 0, max: 20 },
                  ].map(({ label, pts, max }) => (
                    <div key={label}>
                      <div className="flex justify-between text-xs mb-0.5">
                        <span className="text-slate-500">{label}</span>
                        <span className="text-slate-700 font-medium">{pts}/{max}</span>
                      </div>
                      <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                        <div className="h-full bg-emerald-400 rounded-full" style={{ width: `${(pts / max) * 100}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              {health.insights?.[0] && (
                <p className="text-xs text-slate-500 bg-slate-50 rounded-xl px-3 py-2 leading-relaxed">
                  💡 {health.insights[0]}
                </p>
              )}
            </div>
          ) : (
            <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm flex items-center justify-center h-28">
              <p className="text-sm text-slate-400 text-center">Upgrade to Analyst to see health score</p>
            </div>
          )}
        </div>

        {/* Col 3: Recent Transactions */}
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden"
          style={{ background: 'linear-gradient(180deg, #f0fdf9 0%, #ffffff 40%)' }}>
          <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
            <h2 className="text-base font-semibold text-slate-900">Transactions</h2>
            <a href="/transactions" className="text-xs text-emerald-600 font-semibold hover:underline flex items-center gap-1">
              See All <ArrowRight className="w-3 h-3" />
            </a>
          </div>
          {loading ? (
            <div className="p-5 space-y-3">{Array(5).fill(0).map((_, i) => <Skeleton key={i} className="h-12" />)}</div>
          ) : activity.length === 0 ? (
            <div className="flex items-center justify-center py-12 text-slate-400 text-sm">No transactions yet</div>
          ) : (
            <div className="divide-y divide-slate-50">
              {activity.map((tx: any) => {
                const ci = tx.category.length % txColors.length
                return (
                  <div key={tx.id} className="flex items-center justify-between px-5 py-3.5 hover:bg-slate-50 transition-colors">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold shrink-0"
                        style={{ background: txColors[ci], color: txIconColors[ci] }}>
                        {tx.category.slice(0, 1).toUpperCase()}
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-slate-800">{tx.category}</p>
                        <p className="text-xs text-slate-400">{tx.date}</p>
                      </div>
                    </div>
                    <span className={`text-sm font-bold ${tx.type === 'income' ? 'text-emerald-600' : 'text-slate-700'}`}>
                      {tx.type === 'income' ? '+' : '-'}{formatINR(tx.amount)}
                    </span>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>

      {/* Bottom row: area chart + monthly summary */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2 bg-white rounded-2xl p-5 border border-slate-100 shadow-sm">
          <div className="flex items-center justify-between mb-1">
            <h2 className="text-base font-semibold text-slate-900">Expenses Over Time</h2>
            <span className="text-xs text-slate-400 bg-slate-100 px-3 py-1 rounded-full">{year}</span>
          </div>
          {areaData.length > 0 && (
            <p className="text-sm text-slate-500 mb-4">
              Peak: {formatINR(Math.max(...areaData.map((d) => d.value)))}
            </p>
          )}
          {loading ? <Skeleton className="h-52" /> : (
            <ResponsiveContainer width="100%" height={210}>
              <AreaChart data={areaData} margin={{ top: 5, right: 5, bottom: 0, left: -15 }}>
                <defs>
                  <linearGradient id="expGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#93c5fd" stopOpacity={0.5} />
                    <stop offset="95%" stopColor="#93c5fd" stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} axisLine={false} tickLine={false}
                  tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`} />
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                <Tooltip contentStyle={{ fontSize: 12, borderRadius: 12, border: 'none', boxShadow: '0 4px 20px rgba(0,0,0,0.1)' }}
                  formatter={(v) => formatINR(Number(v))} />
                <Area type="monotone" dataKey="value" name="Expenses"
                  stroke="#3b82f6" strokeWidth={2.5} fill="url(#expGrad)" dot={false}
                  activeDot={{ r: 5, fill: '#3b82f6', strokeWidth: 0 }} />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm">
          <h2 className="text-base font-semibold text-slate-900 mb-4">Monthly Summary</h2>
          {loading ? (
            <div className="space-y-3">{Array(4).fill(0).map((_, i) => <Skeleton key={i} className="h-10" />)}</div>
          ) : (
            <div className="space-y-3">
              {monthly.filter((m) => m.income > 0 || m.expenses > 0).slice(-4).reverse().map((m) => {
                const net = m.income - m.expenses
                const isPos = net >= 0
                return (
                  <div key={m.month} className="flex items-center justify-between p-3 bg-slate-50 rounded-xl">
                    <div>
                      <p className="text-sm font-semibold text-slate-800">{m.month_name.slice(0, 3)}</p>
                      <p className="text-xs text-slate-400">{m.income > 0 ? 'Has data' : 'No data'}</p>
                    </div>
                    <div className="text-right">
                      <p className={`text-sm font-bold ${isPos ? 'text-emerald-600' : 'text-red-500'}`}>
                        {isPos ? '+' : ''}{formatINR(net)}
                      </p>
                      <p className="text-xs text-slate-400">{formatINR(m.expenses)} spent</p>
                    </div>
                  </div>
                )
              })}
              {monthly.filter((m) => m.income > 0 || m.expenses > 0).length === 0 && (
                <p className="text-sm text-slate-400 text-center py-6">Add transactions to see trends</p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
