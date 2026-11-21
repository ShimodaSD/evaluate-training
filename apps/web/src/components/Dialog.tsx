import { useEffect, useRef, type ReactNode } from 'react'

interface Props {
  title: string
  open: boolean
  onClose: () => void
  children: ReactNode
}

/** Modal nativo (<dialog>): foco, Esc e fundo vêm do navegador. */
export function Dialog({ title, open, onClose, children }: Props) {
  const ref = useRef<HTMLDialogElement>(null)

  useEffect(() => {
    const dialog = ref.current
    if (!dialog) return
    if (open && !dialog.open) dialog.showModal?.()
    if (!open && dialog.open) dialog.close?.()
  }, [open])

  return (
    <dialog ref={ref} className="dialog" onClose={onClose} aria-labelledby="dialog-title">
      <header className="dialog__header">
        <h2 id="dialog-title">{title}</h2>
        <button
          type="button"
          className="button button--ghost"
          onClick={onClose}
          aria-label="Fechar"
        >
          ✕
        </button>
      </header>
      {open ? children : null}
    </dialog>
  )
}
