'use client'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { CheckCircle2, XCircle, Clock, Loader2, AlertCircle, RefreshCw } from 'lucide-react'
import { getPendingApprovals, approveUser, rejectUser } from '@/lib/api'
import { getUser, AuthUser } from '@/lib/auth'
import { format } from 'date-fns'

export default function ApprovalsPage() {
  const router = useRouter()
  const user = getUser() as AuthUser
  const [pending, setPending] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [actionId, setActionId] = useState<string | null>(null)
  const [rejectId, setRejectId] = useState<string | null>(null)
  const [rejectReason, setRejectReason] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    if (user?.role !== 'admin') { router.replace('/dashboard'); return }
    fetchPending()
  }, [])

  const fetchPending = async () => {
    setLoading(true)
    try {
      const res = await getPendingApprovals()
      setPending(res.data)
    } catch {
      setError('Failed to load pending approvals.')
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async (id: string) => {
    setActionId(id)
    try {
      await approveUser(id)
      fetchPending()
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Approval failed.')
    } finally { setActionId(null) }
  }

  const handleReject = async () => {
    if (!rejectId || !rejectReason.trim()) return
    setActionId(rejectId)
    try {
      await rejectUser(rejectId, rejectReason.trim())
      setRejectId(null)
      setRejectReason('')
      fetchPending()
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Rejection failed.')
    } finally { setActionId(null) }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Pending Approvals</h1>
          <p className="text-sm text-slate-500 mt-0.5">Analyst registrations waiting for your review</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-slate-500 bg-slate-100 px-3 py-1.5 rounded-xl">
            {pending.length} pending
          </span>
          <button onClick={fetchPending}
            className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-800 bg-slate-100 hover:bg-slate-200 px-3 py-1.5 rounded-xl transition-colors">
            <RefreshCw className="w-3.5 h-3.5" /> Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 bg-red-50 border border-red-100 text-red-700 rounded-xl px-4 py-3 text-sm">
          <AlertCircle className="w-4 h-4 shrink-0" /> {error}
        </div>
      )}

      {loading ? (
        <div className="grid gap-4">
          {Array(3).fill(0).map((_, i) => (
            <div key={i} className="animate-pulse bg-slate-100 rounded-2xl h-24" />
          ))}
        </div>
      ) : pending.length === 0 ? (
        <div className="bg-white rounded-2xl border border-slate-100 p-16 text-center shadow-sm">
          <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto mb-4" />
          <p className="text-lg font-semibold text-slate-800 mb-1">All caught up!</p>
          <p className="text-slate-400 text-sm">No pending approval requests right now.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {pending.map((u) => (
            <div key={u.id} className="bg-white rounded-2xl border border-slate-100 shadow-sm p-5 flex items-center justify-between gap-4 hover:border-slate-200 transition-colors">
              <div className="flex items-center gap-4 min-w-0">
                <div className="w-11 h-11 rounded-full bg-purple-100 text-purple-700 flex items-center justify-center text-sm font-bold shrink-0">
                  {u.full_name.split(' ').map((n: string) => n[0]).join('').slice(0, 2).toUpperCase()}
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <p className="text-base font-semibold text-slate-900">{u.full_name}</p>
                    <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-purple-100 text-purple-700 shrink-0">
                      Analyst request
                    </span>
                  </div>
                  <p className="text-sm text-slate-500 truncate">{u.email}</p>
                  <div className="flex items-center gap-1 mt-1">
                    <Clock className="w-3 h-3 text-slate-400" />
                    <p className="text-xs text-slate-400">
                      Registered {format(new Date(u.created_at), 'dd MMM yyyy, h:mm a')}
                    </p>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <button
                  onClick={() => { setRejectId(u.id); setRejectReason('') }}
                  className="flex items-center gap-1.5 px-4 py-2 text-sm text-red-600 bg-red-50 hover:bg-red-100 rounded-xl font-medium transition-colors">
                  <XCircle className="w-4 h-4" /> Reject
                </button>
                <button
                  onClick={() => handleApprove(u.id)}
                  disabled={actionId === u.id}
                  className="flex items-center gap-1.5 px-4 py-2 text-sm text-white bg-emerald-500 hover:bg-emerald-600 rounded-xl font-medium transition-colors disabled:opacity-60">
                  {actionId === u.id
                    ? <Loader2 className="w-4 h-4 animate-spin" />
                    : <CheckCircle2 className="w-4 h-4" />
                  }
                  Approve
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Reject modal */}
      {rejectId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6">
            <h3 className="text-base font-bold text-slate-900 mb-1">Reject Application</h3>
            <p className="text-sm text-slate-500 mb-4">
              Please provide a reason. This will be visible to the applicant.
            </p>
            <textarea
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              rows={3}
              placeholder="e.g. We cannot verify your organization details at this time..."
              className="w-full px-4 py-3 border border-slate-200 rounded-xl text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-red-400 resize-none bg-slate-50 mb-4"
            />
            <div className="flex gap-3">
              <button
                onClick={() => setRejectId(null)}
                className="flex-1 py-2.5 border border-slate-200 rounded-xl text-sm font-medium text-slate-700 hover:bg-slate-50">
                Cancel
              </button>
              <button
                onClick={handleReject}
                disabled={!rejectReason.trim() || !!actionId}
                className="flex-1 py-2.5 bg-red-500 hover:bg-red-600 text-white rounded-xl text-sm font-medium disabled:opacity-60 flex items-center justify-center gap-2">
                {actionId ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
                Confirm Rejection
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
