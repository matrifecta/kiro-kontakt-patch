import kontaktRaw from "@/data/kontakt-libs.json"
import dsRaw from "@/data/ds-libs.json"

export type Library = {
  name: string
  kw: string
  has_cover?: boolean
}

export const kontaktLibraries = kontaktRaw as Library[]
export const dsLibraries = dsRaw as Library[]

export function keywordsFor(libs: Library[]) {
  const counts = new Map<string, number>()
  for (const lib of libs) {
    for (const word of lib.kw.split(/\s+/).filter(Boolean)) {
      counts.set(word, (counts.get(word) ?? 0) + 1)
    }
  }
  return [...counts.entries()].sort((a, b) => a[0].localeCompare(b[0]))
}
