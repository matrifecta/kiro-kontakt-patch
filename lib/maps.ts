import mapsData from "@/data/maps.json"

export type MapId = "created-in-cursor" | "imported-and-modified"
export type Origin = "cursor" | "kiro"
export type Cohesion = "complete" | "spec-only" | "partial"

export type RegistryProject = {
  slug: string
  name: string
  map: MapId
  origin: Origin
  cohesion: Cohesion
  kiro_folder: string | null
  working_relpath: string
  summary: string
  missing: string[]
  can_start: boolean
  start_note: string
}

export type CanonicalRoot = {
  path: string
  role: string
  on_this_machine: boolean
}

export type FilesystemRef = {
  path: string
  count: number
  files: string[]
  kind: string
}

export const mapsCatalog = mapsData as {
  home_root: string
  maps: { id: MapId; title: string; blurb: string }[]
  projects: RegistryProject[]
  canonical_roots: CanonicalRoot[]
  filesystem_refs: FilesystemRef[]
  ref_kinds: string[]
  ref_count: number
}

export const createdProjects = mapsCatalog.projects.filter(
  (project) => project.map === "created-in-cursor"
)
export const importedProjects = mapsCatalog.projects.filter(
  (project) => project.map === "imported-and-modified"
)

export const cohesionLabel: Record<Cohesion, string> = {
  complete: "Cohesive enough to continue",
  partial: "Partial — scripts or spec gaps",
  "spec-only": "Spec only — code not in the archive",
}
