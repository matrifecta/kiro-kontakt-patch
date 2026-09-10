import type { Metadata } from "next"
import { Geist, Geist_Mono } from "next/font/google"

import { StudioShell } from "@/components/studio-shell"
import "./globals.css"

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
})

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
})

export const metadata: Metadata = {
  title: "Studio Hub — Kontakt on CachyOS",
  description:
    "Crtomir’s CachyOS studio map: Kontakt 8 catalogs, DecentSampler, Wine/NTFS runbook, and the Kiro specs that built it.",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${geistSans.variable} ${geistMono.variable} min-h-dvh font-sans antialiased`}
      >
        <StudioShell>{children}</StudioShell>
      </body>
    </html>
  )
}
