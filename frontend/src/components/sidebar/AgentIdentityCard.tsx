// DiceBear "Avataaars" illustrated portrait — curly brown hair, round glasses,
// light beard, blue jacket, on a lavender background. Seeded so AGENT-007
// always renders the same character.
const AVATAR_URL =
  'https://api.dicebear.com/7.x/avataaars/svg?seed=agent007' +
  '&backgroundType=solid&backgroundColor=c9c2f5' +
  '&top=shortCurly&hairColor=724133' +
  '&facialHair=beardLight&facialHairColor=724133&facialHairProbability=100' +
  '&accessories=round&accessoriesColor=000000&accessoriesProbability=100' +
  '&clothing=blazerAndShirt&clothesColor=2563eb' +
  '&skinColor=ffdbb4&mouth=smile'

/** Static identity header for the Run page's right-hand result panel. */
export default function AgentIdentityCard() {
  return (
    <div className="flex flex-col items-center gap-3 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-5 text-center">
      <img
        src={AVATAR_URL}
        alt="Agent avatar"
        className="h-20 w-20 rounded-full border border-[var(--color-border)] bg-[#C9C2F5] object-cover"
      />
      <div className="flex items-center gap-1.5">
        <span className="h-1.5 w-1.5 rounded-full bg-[#1E8E3E] node-pulse" />
        <span className="font-mono text-[10px] uppercase tracking-wide text-[var(--color-text-muted)]">
          Live
        </span>
      </div>
      <div>
        <div className="font-mono text-xs text-[var(--color-text-muted)]">AGENT-007</div>
        <div className="text-sm font-semibold text-[var(--color-text)]">AetherMesh Runtime Agent</div>
      </div>
    </div>
  )
}
