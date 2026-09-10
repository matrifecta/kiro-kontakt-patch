"use client"

import { useMemo, useState } from "react"

import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { keywordsFor, type Library } from "@/lib/libraries"
import { cn } from "cn"

export function LibraryBrowser({
  libraries,
  emptyLabel,
}: {
  libraries: Library[]
  emptyLabel: string
}) {
  const [query, setQuery] = useState("")
  const [active, setActive] = useState<string[]>([])
  const chips = useMemo(() => keywordsFor(libraries), [libraries])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return libraries.filter((lib) => {
      const words = lib.kw.split(/\s+/).filter(Boolean)
      if (active.length && !active.every((k) => words.includes(k))) return false
      if (!q) return true
      return lib.name.toLowerCase().includes(q) || words.some((w) => w.includes(q))
    })
  }, [libraries, query, active])

  function toggle(word: string) {
    setActive((prev) =>
      prev.includes(word) ? prev.filter((w) => w !== word) : [...prev, word]
    )
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <Input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search by name"
          className="max-w-md"
        />
        <p className="text-sm text-muted-foreground">
          {filtered.length} of {libraries.length}
          {active.length ? ` · ${active.join(" + ")}` : ""}
        </p>
      </div>
      <div className="flex flex-wrap gap-1.5">
        {chips.map(([word, count]) => {
          const on = active.includes(word)
          return (
            <button
              key={word}
              type="button"
              onClick={() => toggle(word)}
              className={cn(
                "rounded-full border px-2.5 py-0.5 text-xs transition-colors",
                on
                  ? "border-primary bg-primary text-primary-foreground"
                  : "border-border bg-card text-muted-foreground hover:text-foreground"
              )}
            >
              {word} {count}
            </button>
          )}
        )}
        {active.length > 0 && (
          <button
            type="button"
            onClick={() => setActive([])}
            className="rounded-full border border-destructive/40 bg-destructive/10 px-2.5 py-0.5 text-xs text-destructive"
          >
            Clear
          </button>
        )}
      </div>
      {filtered.length === 0 ? (
        <p className="rounded-xl border border-dashed border-border px-4 py-10 text-center text-sm text-muted-foreground">
          {emptyLabel}
        </p>
      ) : (
        <ul className="divide-y divide-border overflow-hidden rounded-xl ring-1 ring-foreground/10">
          {filtered.map((lib) => (
            <li
              key={lib.name}
              className="flex items-center justify-between gap-3 bg-card px-4 py-2.5"
            >
              <span className="text-sm font-medium">{lib.name}</span>
              <span className="flex flex-wrap justify-end gap-1">
                {lib.kw
                  .split(/\s+/)
                  .filter(Boolean)
                  .map((word) => (
                    <Badge key={word} variant="secondary">
                      {word}
                    </Badge>
                  ))}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
