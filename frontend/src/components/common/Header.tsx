import type { ReactNode } from 'react'
import { NavLink } from 'react-router-dom'

function IconShell({ children }: { children: ReactNode }) {
  return (
    <svg
      viewBox="0 0 24 24"
      width="18"
      height="18"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {children}
    </svg>
  )
}

const DashboardIcon = () => (
  <IconShell>
    <path d="M3 11.5 12 4l9 7.5" />
    <path d="M5 10v9a1 1 0 0 0 1 1h4v-6h4v6h4a1 1 0 0 0 1-1v-9" />
  </IconShell>
)

const PromptIcon = () => (
  <IconShell>
    <path d="M21 14a2 2 0 0 1-2 2H8l-4 4V6a2 2 0 0 1 2-2h13a2 2 0 0 1 2 2z" />
  </IconShell>
)

const RunIcon = () => (
  <IconShell>
    <circle cx="12" cy="12" r="9" />
    <path d="M10 8.5v7l6-3.5z" fill="currentColor" stroke="none" />
  </IconShell>
)

const PastRunsIcon = () => (
  <IconShell>
    <path d="M3 3v6h6" />
    <path d="M3.5 13a8.5 8.5 0 1 0 2-8.6L3 9" />
    <path d="M12 7.5V12l3.5 2" />
  </IconShell>
)

const PolicyIcon = () => (
  <IconShell>
    <path d="M12 3 4 6.5V11c0 5 3.5 8.7 8 10 4.5-1.3 8-5 8-10V6.5z" />
  </IconShell>
)

const AboutIcon = () => (
  <IconShell>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 11v5.5" />
    <circle cx="12" cy="7.75" r="0.9" fill="currentColor" stroke="none" />
  </IconShell>
)

const LogsIcon = () => (
  <IconShell>
    <path d="M4 4h16v16H4z" />
    <path d="M7 9h10M7 13h10M7 17h6" />
  </IconShell>
)

const TimelineIcon = () => (
  <IconShell>
    <path d="M4 12h16" />
    <circle cx="7" cy="12" r="1.5" fill="currentColor" stroke="none" />
    <circle cx="13" cy="12" r="1.5" fill="currentColor" stroke="none" />
    <circle cx="19" cy="12" r="1.5" fill="currentColor" stroke="none" />
  </IconShell>
)

const GraphIcon = () => (
  <IconShell>
    <circle cx="5" cy="6" r="2" />
    <circle cx="19" cy="6" r="2" />
    <circle cx="12" cy="18" r="2" />
    <path d="M6.7 7.3 10.5 16M17.3 7.3 13.5 16M7 6h10" />
  </IconShell>
)

const ReplayIcon = () => (
  <IconShell>
    <path d="M3 11a9 9 0 1 1 2.6 6.4" />
    <path d="M3 17v-5h5" />
  </IconShell>
)

const NAV_ITEMS: { to: string; label: string; Icon: () => ReactNode; end?: boolean }[] = [
  { to: '/', label: 'Dashboard', Icon: DashboardIcon, end: true },
  { to: '/prompt', label: 'Prompt', Icon: PromptIcon },
  { to: '/run', label: 'Run', Icon: RunIcon },
  { to: '/runs', label: 'Past runs', Icon: PastRunsIcon },
  { to: '/policy', label: 'Policy', Icon: PolicyIcon },
  { to: '/logs', label: 'Logs', Icon: LogsIcon },
  { to: '/timeline', label: 'Timeline', Icon: TimelineIcon },
  { to: '/graph', label: 'Workflow graph', Icon: GraphIcon },
  { to: '/replay', label: 'Replay', Icon: ReplayIcon },
  { to: '/about', label: 'About', Icon: AboutIcon },
]

export default function Header() {
  return (
    <aside className="flex h-screen w-56 shrink-0 flex-col border-r border-[var(--color-border)] bg-[var(--color-surface)]">
      <div className="px-5 py-5">
        <span className="font-mono text-base font-semibold tracking-tight text-[var(--color-text)]">
          AetherMesh
        </span>
      </div>
      <nav className="flex flex-1 flex-col gap-0.5 px-3">
        {NAV_ITEMS.map(({ to, label, Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `flex items-center gap-2.5 rounded-md px-3 py-2 text-sm transition-colors ${
                isActive
                  ? 'bg-[var(--color-primary-soft)] font-medium text-[var(--color-text)]'
                  : 'text-[var(--color-text-muted)] hover:bg-[var(--color-surface-hover)] hover:text-[var(--color-text)]'
              }`
            }
          >
            <Icon />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
