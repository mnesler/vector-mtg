'use client';

import type { Metadata } from "next";
import "./globals.css";
import AppBar from "../components/AppBar";
import NavigationDrawer from "../components/NavigationDrawer";
import { useState } from "react";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  return (
    <html lang="en" data-theme="wintry">
      <body>
        <AppBar onMenuClick={() => setIsDrawerOpen(true)} />
        <NavigationDrawer
          isOpen={isDrawerOpen}
          onClose={() => setIsDrawerOpen(false)}
        />
        {children}
      </body>
    </html>
  );
}
