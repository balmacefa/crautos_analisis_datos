# 🚗 Crautos Wrapped

Crautos Wrapped is a premium, data-driven storytelling experience that analyzes the Costa Rican automotive market. It transforms complex marketplace statistics into an interactive, visual narrative—much like Spotify Wrapped—allowing users to explore trends, prices, and insights with high-fidelity animations.

## ✨ Key Features

- **Interactive Stories**: A cinematic walkthrough of yearly market data (Total listings, investment averages, geographical density).
- **Market Insights Dashboard**: Advanced analytics including depreciation curves, bargain detections, and vehicle-specific comparisons.
- **Premium UI/UX**:
  - Dark mode glassmorphism aesthetics.
  - Fluid animations powered by **Framer Motion**.
  - Interactive confetti celebrations with **Canvas-Confetti**.
- **Real-time Search**: Powered by **Typesense** for lightning-fast model and brand lookups.

## 🛠️ Tech Stack

- **Framework**: [Next.js](https://nextjs.org) (App Router)
- **Styling**: [Tailwind CSS 4](https://tailwindcss.com)
- **Animations**: [Framer Motion](https://www.framer.com/motion/)
- **Data Fetching**: [SWR](https://swr.vercel.app/)
- **Icons**: [Lucide React](https://lucide.dev)

## 🚀 Getting Started

### Prerequisites

Ensure you have the full stack running (API + Scraper) or access to the production endpoints.

### Option 1: Docker (Recommended)

The easiest way to run the frontend is through the root project's Docker setup:

```bash
# From the root directory
docker compose -f docker-compose.dev.yml up -d --build
```
The application will be available at [http://localhost:3001](http://localhost:3001).

### Option 2: Local Development

If you prefer to run it manually:

1.  **Install dependencies**:
    ```bash
    npm install
    ```
2.  **Configure environment**: Create a `.env.local` file (see `.env.example` if available).
3.  **Run the dev server**:
    ```bash
    npm run dev
    ```
    Access it at [http://localhost:3000](http://localhost:3000).

## 📊 Environment Variables

| Variable | Description |
| :--- | :--- |
| `NEXT_PUBLIC_API_URL` | Base URL for the FastAPI backend. |
| `NEXT_PUBLIC_TYPESENSE_URL` | Endpoint for the Typesense search engine. |
| `NEXT_PUBLIC_TYPESENSE_API_KEY` | Public key for search operations. |

## 🧪 Testing

The project uses Playwright for End-to-End testing.

```bash
npx playwright test
```

---

Developed as part of the **Crautos Analisis Datos** ecosystem.
