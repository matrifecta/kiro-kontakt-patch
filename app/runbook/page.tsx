import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { runbook } from "@/lib/studio"

export default function RunbookPage() {
  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-2">
        <p className="text-xs font-medium tracking-[0.22em] text-primary uppercase">
          Operations
        </p>
        <h1 className="font-heading text-3xl font-medium tracking-tight">
          Runbook
        </h1>
        <p className="max-w-2xl text-sm leading-relaxed text-muted-foreground">
          Copy-paste for the CachyOS machine. After a WirePlumber upgrade, make
          every layer agree on one number (128): forced graph quantum, WineASIO
          buffer, and JACK node.latency. Watch pw-top ERR on the SSL input node,
          not only Kontakt.
        </p>
      </header>

      <div className="flex flex-col gap-3">
        {runbook.map((item) => (
          <Card key={item.title}>
            <CardHeader>
              <CardTitle>{item.title}</CardTitle>
            </CardHeader>
            <CardContent>
              <pre className="overflow-x-auto rounded-lg bg-background p-3 font-mono text-xs leading-relaxed text-foreground/90 ring-1 ring-foreground/10">
                {item.body}
              </pre>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
