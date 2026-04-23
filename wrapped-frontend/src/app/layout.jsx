import { ThemeProvider } from "@/context/ThemeContext";
import "./globals.css";

export const metadata = {
  title: "Crautos Wrapped 2024",
  description: "Una experiencia inmersiva para explorar el mercado automotriz de Costa Rica con datos en tiempo real de Crautos.",
  author: "Antigravity Dev Team",
  keywords: ["crautos", "wrapped", "costa rica", "autos usados", "mercado automotriz", "estadísticas"],
  icons: {
    icon: "/favicon.png",
  },
  openGraph: {
    title: "Crautos Wrapped 2024",
    description: "Descubre los secretos del mercado automotriz de Costa Rica.",
    url: "https://crautos-wrapped.vercel.app",
    siteName: "Crautos Wrapped",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
      },
    ],
    locale: "es_CR",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Crautos Wrapped 2024",
    description: "Tu historia con el mercado automotriz en tiempo real.",
    images: ["/og-image.png"],
  },
  viewport: "width=device-width, initial-scale=1, maximum-scale=1, user-scalable=0",
};

export default function RootLayout({ children }) {
  return (
    <html lang="es" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="true" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;800&family=JetBrains+Mono:wght@500;700;800&display=swap" rel="stylesheet" />
      </head>
      <body>
        <ThemeProvider>
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
