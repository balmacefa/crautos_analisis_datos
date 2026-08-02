"use client";

import React from 'react';
import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * Shared sticky header for internal (desktop-oriented) pages such as
 * Search and Insights. Keeps back-navigation, title and status treatment
 * consistent across pages instead of each page hand-rolling its own.
 */
export const PageHeader = ({ eyebrow, title, accent, subtitle, actions, children, className }) => {
  return (
    <header className={cn(
      "sticky top-0 z-40 glass border-b border-slate-200 dark:border-white/5 backdrop-blur-xl transition-all",
      className
    )}>
      <div className="max-w-[1400px] mx-auto px-4 md:px-6 py-4 md:py-0 md:h-20 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-4 md:gap-6 shrink-0">
          <Link
            href="/"
            className="p-3 bg-slate-100 dark:bg-white/5 hover:bg-slate-200 dark:hover:bg-white/10 rounded-2xl transition-all border border-slate-200 dark:border-white/5 group"
          >
            <ArrowLeft size={18} className="group-hover:-translate-x-1 transition-transform" />
          </Link>
          <div>
            <h1 className="text-xl md:text-2xl font-black italic tracking-tighter uppercase leading-none text-slate-900 dark:text-white">
              {title}{accent && <span className="text-cyan-600 dark:text-cyan-400">{accent}</span>}
            </h1>
            {subtitle && (
              <p className="text-[9px] font-black uppercase tracking-widest text-slate-400 dark:text-white/30 mt-1">
                {subtitle}
              </p>
            )}
          </div>
        </div>

        {actions}
      </div>

      {children}
    </header>
  );
};
