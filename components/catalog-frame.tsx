type CatalogFrameProps = {
  src: string
  title: string
}

export function CatalogFrame({ src, title }: CatalogFrameProps) {
  return (
    <div className="overflow-hidden rounded-xl bg-white ring-1 ring-foreground/10">
      <iframe
        title={title}
        src={src}
        className="h-[min(78dvh,920px)] w-full border-0 bg-white"
      />
    </div>
  )
}
