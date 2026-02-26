import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RAG Chatbot",
  description: "AI-powered chatbot with citations for your organization",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen">{children}</body>
    </html>
  );
}
