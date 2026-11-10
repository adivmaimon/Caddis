// Render and behaviour tests for plugin/hooks/panel.tsx. Nothing sits beneath the mod in a
// test, so each hook here stands for the engine: the repo, the files and the panes are mocked.
// tests/test_panel.py copies plugin/ and this file to a temp folder and runs
// `claude plugin test` there, so the plugin directory never holds a test.
import { expect, mock, test } from 'claude-code/testing'
import type { Engine, MockClock } from 'claude-code/testing'
import type { On } from 'claude-code'

const ROOT = '/repo'
const STATUS_FILE = `${ROOT}/.git/caddis-build.json`
const SURFACES = ['terminal', 'desktop', 'vscode', 'mobile'] as const

const PANE = {
  plugin: 'caddis',
  component: 'Pane',
  requestId: 'caddis-build',
  props: {
    title: 'Caddis build',
    isFocused: false,
    bodyColumns: 48,
    placement: 'dock',
    scroll: { offset: 0, bodyRows: 24 },
    view: {},
  },
} as const

function status(over: Record<string, unknown> = {}) {
  return {
    version: 1,
    start: 1000,
    estimate: 55 * 60,
    elapsed: 30 * 60,
    left: 25 * 60,
    phases_done: 2,
    phases_total: 5,
    last_activity: 2700,
    idle: 60,
    quiet: false,
    done: false,
    current: 'project-search Phase 3 - Query',
    projects: [
      {
        name: 'project-search',
        complete: false,
        phases: [
          { name: 'Phase 1 - Schema', done: true },
          { name: 'Phase 2 - Indexer', done: true },
          { name: 'Phase 3 - Query', done: false },
        ],
        current: 'Phase 3 - Query',
        decisions: 2,
      },
      {
        name: 'project-upload',
        complete: false,
        phases: [
          { name: 'Phase 1 - Queue', done: false },
          { name: 'Phase 2 - UI', done: false },
        ],
        current: 'Phase 1 - Queue',
        decisions: 1,
      },
    ],
    ...over,
  }
}

type World = {
  config?: string | null
  file?: Record<string, unknown> | null
  placed?: boolean
  // A `.git` file naming a git dir relative to the root, as a submodule has, and where the
  // status file then is (the engine folds `..` before a path reaches these hooks).
  gitdir?: { line: string; file: string }
}

// The engine beneath the mod: a repo at ROOT, its caddis.md and status file, and the panes.
function world(on: On, w: World) {
  const seen = { opens: [] as string[], statuses: [] as (string | undefined)[], stats: [] as string[] }
  const config = w.config === undefined ? '## Workflow\n\n- Pause after each phase: no\n' : w.config
  let file = w.file === undefined ? status() : w.file
  const statusFile = w.gitdir ? w.gitdir.file : STATUS_FILE
  let mtime = 1
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('session.repo', () => ({ value: { root: ROOT, remote: null, internal: false, name: null } }))
  on('command.register', () => ({ value: { command: 'caddis-panel' } }))
  on('fs.exists', (_, e) => ({ value: e.path === `${ROOT}/.caddis/caddis.md` && config !== null }))
  on('fs.stat', (_, e) => {
    seen.stats.push(e.path)
    if (e.path === `${ROOT}/.git`) {
      return { value: { kind: w.gitdir ? 'file' : 'dir', size: 0, mtimeMs: 1, isLink: false } }
    }
    if (e.path === statusFile && file) return { value: { kind: 'file', size: 1, mtimeMs: mtime, isLink: false } }
    return { deny: 'no such file' }
  })
  on('fs.read', (_, e) => {
    if (e.path === statusFile && file) return { value: JSON.stringify(file) }
    if (e.path === `${ROOT}/.git` && w.gitdir) return { value: `gitdir: ${w.gitdir.line}\n` }
    if (e.path === `${ROOT}/.caddis/caddis.md` && config !== null) return { value: config }
    return { deny: 'no such file' }
  })
  on('ui.open', (_, e) => {
    seen.opens.push(e.id)
    return { value: w.placed === false ? { isPlaced: false, reason: 'no-surface' } : { isPlaced: true } }
  })
  on('ui.status', (_, e) => {
    seen.statuses.push(e.text)
    return { value: undefined }
  })
  const write = (next: Record<string, unknown>) => {
    file = next
    mtime += 1
  }
  return { seen, write }
}

async function start($: Engine, clock: MockClock) {
  await $.session.start({ cwd: ROOT, surface: 'desktop', isInteractive: true })
  await clock.advance(2000)
}

test('a new build opens the panel, drawn mid-build on every surface', async ($, on) => {
  const { seen } = world(on, {})
  await start($, mock.clock(on))
  expect(seen.opens).toEqual(['caddis-build'])
  for (const surface of SURFACES) {
    const ui = await $.ui.mount({ ...PANE, surface })
    expect((await ui.find({ type: 'Text', text: /30m \/ ~55m/ }))?.text).toBe('30m / ~55m')
    expect((await ui.find({ type: 'Text', text: /40%/ })) != null).toBe(true)
    expect((await ui.find({ type: 'Text', text: /project-upload/ }))?.text).toBe('project-upload')
    expect((await ui.find({ type: 'Text', text: /Phase 3 - Query/ })) != null).toBe(true)
    expect((await ui.find({ type: 'Text', text: /Decisions: 3/ })) != null).toBe(true)
    expect(await ui.find({ type: 'Text', text: /no commits or edits/ })).toBe(undefined)
    await ui.unmount()
  }
})

test('the bar fits a narrow pane', async ($, on) => {
  world(on, {})
  await start($, mock.clock(on))
  for (const [cols, width] of [[20, 13], [48, 30]] as const) {
    const ui = await $.ui.mount({ ...PANE, surface: 'terminal', props: { ...PANE.props, bodyColumns: cols } })
    const filled = (await ui.find({ type: 'Text', text: /^▓+$/ }))?.text ?? ''
    const empty = (await ui.find({ type: 'Text', text: /^░+$/ }))?.text ?? ''
    expect(filled.length + empty.length).toBe(width)
    await ui.unmount()
  }
})

test('a .git file leads to the git dir it names', async ($, on) => {
  const file = '/.git/modules/repo/caddis-build.json'
  const { seen } = world(on, { gitdir: { line: '../.git/modules/repo', file } })
  await start($, mock.clock(on))
  expect(seen.stats).toContain(file)
  expect(seen.opens).toEqual(['caddis-build'])
})

test('with Build panel off, no pane opens and the status line shows progress', async ($, on) => {
  const config = '## Workflow\n\n- Pause after each phase: no\n- Build panel: off\n\n## Commands\n'
  const { seen, write } = world(on, { config })
  const clock = mock.clock(on)
  await start($, clock)
  expect(seen.opens).toEqual([])
  expect(seen.statuses).toEqual([
    'Caddis build: 2/5 phases, project-search Phase 3 - Query, 30m of ~55m',
  ])
  write(status({ phases_done: 5, done: true }))
  await clock.advance(2000)
  expect(seen.statuses[seen.statuses.length - 1]).toBe(undefined)
})

test('a pane the surface cannot place falls back to the status line', async ($, on) => {
  const { seen } = world(on, { placed: false, file: status({ quiet: true, idle: 25 * 60 }) })
  await start($, mock.clock(on))
  expect(seen.opens).toEqual(['caddis-build'])
  expect(seen.statuses).toEqual([
    'Caddis build: 2/5 phases, project-search Phase 3 - Query, 30m of ~55m, quiet for 25m',
  ])
})

test('a placed pane leaves the status line alone', async ($, on) => {
  const { seen } = world(on, {})
  await start($, mock.clock(on))
  expect(seen.statuses).toEqual([])
})

test('a Build panel line outside Workflow does not turn the pane off', async ($, on) => {
  const { seen } = world(on, { config: '## Workflow\n\n## Notes\n- Build panel: off\n' })
  await start($, mock.clock(on))
  expect(seen.opens).toEqual(['caddis-build'])
})

test('a quiet build shows the warning on every surface', async ($, on) => {
  world(on, { file: status({ quiet: true, idle: 25 * 60 }) })
  await start($, mock.clock(on))
  for (const surface of SURFACES) {
    const ui = await $.ui.mount({ ...PANE, surface })
    expect((await ui.find({ type: 'Text', text: /no commits or edits/ }))?.text).toBe(
      '⚠ no commits or edits for 25m',
    )
    await ui.unmount()
  }
})

test('the panel moves on as phases finish and says done at the end', async ($, on) => {
  const { seen, write } = world(on, {})
  const clock = mock.clock(on)
  await start($, clock)
  write(status({ phases_done: 5, done: true, elapsed: 50 * 60, left: 0 }))
  await clock.advance(2000)
  expect(seen.opens).toEqual(['caddis-build'])
  for (const surface of SURFACES) {
    const ui = await $.ui.mount({ ...PANE, surface })
    expect((await ui.find({ type: 'Text', text: /^done$/ }))?.text).toBe('done')
    expect((await ui.find({ type: 'Text', text: /100%/ })) != null).toBe(true)
    await ui.unmount()
  }
})

test('a finished file from an earlier build opens nothing', async ($, on) => {
  const { seen } = world(on, { file: status({ done: true }) })
  const clock = mock.clock(on)
  await start($, clock)
  await clock.advance(10000)
  expect(seen.opens).toEqual([])
  expect(seen.statuses).toEqual([])
})

test('a repo without .caddis/caddis.md arms no timer', async ($, on) => {
  const { seen } = world(on, { config: null })
  const clock = mock.clock(on)
  await start($, clock)
  await clock.advance(10000)
  expect(seen.stats).toEqual([])
  expect(seen.opens).toEqual([])
})
