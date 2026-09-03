import type { ReactNode } from 'react'

export type StatusKind = 'loading' | 'empty' | 'error' | 'permission' | 'human-required' | 'terminal'

interface StatusMessageProps {
  kind: StatusKind
  title?: string
  children?: ReactNode
  action?: ReactNode
  id?: string
}

export function StatusMessage({ kind, title, children, action, id }: StatusMessageProps) {
  const role = kind === 'loading' || kind === 'empty' ? 'status' : 'alert'
  return (
    <div
      id={id}
      className={`status-message status-${kind}`}
      role={role}
      aria-live={kind === 'loading' ? 'polite' : 'assertive'}
    >
      {title && <strong className="status-title">{title}</strong>}
      {children && <div className="status-content">{children}</div>}
      {action && <div className="status-actions">{action}</div>}
    </div>
  )
}
