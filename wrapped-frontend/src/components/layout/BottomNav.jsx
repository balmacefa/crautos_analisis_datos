"use client";

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Home, Compass, Search, LayoutDashboard, Calculator, Globe2 } from 'lucide-react';
import { useTheme } from '@/context/ThemeContext';
import { cn } from '@/lib/utils';

const NavItem = ({ icon: Icon, label, active, href }) => (
  <Link
    href={href}
    className={cn(
      "flex flex-1 min-w-0 flex-col items-center gap-1 transition-all duration-300",
      active ? 'text-cyan-500' : 'text-slate-500 hover:text-slate-300'
    )}
  >
    <div className={cn(
      "p-1.5 rounded-xl transition-all duration-300",
      active ? 'bg-cyan-500/10' : ''
    )}>
      <Icon size={20} className={active ? 'drop-shadow-[0_0_8px_rgba(6,182,212,0.6)]' : ''} />
    </div>
    <span className="text-[8px] font-medium uppercase truncate max-w-full">{label}</span>
  </Link>
);

export const BottomNav = () => {
  const { theme } = useTheme();
  const pathname = usePathname();

  const getActiveTab = () => {
    if (pathname === '/tour') return 'Tour';
    if (pathname === '/search') return 'Explorer';
    if (pathname === '/insights') return 'Insights';
    if (pathname.startsWith('/mercados')) return 'Mercados';
    if (pathname === '/math') return 'Aprender';
    if (pathname === '/') return 'Inicio';
    return '';
  };

  const activeTab = getActiveTab();

  return (
    <nav className={cn(
      "fixed bottom-6 left-1/2 -translate-x-1/2 w-[calc(100%-32px)] max-w-md p-3 rounded-[28px] glass z-50 flex items-center gap-1 px-3 shadow-2xl overflow-hidden",
      theme === 'dark' ? 'glass-dark' : 'bg-white/90 border-slate-200'
    )}>
      {/* Navigation Indicator Background */}
      <div className="absolute inset-0 bg-gradient-to-t from-white/5 to-transparent pointer-events-none" />
      
      <NavItem 
        icon={Home} 
        label="Inicio" 
        active={activeTab === 'Inicio'} 
        href="/"
      />
      <NavItem 
        icon={Compass} 
        label="Tour" 
        active={activeTab === 'Tour'} 
        href="/tour"
      />
      <NavItem 
        icon={Search} 
        label="Explorer" 
        active={activeTab === 'Explorer'} 
        href="/search"
      />
      <NavItem
        icon={LayoutDashboard}
        label="Insights"
        active={activeTab === 'Insights'}
        href="/insights"
      />
      <NavItem
        icon={Globe2}
        label="Mercados"
        active={activeTab === 'Mercados'}
        href="/mercados"
      />
      <NavItem
        icon={Calculator}
        label="Aprender"
        active={activeTab === 'Aprender'}
        href="/math"
      />
    </nav>
  );
};
