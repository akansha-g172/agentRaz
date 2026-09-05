import type { Recommendation } from '../types'

interface Props {
  product: Recommendation
  onAdd: () => void
  inCart?: boolean
}

export default function ProductCard({ product, onAdd, inCart }: Props) {
  const specs = product.specifications ?? {}
  const specLine = [specs.ram, specs.storage, specs.weight].filter(Boolean).join(' • ')

  return (
    <article className="rounded-xl border border-slate-700 bg-slate-800/60 p-5 shadow-lg transition hover:border-brand-500/50">
      <div className="mb-3 flex items-start justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-white">{product.name}</h3>
          <p className="text-sm text-slate-400">{product.brand}</p>
        </div>
        <div className="text-right">
          <p className="text-xl font-bold text-emerald-400">₹{product.price.toLocaleString('en-IN')}</p>
          <p className="text-xs text-slate-500">Score {product.recommendation_score}</p>
        </div>
      </div>
      {specLine && <p className="mb-3 text-sm text-slate-300">{specLine}</p>}
      <ul className="mb-4 space-y-1">
        {product.reasons.slice(0, 4).map((r) => (
          <li key={r} className="flex items-center gap-2 text-sm text-emerald-300/90">
            <span>✓</span> {r}
          </li>
        ))}
      </ul>
      <button
        onClick={onAdd}
        disabled={inCart}
        className="w-full rounded-lg bg-brand-600 py-2 text-sm font-medium text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:bg-slate-600"
      >
        {inCart ? 'In Cart' : 'Add to Cart'}
      </button>
    </article>
  )
}
