import grokIndexData from "@/data/grok-index.json"

export type IndexProject = {
  slug: string
  name: string
  map: "created-in-cursor" | "imported-and-modified"
  origin: "cursor" | "kiro"
  kiro_claimed: string | null
  archive_cohesion: "complete" | "partial" | "spec-only"
  living_copy: string
  backdrop: string
  in_repo: string[]
  not_in_repo: string[]
  next_agent: string
  composer_why: string
  can_start: boolean
}

export const grokIndex = grokIndexData as {
  frozen_at: string
  frozen_by: string
  purpose: string
  layout: Record<string, string>
  pipeline: { agent: string; status: string; job: string }[]
  confirmed_endpoints: { name: string; state: string; detail: string }[]
  open_items: string[]
  projects: IndexProject[]
  composer_targets: { path: string; kind: string; note: string }[]
  do_not_touch_this_pass: string[]
}

export const cohesionLabel = {
  complete: "Cohesive enough to continue",
  partial: "Partial — scripts or spec gaps",
  "spec-only": "Spec only — code not in the archive",
} as const
