interface Props {
  steps: { label: string; done: boolean; active?: boolean }[]
}

export default function WorkflowSteps({ steps }: Props) {
  return (
    <div className="flex flex-wrap gap-3">
      {steps.map((step, i) => (
        <div
          key={step.label}
          className={`flex items-center gap-2 rounded-full border px-3 py-1.5 text-sm ${
            step.done
              ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300'
              : step.active
                ? 'border-brand-500/40 bg-brand-500/10 text-brand-300'
                : 'border-slate-700 bg-slate-800/50 text-slate-400'
          }`}
        >
          <span>{step.done ? '✓' : i + 1}</span>
          <span>{step.label}</span>
        </div>
      ))}
    </div>
  )
}
