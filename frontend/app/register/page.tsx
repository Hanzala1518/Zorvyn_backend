'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { registerUser } from '@/lib/api'
import { Eye as EyeIcon, EyeOff, Loader2, AlertCircle, CheckCircle2, TrendingUp, ShieldCheck, BarChart3 } from 'lucide-react'

const ROLES = [
  {
    value: 'viewer',
    label: 'Viewer',
    description: 'View dashboard and transaction reports only',
    icon: 'eye',
    color: 'border-blue-200 bg-blue-50',
    activeColor: 'border-blue-500 bg-blue-50 ring-2 ring-blue-300',
    iconColor: 'text-blue-600',
    badge: 'Instant access',
    badgeColor: 'bg-emerald-100 text-emerald-700',
  },
  {
    value: 'analyst',
    label: 'Analyst',
    description: 'Create transactions, run analytics, export reports',
    icon: 'chart',
    color: 'border-purple-200 bg-purple-50',
    activeColor: 'border-purple-500 bg-purple-50 ring-2 ring-purple-300',
    iconColor: 'text-purple-600',
    badge: 'Requires approval',
    badgeColor: 'bg-amber-100 text-amber-700',
  },
]

export default function RegisterPage() {
  const router = useRouter()
  const [form, setForm] = useState({ full_name: '', email: '', password: '', role: 'viewer' })
  const [showPw, setShowPw] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState<{ message: string; requires_approval: boolean } | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await registerUser(form)
      setSuccess({ message: res.data.message, requires_approval: res.data.requires_approval })
    } catch (err: any) {
      const detail = err?.response?.data?.detail
      if (Array.isArray(detail)) {
        setError(detail.map((d: any) => d.msg).join('. '))
      } else {
        setError(detail || 'Registration failed. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6"
        style={{ background: 'linear-gradient(135deg, #c8d8eb 0%, #dce8f5 50%, #e8f0f8 100%)' }}>
        <div className="bg-white rounded-3xl shadow-xl p-10 max-w-md w-full text-center">
          <div className={`w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-5 ${success.requires_approval ? 'bg-amber-100' : 'bg-emerald-100'}`}>
            {success.requires_approval
              ? <ShieldCheck className="w-8 h-8 text-amber-500" />
              : <CheckCircle2 className="w-8 h-8 text-emerald-500" />}
          </div>
          <h2 className="text-2xl font-bold text-slate-900 mb-2">
            {success.requires_approval ? 'Request Submitted!' : 'Account Created!'}
          </h2>
          <p className="text-slate-500 text-sm leading-relaxed mb-6">{success.message}</p>
          {success.requires_approval && (
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-6 text-left">
              <p className="text-sm text-amber-800 font-medium mb-1">What happens next?</p>
              <ul className="text-xs text-amber-700 space-y-1 list-disc list-inside">
                <li>An admin has been notified of your request</li>
                <li>You will be able to log in once they approve</li>
                <li>This usually takes less than 24 hours</li>
              </ul>
            </div>
          )}
          <Link href="/login"
            className="inline-flex items-center justify-center w-full py-3 bg-emerald-500 hover:bg-emerald-600 text-white font-semibold rounded-xl text-sm transition-colors">
            {success.requires_approval ? 'Back to Sign In' : 'Sign In Now'}
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-6"
      style={{ background: 'linear-gradient(135deg, #c8d8eb 0%, #dce8f5 50%, #e8f0f8 100%)' }}>
      <div className="w-full max-w-lg">
        <div className="bg-white rounded-3xl shadow-xl p-8">
          <div className="flex items-center gap-2.5 mb-7">
            <div className="w-8 h-8 bg-emerald-500 rounded-xl flex items-center justify-center">
              <TrendingUp className="w-4 h-4 text-white" />
            </div>
            <span className="text-slate-900 font-bold text-lg">FinanceDesk</span>
          </div>

          <h2 className="text-2xl font-bold text-slate-900 mb-1">Create your account</h2>
          <p className="text-slate-500 text-sm mb-6">Choose your role carefully — it determines what you can do</p>

          {error && (
            <div className="flex items-start gap-2.5 bg-red-50 border border-red-100 text-red-700 rounded-xl px-4 py-3 text-sm mb-5">
              <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Role selector */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Select your role</label>
              <div className="grid grid-cols-2 gap-3">
                {ROLES.map((role) => {
                  const isActive = form.role === role.value
                  return (
                    <button
                      key={role.value}
                      type="button"
                      onClick={() => setForm({ ...form, role: role.value })}
                      className={`text-left p-4 rounded-xl border-2 transition-all ${isActive ? role.activeColor : role.color + ' border-transparent'}`}
                    >
                      {role.icon === 'eye'
                        ? <EyeIcon className={`w-5 h-5 mb-2 ${role.iconColor}`} />
                        : <BarChart3 className={`w-5 h-5 mb-2 ${role.iconColor}`} />}
                      <p className="text-sm font-semibold text-slate-800">{role.label}</p>
                      <p className="text-xs text-slate-500 mt-0.5 mb-2 leading-relaxed">{role.description}</p>
                      <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${role.badgeColor}`}>
                        {role.badge}
                      </span>
                    </button>
                  )
                })}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Full name</label>
              <input value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                placeholder="Jane Smith" required
                className="w-full px-4 py-3 rounded-xl border border-slate-200 text-slate-900 text-sm placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-transparent bg-slate-50" />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Email address</label>
              <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })}
                placeholder="you@example.com" required
                className="w-full px-4 py-3 rounded-xl border border-slate-200 text-slate-900 text-sm placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-transparent bg-slate-50" />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Password</label>
              <div className="relative">
                <input type={showPw ? 'text' : 'password'} value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  placeholder="Min 8 chars, 1 uppercase, 1 number" required
                  className="w-full px-4 py-3 pr-11 rounded-xl border border-slate-200 text-slate-900 text-sm placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-transparent bg-slate-50" />
                <button type="button" onClick={() => setShowPw(!showPw)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
                  {showPw ? <EyeOff className="w-4 h-4" /> : <EyeIcon className="w-4 h-4" />}
                </button>
              </div>
              <div className="flex gap-3 mt-2">
                {[
                  { label: '8+ chars', met: form.password.length >= 8 },
                  { label: 'Uppercase', met: /[A-Z]/.test(form.password) },
                  { label: 'Number', met: /\d/.test(form.password) },
                ].map((hint) => (
                  <div key={hint.label} className={`flex items-center gap-1 text-xs ${hint.met ? 'text-emerald-600' : 'text-slate-400'}`}>
                    <div className={`w-1.5 h-1.5 rounded-full ${hint.met ? 'bg-emerald-500' : 'bg-slate-300'}`} />
                    {hint.label}
                  </div>
                ))}
              </div>
            </div>

            <button type="submit" disabled={loading}
              className="w-full py-3 bg-emerald-500 hover:bg-emerald-600 text-white font-semibold rounded-xl text-sm flex items-center justify-center gap-2 transition-colors disabled:opacity-60 mt-1">
              {loading ? <><Loader2 className="w-4 h-4 animate-spin" /> Creating account...</> : 'Create account'}
            </button>
          </form>

          <p className="text-center text-sm text-slate-500 mt-5">
            Already have an account?{' '}
            <Link href="/login" className="text-emerald-600 font-semibold hover:underline">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  )
}