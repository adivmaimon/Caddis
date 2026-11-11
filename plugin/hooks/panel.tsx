// Caddis build panel: shows a running /caddis:build beside the chat. It reads the status file
// progress.sh writes (caddis-build.json in the git dir) and draws it; nothing else. With
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
// The bar's widest; a narrower pane gets a shorter one, so the body never scrolls sideways.
const BAR = 30

function statusLine(s: BuildStatus): string {
  const quiet = s.quiet ? `, quiet for ${fmt(s.idle)}` : ''
  const current = s.current ? `, ${s.current}` : ''
  return `Caddis build: ${s.phases_done}/${s.phases_total} phases${current}, ${fmt(s.elapsed)} of ~${fmt(s.estimate)}${quiet}`
}

// Change a shape tag when its fields change: it declines what an older version stored.
const build = atom({ plugin: 'caddis', key: 'build' } as const, null, { shape: 'build-2' })
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
      $.clock.every(POLL_MS, async () => {
        try {
          const st = await $.fs.stat(file)
          if (st.kind !== 'file' || st.mtimeMs === seen) return
          const status = JSON.parse(String(await $.fs.read(file))) as BuildStatus
          seen = st.mtimeMs
          await update($, build, () => status)
          let last = await read($, watch)
          // A build is new when it is running and started at another time than the last one
          // seen, so a finished file from an earlier session never reopens the panel.
          if (!status.done && status.start !== last.start) {
            let onStatusLine = !panelOn(String(await $.fs.read(config)))
            if (!onStatusLine) {
              // A pane this surface can't place, or an open that fails, falls back to the line.
              onStatusLine = !(await $.ui.open({ id: PANE, title: TITLE }).catch(() => ({ isPlaced: false }))).isPlaced
            }
            last = { start: status.start, status: onStatusLine }
            await update($, watch, () => last)
          }
          if (last.status && last.start === status.start) {
            await $.ui.status(status.done ? undefined : statusLine(status))
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
      return (
        <Box flexDirection="column" paddingX={1}>
          <Text weight="bold">Caddis build</Text>
          <Text dimColor>No build running. /caddis:build starts one.</Text>
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
