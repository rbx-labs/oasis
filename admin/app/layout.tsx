import "./globals.css";
import type { Metadata } from "next";
import React from "react";

export const metadata: Metadata = {
  title: "My home",
  description: "My home",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body suppressHydrationWarning className="bg-gray-100">
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <h1>Welcome to Admin page</h1>
            <p>
              This is for internal use case only accessible from local machine.
            </p>
          </div>
        </div>
        <div className="container mx-auto">{children}</div>
      </body>
    </html>
  );
}
