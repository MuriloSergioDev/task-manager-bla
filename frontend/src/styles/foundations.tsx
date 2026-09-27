// Doc blocks for Storybook's Foundations page. They parse tokens.css itself
// (imported as raw text), so the page shows exactly what the source says --
// values *and* the comments explaining them -- and can't drift out of date.
import tokensSource from './tokens.css?raw'

interface Token {
  name: string
  value: string
  note: string
  /** Sub-properties such as `--text-title--line-height`, keyed by suffix. */
  modifiers: Record<string, string>
}

const DECLARATION = /^\s*(--[\w-]+):\s*([^;]+);\s*(?:\/\*\s*(.*?)\s*\*\/)?/

function parseTokens(source: string): Token[] {
  const tokens: Token[] = []
  for (const line of source.split('\n')) {
    const match = DECLARATION.exec(line)
    if (!match) continue
    const [, name, value, note = ''] = match
    const [base, modifier] = name.split(/(?<=\w)--(?=[a-z])/)
    const parent = modifier ? tokens.find((token) => token.name === base) : undefined
    if (parent && modifier) {
      parent.modifiers[modifier] = value.trim()
    } else {
      tokens.push({ name, value: value.trim(), note, modifiers: {} })
    }
  }
  return tokens
}

const TOKENS = parseTokens(tokensSource)

function byPrefix(prefix: string): Token[] {
  return TOKENS.filter((token) => token.name.startsWith(prefix))
}

/** `--color-ink` -> `ink`: the suffix is what goes after `bg-`/`text-`/`border-`. */
function utilityName(token: Token, prefix: string): string {
  return token.name.slice(prefix.length)
}

export function ColorPalette() {
  const colors = byPrefix('--color-')
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
      {colors.map((token) => (
        <div key={token.name} className="overflow-hidden rounded-control border border-line bg-sheet">
          <div className="h-14 border-b border-line" style={{ background: token.value }} />
          <div className="px-3 py-2">
            <p className="text-sm font-semibold text-ink">{utilityName(token, '--color-')}</p>
            <p className="text-label text-muted tabular-nums">{token.value}</p>
            {token.note && <p className="mt-1 text-label text-muted">{token.note}</p>}
          </div>
        </div>
      ))}
    </div>
  )
}

export function TypeScale() {
  const steps = byPrefix('--text-')
  return (
    <div className="divide-y divide-line rounded-sheet border border-line bg-sheet">
      {steps.map((token) => (
        <div key={token.name} className="flex flex-col gap-2 px-5 py-4 sm:flex-row sm:items-baseline sm:gap-6">
          <div className="sm:w-48 sm:shrink-0">
            <p className="text-sm font-semibold text-ink">text-{utilityName(token, '--text-')}</p>
            <p className="text-label text-muted tabular-nums">
              {token.value}
              {token.modifiers['line-height'] && ` / ${token.modifiers['line-height']}`}
              {token.modifiers['letter-spacing'] && `, ${token.modifiers['letter-spacing']}`}
            </p>
          </div>
          <div>
            <p
              className="font-bold text-ink"
              style={{
                fontSize: token.value,
                lineHeight: token.modifiers['line-height'],
                letterSpacing: token.modifiers['letter-spacing'],
              }}
            >
              Renew SSL certificate
            </p>
            {token.note && <p className="mt-1 text-label text-muted">{token.note}</p>}
          </div>
        </div>
      ))}
    </div>
  )
}

export function RadiusScale() {
  return (
    <div className="flex flex-wrap gap-6">
      {byPrefix('--radius-').map((token) => (
        <div key={token.name} className="w-40">
          <div className="h-20 border-2 border-ink bg-sheet" style={{ borderRadius: token.value }} />
          <p className="mt-2 text-sm font-semibold text-ink">rounded-{utilityName(token, '--radius-')}</p>
          <p className="text-label text-muted">{token.value}</p>
          {token.note && <p className="text-label text-muted">{token.note}</p>}
        </div>
      ))}
    </div>
  )
}

/** Any remaining group (tracking, widths, shadow, motion) as a plain table. */
export function TokenTable({ prefix }: { prefix: string }) {
  return (
    <table className="mb-4 w-full table-fixed text-sm">
      <tbody>
        {byPrefix(prefix).map((token) => (
          <tr key={token.name} className="border-b border-line">
            <td className="w-1/3 py-2 pr-4 font-semibold text-ink">{token.name}</td>
            <td className="w-1/3 py-2 pr-4 text-muted">{token.value}</td>
            <td className="py-2 text-muted">{token.note}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
