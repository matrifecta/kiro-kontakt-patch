import Link from "next/link"

import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  cohesionLabel,
  createdProjects,
  importedProjects,
  mapsCatalog,
  type RegistryProject,
} from "@/lib/maps"

export default function MapsPage() {
  return (
    <div className="flex flex-col gap-8">
      <header className="flex flex-col gap-2">
        <p className="text-xs font-medium tracking-[0.22em] text-primary uppercase">
          Cursor Projects
        </p>
        <h1 className="font-heading text-3xl font-medium tracking-tight">
          Two maps under your home folder
        </h1>
        <p className="max-w-2xl text-sm leading-relaxed text-muted-foreground">
          Root is{" "}
          <code className="rounded bg-muted px-1.5 py-0.5 text-xs">
            {mapsCatalog.home_root}
          </code>{" "}
          — on CachyOS that is{" "}
          <code className="rounded bg-muted px-1.5 py-0.5 text-xs">
            /home/phnx/Cursor Projects
          </code>
          . Kiro achievements live in the frozen backdrop DB beside the two
          maps. Working files are the symlinks; the DB is the snapshot of what
          Kiro already did.
        </p>
        <p className="text-sm">
          <Link href="/maps/paths" className="text-primary hover:underline">
            Filesystem paths cited in the imported code
          </Link>
        </p>
      </header>

      <div className="grid gap-6 lg:grid-cols-2">
        <MapColumn
          title="Created in Cursor"
          folder="created-in-cursor/"
          blurb="New work. Studio Hub is the first project in this map."
          projects={createdProjects}
        />
        <MapColumn
          title="Imported and modified"
          folder="imported-and-modified/"
          blurb="Kiro specs and scripts, linked here so edits stay in git. Backdrop DB is read-only."
          projects={importedProjects}
        />
      </div>
    </div>
  )
}

function MapColumn({
  title,
  folder,
  blurb,
  projects,
}: {
  title: string
  folder: string
  blurb: string
  projects: RegistryProject[]
}) {
  return (
    <section className="flex flex-col gap-3">
      <div>
        <h2 className="font-heading text-lg">{title}</h2>
        <p className="text-xs text-muted-foreground">
          <code>{folder}</code>
        </p>
        <p className="mt-1 text-sm text-muted-foreground">{blurb}</p>
      </div>
      {projects.map((project) => (
        <Card key={project.slug}>
          <CardHeader>
            <div className="flex flex-wrap items-start justify-between gap-2">
              <CardTitle>{project.name}</CardTitle>
              <Badge variant={project.can_start ? "default" : "secondary"}>
                {cohesionLabel[project.cohesion]}
              </Badge>
            </div>
            <CardDescription>
              <code className="text-xs">{project.working_relpath}</code>
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-2">
            <p className="text-sm leading-relaxed">{project.summary}</p>
            <p className="text-sm leading-relaxed text-muted-foreground">
              {project.start_note}
            </p>
            {project.missing.length > 0 && (
              <ul className="list-disc space-y-1 pl-4 text-xs text-muted-foreground">
                {project.missing.map((gap) => (
                  <li key={gap}>{gap}</li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      ))}
    </section>
  )
}
