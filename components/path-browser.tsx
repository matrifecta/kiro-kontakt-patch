"use client"

import { useMemo, useState } from "react"

import { Input } from "@/components/ui/input"
import { mapsCatalog } from "@/lib/maps"

export function PathBrowser() {
  const [query, setQuery] = useState("")
  const [kind, setKind] = useState("all")
  const kinds = mapsCatalog.ref_kinds

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return mapsCatalog.filesystem_refs.filter((ref) => {
      if (kind !== "all" && ref.kind !== kind) return false
      if (!q) return true
      return ref.path.toLowerCase().includes(q)
    })
  }, [query, kind])

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <Input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Filter cited paths"
          className="max-w-md"
        />
        <select
          value={kind}
          onChange={(event) => setKind(event.target.value)}
          className="h-8 rounded-lg border border-input bg-transparent px-2 text-sm"
        >
          <option value="all">All kinds</option>
          {kinds.map((value) => (
            <option key={value} value={value}>
              {value}
            </option>
          ))}
        </select>
        <p className="text-sm text-muted-foreground">
          {filtered.length} of {mapsCatalog.filesystem_refs.length}
        </p>
      </div>
      <ul className="divide-y divide-border overflow-hidden rounded-xl ring-1 ring-foreground/10">
        {filtered.map((ref) => (
          <li key={ref.path} className="bg-card px-4 py-2.5">
            <p className="font-mono text-xs break-all">{ref.path}</p>
            <p className="mt-0.5 text-xs text-muted-foreground">
              {ref.kind} · cited {ref.count}×
            </p>
          </li>
        ))}
      </ul>
    </div>
  )
}
