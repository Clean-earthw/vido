
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import type { Metadata, Viewport } from "next";

export const metadata: Metadata = {
  title: "Frame — learn anything, watch it explained",
  description:
    "Frame turns any confusing topic into a short, narrated explainer video, built fresh by AI.",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
