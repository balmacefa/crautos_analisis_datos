"use client";

import React from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Car, Package, Globe2, ChevronRight, Sparkles } from 'lucide-react';
import { useTheme } from '@/context/ThemeContext';
import { Badge } from '@/components/ui/Badge';
import { Card } from '@/components/ui/Card';
import { Background } from '@/components/layout/Background';
import { PageHeader } from '@/components/layout/PageHeader';
import { BottomNav } from '@/components/layout/BottomNav';
import { cn } from '@/lib/utils';

/**
 * Skeleton hub for the open-data pivot: one entry point that lists every
 * data vertical (cars today, more Costa Rica sources tomorrow) instead of
 * hard-wiring the whole app to cars. New sources register themselves here
 * as they graduate from the backend pilot stage — see TODO.md.
 */
const VERTICALS = [
  {
    id: 'autos',
    icon: Car,
    title: 'CrAutos',
    subtitle: 'Mercado de vehículos usados',
    description: 'La fuente original del proyecto. Explora, compara y analiza miles de autos publicados en Costa Rica.',
    status: 'LIVE',
    statusVariant: 'emerald',
    href: '/search',
    color: 'cyan',
  },
  {
    id: 'epa',
    icon: Package,
    title: 'EPA en Línea',
    subtitle: 'Ferretería · Hogar y construcción',
    description: 'Primera fuente no-automotriz del pivot. Piloto de 2 categorías mientras se valida el scraper y la data.',
    status: 'PILOTO',
    statusVariant: 'amber',
    href: '/mercados/epa',
    color: 'amber',
  },
  {
    id: 'proximamente',
    icon: Globe2,
    title: 'Próxima fuente',
    subtitle: '¿Qué sitio de Costa Rica sigue?',
    description: 'Este es un espacio abierto: cualquier sitio web costarricense con productos públicos puede sumarse aquí.',
    status: 'PRÓXIMAMENTE',
    statusVariant: 'secondary',
    href: null,
    color: 'slate',
  },
];

function VerticalCard({ vertical, index }) {
  const { theme } = useTheme();
  const Icon = vertical.icon;
  const disabled = !vertical.href;

  const content = (
    <Card
      delay={0.1 * index}
      variant={theme === 'dark' ? 'glass' : 'white'}
      hover={!disabled}
      className={cn(
        'group',
        disabled ? 'opacity-60 border-dashed' : 'cursor-pointer'
      )}
    >
      <div className="relative z-10 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={cn(
              'p-2 rounded-lg',
              theme === 'dark' ? 'bg-white/5 text-white/80' : 'bg-slate-50 text-slate-700'
            )}>
              <Icon size={22} />
            </div>
            <div>
              <h2 className="text-lg font-bold font-display leading-tight">{vertical.title}</h2>
              <p className="text-[10px] uppercase tracking-widest text-slate-400">{vertical.subtitle}</p>
            </div>
          </div>
          <Badge variant={vertical.statusVariant}>{vertical.status}</Badge>
        </div>

        <p className="text-sm leading-relaxed text-slate-400 group-hover:text-slate-300">
          {vertical.description}
        </p>

        {!disabled && (
          <div className="flex items-center gap-1 text-sm font-bold text-cyan-500 dark:text-cyan-400">
            EXPLORAR <ChevronRight size={16} className="group-hover:translate-x-1 transition-transform" />
          </div>
        )}
      </div>
    </Card>
  );

  if (disabled) {
    return <div aria-disabled="true">{content}</div>;
  }

  return (
    <Link href={vertical.href} className="block focus:outline-none focus:ring-2 focus:ring-cyan-500 rounded-[2.5rem]">
      {content}
    </Link>
  );
}

export default function MercadosPage() {
  const { theme } = useTheme();

  return (
    <div className="min-h-screen pb-32 relative overflow-x-hidden">
      <Background />

      <PageHeader
        eyebrow="DATOS ABIERTOS"
        title="MERCADOS"
        accent=" ABIERTOS"
        subtitle="COSTA RICA · TODO EL MERCADO, UNA SOLA FUENTE"
      />

      <main className="max-w-md md:max-w-2xl mx-auto px-6 pt-8 space-y-6">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className={cn(
            'flex items-center gap-3 p-4 rounded-2xl border',
            theme === 'dark' ? 'bg-white/5 border-white/10' : 'bg-slate-50 border-slate-200'
          )}
        >
          <Sparkles size={18} className="text-cyan-400 shrink-0" />
          <p className="text-xs leading-relaxed text-slate-400">
            Este proyecto empezó con autos y está creciendo hacia cualquier
            producto vendido en sitios web de Costa Rica, como una iniciativa
            de datos abiertos para todo el público. Un mundo pequeño hoy, con
            espacio para crecer.
          </p>
        </motion.div>

        <div className="space-y-6">
          {VERTICALS.map((vertical, i) => (
            <VerticalCard key={vertical.id} vertical={vertical} index={i} />
          ))}
        </div>
      </main>

      <BottomNav />
    </div>
  );
}
