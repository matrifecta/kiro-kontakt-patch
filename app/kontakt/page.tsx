import { CatalogFrame } from "@/components/catalog-frame"
import { LibraryBrowser } from "@/components/library-browser"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { kontaktLibraries } from "@/lib/libraries"

export default function KontaktPage() {
  return (
    <div className="flex flex-col gap-5">
      <header className="flex flex-col gap-2">
        <p className="text-xs font-medium tracking-[0.22em] text-primary uppercase">
          Libraries
        </p>
        <h1 className="font-heading text-3xl font-medium tracking-tight">
          Kontakt catalog
        </h1>
        <p className="max-w-2xl text-sm leading-relaxed text-muted-foreground">
          {kontaktLibraries.length} registered libraries from komplete.db3
          (content_type=2), snapshot 10 Sep 2026. The HTML view is the catalog
          you built in Kiro — jump-index, name-only keyword filter, embedded
          banners. Folder links are desktop-only; this portable copy is
          phone-safe.
        </p>
      </header>

      <Tabs defaultValue="catalog">
        <TabsList>
          <TabsTrigger value="catalog">HTML catalog</TabsTrigger>
          <TabsTrigger value="list">Quick list</TabsTrigger>
        </TabsList>
        <TabsContent value="catalog" className="pt-4">
          <CatalogFrame
            src="/catalogs/KONTAKT-CATALOG-portable.html"
            title="Kontakt library catalog"
          />
        </TabsContent>
        <TabsContent value="list" className="pt-4">
          <LibraryBrowser
            libraries={kontaktLibraries}
            emptyLabel="No Kontakt library matches that filter."
          />
        </TabsContent>
      </Tabs>
    </div>
  )
}
