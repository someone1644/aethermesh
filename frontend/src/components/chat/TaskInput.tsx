import { useState, type FormEvent } from 'react'
import { useEvents } from '../../hooks/useEvents'
import { useRuntime } from '../../hooks/useRuntime'

export default function TaskInput() {
  const [task, setTask] = useState('')
  const { simulateLiveRun } = useEvents()
  const { isLive } = useRuntime()

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (!task.trim() || isLive) return
    simulateLiveRun(task.trim())
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <input
        type="text"
        value={task}
        onChange={(e) => setTask(e.target.value)}
        placeholder="Describe a task for AetherMesh to run…"
        disabled={isLive}
        className="flex-1 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2.5 text-sm text-[var(--color-text)] placeholder:text-[var(--color-text-faint)] focus:outline-none input-glow transition-all disabled:opacity-50"
      />
      <button
        type="submit"
        disabled={isLive || !task.trim()}
        className="rounded-lg btn-primary px-5 py-2.5 text-sm font-medium"
      >
        {isLive ? 'Running…' : 'Run'}
      </button>
    </form>
  )
}
