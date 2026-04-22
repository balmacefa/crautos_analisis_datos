"use client"
import React from 'react';
import Link from 'next/link';
import { 
  Search, 
  Compass, 
  BarChart3, 
  ChevronRight,
  Sparkles
} from 'lucide-react';
import { useTheme } from '@/context/ThemeContext';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Card } from '@/components/ui/Card';
import { Background } from '@/components/layout/Background';
import { Header } from '@/components/layout/Header';
import { BottomNav } from '@/components/layout/BottomNav';
import { motion } from 'framer-motion';

export default function App() {
  const { theme } = useTheme();

  return (
    <div className="min-h-screen pb-32 max-w-md mx-auto relative px-6 overflow-x-hidden">
      <Background />
      <Header />

      {/* Main Content */}
      <main className="space-y-6">
        
        {/* Card 1: Interactive Tour */}
        <Link href="/tour" className="block focus:outline-none focus:ring-2 focus:ring-cyan-500 rounded-[2.5rem]">
          <Card 
            delay={0.1} 
            variant={theme === 'dark' ? 'glass' : 'white'}
            className="group cursor-pointer"
          >
            {/* Card background image/effect */}
            <div className="absolute top-0 right-0 w-2/3 h-full overflow-hidden pointer-events-none opacity-40">
               <div className="absolute inset-0 bg-gradient-to-l from-transparent via-transparent to-transparent z-10" />
               <div className="absolute top-0 right-0 w-full h-full transform translate-x-1/4 skew-x-12 bg-gradient-to-r from-cyan-500/20 to-purple-500/20 blur-2xl flex items-center">
                  <img src="/images/tour-bg.png" alt="Tour Background" className="absolute mix-blend-screen opacity-50 object-cover object-center scale-150 rounded-full" />
               </div>
               <motion.div 
                 animate={{ x: [-100, 200] }}
                 transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
                 className="absolute top-1/4 right-0 w-32 h-[1px] bg-cyan-400 shadow-[0_0_15px_#22d3ee] rotate-[-5deg]" 
               />
               <motion.div 
                 animate={{ x: [200, -100] }}
                 transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
                 className="absolute top-1/2 right-0 w-48 h-[1px] bg-purple-400 shadow-[0_0_15px_#a855f7] rotate-[-5deg]" 
               />
            </div>

            <div className="relative z-10 space-y-4 pr-12">
              <div className="flex items-center gap-3">
                <div className={theme === 'dark' ? 'bg-cyan-500/10 text-cyan-400 p-2 rounded-lg' : 'bg-cyan-50 text-cyan-600 p-2 rounded-lg'}>
                  <Compass size={24} />
                </div>
                <h2 className="text-xl font-bold font-display">Interactive Tour</h2>
              </div>
              
              <p className="text-sm leading-relaxed text-slate-400 group-hover:text-slate-300">
                Descubre tu historia con el mercado. Un viaje inmersivo, estilo <span className="font-semibold italic">Spotify Wrapped</span>.
              </p>

              <Button variant="primary" className="mt-2">
                COMENZAR <ChevronRight size={16} className="ml-1 group-hover:translate-x-1 transition-transform" />
              </Button>
            </div>
          </Card>
        </Link>

        {/* Card 2: Market Explorer */}
        <Link href="/search" className="block focus:outline-none focus:ring-2 focus:ring-purple-500 rounded-[2.5rem]">
          <Card 
            delay={0.2} 
            variant={theme === 'dark' ? 'glass' : 'white'}
            className="group cursor-pointer"
          >
            <div className="absolute top-0 right-0 w-2/3 h-full overflow-hidden pointer-events-none opacity-40">
              <div className="absolute -top-12 -right-12 w-48 h-48 bg-purple-500/5 blur-3xl rounded-full" />
              <div className="absolute top-0 right-0 w-full h-full transform translate-x-1/4 skew-x-12 bg-gradient-to-r from-purple-500/20 to-indigo-500/20 blur-2xl flex items-center">
                  <img src="/images/search-bg.png" alt="Search Background" className="absolute mix-blend-screen opacity-50 object-cover object-center scale-150 rounded-full" />
              </div>
            </div>
            
            <div className="relative z-10 space-y-4">
              <div className="flex items-center gap-3">
                <div className={theme === 'dark' ? 'bg-purple-500/10 text-purple-400 p-2 rounded-lg' : 'bg-purple-50 text-purple-600 p-2 rounded-lg'}>
                  <Search size={24} />
                </div>
                <h2 className="text-xl font-bold font-display">Market Explorer</h2>
              </div>

              <div className="flex flex-wrap gap-2">
                <Badge variant="cyan">Top Ventas</Badge>
                <Badge variant="purple">Híbridos</Badge>
              </div>
              
              <p className="text-sm leading-relaxed text-slate-400 group-hover:text-slate-300">
                Busca y compara vehículos con filtros avanzados potenciados por <span className="font-semibold text-purple-400">IA</span>.
              </p>

              <div className={theme === 'dark' ? 'p-3 rounded-xl flex items-center gap-3 bg-white/5 border border-white/10' : 'p-3 rounded-xl flex items-center gap-3 bg-slate-50 border border-slate-200'}>
                <Sparkles size={14} className="text-purple-400" />
                <div className="flex-1 space-y-1">
                  <div className="h-1.5 w-2/3 rounded-full bg-cyan-500/30" />
                  <div className="h-1.5 w-1/2 rounded-full bg-cyan-500/20" />
                </div>
                <Badge className="text-[8px]">AI suggest</Badge>
              </div>

              <Button variant="purple" className="w-full mt-2">
                EXPLORAR <ChevronRight size={16} className="ml-1 group-hover:translate-x-1 transition-transform" />
              </Button>
            </div>
          </Card>
        </Link>
      </main>

      <BottomNav />

      {/* Footer Meta */}
      <footer className="mt-12 text-center pb-8 opacity-40 text-[10px] font-mono tracking-widest uppercase">
        <div className="flex items-center justify-center gap-4">
          <div>v.4.3.0 UNIFIED</div>
          <div>EST. 2026</div>
        </div>
      </footer>
    </div>
  );
}
