import { useState } from 'react'
import { Link } from 'react-router-dom'
import ProductCard from '../components/ProductCard'
import WorkflowSteps from '../components/WorkflowSteps'
import { api } from '../services/api'
import type { CartLineItem, Recommendation, SearchResponse } from '../types'

export default function BuyerPage() {
  const [query, setQuery] = useState('I need a laptop under ₹70k for coding')
  const [loading, setLoading] = useState(false)
  const [step, setStep] = useState(0)
  const [result, setResult] = useState<SearchResponse | null>(null)
  const [cart, setCart] = useState<{ product_id: number; quantity: number }[]>([])
  const [cartDetails, setCartDetails] = useState<CartLineItem[]>([])
  const [subtotal, setSubtotal] = useState(0)
  const [orderResult, setOrderResult] = useState<{ session_id: string; policy: { policy_result: string; reason: string }; order: { id: string; status: string } } | null>(null)
  const [error, setError] = useState<string | null>(null)

  const runSearch = async () => {
    setLoading(true)
    setError(null)
    setOrderResult(null)
    setStep(1)
    try {
      setStep(2)
      const data = await api.search(query)
      setStep(4)
      setResult(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Search failed')
    } finally {
      setLoading(false)
    }
  }

  const addToCart = async (product: Recommendation) => {
    const items = [...cart.filter((i) => i.product_id !== product.product_id), { product_id: product.product_id, quantity: 1 }]
    setCart(items)
    try {
      const calc = await api.calculateCart(items)
      setCartDetails(calc.items)
      setSubtotal(calc.subtotal)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Cart calculation failed')
    }
  }

  const checkout = async () => {
    if (!cart.length) return
    setLoading(true)
    setError(null)
    try {
      const order = await api.createOrder(cart)
      setOrderResult(order)
      localStorage.setItem('lastSessionId', order.session_id)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Order blocked by policy')
    } finally {
      setLoading(false)
    }
  }

  const steps = [
    { label: 'Understanding request', done: step >= 1, active: step === 1 },
    { label: 'Finding products', done: step >= 2, active: step === 2 },
    { label: 'Checking constraints', done: step >= 3, active: step === 3 },
    { label: 'Ranking products', done: step >= 4, active: step === 4 },
  ]

  return (
    <div className="space-y-8">
      <section>
        <h2 className="mb-2 text-2xl font-bold text-white">Buyer Console</h2>
        <p className="mb-6 text-slate-400">Describe what you need — the Buyer Agent extracts intent and ranks products deterministically.</p>
        <div className="flex gap-3">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="flex-1 rounded-xl border border-slate-700 bg-slate-800 px-4 py-3 text-white placeholder-slate-500 focus:border-brand-500 focus:outline-none"
            placeholder="I need a laptop under ₹70k for coding"
          />
          <button
            onClick={runSearch}
            disabled={loading}
            className="rounded-xl bg-brand-600 px-6 py-3 font-medium text-white hover:bg-brand-700 disabled:opacity-50"
          >
            {loading ? 'Searching…' : 'Search'}
          </button>
        </div>
      </section>

      {(loading || result) && (
        <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
          <h3 className="mb-4 text-sm font-medium uppercase tracking-wide text-slate-400">Agent Workflow</h3>
          <WorkflowSteps steps={steps} />
        </section>
      )}

      {result?.intent && (
        <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
          <h3 className="mb-3 text-sm font-medium uppercase text-slate-400">Extracted Intent</h3>
          <pre className="overflow-x-auto rounded-lg bg-slate-950 p-4 text-sm text-slate-300">
            {JSON.stringify(result.intent, null, 2)}
          </pre>
        </section>
      )}

      {error && (
        <div className="rounded-xl border border-red-500/40 bg-red-500/10 p-4 text-red-300">{error}</div>
      )}

      {result?.recommendations && (
        <section>
          <h3 className="mb-4 text-xl font-semibold text-white">AI Recommendations</h3>
          <div className="grid gap-4 md:grid-cols-2">
            {result.recommendations.map((p) => (
              <ProductCard
                key={p.product_id}
                product={p}
                onAdd={() => addToCart(p)}
                inCart={cart.some((c) => c.product_id === p.product_id)}
              />
            ))}
          </div>
        </section>
      )}

      {cart.length > 0 && (
        <section className="rounded-xl border border-slate-700 bg-slate-800/40 p-5">
          <h3 className="mb-4 text-lg font-semibold">Cart</h3>
          <ul className="mb-4 space-y-2">
            {cartDetails.map((item) => (
              <li key={item.product_id} className="flex justify-between text-sm text-slate-300">
                <span>{item.name} × {item.quantity}</span>
                <span>₹{item.line_total.toLocaleString('en-IN')}</span>
              </li>
            ))}
          </ul>
          <div className="mb-4 flex justify-between border-t border-slate-700 pt-3 font-semibold text-white">
            <span>Subtotal</span>
            <span>₹{subtotal.toLocaleString('en-IN')}</span>
          </div>
          <button
            onClick={checkout}
            disabled={loading}
            className="rounded-lg bg-emerald-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
          >
            Create Order (Policy Check)
          </button>
        </section>
      )}

      {orderResult && (
        <section className={`rounded-xl border p-5 ${orderResult.policy.policy_result === 'APPROVED' ? 'border-emerald-500/40 bg-emerald-500/10' : 'border-red-500/40 bg-red-500/10'}`}>
          <h3 className="mb-2 font-semibold text-white">Policy Result: {orderResult.policy.policy_result}</h3>
          <p className="mb-2 text-sm text-slate-300">{orderResult.policy.reason}</p>
          <p className="text-sm text-slate-400">Order {orderResult.order.id.slice(0, 8)}… — {orderResult.order.status}</p>
          <Link to="/audit" state={{ sessionId: orderResult.session_id }} className="mt-3 inline-block text-sm text-brand-400 hover:underline">
            View audit trail →
          </Link>
        </section>
      )}
    </div>
  )
}
