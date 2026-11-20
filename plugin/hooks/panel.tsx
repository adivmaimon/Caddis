// Caddis build panel: shows a running /caddis:build beside the chat. It reads the status file
// progress.sh writes (caddis-build.json in the git dir) and draws it while progress.sh keeps
// writing it. With no live build (none started, finished, or stopped without a last write) it
// shows the active projects as their files stand now, so it never draws a build that is over. With
// Workflow's `Build panel: off`, or where no pane can be placed, it shows the same progress on
// the status line. Outside a repo with .caddis/caddis.md it arms nothing, and no hook lets an
// error out (Invariant 6).
import { atom, read, update } from 'claude-code'
import type { Register } from 'claude-code'

import type { Activity, BuildStatus, ProjectStatus } from '../types/panel-state'

const PANE = 'caddis-build'
const TITLE = 'Caddis build'
// progress.sh rewrites the file every 15s; a 2s poll shows each write promptly for one stat.
const POLL_MS = 2000
// A status file not rewritten for this long has no progress.sh behind it: a build stopped at a
// gate, a Monitor timed out, or a session ended. Eight missed ticks, so a slow tick isn't one.
const STALE_MS = 120_000
const ACTIVE = '.caddis/projects/active'
// The bar's widest; a narrower pane gets a shorter one, so the body never scrolls sideways.
const BAR = 30

function statusLine(s: BuildStatus): string {
  const quiet = s.quiet ? `, quiet for ${fmt(s.idle)}` : ''
  const current = s.current ? `, ${s.current}` : ''
  return `Caddis build: ${s.phases_done}/${s.phases_total} phases${current}, ${fmt(s.elapsed)} of ~${fmt(s.estimate)}${quiet}`
}

// Change a shape tag when its fields change: it declines what an older version stored.
const build = atom({ plugin: 'caddis', key: 'build' } as const, null, { shape: 'build-2' })
// The active projects as their files stand, drawn when no build is live.
const active = atom({ plugin: 'caddis', key: 'active' } as const, [] as ProjectStatus[], { shape: 'active-1' })
const watch = atom({ plugin: 'caddis', key: 'watch' } as const, { start: 0, status: false }, {
  shape: 'watch-1',
})

// The git dir named by a `.git` file (worktrees, submodules), relative to the repo root.
function gitdirOf(text: string, root: string): string {
  const path = (text.match(/^gitdir:\s*(.+)$/m)?.[1] ?? '').trim()
  return path.startsWith('/') ? path : `${root}/${path}`
}

// Workflow's `- Build panel: off` turns the pane off. A missing line means on (Invariant 9).
function panelOn(config: string): boolean {
  const workflow = config.split(/^## /m).find(part => part.startsWith('Workflow')) ?? ''
  return !/^-\s*Build panel:\s*off\b/im.test(workflow)
}

function fmt(seconds: number): string {
  const m = Math.floor(Math.max(0, seconds) / 60)
  if (m < 1) return '<1m'
  if (m < 60) return `${m}m`
  return `${Math.floor(m / 60)}h${m % 60}m`
}

function ago(seconds: number): string {
  return seconds < 60 ? `${Math.max(0, Math.floor(seconds))}s ago` : `${fmt(seconds)} ago`
}

// The line under the phase in progress, so a long phase still shows its builder working.
function activityLine(a: Activity, now: number): string {
  const edit = a.last_edit === null ? null : `last edit ${ago(now - a.last_edit)}`
  if (a.changed === 0) return edit ?? 'no edits yet'
  const files = `${a.changed} file${a.changed === 1 ? '' : 's'} changed`
  return edit ? `${files}, ${edit}` : files
}

// One project file read the way progress.sh reads it: its phases, the first open one, and
// the bullets under Decisions During Build.
export function parseProject(name: string, text: string): ProjectStatus {
  const phases = [...text.matchAll(/^### (Phase \d+.*)$/gm)].map(m => {
    const done = / - DONE \(/.test(m[1])
    return { name: done ? m[1].replace(/ - DONE \(.*$/, '') : m[1].trim(), done }
  })
  const decided = text.split(/^## Decisions During Build.*$/m)[1]?.split(/^## /m)[0] ?? ''
  return {
    name: name.replace(/\.md$/, ''),
    complete: false,
    phases,
    current: phases.find(p => !p.done)?.name ?? null,
    decisions: (decided.match(/^\s*[-*] /gm) ?? []).length,
    activity: null,
  }
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    const started = await next(e)
    try {
      const repo = await $.session.repo()
      if (!repo) return started
      const config = `${repo.root}/.caddis/caddis.md`
      if (!(await $.fs.exists(config))) return started

      let gitDir = `${repo.root}/.git`
      if ((await $.fs.stat(gitDir)).kind === 'file') {
        gitDir = gitdirOf(String(await $.fs.read(gitDir)), repo.root)
      }
      const file = `${gitDir}/caddis-build.json`
      await $.command.register({ name: 'caddis-panel', description: 'Open the Caddis build panel' })

      let seen = -1
      let status: BuildStatus | null = null
      let shown: BuildStatus | null | undefined
      let line: string | undefined
      const files = new Map<string, { mtimeMs: number; project: ProjectStatus }>()
      let listed = ''

      // The active projects, re-reading only files whose mtime moved.
      const scanActive = async () => {
        const entries = (await $.fs.list(`${repo.root}/${ACTIVE}`).catch(() => []))
          .filter(f => f.kind === 'file' && /^(project|task)-.*\.md$/.test(f.name))
          .sort((a, b) => a.name.localeCompare(b.name))
        let changed = entries.length !== files.size
        for (const f of entries) {
          const had = files.get(f.name)
          if (had && had.mtimeMs === f.mtimeMs) continue
          const text = String(await $.fs.read(`${repo.root}/${ACTIVE}/${f.name}`))
          files.set(f.name, { mtimeMs: f.mtimeMs, project: parseProject(f.name, text) })
          changed = true
        }
        const names = entries.map(f => f.name)
        for (const name of [...files.keys()]) if (!names.includes(name)) files.delete(name)
        const key = names.join('\n')
        if (changed || key !== listed) {
          listed = key
          await update($, active, () => names.map(n => files.get(n)!.project))
        }
      }

      $.clock.every(POLL_MS, async () => {
        try {
          const now = await $.clock.now()
          const st = await $.fs.stat(file).catch(() => null)
          if (st?.kind === 'file' && st.mtimeMs !== seen) {
            status = JSON.parse(String(await $.fs.read(file))) as BuildStatus
            seen = st.mtimeMs
          } else if (st?.kind !== 'file') {
            status = null
          }
          const live = status && !status.done && st && now - st.mtimeMs < STALE_MS ? status : null
          // A build that just finished keeps its done view until the next one; a stopped one goes.
          const draw = live ?? (status?.done && st && now - st.mtimeMs < STALE_MS ? status : null)
          if (draw !== shown) {
            shown = draw
            await update($, build, () => draw)
          }
          if (!live) await scanActive()
          if (!status) return
          let last = await read($, watch)
          // A build is new when it is running and started at another time than the last one
          // seen, so a finished file from an earlier session never reopens the panel.
          if (live && status.start !== last.start) {
            let onStatusLine = !panelOn(String(await $.fs.read(config)))
            if (!onStatusLine) {
              // A pane this surface can't place, or an open that fails, falls back to the line.
              onStatusLine = !(await $.ui.open({ id: PANE, title: TITLE }).catch(() => ({ isPlaced: false }))).isPlaced
            }
            last = { start: status.start, status: onStatusLine }
            await update($, watch, () => last)
          }
          if (last.status && last.start === status.start) {
            const want = live ? statusLine(live) : undefined
            if (want !== line) {
              line = want
              await $.ui.status(want)
            }
          }
        } catch {
          // No status file yet, or one mid-replace: the next poll tries again.
        }
      })
    } catch {
      // The panel is optional: a failure here leaves the session and the text reports alone.
    }
    return started
  })

  on('command.run', { command: 'caddis-panel' }, async $ => {
    try {
      await $.ui.open({ id: PANE, title: TITLE })
    } catch {
      return { text: 'The Caddis build panel could not open here.' }
    }
    return { text: 'Caddis build panel opened.' }
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text } = $.ui.resolve(e)
    const s = await read($, build)
    if (!s) {
      const projects = await read($, active)
      return (
        <Box flexDirection="column" paddingX={1}>
          <Text weight="bold">Caddis build</Text>
          <Text dimColor>No build running. /caddis:build starts one.</Text>
          {projects.length === 0 && <Text dimColor>No active projects.</Text>}
          {projects.map(p => (
            <Box flexDirection="column" marginTop={1}>
              <Text weight="bold">{p.name}</Text>
              {p.phases.length === 0 && <Text dimColor>no phases</Text>}
              {p.phases.map(ph => (
                <Text dimColor={!ph.done && ph.name !== p.current}>
                  {ph.done ? <Text color="success">✓</Text> : ph.name === p.current ? '●' : '○'} {ph.name}
                </Text>
              ))}
            </Box>
          ))}
        </Box>
      )
    }

    const total = Math.max(1, s.phases_total)
    // The body less the paddingX on each side and the ' 100%' after the bar.
    const bar = Math.max(4, Math.min(BAR, (e.props.bodyColumns || BAR + 7) - 7))
    const filled = Math.round((bar * s.phases_done) / total)
    const pct = Math.round((100 * s.phases_done) / total)
    const decisions = s.projects.reduce((n, p) => n + p.decisions, 0)
    const time = s.done
      ? 'done'
      : `${fmt(s.elapsed)} / ~${fmt(s.estimate)}${s.left !== null && s.left < 0 ? ' (over)' : ''}`

    const project = (p: ProjectStatus) => (
      <Box flexDirection="column" marginTop={1}>
        <Box flexDirection="row">
          <Text weight="bold">{p.name}</Text>
          {p.complete && <Text color="success">  complete</Text>}
        </Box>
        {p.phases.length === 0 && <Text dimColor>no phases</Text>}
        {p.phases.map(ph =>
          ph.done ? (
            <Text>
              <Text color="success">✓</Text> {ph.name}
            </Text>
          ) : ph.name === p.current ? (
            <Box flexDirection="column">
              <Text>
                <Text color="suggestion">●</Text> <Text weight="bold">{ph.name}</Text>
              </Text>
              {p.activity && !s.done && (
                <Text dimColor>  {activityLine(p.activity, s.start + s.elapsed)}</Text>
              )}
            </Box>
          ) : (
            <Text dimColor>○ {ph.name}</Text>
          ),
        )}
      </Box>
    )

    return (
      <Box flexDirection="column" paddingX={1}>
        <Box flexDirection="row" justifyContent="space-between">
          <Text weight="bold">Caddis build</Text>
          <Text dimColor>{time}</Text>
        </Box>
        <Box flexDirection="row">
          <Text color="success">{'▓'.repeat(filled)}</Text>
          <Text dimColor>{'░'.repeat(bar - filled)}</Text>
          <Text> {pct}%</Text>
        </Box>
        {s.projects.map(project)}
        {s.quiet && !s.done && (
          <Box marginTop={1}>
            <Text color="warning">⚠ no commits or edits for {fmt(s.idle)}</Text>
          </Box>
        )}
        <Box marginTop={1}>
          <Text dimColor>
            {s.phases_done}/{s.phases_total} phases   Decisions: {decisions}
          </Text>
        </Box>
      </Box>
    )
  })
}
