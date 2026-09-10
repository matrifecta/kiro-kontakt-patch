import Link from "next/link"

import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { cohesionLabel, grokIndex } from "@/lib/grok-index"

export default function IndexPage() {
  return (
    <div className="flex flex-col gap-8">
      <header className="flex flex-col gap-2">
        <p className="text-xs font-medium tracking-[0.22em] text-primary uppercase">
          Grok freeze
        </p>
        <h1 className="font-heading text-3xl font-medium tracking-tight">
          General index of project state
        </h1>
        <p className="max-w-2xl text-sm leading-relaxed text-muted-foreground">
          {grokIndex.purpose} Frozen {grokIndex.frozen_at} by {grokIndex.frozen_by}.
          Living copies sit under{" "}
          <code className="rounded bg-muted px-1.5 py-0.5 text-xs">
            ~/Cursor Projects
          </code>
          . The backdrop DB is read-only.
        </p>
      </header>

      <section className="grid gap-3 md:grid-cols-3">
        {grokIndex.pipeline.map((step) => (
          <Card key={step.agent} size="sm">
            <CardHeader>
              <div className="flex items-start justify-between gap-2">
                <CardTitle className="capitalize">{step.agent}</CardTitle>
                <Badge variant={step.status === "done" ? "default" : "secondary"}>
                  {step.status}
                </Badge>
              </div>
              <CardDescription>{step.job}</CardDescription>
            </CardHeader>
          </Card>
        ))}
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="font-heading text-lg">Projects</h2>
        <div className="flex flex-col gap-3">
          {grokIndex.projects.map((project) => (
            <Card key={project.slug}>
              <CardHeader>
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <CardTitle>{project.name}</CardTitle>
                  <div className="flex flex-wrap gap-1">
                    <Badge variant="secondary">{project.map}</Badge>
                    <Badge
                      variant={project.can_start ? "default" : "secondary"}
                    >
                      {cohesionLabel[project.archive_cohesion]}
                    </Badge>
                  </div>
                </div>
                <CardDescription>
                  Next: {project.next_agent}
                  {project.kiro_claimed ? ` · Kiro claimed ${project.kiro_claimed}` : ""}
                </CardDescription>
              </CardHeader>
              <CardContent className="grid gap-3 text-sm md:grid-cols-2">
                <div>
                  <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
                    Living copy
                  </p>
                  <p className="font-mono text-xs break-all">{project.living_copy}</p>
                  <p className="mt-2 text-xs font-medium tracking-wide text-muted-foreground uppercase">
                    In repo
                  </p>
                  <ul className="list-disc pl-4 text-muted-foreground">
                    {project.in_repo.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
                    Composer note
                  </p>
                  <p className="text-muted-foreground">{project.composer_why}</p>
                  {project.not_in_repo.length > 0 && (
                    <>
                      <p className="mt-2 text-xs font-medium tracking-wide text-muted-foreground uppercase">
                        Not in git (CachyOS)
                      </p>
                      <ul className="list-disc pl-4 text-muted-foreground">
                        {project.not_in_repo.map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ul>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="font-heading text-lg">Composer targets</h2>
        <p className="text-sm text-muted-foreground">
          HTML / web / hypertext and databases that may store markup. Composer
          inspects these next. Do not implement yet.
        </p>
        <ul className="divide-y divide-border overflow-hidden rounded-xl ring-1 ring-foreground/10">
          {grokIndex.composer_targets.map((target) => (
            <li key={target.path} className="bg-card px-4 py-3">
              <p className="font-mono text-xs break-all">{target.path}</p>
              <p className="mt-1 text-xs text-muted-foreground">
                {target.kind} — {target.note}
              </p>
            </li>
          ))}
        </ul>
        <p className="text-sm">
          <Link href="/maps" className="text-primary hover:underline">
            Two maps
          </Link>
          {" · "}
          <Link href="/maps/paths" className="text-primary hover:underline">
            Cited filesystem paths
          </Link>
        </p>
      </section>
    </div>
  )
}
