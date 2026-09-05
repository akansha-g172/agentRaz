import { useEffect, useState } from 'react'
import { api } from '../services/api'
import type { AnalyticsSummary } from '../types'

function MetricCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="rounded-xl border border-slate-700 bg-slate-800/60 p-5">
      <p className="text-sm text-slate-400">{label}</p>
      <p className="mt-1 text-2xl font-bold text-white">{value}</p>
      {sub && <p className="mt-1 text-xs text-slate-500">{sub}</p>}
    </div>
  )
}

export default function MerchantPage() {
  const [data, setData] = useState<AnalyticsSummary | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.getAnalytics()
      .then(setData)
      .catch((e) => setError(e.message))
  }, [])

  if (error) return <div className="text-red-400">{error}</div>
  if (!data) return <div className="text-slate-400">Loading analytics…</div>

  const { revenue, conversion, aov, upsell, uplift } = data

  return (
    <div className="space-y-8">
      <section>
        <h2 className="mb-2 text-2xl font-bold text-white">Merchant Dashboard</h2>
        <p className="text-slate-400">AI-driven growth metrics from live PostgreSQL data.</p>
      </section>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <MetricCard
          label="AI Revenue"
          value={`₹${revenue.total_revenue.toLocaleString('en-IN')}`}
          sub={`${revenue.paid_orders} paid orders`}
        />
        <MetricCard
          label="Conversion Rate"
          value={`${conversion.conversion_rate}%`}
          sub={`${conversion.orders_paid} / ${conversion.sessions} sessions`}
        />
        <MetricCard
          label="Average Order Value"
          value={`₹${aov.average_order_value.toLocaleString('en-IN')}`}
        />
        <MetricCard
          label="Revenue / Session"
          value={`₹${uplift.revenue_per_session.toLocaleString('en-IN')}`}
        />
        <MetricCard
          label="Upsell Rate"
          value={`${upsell.upsell_rate}%`}
          sub={`Avg ${upsell.avg_items_per_order} items/order`}
        />
        <MetricCard
          label="Cross-sell Rate"
          value={`${upsell.cross_sell_rate}%`}
        />
      </div>

      <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
        <h3 className="mb-4 text-lg font-semibold text-white">Revenue Overview</h3>
        <div className="space-y-3">
          {[
            { label: 'Total Revenue', pct: Math.min(100, revenue.total_revenue / 100000 * 100) },
            { label: 'Conversion', pct: conversion.conversion_rate },
            { label: 'Upsell', pct: upsell.upsell_rate },
          ].map((bar) => (
            <div key={bar.label}>
              <div className="mb-1 flex justify-between text-sm">
                <span className="text-slate-400">{bar.label}</span>
                <span className="text-slate-300">{bar.pct.toFixed(1)}%</span>
              </div>
              <div className="h-2 rounded-full bg-slate-800">
                <div
                  className="h-2 rounded-full bg-brand-500 transition-all"
                  style={{ width: `${Math.min(100, bar.pct)}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </section>

      <p className="text-xs text-slate-500">
        Synthetic experiment uplift available via <code className="text-slate-400">experiments/evaluate.py</code> (labeled synthetic).
      </p>
    </div>
  )
}
