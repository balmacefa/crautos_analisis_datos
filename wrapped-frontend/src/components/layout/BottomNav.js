"use client";

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Home, Compass, Search, LayoutDashboard } from 'lucide-react';
import { useTheme } from '@/context/ThemeContext';
import { cn } from '@/lib/utils';

const NavItem = ({ icon: Icon, label, active, href }) => (
  <Link 
    href={href}
    className={cn(
      "flex flex-col items-center gap-1 transition-all duration-300",
      active ? 'text-cyan-500' : 'text-slate-500 hover:text-slate-300'
    )}
  >
    <div className={cn(
      "p-2 rounded-xl transition-all duration-300",
      active ? 'bg-cyan-500/10' : ''
    )}>
      <Icon size={24} className={active ? 'drop-shadow-[0_0_8px_rgba(6,182,212,0.6)]' : ''} />
    </div>
    <span className="text-[10px] font-medium tracking-wide uppercase">{label}</span>
  </Link>
);

export const BottomNav = () => {
  const { theme } = useTheme();
  const pathname = usePathname();

  const getActiveTab = () => {
    if (pathname === '/tour') return 'Tour';
    if (pathname === '/search') return 'Explorer';
    if (pathname === '/insights') return 'Insights';
    if (pathname === '/') return 'Inicio';
    return '';
  };

  const activeTab = getActiveTab();

  return (
    <nav className={cn(
      "fixed bottom-6 left-1/2 -translate-x-1/2 w-[calc(100%-48px)] max-w-md p-4 rounded-[32px] glass z-50 flex justify-between items-center px-8 shadow-2xl overflow-hidden",
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
    </nav>
  );
};
