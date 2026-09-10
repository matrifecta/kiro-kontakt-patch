import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { projects, statusLabel } from "@/lib/studio"

export default function MapPage() {
  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-2">
        <p className="text-xs font-medium tracking-[0.22em] text-primary uppercase">
          Source map
        </p>
        <h1 className="font-heading text-3xl font-medium tracking-tight">
          All Kiro projects
        </h1>
        <p className="max-w-2xl text-sm leading-relaxed text-muted-foreground">
          From <code className="rounded bg-muted px-1.5 py-0.5 text-xs">/home/phnx/KIRO</code>.
          Specs and scripts live in this repo under <code className="rounded bg-muted px-1.5 py-0.5 text-xs">kiro/</code>.
          The dirty-fix spec is the long thread; the other four are the supporting
          machine — Wine, USB audio, Turing screens.
        </p>
      </header>

      <div className="flex flex-col gap-3">
        {projects.map((project) => (
          <Card key={project.slug}>
            <CardHeader>
              <div className="flex flex-wrap items-start justify-between gap-2">
                <CardTitle>{project.name}</CardTitle>
                <Badge
                  variant={
                    project.status === "confirmed" ? "default" : "secondary"
                  }
                >
                  {statusLabel[project.status]}
                </Badge>
              </div>
              <CardDescription>
                <code className="text-xs">{project.folder}</code>
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-3">
              <p className="text-sm leading-relaxed">{project.summary}</p>
              <p className="text-sm leading-relaxed text-muted-foreground">
                {project.outcome}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
