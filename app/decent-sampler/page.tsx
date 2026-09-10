import { CatalogFrame } from "@/components/catalog-frame"
import { LibraryBrowser } from "@/components/library-browser"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { dsLibraries } from "@/lib/libraries"

export default function DecentSamplerPage() {
  return (
    <div className="flex flex-col gap-5">
      <header className="flex flex-col gap-2">
        <p className="text-xs font-medium tracking-[0.22em] text-primary uppercase">
          Libraries
        </p>
        <h1 className="font-heading text-3xl font-medium tracking-tight">
          DecentSampler catalog
        </h1>
        <p className="max-w-2xl text-sm leading-relaxed text-muted-foreground">
          {dsLibraries.length} loadable libraries in this portable snapshot
          (home SAMPLE STORE, btrfs, WD Black). Expand a library in the HTML
          view for patches. Global DS config is healthy — the Zauberwinds crash
          was one Reaper project’s doubled path, not missing samples.
        </p>
      </header>

      <Tabs defaultValue="catalog">
        <TabsList>
          <TabsTrigger value="catalog">HTML catalog</TabsTrigger>
          <TabsTrigger value="list">Quick list</TabsTrigger>
        </TabsList>
        <TabsContent value="catalog" className="pt-4">
          <CatalogFrame
            src="/catalogs/DS-CATALOG-portable.html"
            title="DecentSampler library catalog"
          />
        </TabsContent>
        <TabsContent value="list" className="pt-4">
          <LibraryBrowser
            libraries={dsLibraries}
            emptyLabel="No DecentSampler library matches that filter."
          />
        </TabsContent>
      </Tabs>
    </div>
  )
}
