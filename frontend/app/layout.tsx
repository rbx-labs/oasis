import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Oasis Audio Processing",
  description: "Audio processing and transcription platform",
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
