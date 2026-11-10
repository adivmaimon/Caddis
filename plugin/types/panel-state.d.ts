// State contract for the Caddis build panel (plugin/hooks/panel.tsx). BuildStatus mirrors the
// caddis-build.json that plugin/skills/build/scripts/progress.sh writes; change both together.

export type PhaseStatus = { name: string; done: boolean }

export type ProjectStatus = {
  name: string
  complete: boolean
  phases: PhaseStatus[]
  current: string | null
  decisions: number
}

export type BuildStatus = {
  version: number
  start: number
  estimate: number
  elapsed: number
  left: number | null
  phases_done: number
  phases_total: number
  last_activity: number
  idle: number
  quiet: boolean
  done: boolean
  current: string | null
  projects: ProjectStatus[]
}

// The build the panel last opened for, so a reload or an old finished file never reopens it,
// and whether that build reports on the status line instead of the pane.
export type Watch = { start: number; status: boolean }

declare module 'claude-code' {
  interface PluginState {
    caddis: { build: Shaped<BuildStatus | null>; watch: Shaped<Watch> }
  }
}
