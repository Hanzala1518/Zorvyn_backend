"use client";

import { useEffect, useState, useRef } from "react";
import { format } from "date-fns";
import { Plus, Pencil, Trash2, Download, Search, ChevronLeft, ChevronRight } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  getTransactions,
  createTransaction,
  updateTransaction,
  deleteTransaction,
  exportTransactions,
} from "@/lib/api";
import { getUser } from "@/lib/auth";

const INR = (v: number) =>
  new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" }).format(v);

const TX_BG = ['#e0f2fe','#fef3c7','#fce7f3','#ede9fe','#d1fae5','#fee2e2'];
const TX_FG = ['#0284c7','#d97706','#db2777','#7c3aed','#059669','#dc2626'];

const EMPTY_FORM = {
  amount: "",
  type: "expense",
  category: "",
  date: format(new Date(), "yyyy-MM-dd"),
  notes: "",
};

type Transaction = {
  id: string;
  amount: number;
  type: string;
  category: string;
  date: string;
  notes: string;
};

export default function TransactionsPage() {
  const user = getUser();
  const canEdit = user?.role === "admin" || user?.role === "analyst";
  const canDelete = user?.role === "admin";

  const [rows, setRows] = useState<Transaction[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const pageSize = 10;

  const [typeFilter, setTypeFilter] = useState<string>("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [search, setSearch] = useState("");
  const [appliedFilters, setAppliedFilters] = useState<Record<string, string>>({});

  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<Transaction | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");

  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  const anchorRef = useRef<HTMLAnchorElement>(null);

  const fetchRows = (pageNum = page, filters = appliedFilters) => {
    setLoading(true);
    const params: Record<string, unknown> = { page: pageNum, page_size: pageSize, ...filters };
    getTransactions(params)
      .then((res) => {
        setRows(res.data.transactions);
        setTotal(res.data.total);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchRows(page, appliedFilters);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  const applyFilters = () => {
    const f: Record<string, string> = {};
    if (typeFilter) f.type = typeFilter;
    if (categoryFilter) f.category = categoryFilter;
    if (dateFrom) f.date_from = dateFrom;
    if (dateTo) f.date_to = dateTo;
    if (search) f.search = search;
    setAppliedFilters(f);
    setPage(1);
    fetchRows(1, f);
  };

  const resetFilters = () => {
    setTypeFilter("");
    setCategoryFilter("");
    setDateFrom("");
    setDateTo("");
    setSearch("");
    const empty = {};
    setAppliedFilters(empty);
    setPage(1);
    fetchRows(1, empty);
  };

  const openAdd = () => {
    setEditTarget(null);
    setForm(EMPTY_FORM);
    setFormError("");
    setDialogOpen(true);
  };

  const openEdit = (tx: Transaction) => {
    setEditTarget(tx);
    setForm({
      amount: String(tx.amount),
      type: tx.type,
      category: tx.category,
      date: tx.date.slice(0, 10),
      notes: tx.notes || "",
    });
    setFormError("");
    setDialogOpen(true);
  };

  const saveForm = async () => {
    if (!form.amount || !form.category || !form.date) {
      setFormError("Amount, category, and date are required.");
      return;
    }
    setSaving(true);
    setFormError("");
    try {
      const payload = { ...form, amount: parseFloat(form.amount) };
      if (editTarget) {
        await updateTransaction(editTarget.id, payload);
      } else {
        await createTransaction(payload);
      }
      setDialogOpen(false);
      fetchRows();
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setFormError(err?.response?.data?.detail || "Failed to save.");
    } finally {
      setSaving(false);
    }
  };

  const confirmDelete = async () => {
    if (!deleteId) return;
    setDeleting(true);
    try {
      await deleteTransaction(deleteId);
      setDeleteId(null);
      fetchRows();
    } finally {
      setDeleting(false);
    }
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      const res = await exportTransactions(appliedFilters);
      const url = URL.createObjectURL(new Blob([res.data], { type: "text/csv" }));
      const a = anchorRef.current!;
      a.href = url;
      a.download = `transactions_${format(new Date(), "yyyy-MM-dd")}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setExporting(false);
    }
  };

  const start = (page - 1) * pageSize + 1;
  const end = Math.min(page * pageSize, total);

  return (
    <div className="space-y-6">
      {/* eslint-disable-next-line jsx-a11y/anchor-has-content */}
      <a ref={anchorRef} className="hidden" />

      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Transactions</h1>
          <p className="text-sm text-slate-500 mt-0.5">Track and manage all income &amp; expense records</p>
        </div>
        <div className="flex gap-2">
          {canEdit && (
            <button
              onClick={handleExport}
              disabled={exporting}
              className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-200 hover:bg-slate-50 rounded-xl transition-colors disabled:opacity-60"
            >
              <Download className="h-4 w-4" />
              {exporting ? "Exporting…" : "Export CSV"}
            </button>
          )}
          {canEdit && (
            <button
              onClick={openAdd}
              className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-white bg-emerald-500 hover:bg-emerald-600 rounded-xl transition-colors"
            >
              <Plus className="h-4 w-4" />
              Add Transaction
            </button>
          )}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-4">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1">Total Records</p>
          <p className="text-2xl font-bold text-slate-900">{total}</p>
          <p className="text-xs text-slate-400 mt-0.5">matched transactions</p>
        </div>
        <div className="rounded-2xl border shadow-sm p-4" style={{background:'linear-gradient(135deg,#f0fdf4 0%,#ffffff 100%)',borderColor:'#bbf7d0'}}>
          <p className="text-xs font-semibold text-emerald-600 uppercase tracking-wide mb-1">Income (this page)</p>
          <p className="text-2xl font-bold text-emerald-700">{INR(rows.filter(r=>r.type==='income').reduce((s,r)=>s+r.amount,0))}</p>
          <p className="text-xs text-slate-400 mt-0.5">{rows.filter(r=>r.type==='income').length} entries</p>
        </div>
        <div className="rounded-2xl border shadow-sm p-4" style={{background:'linear-gradient(135deg,#fff1f2 0%,#ffffff 100%)',borderColor:'#fecdd3'}}>
          <p className="text-xs font-semibold text-red-500 uppercase tracking-wide mb-1">Expenses (this page)</p>
          <p className="text-2xl font-bold text-red-600">{INR(rows.filter(r=>r.type==='expense').reduce((s,r)=>s+r.amount,0))}</p>
          <p className="text-xs text-slate-400 mt-0.5">{rows.filter(r=>r.type==='expense').length} entries</p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-4">
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-3">Filters</p>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          <Select value={typeFilter} onValueChange={setTypeFilter}>
            <SelectTrigger className="rounded-xl border-slate-200 text-sm">
              <SelectValue placeholder="All Types" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="income">Income</SelectItem>
              <SelectItem value="expense">Expense</SelectItem>
            </SelectContent>
          </Select>
          <Input
            className="rounded-xl border-slate-200 text-sm"
            placeholder="Category"
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
          />
          <Input
            className="rounded-xl border-slate-200 text-sm"
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
          />
          <Input
            className="rounded-xl border-slate-200 text-sm"
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
          />
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400 pointer-events-none" />
            <Input
              className="pl-9 rounded-xl border-slate-200 text-sm"
              placeholder="Search…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && applyFilters()}
            />
          </div>
          <div className="flex gap-2">
            <button
              onClick={applyFilters}
              className="flex-1 py-2 text-sm font-medium text-white bg-emerald-500 hover:bg-emerald-600 rounded-xl transition-colors"
            >
              Apply
            </button>
            <button
              onClick={resetFilters}
              className="flex-1 py-2 text-sm font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-xl transition-colors"
            >
              Reset
            </button>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
        {loading ? (
          <div className="space-y-2 p-5">
            {Array.from({ length: pageSize }).map((_, i) => (
              <div key={i} className="h-11 animate-pulse rounded-xl bg-slate-100" />
            ))}
          </div>
        ) : rows.length === 0 ? (
          <div className="p-16 text-center">
            <div className="w-12 h-12 rounded-2xl bg-slate-100 flex items-center justify-center mx-auto mb-4">
              <Search className="w-6 h-6 text-slate-400" />
            </div>
            <p className="text-base font-semibold text-slate-700 mb-1">No transactions found</p>
            <p className="text-sm text-slate-400">Try adjusting your filters or add a new transaction.</p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow className="border-slate-100 bg-slate-50/60">
                <TableHead className="text-xs font-semibold text-slate-500 uppercase tracking-wide pl-5">Date</TableHead>
                <TableHead className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Category</TableHead>
                <TableHead className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Type</TableHead>
                <TableHead className="text-xs font-semibold text-slate-500 uppercase tracking-wide text-right">Amount</TableHead>
                <TableHead className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Notes</TableHead>
                {(canEdit || canDelete) && (
                  <TableHead className="text-xs font-semibold text-slate-500 uppercase tracking-wide text-right pr-5">Actions</TableHead>
                )}
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((tx) => (
                <TableRow key={tx.id} className="border-slate-50 hover:bg-slate-50/50 transition-colors">
                  <TableCell className="text-sm text-slate-600 pl-5">
                    {format(new Date(tx.date), "MMM d, yyyy")}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2.5">
                      <div className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0"
                        style={{background: TX_BG[tx.category.length % TX_BG.length], color: TX_FG[tx.category.length % TX_FG.length]}}>
                        {tx.category.slice(0,1).toUpperCase()}
                      </div>
                      <span className="font-medium text-slate-800">{tx.category}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize ${
                      tx.type === "income"
                        ? "bg-emerald-100 text-emerald-700"
                        : "bg-red-100 text-red-600"
                    }`}>
                      {tx.type}
                    </span>
                  </TableCell>
                  <TableCell className={`text-right font-semibold ${tx.type === "income" ? "text-emerald-600" : "text-red-500"}`}>
                    {INR(tx.amount)}
                  </TableCell>
                  <TableCell className="text-slate-400 text-sm max-w-[180px] truncate">
                    {tx.notes ? tx.notes.slice(0, 40) : "—"}
                  </TableCell>
                  {(canEdit || canDelete) && (
                    <TableCell className="text-right pr-5">
                      <div className="flex justify-end gap-1">
                        {canEdit && (
                          <button
                            onClick={() => openEdit(tx)}
                            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
                          >
                            <Pencil className="h-4 w-4" />
                          </button>
                        )}
                        {canDelete && (
                          <button
                            onClick={() => setDeleteId(tx.id)}
                            className="p-1.5 rounded-lg text-slate-400 hover:text-red-600 hover:bg-red-50 transition-colors"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        )}
                      </div>
                    </TableCell>
                  )}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>

      {/* Pagination */}
      {total > 0 && (
        <div className="flex items-center justify-between text-sm text-slate-500 px-1">
          <span>Showing <span className="font-medium text-slate-700">{start}–{end}</span> of <span className="font-medium text-slate-700">{total}</span> results</span>
          <div className="flex gap-1.5">
            <button
              disabled={page === 1}
              onClick={() => setPage((p) => p - 1)}
              className="p-2 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <button
              disabled={end >= total}
              onClick={() => setPage((p) => p + 1)}
              className="p-2 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {/* Add / Edit Dialog */}
      {dialogOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg p-6">
            <h3 className="text-base font-bold text-slate-900 mb-4">
              {editTarget ? "Edit Transaction" : "Add Transaction"}
            </h3>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-sm font-medium text-slate-700">Amount</label>
                  <Input
                    type="number"
                    step="0.01"
                    value={form.amount}
                    onChange={(e) => setForm((f) => ({ ...f, amount: e.target.value }))}
                    placeholder="0.00"
                    className="rounded-xl border-slate-200"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm font-medium text-slate-700">Type</label>
                  <Select value={form.type} onValueChange={(v) => setForm((f) => ({ ...f, type: v }))}>
                    <SelectTrigger className="rounded-xl border-slate-200">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="income">Income</SelectItem>
                      <SelectItem value="expense">Expense</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-sm font-medium text-slate-700">Category</label>
                  <Input
                    value={form.category}
                    onChange={(e) => setForm((f) => ({ ...f, category: e.target.value }))}
                    placeholder="e.g. Food"
                    className="rounded-xl border-slate-200"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm font-medium text-slate-700">Date</label>
                  <Input
                    type="date"
                    value={form.date}
                    onChange={(e) => setForm((f) => ({ ...f, date: e.target.value }))}
                    className="rounded-xl border-slate-200"
                  />
                </div>
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-slate-700">Notes</label>
                <Textarea
                  value={form.notes}
                  onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
                  placeholder="Optional notes…"
                  rows={3}
                  className="rounded-xl border-slate-200 resize-none"
                />
              </div>
              {formError && (
                <p className="text-sm text-red-500 bg-red-50 rounded-xl px-3 py-2">{formError}</p>
              )}
              <div className="flex gap-3 pt-1">
                <button
                  onClick={() => setDialogOpen(false)}
                  className="flex-1 py-2.5 border border-slate-200 rounded-xl text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={saveForm}
                  disabled={saving}
                  className="flex-1 py-2.5 bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl text-sm font-medium disabled:opacity-60 transition-colors"
                >
                  {saving ? "Saving…" : "Save"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirm */}
      {deleteId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm p-6">
            <div className="w-11 h-11 rounded-full bg-red-100 flex items-center justify-center mb-4">
              <Trash2 className="w-5 h-5 text-red-500" />
            </div>
            <h3 className="text-base font-bold text-slate-900 mb-1">Delete Transaction</h3>
            <p className="text-sm text-slate-500 mb-5">
              Are you sure you want to delete this transaction? This action cannot be undone.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setDeleteId(null)}
                className="flex-1 py-2.5 border border-slate-200 rounded-xl text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={confirmDelete}
                disabled={deleting}
                className="flex-1 py-2.5 bg-red-500 hover:bg-red-600 text-white rounded-xl text-sm font-medium disabled:opacity-60 transition-colors"
              >
                {deleting ? "Deleting…" : "Delete"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
