import Link from "next/link"
import { ArrowRight } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { dsLibraries, kontaktLibraries } from "@/lib/libraries"
import { endpoints, openItems, projects, statusLabel } from "@/lib/studio"

export default function HomePage() {
  return (
    <div className="flex flex-col gap-8">
      <section className="flex flex-col gap-3">
        <p className="text-xs font-medium tracking-[0.22em] text-primary uppercase">
          CachyOS studio
        </p>
        <h1 className="font-heading max-w-3xl text-3xl font-medium tracking-tight text-balance md:text-4xl">
          Kontakt 8, DecentSampler, and the machine that has to stay quiet at 128.
        </h1>
        <p className="max-w-2xl text-sm leading-relaxed text-muted-foreground md:text-base">
          This hub is the map of the Kiro work on your Plasma box: the portable
          library catalogs, the five specs, and the confirmed audio endpoints.
          It does not talk to Wine from here — it keeps the working picture in
          one place so the next change does not undo the last one.
        </p>
      </section>

      <section className="grid gap-3 sm:grid-cols-3">
        <Stat
          label="Kontakt libraries"
          value={String(kontaktLibraries.length)}
          href="/kontakt"
        />
        <Stat
          label="DecentSampler libraries"
          value={String(dsLibraries.length)}
          href="/decent-sampler"
        />
        <Stat label="Kiro projects" value={String(projects.length)} href="/map" />
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Confirmed endpoints</CardTitle>
            <CardDescription>
              Stage 16rr / 16ss — do not split quantum, ASIO buffer, and JACK latency.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            {endpoints.map((item) => (
              <div key={item.name} className="flex flex-col gap-1">
                <p className="text-sm font-medium">{item.name}</p>
                <p className="text-sm leading-relaxed text-muted-foreground">
                  {item.detail}
                </p>
              </div>
            ))}
            <Link
              href="/runbook"
              className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
            >
              Open the runbook <ArrowRight className="size-3.5" />
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Still open</CardTitle>
            <CardDescription>
              Isolated leftovers — not the audio clock, not a missing Workspace mount.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            {openItems.map((item) => (
              <div key={item.title} className="flex flex-col gap-1">
                <p className="text-sm font-medium">{item.title}</p>
                <p className="text-sm leading-relaxed text-muted-foreground">
                  {item.detail}
                </p>
              </div>
            ))}
          </CardContent>
        </Card>
      </section>

      <section className="flex flex-col gap-3">
        <div className="flex items-end justify-between gap-3">
          <h2 className="font-heading text-lg">Kiro map</h2>
          <Link href="/map" className="text-sm text-primary hover:underline">
            Full map
          </Link>
        </div>
        <div className="grid gap-3 md:grid-cols-2">
          {projects.map((project) => (
            <Link key={project.slug} href="/map" className="block">
              <Card className="h-full transition-colors hover:bg-accent/40">
                <CardHeader>
                  <div className="flex items-start justify-between gap-2">
                    <CardTitle>{project.name}</CardTitle>
                    <Badge
                      variant={
                        project.status === "confirmed" ? "default" : "secondary"
                      }
                    >
                      {statusLabel[project.status]}
                    </Badge>
                  </div>
                  <CardDescription>{project.summary}</CardDescription>
                </CardHeader>
              </Card>
            </Link>
          ))}
        </div>
      </section>
    </div>
  )
}

function Stat({
  label,
  value,
  href,
}: {
  label: string
  value: string
  href: string
}) {
  return (
    <Link href={href}>
      <Card size="sm" className="h-full transition-colors hover:bg-accent/40">
        <CardHeader>
          <CardDescription>{label}</CardDescription>
          <p className="font-heading text-3xl font-medium tracking-tight">
            {value}
          </p>
        </CardHeader>
      </Card>
    </Link>
  )
}
