import type { Metadata } from "next";
import "./globals.css";
import ThemeSwitcher from "../components/ThemeSwitcher";

export const metadata: Metadata = {
  title: "MTG Rule Engine",
  description: "Vector-powered Magic: The Gathering rule engine and card explorer",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" data-theme="wintry">
      <body>
        <ThemeSwitcher />
        {children}
      </body>
    </html>
  );
}
