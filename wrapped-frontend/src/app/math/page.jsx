"use client";
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Calculator,
  ChevronRight,
  ArrowLeft,
  BookA,
  Gamepad2,
  Star,
  Lock,
  Unlock,
  CheckCircle2
} from 'lucide-react';
import Link from 'next/link';
import { useTheme } from '@/context/ThemeContext';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Background } from '@/components/layout/Background';

const CHAPTERS = [
  {
    id: "arithmetic",
    title: "Aritmética Básica",
    description: "Suma, resta, multiplicación y división",
    color: "from-blue-500 to-cyan-500",
    icon: <Calculator className="text-white" size={24} />,
    levels: [
      { id: "arithmetic-1", title: "Nivel 1: Sumas simples", stars: 3, maxStars: 3, unlocked: true },
      { id: "arithmetic-2", title: "Nivel 2: Restas", stars: 1, maxStars: 3, unlocked: true },
      { id: "arithmetic-3", title: "Nivel 3: Multiplicador", stars: 0, maxStars: 3, unlocked: false },
      { id: "arithmetic-4", title: "Nivel 4: El Gran Divisor", stars: 0, maxStars: 3, unlocked: false },
    ]
  },
  {
    id: "fractions",
    title: "Fracciones y Exponentes",
    description: "Domina las partes y las potencias",
    color: "from-purple-500 to-indigo-500",
    icon: <BookA className="text-white" size={24} />,
    levels: [
      { id: "fractions-1", title: "Nivel 1: Mitades y cuartos", stars: 0, maxStars: 3, unlocked: false },
      { id: "fractions-2", title: "Nivel 2: Potencia al cuadrado", stars: 0, maxStars: 3, unlocked: false },
    ]
  },
  {
    id: "geometry",
    title: "Geometría y Ángulos",
    description: "Figuras, áreas y grados",
    color: "from-green-500 to-emerald-500",
    icon: <Gamepad2 className="text-white" size={24} />,
    levels: [
      { id: "geometry-1", title: "Nivel 1: Triángulos mágicos", stars: 0, maxStars: 3, unlocked: false },
      { id: "geometry-2", title: "Nivel 2: Grados y radianes", stars: 0, maxStars: 3, unlocked: false },
    ]
  },
  {
    id: "trigonometry",
    title: "Trigonometría",
    description: "Seno, coseno y tangente",
    color: "from-orange-500 to-red-500",
    icon: <Calculator className="text-white" size={24} />,
    levels: [
      { id: "trigonometry-1", title: "Nivel 1: Seno y Coseno", stars: 0, maxStars: 3, unlocked: false },
      { id: "trigonometry-2", title: "Nivel 2: Identidades", stars: 0, maxStars: 3, unlocked: false },
    ]
  }
];

export default function MathPage() {
  const { theme } = useTheme();

  // viewState can be 'chapters' or 'levels'
  const [viewState, setViewState] = useState('chapters');
  const [selectedChapterId, setSelectedChapterId] = useState(null);

  const activeChapter = CHAPTERS.find(c => c.id === selectedChapterId);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="min-h-screen pb-32 max-w-md mx-auto relative px-6 overflow-x-hidden pt-24"
    >
      <Background />

      {/* Background Floating Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none z-0">
         <motion.div
           animate={{ y: [0, -30, 0], rotate: [0, 15, -15, 0] }}
           transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
           className="absolute top-[10%] left-[5%] opacity-[0.03] dark:opacity-[0.05]"
         >
           <Calculator size={120} />
         </motion.div>
         <motion.div
           animate={{ y: [0, 40, 0], rotate: [0, -20, 20, 0] }}
           transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
           className="absolute top-[40%] right-[10%] opacity-[0.03] dark:opacity-[0.05]"
         >
           <Gamepad2 size={100} />
         </motion.div>
         <motion.div
           animate={{ y: [0, -20, 0], rotate: [0, 30, 0] }}
           transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
           className="absolute bottom-[20%] left-[15%] opacity-[0.03] dark:opacity-[0.05]"
         >
           <Star size={80} />
         </motion.div>
      </div>

      {/* Header temporal o puedes usar el Header global si quisieras */}
      <div className="absolute top-0 left-0 w-full p-6 flex justify-between items-center z-50">
        <Link href="/" className={cn("p-2 rounded-full backdrop-blur-md border", theme === 'dark' ? 'bg-white/5 border-white/10 text-white' : 'bg-black/5 border-black/10 text-slate-800')}>
            <ArrowLeft size={20} />
        </Link>
        <div className="flex items-center gap-2">
            <Badge variant="purple" className="flex items-center gap-1">
                <Star size={12} className="text-yellow-400 fill-yellow-400" />
                <span className="font-bold">120</span>
            </Badge>
        </div>
      </div>

      <main className="space-y-6 relative z-10">
         {viewState === 'chapters' && (
           <AnimatePresence mode="wait">
             <motion.div
               key="chapters-view"
               initial={{ opacity: 0, x: -20 }}
               animate={{ opacity: 1, x: 0 }}
               exit={{ opacity: 0, x: -20 }}
               className="space-y-8"
             >
               <div className="text-center mb-8">
                  <motion.div
                     initial={{ scale: 0.8, opacity: 0 }}
                     animate={{ scale: 1, opacity: 1 }}
                     className="inline-flex items-center justify-center p-4 rounded-full bg-indigo-500/10 text-indigo-500 mb-4"
                  >
                     <Calculator size={48} />
                  </motion.div>
                  <h1 className="text-3xl font-bold font-display mb-2">Math Quest</h1>
                  <p className={cn("text-sm", theme === 'dark' ? 'text-slate-400' : 'text-slate-600')}>
                      Aprende matemáticas jugando. Completa niveles y obtén recompensas.
                  </p>
               </div>

               <div className="space-y-4">
                 {CHAPTERS.map((chapter, idx) => (
                   <motion.div
                     key={chapter.id}
                     initial={{ opacity: 0, y: 20 }}
                     animate={{ opacity: 1, y: 0 }}
                     transition={{ delay: idx * 0.1 }}
                   >
                     <Card
                        variant={theme === 'dark' ? 'glass' : 'white'}
                        className="group cursor-pointer hover:border-indigo-500/50 transition-colors"
                        onClick={() => {
                          setSelectedChapterId(chapter.id);
                          setViewState('levels');
                        }}
                     >
                        <div className="flex items-center gap-4">
                           <div className={cn("p-3 rounded-xl bg-gradient-to-br shadow-lg", chapter.color)}>
                              {chapter.icon}
                           </div>
                           <div className="flex-1">
                              <h3 className="font-bold text-lg">{chapter.title}</h3>
                              <p className={cn("text-xs mt-1", theme === 'dark' ? 'text-slate-400' : 'text-slate-500')}>
                                {chapter.description}
                              </p>
                           </div>
                           <ChevronRight className="text-slate-400 group-hover:text-indigo-400 group-hover:translate-x-1 transition-all" />
                        </div>
                     </Card>
                   </motion.div>
                 ))}
               </div>
             </motion.div>
           </AnimatePresence>
         )}

         {viewState === 'levels' && activeChapter && (
           <AnimatePresence mode="wait">
             <motion.div
               key="levels-view"
               initial={{ opacity: 0, x: 20 }}
               animate={{ opacity: 1, x: 0 }}
               exit={{ opacity: 0, x: 20 }}
               className="space-y-6"
             >
               <div className="flex items-center gap-4 mb-8">
                  <button
                    onClick={() => setViewState('chapters')}
                    className={cn("p-2 rounded-full transition-colors", theme === 'dark' ? 'hover:bg-white/10' : 'hover:bg-black/5')}
                  >
                     <ArrowLeft size={24} />
                  </button>
                  <div>
                    <h2 className="text-2xl font-bold">{activeChapter.title}</h2>
                    <p className={cn("text-xs", theme === 'dark' ? 'text-slate-400' : 'text-slate-500')}>
                      Selecciona un nivel para jugar
                    </p>
                  </div>
               </div>

               <div className="relative pl-6 space-y-8 before:absolute before:inset-0 before:ml-8 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-slate-300 dark:before:via-slate-700 before:to-transparent">
                  {activeChapter.levels.map((level, idx) => (
                    <div key={level.id} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                      <div className={cn("flex items-center justify-center w-10 h-10 rounded-full border-4 shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2",
                        level.unlocked
                          ? theme === 'dark' ? 'bg-indigo-500 border-indigo-900 text-white' : 'bg-indigo-500 border-indigo-200 text-white'
                          : theme === 'dark' ? 'bg-slate-800 border-slate-700 text-slate-500' : 'bg-slate-200 border-slate-300 text-slate-400'
                      )}>
                        {level.unlocked ? <CheckCircle2 size={20} /> : <Lock size={20} />}
                      </div>
                      <div className="w-[calc(100%-3rem)] md:w-[calc(50%-2.5rem)] p-4 rounded-2xl shadow border backdrop-blur-sm bg-white/50 dark:bg-slate-900/50 dark:border-slate-800">
                        <div className="flex flex-col gap-2">
                           <h4 className="font-bold">{level.title}</h4>
                           <div className="flex gap-1">
                             {[...Array(level.maxStars)].map((_, i) => (
                               <Star
                                 key={i}
                                 size={16}
                                 className={cn(
                                   "transition-colors",
                                   i < level.stars
                                     ? "text-yellow-400 fill-yellow-400"
                                     : "text-slate-300 dark:text-slate-700"
                                 )}
                               />
                             ))}
                           </div>
                           <Button
                             variant={level.unlocked ? "primary" : "outline"}
                             className="w-full mt-2"
                             disabled={!level.unlocked}
                           >
                             {level.unlocked ? "JUGAR" : "BLOQUEADO"}
                           </Button>
                        </div>
                      </div>
                    </div>
                  ))}
               </div>
             </motion.div>
           </AnimatePresence>
         )}
      </main>
    </motion.div>
  );
}
