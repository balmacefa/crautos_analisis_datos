"use client";

import React from 'react';
import { AlertTriangle, ImageOff } from 'lucide-react';
import { useTheme } from '@/context/ThemeContext';
import { Badge } from '@/components/ui/Badge';
import { Background } from '@/components/layout/Background';
import { PageHeader } from '@/components/layout/PageHeader';
import { BottomNav } from '@/components/layout/BottomNav';
import { cn } from '@/lib/utils';

const PILOT_CATEGORIES = ['Rodines', 'Amarre y cuerdas'];

/**
 * Skeleton page for the EPA en Línea vertical (backend/data_scrapper/epaenlinea_scrapper.py).
 * There is no /products API yet — the backend pivot is still pilot-only and
 * unvalidated against the live site (see epaenlinea_strategy.md), so this
 * page intentionally renders placeholder "skeleton" cards instead of faking
 * real product data. Wire this up to a real fetch once the API exposes a
 * generic products endpoint.
 */
function ProductCardSkeleton({ index }) {
  const { theme } = useTheme();
  return (
    <div
      className={cn(
        'relative overflow-hidden rounded-3xl p-4 space-y-3 animate-pulse',
        theme === 'dark' ? 'bg-white/5 border border-white/10' : 'bg-slate-50 border border-slate-200'
      )}
      style={{ animationDelay: `${index * 80}ms` }}
    >
      <div className={cn(
        'h-28 rounded-2xl flex items-center justify-center',
        theme === 'dark' ? 'bg-white/5' : 'bg-slate-200/60'
      )}>
        <ImageOff size={20} className="opacity-20" />
      </div>
      <div className={cn('h-3 w-4/5 rounded-full', theme === 'dark' ? 'bg-white/10' : 'bg-slate-200')} />
      <div className={cn('h-3 w-1/2 rounded-full', theme === 'dark' ? 'bg-white/10' : 'bg-slate-200')} />
      <div className={cn('h-4 w-1/3 rounded-full', theme === 'dark' ? 'bg-cyan-500/20' : 'bg-cyan-100')} />
    </div>
  );
}

export default function EpaMercadoPage() {
  const { theme } = useTheme();

  return (
    <div className="min-h-screen pb-32 relative overflow-x-hidden">
      <Background />

      <PageHeader
        eyebrow="PILOTO"
        title="EPA"
        accent=" EN LÍNEA"
        subtitle="FERRETERÍA · HOGAR Y CONSTRUCCIÓN"
        backHref="/mercados"
      />

      <main className="max-w-md md:max-w-2xl mx-auto px-6 pt-8 space-y-6">
        <div
          className={cn(
            'flex items-start gap-3 p-4 rounded-2xl border',
            theme === 'dark' ? 'bg-amber-500/10 border-amber-500/20' : 'bg-amber-50 border-amber-200'
          )}
        >
          <AlertTriangle size={18} className="text-amber-500 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <p className="text-xs font-bold uppercase tracking-widest text-amber-500">Esqueleto — sin datos en vivo aún</p>
            <p className="text-xs leading-relaxed text-slate-400">
              Esta vista es un placeholder. El scraper de <span className="font-semibold">cr.epaenlinea.com</span> está
              en fase piloto (2 categorías) y sus selectores no han sido validados contra el sitio real. La API todavía
              no expone un endpoint genérico de productos — cuando eso exista, estas tarjetas se conectarán a datos reales.
            </p>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          {PILOT_CATEGORIES.map((cat) => (
            <Badge key={cat} variant="amber">{cat}</Badge>
          ))}
          <Badge variant="secondary">+ más categorías próximamente</Badge>
        </div>

        <div className="grid grid-cols-2 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <ProductCardSkeleton key={i} index={i} />
          ))}
        </div>
      </main>

      <BottomNav />
    </div>
  );
}
