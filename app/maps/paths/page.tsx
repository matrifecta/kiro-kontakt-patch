import { PathBrowser } from "@/components/path-browser"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { mapsCatalog } from "@/lib/maps"

export default function PathsPage() {
  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-2">
        <p className="text-xs font-medium tracking-[0.22em] text-primary uppercase">
          Machine paths
        </p>
        <h1 className="font-heading text-3xl font-medium tracking-tight">
          Paths the Kiro work already knew
        </h1>
        <p className="max-w-2xl text-sm leading-relaxed text-muted-foreground">
          Pulled from the imported specs and scripts. This Cloud Agent cannot
          open <code className="rounded bg-muted px-1.5 py-0.5 text-xs">/home/phnx</code>{" "}
          or <code className="rounded bg-muted px-1.5 py-0.5 text-xs">/mnt/*</code>{" "}
          — those live on CachyOS. Cursor will not pop a Kiro-style “approve
          lookup” dialog for them from here. On the Plasma box, run{" "}
          <code className="rounded bg-muted px-1.5 py-0.5 text-xs">
            bash tools/bootstrap-cursor-projects.sh
          </code>{" "}
          so <code className="rounded bg-muted px-1.5 py-0.5 text-xs">~/Cursor Projects</code>{" "}
          exists, then open that folder as a workspace if you want local file access.
        </p>
      </header>

      <section className="flex flex-col gap-3">
        <h2 className="font-heading text-lg">Canonical roots</h2>
        <div className="grid gap-3 md:grid-cols-2">
          {mapsCatalog.canonical_roots.map((root) => (
            <Card key={root.path} size="sm">
              <CardHeader>
                <CardTitle className="font-mono text-sm">{root.path}</CardTitle>
                <CardDescription>{root.role}</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-xs text-muted-foreground">
                  {root.on_this_machine
                    ? "Present in this Cloud session after bootstrap."
                    : "On the CachyOS machine only — not visible here."}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="font-heading text-lg">All cited paths</h2>
        <PathBrowser />
      </section>
    </div>
  )
}
