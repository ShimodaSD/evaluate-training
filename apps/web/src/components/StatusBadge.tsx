import type { WorkoutStatus } from '../api/types'

const LABELS: Record<WorkoutStatus, { icon: string; label: string }> = {
  done: { icon: '✓', label: 'Cumprido' },
  partial: { icon: '◐', label: 'Parcial' },
  missed: { icon: '✕', label: 'Não feito' },
  planned: { icon: '○', label: 'Planejado' },
}

export function StatusBadge({ status }: { status: WorkoutStatus }) {
  const { icon, label } = LABELS[status]
  return (
    <span className={`badge badge--${status}`}>
      <span aria-hidden="true">{icon}</span> {label}
    </span>
  )
}
